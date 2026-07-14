"""Kafka 实验共享原语：只管理 lab_kafka_ 前缀的隔离资源。"""

from __future__ import annotations

import json
import os
import time
import uuid
from collections.abc import Iterable
from typing import Any

from confluent_kafka import Consumer, KafkaException, Message, Producer, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic


BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
PREFIX = "lab_kafka_"


def client_config(name: str) -> dict[str, Any]:
    return {
        "bootstrap.servers": BOOTSTRAP,
        "client.id": f"{name}-{uuid.uuid4().hex[:8]}",
        "socket.timeout.ms": 10_000,
    }


def require_lab_name(name: str) -> None:
    if not name.startswith(PREFIX):
        raise ValueError(f"实验资源必须以 {PREFIX} 开头：{name}")


def admin_client(name: str = "lab-admin") -> AdminClient:
    return AdminClient(client_config(name))


def recreate_topic(
    name: str,
    partitions: int = 1,
    replication_factor: int = 1,
    config: dict[str, str] | None = None,
) -> None:
    """删除并重建一个隔离 Topic；绝不接受非实验前缀。"""

    require_lab_name(name)
    admin = admin_client()
    metadata = admin.list_topics(timeout=10)
    if name in metadata.topics:
        admin.delete_topics([name], operation_timeout=10)[name].result()
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if name not in admin.list_topics(timeout=5).topics:
                break
            time.sleep(0.25)
        else:
            raise RuntimeError(f"等待 Topic 删除超时：{name}")

    admin.create_topics(
        [NewTopic(name, partitions, replication_factor, config=config or {})],
        operation_timeout=10,
    )[name].result()
    print(f"[准备] Topic={name} partitions={partitions} rf={replication_factor}")


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")


def json_value(message: Message) -> Any:
    if message.value() is None:
        return None
    return json.loads(message.value().decode("utf-8"))


def make_producer(name: str, **overrides: Any) -> Producer:
    config = client_config(name)
    config.update({"acks": "all", "enable.idempotence": True})
    config.update(overrides)
    return Producer(config)


def flush_or_fail(producer: Producer, timeout: float = 15) -> None:
    remaining = producer.flush(timeout)
    if remaining:
        raise RuntimeError(f"Producer 超时，仍有 {remaining} 条消息未确认")


def consume_exact(
    topic: str,
    count: int,
    *,
    group: str | None = None,
    isolation_level: str = "read_uncommitted",
    timeout: float = 20,
) -> list[Message]:
    require_lab_name(topic)
    group_id = group or f"{PREFIX}reader_{uuid.uuid4().hex}"
    require_lab_name(group_id)
    config = client_config("lab-consumer")
    config.update(
        {
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "isolation.level": isolation_level,
        }
    )
    consumer = Consumer(config)
    messages: list[Message] = []
    consumer.subscribe([topic])
    deadline = time.monotonic() + timeout
    try:
        while len(messages) < count and time.monotonic() < deadline:
            message = consumer.poll(0.5)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())
            messages.append(message)
    finally:
        consumer.close()
    if len(messages) != count:
        raise AssertionError(f"期望消费 {count} 条，实际 {len(messages)} 条")
    return messages


def topic_high_watermarks(topic: str, partitions: Iterable[int]) -> dict[int, int]:
    consumer = Consumer(
        {
            **client_config("watermark-reader"),
            "group.id": f"{PREFIX}watermark_{uuid.uuid4().hex}",
        }
    )
    try:
        return {
            partition: consumer.get_watermark_offsets(
                TopicPartition(topic, partition), timeout=10, cached=False
            )[1]
            for partition in partitions
        }
    finally:
        consumer.close()
