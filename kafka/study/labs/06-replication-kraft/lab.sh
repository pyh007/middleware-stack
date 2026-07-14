#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."
compose=(docker compose -f docker-compose.yml)
topic='lab_kafka_replication_kraft'

"${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --delete --topic "$topic" --if-exists
"${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create --topic "$topic" --partitions 3 --replication-factor 1

echo '[KRaft quorum]'
"${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-metadata-quorum.sh \
  --bootstrap-server localhost:9092 describe --status

echo '[Topic replicas/ISR]'
description=$("${compose[@]}" exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic "$topic" | tr -d '\r')
printf '%s\n' "$description"

partition_lines=$(printf '%s\n' "$description" | grep -c 'Partition:')
rf_one_lines=$(printf '%s\n' "$description" | grep 'Partition:' | grep -c 'Replicas: 1')
[[ "$partition_lines" -eq 3 && "$rf_one_lines" -eq 3 ]]

echo '[证据] 当前默认环境是单 Broker、三分区、RF=1、ISR={1}。'
echo '[边界] acks=all 在 RF=1 时仍只有一份数据，不能提供机器故障冗余。'
echo '[变量练习] 显式运行 make -C kafka cluster-failover，观察 RF=3 的 Leader 与 ISR 变化。'
