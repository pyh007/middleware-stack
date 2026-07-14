#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -f docker-compose.yml)
KEY="lab:redis:05:crash-marker"
VALUE="aof-survived"

printf '%s\n' \
  '[风险] 将向主学习实例写入一个实验键，并对 redis 服务发送 SIGKILL。' \
  '[边界] 命名卷不会删除；6379 会短暂不可用；脚本恢复服务后只删除该实验键。'

"${COMPOSE[@]}" up -d --wait
"${COMPOSE[@]}" exec -T -e REDISCLI_AUTH=redis123456 redis redis-cli SET "$KEY" "$VALUE" >/dev/null
"${COMPOSE[@]}" exec -T -e REDISCLI_AUTH=redis123456 redis redis-cli WAITAOF 1 0 5000 >/dev/null
"${COMPOSE[@]}" kill -s SIGKILL redis
"${COMPOSE[@]}" up -d --wait

RECOVERED=$("${COMPOSE[@]}" exec -T -e REDISCLI_AUTH=redis123456 redis redis-cli --raw GET "$KEY")
if [[ "$RECOVERED" != "$VALUE" ]]; then
  printf '恢复校验失败：期望 %s，实际 %s\n' "$VALUE" "$RECOVERED" >&2
  exit 1
fi
"${COMPOSE[@]}" exec -T -e REDISCLI_AUTH=redis123456 redis redis-cli DEL "$KEY" >/dev/null
printf '崩溃恢复证据：SIGKILL 后键 %s=%s，AOF 数据卷恢复成功。\n' "$KEY" "$RECOVERED"
