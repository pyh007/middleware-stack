"""证明 key 的分区边界与 partition 内 offset 顺序。"""

from __future__ import annotations

from collections import defaultdict

from lab_common import flush_or_fail, json_bytes, make_producer, recreate_topic


TOPIC = "lab_kafka_records_partitions"


def main() -> None:
    recreate_topic(TOPIC, partitions=3)
    delivered: list[tuple[int, str, int, int]] = []
    producer = make_producer("records-partitions")

    def callback(error, message, sequence: int, key: str) -> None:
        if error:
            raise RuntimeError(error)
        delivered.append((sequence, key, message.partition(), message.offset()))

    for sequence in range(1, 13):
        key = ("account-a", "account-b", "account-c")[sequence % 3]
        producer.produce(
            TOPIC,
            key=key.encode(),
            value=json_bytes({"sequence": sequence, "account": key}),
            on_delivery=lambda err, msg, s=sequence, k=key: callback(err, msg, s, k),
        )
    flush_or_fail(producer)

    by_key: dict[str, set[int]] = defaultdict(set)
    by_partition: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for sequence, key, partition, offset in sorted(delivered):
        by_key[key].add(partition)
        by_partition[partition].append((sequence, offset))
        print(f"sequence={sequence:02d} key={key} partition={partition} offset={offset}")

    assert len(delivered) == 12
    assert all(len(partitions) == 1 for partitions in by_key.values())
    for partition, records in by_partition.items():
        offsets = [offset for _, offset in records]
        assert offsets == sorted(offsets), (partition, records)

    print(f"[证据] key->partition={dict(by_key)}")
    print("[结论] 相同 key 稳定进入同一分区；offset 只在各自分区内递增，不构成全局顺序。")
    print("[变量练习] 把分区数从 3 改成 5，先预测 key 映射是否仍保持不变。")


if __name__ == "__main__":
    main()
