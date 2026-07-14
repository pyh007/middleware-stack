#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."
compose=(docker compose -p kafka-study-cluster -f study/labs/06-replication-kraft/docker-compose.yml)
topic='lab_kafka_failover'

cleanup() {
  status=$?
  trap - EXIT
  echo '[清理] 停止三节点集群并删除实验数据卷。'
  "${compose[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT

echo '[1/7] 启动独立三节点 KRaft 集群（端口 19092/19093/19094）。'
"${compose[@]}" up -d --wait

echo '[2/7] 创建 RF=3、min.insync.replicas=2 的隔离 Topic。'
"${compose[@]}" exec -T broker1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server broker1:29092 --create --topic "$topic" --partitions 1 \
  --replication-factor 3 --config min.insync.replicas=2

describe() {
  "${compose[@]}" exec -T "$client" /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server broker1:29092,broker2:29092,broker3:29092 --describe --topic "$topic" 2>/dev/null | tr -d '\r'
}

client=broker1
before=$(describe)
printf '%s\n' "$before"
leader=$(printf '%s\n' "$before" | awk '{for (i=1;i<=NF;i++) if ($i=="Leader:") {print $(i+1); exit}}')
[[ "$leader" =~ ^[123]$ ]]
echo "[3/7] 初始 Leader=${leader}；写入故障前记录。"
printf 'k1:before-1\nk2:before-2\n' | "${compose[@]}" exec -T broker1 \
  /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server broker1:29092 \
  --topic "$topic" --reader-property parse.key=true --reader-property key.separator=: --command-property acks=all

echo "[4/7] 显式停止 Leader broker${leader}。"
"${compose[@]}" stop "broker$leader"
if [[ "$leader" == 1 ]]; then client=broker2; else client=broker1; fi

after=''
for _ in {1..30}; do
  after=$(describe || true)
  new_leader=$(printf '%s\n' "$after" | awk '{for (i=1;i<=NF;i++) if ($i=="Leader:") {print $(i+1); exit}}')
  if [[ "$new_leader" =~ ^[123]$ && "$new_leader" != "$leader" ]]; then break; fi
  sleep 1
done
[[ "$new_leader" =~ ^[123]$ && "$new_leader" != "$leader" ]]
printf '%s\n' "$after"
echo "[5/7] 新 Leader=${new_leader}；用剩余节点写入故障后记录。"
printf 'k3:after-1\nk4:after-2\n' | "${compose[@]}" exec -T "$client" \
  /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server broker1:29092,broker2:29092,broker3:29092 --topic "$topic" \
  --reader-property parse.key=true --reader-property key.separator=: --command-property acks=all

echo '[6/7] 从头读取 4 条，验证已确认记录在 Leader 切换后仍存在。'
records=$("${compose[@]}" exec -T "$client" /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server broker1:29092,broker2:29092,broker3:29092 --topic "$topic" \
  --from-beginning --max-messages 4 --timeout-ms 15000 --formatter-property print.key=true | tr -d '\r')
printf '%s\n' "$records"
[[ $(printf '%s\n' "$records" | grep -cE 'before-|after-') -eq 4 ]]

echo "[7/7] 重启 broker${leader}，等待 ISR 恢复为 3。"
"${compose[@]}" start "broker$leader"
for _ in {1..40}; do
  recovered=$(describe || true)
  if printf '%s\n' "$recovered" | grep -Eq 'Isr: ([0-9]+,){2}[0-9]+'; then break; fi
  sleep 1
done
printf '%s\n' "$recovered"
printf '%s\n' "$recovered" | grep -Eq 'Isr: ([0-9]+,){2}[0-9]+'
echo "[证据] Leader ${leader} -> ${new_leader}；停一台后仍可 acks=all 写入；4 条记录完整；ISR 已恢复。"
