#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -p redis-study-sentinel -f study/labs/06-replication-cluster/docker-compose.sentinel.yml)
KEY="lab:redis:06:sentinel-marker"

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

printf '%s\n' \
  '[风险] 将启动 1 主 1 从 1 Sentinel 的隔离拓扑，并停止原主节点。' \
  '[边界] 拓扑不暴露宿主机端口；quorum=1 只为教学，生产至少部署 3 个 Sentinel。'
"${COMPOSE[@]}" up -d --wait
REPLICA_IP=$("${COMPOSE[@]}" exec -T sentinel getent hosts replica | awk '{print $1}')
"${COMPOSE[@]}" exec -T primary redis-cli SET "$KEY" before-failover >/dev/null

for _ in $(seq 1 50); do
  VALUE=$("${COMPOSE[@]}" exec -T replica redis-cli --raw GET "$KEY" 2>/dev/null || true)
  [[ "$VALUE" == "before-failover" ]] && break
  sleep 0.1
done
if [[ "${VALUE:-}" != "before-failover" ]]; then
  printf '复制校验失败：副本未读到 %s\n' "$KEY" >&2
  exit 1
fi

BEFORE=$("${COMPOSE[@]}" exec -T primary redis-cli --raw INFO replication | sed -n 's/^master_repl_offset://p' | tr -d '\r')
REPLICA_OFFSET=$("${COMPOSE[@]}" exec -T replica redis-cli --raw INFO replication | sed -n 's/^slave_repl_offset://p' | tr -d '\r')
printf '复制证据：主 offset=%s，副本 offset=%s，键已同步。\n' "$BEFORE" "$REPLICA_OFFSET"

"${COMPOSE[@]}" stop primary >/dev/null
PROMOTED=0
for _ in $(seq 1 120); do
  ROLE=$("${COMPOSE[@]}" exec -T replica redis-cli --raw ROLE 2>/dev/null | sed -n '1p' || true)
  if [[ "$ROLE" == "master" ]]; then
    PROMOTED=1
    break
  fi
  sleep 0.25
done
if [[ "$PROMOTED" != 1 ]]; then
  "${COMPOSE[@]}" logs sentinel >&2
  printf 'Sentinel 未在 30 秒内提升副本。\n' >&2
  exit 1
fi

"${COMPOSE[@]}" exec -T replica redis-cli SET "$KEY" after-failover >/dev/null
for _ in $(seq 1 80); do
  DISCOVERED_HOST=$("${COMPOSE[@]}" exec -T sentinel redis-cli --raw -p 26379 SENTINEL get-master-addr-by-name lab-primary 2>/dev/null | sed -n '1p' || true)
  [[ "$DISCOVERED_HOST" == "replica" || "$DISCOVERED_HOST" == "$REPLICA_IP" ]] && break
  sleep 0.1
done
if [[ "$DISCOVERED_HOST" != "replica" && "$DISCOVERED_HOST" != "$REPLICA_IP" ]]; then
  printf 'Sentinel 发现地址未切换到 replica，当前=%s\n' "$DISCOVERED_HOST" >&2
  exit 1
fi
DISCOVERED=$("${COMPOSE[@]}" exec -T sentinel redis-cli --raw -p 26379 SENTINEL get-master-addr-by-name lab-primary | paste -sd ':' -)
printf '故障转移证据：replica 已提升为 master，Sentinel 当前主节点=%s，可写值=after-failover。\n' "$DISCOVERED"

"${COMPOSE[@]}" start primary >/dev/null
for _ in $(seq 1 80); do
  ROLE=$("${COMPOSE[@]}" exec -T primary redis-cli --raw ROLE 2>/dev/null | sed -n '1p' || true)
  [[ "$ROLE" == "slave" ]] && break
  sleep 0.25
done
if [[ "$ROLE" != "slave" ]]; then
  printf '原主恢复后未成为新主的副本，当前 role=%s\n' "$ROLE" >&2
  exit 1
fi
printf '回归证据：原主恢复后角色=%s，避免双主继续写入。\n' "$ROLE"
