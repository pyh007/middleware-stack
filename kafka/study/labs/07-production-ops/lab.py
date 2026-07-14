"""生成受控 lag，并从元数据、消费位点和磁盘分布完成一次巡检。"""

from __future__ import annotations

import json
import subprocess
import time

from confluent_kafka import Consumer, KafkaException, TopicPartition

from lab_common import admin_client, client_config, flush_or_fail, json_bytes, make_producer, recreate_topic, topic_high_watermarks


TOPIC = "lab_kafka_production_ops"
GROUP = "lab_kafka_production_ops_group"


def main() -> None:
    recreate_topic(TOPIC, partitions=3)
    producer = make_producer("ops-seed")
    for sequence in range(20):
        producer.produce(TOPIC, partition=sequence % 3, key=str(sequence % 5).encode(), value=json_bytes({"sequence": sequence}))
    flush_or_fail(producer)

    consumer = Consumer(
        {
            **client_config("ops-consumer"),
            "group.id": GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
    processed = 0
    deadline = time.monotonic() + 15
    try:
        while processed < 8 and time.monotonic() < deadline:
            message = consumer.poll(0.5)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())
            consumer.commit(message=message, asynchronous=False)
            processed += 1
    finally:
        consumer.close()
    assert processed == 8

    verifier = Consumer({**client_config("ops-verifier"), "group.id": GROUP})
    try:
        positions = verifier.committed([TopicPartition(TOPIC, p) for p in range(3)], timeout=10)
    finally:
        verifier.close()
    committed = {item.partition: max(item.offset, 0) for item in positions}
    highs = topic_high_watermarks(TOPIC, range(3))
    lag = {p: highs[p] - committed[p] for p in range(3)}
    assert sum(lag.values()) == 12, (committed, highs, lag)

    metadata = admin_client("ops-admin").list_topics(topic=TOPIC, timeout=10)
    brokers = sorted(metadata.brokers)
    command = [
        "docker", "compose", "-f", "docker-compose.yml", "exec", "-T", "kafka",
        "/opt/kafka/bin/kafka-log-dirs.sh", "--bootstrap-server", "localhost:9092",
        "--describe", "--topic-list", TOPIC,
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout[result.stdout.index("{"):])
    partition_sizes = [
        partition["size"]
        for broker in payload["brokers"]
        for log_dir in broker["logDirs"]
        for partition in log_dir["partitions"]
    ]

    print(f"[元数据] brokers={brokers} partitions={len(metadata.topics[TOPIC].partitions)}")
    print(f"[消费] committed={committed} log_end={highs} lag={lag}")
    print(f"[磁盘] partition_sizes={partition_sizes} total_bytes={sum(partition_sizes)}")
    print("[诊断顺序] 影响范围 -> 生产/消费速率 -> 分区 lag -> Group 状态 -> Broker/磁盘/网络。")
    print("[安全边界] 当前 PLAINTEXT 仅监听 127.0.0.1；生产必须启用认证、加密、ACL 与凭据轮换。")


if __name__ == "__main__":
    main()
