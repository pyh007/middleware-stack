"""消费一部分并提交，量化 Consumer Group 的 committed offset 与 lag。"""

from __future__ import annotations

import time

from confluent_kafka import Consumer, KafkaException, TopicPartition

from lab_common import PREFIX, client_config, flush_or_fail, json_bytes, make_producer, recreate_topic, topic_high_watermarks


TOPIC = "lab_kafka_consumer_groups"
GROUP = "lab_kafka_consumer_groups_main"


def new_consumer() -> Consumer:
    config = client_config("consumer-groups")
    config.update(
        {
            "group.id": GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    return Consumer(config)


def consume_and_commit(count: int) -> list[tuple[int, int]]:
    consumer = new_consumer()
    consumed: list[tuple[int, int]] = []
    consumer.subscribe([TOPIC])
    deadline = time.monotonic() + 20
    try:
        while len(consumed) < count and time.monotonic() < deadline:
            message = consumer.poll(0.5)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())
            consumer.commit(message=message, asynchronous=False)
            consumed.append((message.partition(), message.offset()))
    finally:
        consumer.close()
    assert len(consumed) == count, consumed
    return consumed


def committed_and_lag() -> tuple[dict[int, int], dict[int, int]]:
    consumer = new_consumer()
    try:
        committed = consumer.committed(
            [TopicPartition(TOPIC, partition) for partition in range(3)], timeout=10
        )
    finally:
        consumer.close()
    offsets = {position.partition: max(position.offset, 0) for position in committed}
    highs = topic_high_watermarks(TOPIC, range(3))
    lag = {partition: highs[partition] - offsets[partition] for partition in range(3)}
    return offsets, lag


def main() -> None:
    assert GROUP.startswith(PREFIX)
    recreate_topic(TOPIC, partitions=3)
    producer = make_producer("consumer-groups-seed")
    for sequence in range(12):
        producer.produce(
            TOPIC,
            partition=sequence % 3,
            key=f"key-{sequence % 3}".encode(),
            value=json_bytes({"sequence": sequence}),
        )
    flush_or_fail(producer)

    first = consume_and_commit(5)
    offsets1, lag1 = committed_and_lag()
    assert sum(lag1.values()) == 7, (offsets1, lag1, first)
    print(f"[阶段一] processed={first} committed={offsets1} lag={lag1}")

    second = consume_and_commit(7)
    offsets2, lag2 = committed_and_lag()
    assert sum(lag2.values()) == 0, (offsets2, lag2, second)
    print(f"[阶段二] processed={second} committed={offsets2} lag={lag2}")
    print("[结论] lag=各分区 log-end-offset - committed-offset；latest/earliest 只影响无提交位点的组。")
    print("[变量练习] 把第一阶段消费数改为 2，先预测每个分区而不是总量的 lag。")


if __name__ == "__main__":
    main()
