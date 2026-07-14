"""用 aborted/committed 事务证明 read_committed 与位点原子提交。"""

from __future__ import annotations

import time

from confluent_kafka import Consumer, KafkaException, Producer, TopicPartition

from lab_common import PREFIX, client_config, consume_exact, flush_or_fail, json_bytes, make_producer, recreate_topic


INPUT = "lab_kafka_delivery_input"
OUTPUT = "lab_kafka_delivery_output"
GROUP = "lab_kafka_delivery_processor"


def main() -> None:
    recreate_topic(INPUT, partitions=1)
    recreate_topic(OUTPUT, partitions=1)
    seed = make_producer("delivery-seed")
    for sequence in range(4):
        seed.produce(INPUT, partition=0, key=str(sequence).encode(), value=json_bytes({"sequence": sequence}))
    flush_or_fail(seed)

    consumer_config = client_config("delivery-processor")
    consumer_config.update(
        {
            "group.id": GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "isolation.level": "read_committed",
        }
    )
    consumer = Consumer(consumer_config)
    consumer.subscribe([INPUT])

    tx_config = client_config("transactional-producer")
    tx_config.update(
        {
            "transactional.id": f"{PREFIX}delivery_tx_v1",
            "transaction.timeout.ms": 20_000,
        }
    )
    producer = Producer(tx_config)
    producer.init_transactions(20)

    deadline = time.monotonic() + 15
    first = None
    while first is None and time.monotonic() < deadline:
        candidate = consumer.poll(0.5)
        if candidate is not None:
            if candidate.error():
                raise KafkaException(candidate.error())
            first = candidate
    assert first is not None

    producer.begin_transaction()
    producer.produce(OUTPUT, key=first.key(), value=json_bytes({"sequence": 0, "attempt": "aborted"}))
    producer.send_offsets_to_transaction(
        [TopicPartition(INPUT, 0, first.offset() + 1)], consumer.consumer_group_metadata(), 10
    )
    producer.abort_transaction(10)
    consumer.seek(TopicPartition(INPUT, 0, first.offset()))
    print("[故障注入] 第一笔输出与 offset 一起 abort，随后 seek 回输入位置重试。")

    producer.begin_transaction()
    processed = 0
    last_offset = -1
    deadline = time.monotonic() + 15
    while processed < 4 and time.monotonic() < deadline:
        message = consumer.poll(0.5)
        if message is None:
            continue
        if message.error():
            raise KafkaException(message.error())
        producer.produce(
            OUTPUT,
            key=message.key(),
            value=json_bytes({"sequence": int(message.key()), "attempt": "committed"}),
        )
        last_offset = message.offset()
        processed += 1
    assert processed == 4
    producer.send_offsets_to_transaction(
        [TopicPartition(INPUT, 0, last_offset + 1)], consumer.consumer_group_metadata(), 10
    )
    producer.commit_transaction(10)
    consumer.close()

    dirty = consume_exact(OUTPUT, 5, isolation_level="read_uncommitted")
    clean = consume_exact(OUTPUT, 4, isolation_level="read_committed")
    assert len(dirty) == 5 and len(clean) == 4

    verifier = Consumer({**client_config("offset-verifier"), "group.id": GROUP})
    try:
        committed = verifier.committed([TopicPartition(INPUT, 0)], timeout=10)[0].offset
    finally:
        verifier.close()
    assert committed == 4, committed
    print(f"[证据] read_uncommitted={len(dirty)} read_committed={len(clean)} committed_input_offset={committed}")
    print("[边界] Kafka 事务原子化 Kafka 内的输出与位点；外部数据库仍需 outbox、幂等键或协调方案。")
    print("[变量练习] 将下游改为 read_uncommitted，说明为何会观察到已回滚输出。")


if __name__ == "__main__":
    main()
