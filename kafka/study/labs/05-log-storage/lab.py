"""滚动多个日志段，并用 keyed records/tombstone 重建压缩主题的逻辑状态。"""

from __future__ import annotations

import subprocess

from lab_common import consume_exact, flush_or_fail, json_bytes, json_value, make_producer, recreate_topic


SEGMENT_TOPIC = "lab_kafka_log_storage"
COMPACT_TOPIC = "lab_kafka_log_compaction"


def inspect_segment_files() -> list[str]:
    command = (
        "for file in /var/lib/kafka/data/lab_kafka_log_storage-0/*.log; "
        "do bytes=$(wc -c < \"$file\"); echo \"$(basename \"$file\") $bytes bytes\"; done"
    )
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "exec", "-T", "kafka", "sh", "-lc", command],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    for line in lines:
        print(f"[段文件] {line}")
    return lines


def main() -> None:
    recreate_topic(
        SEGMENT_TOPIC,
        partitions=1,
        config={"cleanup.policy": "delete", "segment.bytes": "1048576", "retention.ms": "3600000"},
    )
    producer = make_producer("segment-writer", **{"linger.ms": 0, "batch.num.messages": 10})
    for sequence in range(4000):
        producer.produce(
            SEGMENT_TOPIC,
            partition=0,
            key=f"key-{sequence % 20}".encode(),
            value=json_bytes({"sequence": sequence, "body": f"{sequence:08d}-" + "x" * 700}),
        )
    flush_or_fail(producer)
    segments = inspect_segment_files()
    assert len(segments) >= 2, segments

    recreate_topic(
        COMPACT_TOPIC,
        partitions=1,
        config={"cleanup.policy": "compact", "segment.bytes": "1048576", "min.cleanable.dirty.ratio": "0.01"},
    )
    compact = make_producer("compact-writer")
    events = [
        (b"user-1", {"version": 1, "name": "old"}),
        (b"user-1", {"version": 2, "name": "new"}),
        (b"user-2", {"version": 1, "name": "temporary"}),
        (b"user-2", None),
    ]
    for key, value in events:
        compact.produce(COMPACT_TOPIC, partition=0, key=key, value=None if value is None else json_bytes(value))
    flush_or_fail(compact)

    physical = consume_exact(COMPACT_TOPIC, 4)
    logical: dict[str, object] = {}
    for message in physical:
        key = message.key().decode()
        value = json_value(message)
        print(f"[压缩记录] offset={message.offset()} key={key} value={value}")
        if value is None:
            logical.pop(key, None)
        else:
            logical[key] = value
    assert logical == {"user-1": {"name": "new", "version": 2}}, logical

    print(f"[证据] segment_count={len(segments)} logical_state={logical}")
    print("[边界] compaction 是异步物理清理；最新值与 tombstone 语义可确定，但旧记录不会立即消失。")
    print("[变量练习] 把 segment.bytes 调大后重跑，比较段数量与文件大小。")


if __name__ == "__main__":
    main()
