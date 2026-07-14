"""用两个真实 Consumer 观察同一 Group 的分区再分配。"""

from __future__ import annotations

import threading
import time

from confluent_kafka import Consumer

from lab_common import client_config


TOPIC = "lab_kafka_consumer_groups"
GROUP = "lab_kafka_consumer_groups_rebalance"


def run_member(name: str, lifetime: float, assignments: dict[str, list[list[int]]]) -> None:
    config = client_config(name)
    config.update({"group.id": GROUP, "auto.offset.reset": "earliest"})
    consumer = Consumer(config)

    def on_assign(_, partitions) -> None:
        current = sorted(partition.partition for partition in partitions)
        assignments[name].append(current)
        print(f"[分配] member={name} partitions={current}")

    consumer.subscribe([TOPIC], on_assign=on_assign)
    deadline = time.monotonic() + lifetime
    try:
        while time.monotonic() < deadline:
            consumer.poll(0.2)
    finally:
        consumer.close()


def main() -> None:
    assignments: dict[str, list[list[int]]] = {"member-a": [], "member-b": []}
    first = threading.Thread(target=run_member, args=("member-a", 8, assignments))
    first.start()
    time.sleep(2)
    second = threading.Thread(target=run_member, args=("member-b", 4, assignments))
    second.start()
    second.join()
    first.join()

    assert assignments["member-a"] and assignments["member-b"], assignments
    assert any(len(parts) < 3 for parts in assignments["member-a"]), assignments
    print(f"[证据] assignment history={assignments}")
    print("[结论] Group 成员变化触发再均衡；暂停窗口取决于协议、分配器和处理模型。")


if __name__ == "__main__":
    main()
