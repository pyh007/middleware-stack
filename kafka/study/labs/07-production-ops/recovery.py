"""导出、删除并重放隔离 Topic，验证应用级记录恢复及其边界。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from lab_common import consume_exact, flush_or_fail, json_bytes, json_value, make_producer, recreate_topic


TOPIC = "lab_kafka_recovery"


def main() -> None:
    expected = [{"event_id": f"evt-{number}", "amount": number * 10} for number in range(1, 6)]
    recreate_topic(TOPIC, partitions=1)
    producer = make_producer("recovery-seed")
    for record in expected:
        producer.produce(TOPIC, partition=0, key=record["event_id"].encode(), value=json_bytes(record))
    flush_or_fail(producer)

    exported = consume_exact(TOPIC, len(expected))
    with tempfile.TemporaryDirectory(prefix="kafka-study-recovery-") as directory:
        backup = Path(directory) / "records.jsonl"
        with backup.open("w", encoding="utf-8") as file:
            for message in exported:
                file.write(json.dumps({"key": message.key().decode(), "value": json_value(message)}, ensure_ascii=False) + "\n")
        print(f"[备份] exported_records={len(exported)} temporary_file={backup}")

        recreate_topic(TOPIC, partitions=1)
        restore = make_producer("recovery-restore")
        for line in backup.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            restore.produce(TOPIC, partition=0, key=item["key"].encode(), value=json_bytes(item["value"]))
        flush_or_fail(restore)

    restored = [json_value(message) for message in consume_exact(TOPIC, len(expected))]
    assert restored == expected, restored
    print(f"[恢复证据] restored_records={len(restored)} business_payload_match=true")
    print("[边界] 这是应用级导出/重放，不包含 Topic 配置、ACL、事务状态和 Consumer Group 位点；生产恢复需分别保护并验证。")


if __name__ == "__main__":
    main()
