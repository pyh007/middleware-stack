#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$ROOT"
COMPOSE=(docker compose -p redis-study-cluster -f study/labs/06-replication-cluster/docker-compose.cluster.yml)

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

printf '%s\n' \
  '[风险] 将启动 3 个无副本的隔离 Cluster 节点，创建集群并迁移 1 个槽。' \
  '[边界] 不暴露宿主机端口，数据写入 tmpfs；3 主 0 从不具备生产高可用性。'
"${COMPOSE[@]}" up -d --wait

IP1=$("${COMPOSE[@]}" exec -T cluster-1 getent hosts cluster-1 | awk '{print $1}')
IP2=$("${COMPOSE[@]}" exec -T cluster-1 getent hosts cluster-2 | awk '{print $1}')
IP3=$("${COMPOSE[@]}" exec -T cluster-1 getent hosts cluster-3 | awk '{print $1}')
"${COMPOSE[@]}" exec -T cluster-1 redis-cli --cluster create \
  "$IP1:6379" "$IP2:6379" "$IP3:6379" --cluster-replicas 0 --cluster-yes >/dev/null

for _ in $(seq 1 40); do
  STATE=$("${COMPOSE[@]}" exec -T cluster-1 redis-cli --raw CLUSTER INFO | sed -n 's/^cluster_state://p' | tr -d '\r')
  [[ "$STATE" == "ok" ]] && break
  sleep 0.25
done
if [[ "$STATE" != "ok" ]]; then
  printf 'Cluster 未达到 ok，当前状态=%s\n' "$STATE" >&2
  exit 1
fi

TAG=$(python3 study/labs/06-replication-cluster/find_slot_zero.py)
KEY="lab:redis:06:cluster:{$TAG}:marker"
"${COMPOSE[@]}" exec -T cluster-1 redis-cli -c -h "$IP1" SET "$KEY" before-reshard >/dev/null
SOURCE_ID=$("${COMPOSE[@]}" exec -T cluster-1 redis-cli --raw CLUSTER MYID)
TARGET_ID=$("${COMPOSE[@]}" exec -T cluster-2 redis-cli --raw CLUSTER MYID)
BEFORE_OWNER=$("${COMPOSE[@]}" exec -T cluster-1 redis-cli --raw CLUSTER NODES | awk '$9 ~ /(^|,)0(-|$)/ {print $1}')

"${COMPOSE[@]}" exec -T cluster-1 redis-cli --cluster reshard "$IP1:6379" \
  --cluster-from "$SOURCE_ID" --cluster-to "$TARGET_ID" --cluster-slots 1 --cluster-yes >/dev/null

AFTER_OWNER=$("${COMPOSE[@]}" exec -T cluster-2 redis-cli --raw CLUSTER NODES | awk '$9 ~ /(^|,)0(-|$)/ {print $1}')
VALUE=$("${COMPOSE[@]}" exec -T cluster-2 redis-cli -c --raw GET "$KEY")
if [[ "$BEFORE_OWNER" != "$SOURCE_ID" || "$AFTER_OWNER" != "$TARGET_ID" || "$VALUE" != "before-reshard" ]]; then
  printf '槽迁移校验失败：before=%s after=%s value=%s\n' "$BEFORE_OWNER" "$AFTER_OWNER" "$VALUE" >&2
  exit 1
fi
printf 'Cluster 证据：state=ok，slot 0 从 %s 迁移到 %s，键值仍为 %s。\n' \
  "${SOURCE_ID:0:8}" "${TARGET_ID:0:8}" "$VALUE"
