"""观察异步投递、批处理配置、压缩配置与 Broker 端记录数。"""

from __future__ import annotations

import json
import time

from lab_common import flush_or_fail, json_bytes, make_producer, recreate_topic, topic_high_watermarks


TOPIC = "lab_kafka_producer_reliability"


def main() -> None:
    recreate_topic(TOPIC, partitions=3)
    statistics: list[dict] = []
    delivered: list[tuple[int, int]] = []

    def stats_callback(raw: str) -> int:
        statistics.append(json.loads(raw))
        return 0

    producer = make_producer(
        "producer-reliability",
        **{
            "linger.ms": 50,
            "batch.num.messages": 20,
            "compression.type": "gzip",
            "statistics.interval.ms": 100,
            "stats_cb": stats_callback,
        },
    )
    logical_bytes = 0
    for sequence in range(120):
        payload = json_bytes(
            {"sequence": sequence, "kind": "compressible", "body": "kafka-study-" * 80}
        )
        logical_bytes += len(payload)
        producer.produce(
            TOPIC,
            key=f"customer-{sequence % 12}".encode(),
            value=payload,
            on_delivery=lambda error, message: (
                (_ for _ in ()).throw(RuntimeError(error))
                if error
                else delivered.append((message.partition(), message.offset()))
            ),
        )
    producer.poll(0.2)
    flush_or_fail(producer)
    producer.poll(0.2)

    watermarks = topic_high_watermarks(TOPIC, range(3))
    assert len(delivered) == 120
    assert sum(watermarks.values()) == 120, watermarks
    assert len(set(delivered)) == 120

    sampled_txmsgs = max((snapshot.get("txmsgs", 0) for snapshot in statistics), default=0)
    print("[配置] acks=all enable.idempotence=true linger.ms=50 batch.num.messages=20 compression=gzip")
    print(f"[证据] delivery reports={len(delivered)} partition high watermarks={watermarks}")
    print(f"[证据] logical payload bytes={logical_bytes} sampled_client_txmsgs={sampled_txmsgs}")
    print("[边界] delivery report 证明 Broker 已按 acks 条件确认，不等于下游业务已处理。")
    print("[变量练习] 比较 linger.ms=0 与 50 的吞吐和端到端延迟；生产验证应采集客户端指标。")


if __name__ == "__main__":
    main()
