#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -p redis-study-eviction -f study/labs/02-expiration-eviction/docker-compose.eviction.yml)

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

printf '%s\n' \
  '[风险] 将启动 127.0.0.1:6389 的 8MiB 隔离实例并写入约 10MiB 数据。' \
  '[边界] 不连接主学习实例；实例使用 tmpfs，结束后自动删除容器和数据。'
"${COMPOSE[@]}" up -d --wait
PYTHONPATH=study/scripts REDIS_PASSWORD= uv run --project .. python \
  study/labs/02-expiration-eviction/eviction_pressure.py
