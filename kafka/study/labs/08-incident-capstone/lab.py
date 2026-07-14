"""综合复现积压、重复业务事件与“Kafka 丢数”声称，并用位点证据归因。"""

from __future__ import annotations

import time

from confluent_kafka import Consumer, KafkaException, TopicPartition

from lab_common import client_config, flush_or_fail, json_bytes, json_value, make_producer, recreate_topic, topic_high_watermarks


TOPIC = "lab_kafka_incident_capstone"
GROUP = "lab_kafka_incident_capstone_group"


def consumer() -> Consumer:
    return Consumer(
        {
            **client_config("capstone-consumer"),
            "group.id": GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def consume_batch(count: int, seen: set[str]) -> tuple[int, int]:
    instance = consumer()
    instance.subscribe([TOPIC])
    records = duplicates = 0
    deadline = time.monotonic() + 20
    try:
        while records < count and time.monotonic() < deadline:
            message = instance.poll(0.5)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())
            event_id = json_value(message)["event_id"]
            if event_id in seen:
                duplicates += 1
            else:
                seen.add(event_id)
            instance.commit(message=message, asynchronous=False)
            records += 1
    finally:
        instance.close()
    assert records == count
    return records, duplicates


def lag_snapshot() -> tuple[dict[int, int], dict[int, int], int]:
    verifier = consumer()
    try:
        positions = verifier.committed([TopicPartition(TOPIC, p) for p in range(3)], timeout=10)
    finally:
        verifier.close()
    committed = {item.partition: max(item.offset, 0) for item in positions}
    highs = topic_high_watermarks(TOPIC, range(3))
    total_lag = sum(highs[p] - committed[p] for p in range(3))
    return committed, highs, total_lag


def main() -> None:
    recreate_topic(TOPIC, partitions=3)
    producer = make_producer("capstone-producer")
    records = [{"event_id": f"evt-{number:02d}", "amount": number} for number in range(18)]
    records.extend([records[3], records[11]])
    for sequence, record in enumerate(records):
        producer.produce(
            TOPIC,
            partition=sequence % 3,
            key=record["event_id"].encode(),
            value=json_bytes(record),
        )
    flush_or_fail(producer)
    assert sum(topic_high_watermarks(TOPIC, range(3)).values()) == 20

    seen: set[str] = set()
    first_count, first_duplicates = consume_batch(7, seen)
    committed1, highs1, lag1 = lag_snapshot()
    assert lag1 == 13
    print(f"[事故时刻] processed={first_count} committed={committed1} log_end={highs1} lag={lag1}")

    second_count, second_duplicates = consume_batch(13, seen)
    committed2, highs2, lag2 = lag_snapshot()
    total_duplicates = first_duplicates + second_duplicates
    assert lag2 == 0
    assert len(seen) == 18 and total_duplicates == 2

    print(f"[恢复后] processed={first_count + second_count} unique_events={len(seen)} duplicates={total_duplicates}")
    print(f"[位点证据] committed={committed2} log_end={highs2} lag={lag2}")
    print("[根因结论] Kafka 中有 20 条记录且全部消费；业务只有 18 个 event_id，差异来自上游重复，不是 Broker 丢数。")
    print("[处置] 先按 partition/offset/event_id 建证据链，再决定扩容、暂停重试或业务幂等，禁止直接 reset offset。")


if __name__ == "__main__":
    main()
