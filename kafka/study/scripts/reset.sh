#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
compose=(docker compose -f docker-compose.yml)
prefix='lab_kafka_'

topics=$("${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list | tr -d '\r')
while IFS= read -r topic; do
  if [[ "$topic" == "$prefix"* ]]; then
    echo "[reset] 删除 Topic: $topic"
    "${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
      --bootstrap-server localhost:9092 --delete --topic "$topic" </dev/null
  fi
done <<< "$topics"

groups=$("${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list | tr -d '\r')
while IFS= read -r group; do
  if [[ "$group" == "$prefix"* ]]; then
    echo "[reset] 删除 Consumer Group: $group"
    "${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-consumer-groups.sh \
      --bootstrap-server localhost:9092 --delete --group "$group" >/dev/null </dev/null || \
      echo "[reset] Group 仍活跃或尚在协调，保留：$group"
  fi
done <<< "$groups"

echo "[reset] 完成；非 ${prefix} 前缀资源未受影响。"
