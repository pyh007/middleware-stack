"""一键运行 Topic 创建、消息发送和消息消费的端到端学习演示。"""

from __future__ import annotations

import argparse
import time
import uuid

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient

from admin import create_topic
from common import DEFAULT_TOPIC, bytes_to_value, client_config, json_to_bytes


def run_demo(topic: str, count: int) -> None:
    # Topic 可能保留了上次演示的消息。run_id 用来标记本轮数据，确保重复运行时
    # 只把本轮生产的消息计入结果，同时仍能观察消费者扫描历史记录的过程。
    run_id = str(uuid.uuid4())

    print("步骤 1/3：创建 Topic")
    create_topic(AdminClient(client_config("demo-admin")), topic)

    print("\n步骤 2/3：生产消息")
    producer_config = client_config("demo-producer")
    producer_config.update({"acks": "all", "enable.idempotence": True})
    producer = Producer(producer_config)
    for number in range(1, count + 1):
        producer.produce(
            topic,
            key=f"demo-key-{number % 2}".encode(),
            value=json_to_bytes(
                {"run_id": run_id, "number": number, "text": f"端到端消息 {number}"}
            ),
        )
    if producer.flush(10) != 0:
        raise RuntimeError("生产者等待超时，仍有消息未发送")
    print(f"已发送 {count} 条消息。")

    print("\n步骤 3/3：使用全新的消费者组从头消费")
    # 每次生成新的 group.id，确保没有历史 Offset；配合 earliest 可读到刚发送的消息。
    consumer_config = client_config("demo-consumer")
    consumer_config.update(
        {
            "group.id": f"learning-demo-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])
    deadline = time.monotonic() + 15
    received = 0
    try:
        while received < count and time.monotonic() < deadline:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise RuntimeError(message.error())

            value = bytes_to_value(message.value())
            # 新消费者组从 earliest 开始时会先读到旧数据；旧数据同样提交 Offset，
            # 但不计入本轮数量，直到找到携带当前 run_id 的消息。
            consumer.commit(message=message, asynchronous=False)
            if not isinstance(value, dict) or value.get("run_id") != run_id:
                continue

            received += 1
            print(
                f"[{received}/{count}] partition={message.partition()} "
                f"offset={message.offset()} value={value}"
            )
    finally:
        consumer.close()

    if received != count:
        raise RuntimeError(f"演示超时：期望 {count} 条，实际收到 {received} 条")
    print("\n演示完成：Topic、Producer、Consumer 和 Offset 提交均工作正常。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count 必须大于 0")
    return args


if __name__ == "__main__":
    arguments = parse_args()
    run_demo(arguments.topic, arguments.count)
