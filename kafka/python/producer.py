"""学习 Kafka Producer：发送带键的 JSON 消息并观察异步投递结果。"""

from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import KafkaError, Message, Producer

from common import DEFAULT_TOPIC, client_config, json_to_bytes


class DeliveryTracker:
    """统计异步发送结果。

    Producer.produce() 只把消息放入客户端缓冲区，真正的网络发送在后台进行。
    delivery_callback 会在调用 poll() 或 flush() 时被触发，因此不能省略它们。
    """

    def __init__(self) -> None:
        self.succeeded = 0
        self.failed = 0

    def __call__(self, error: KafkaError | None, message: Message) -> None:
        if error is not None:
            self.failed += 1
            print(f"[失败] {error}")
            return

        self.succeeded += 1
        print(
            "[成功] "
            f"topic={message.topic()} partition={message.partition()} "
            f"offset={message.offset()} key={message.key()!r}"
        )


def build_producer() -> Producer:
    config = client_config("learning-producer")
    config.update(
        {
            # acks=all：Leader 要等待所有同步副本确认后才算成功。
            "acks": "all",
            # 幂等生产者可避免因网络重试导致同一条消息被重复写入。
            "enable.idempotence": True,
            # 短暂聚合多条消息，便于观察 Kafka 批量发送机制。
            "linger.ms": 10,
        }
    )
    return Producer(config)


def produce_messages(topic: str, count: int, interval: float) -> None:
    producer = build_producer()
    tracker = DeliveryTracker()

    for sequence in range(1, count + 1):
        # 相同 key 的消息会被稳定地路由到同一分区，因此同一个 key 内可以保序。
        # 这里轮换三个用户，用于在 Kafka UI 中观察 key 与 partition 的关系。
        key = f"user-{sequence % 3}"
        event = {
            "event_id": str(uuid.uuid4()),
            "sequence": sequence,
            "event_type": "learning.message-created",
            "message": f"这是第 {sequence} 条 Kafka 学习消息",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # headers 是独立于消息体的轻量元数据，常用于链路追踪和内容类型。
        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json_to_bytes(event),
            headers={"content-type": "application/json", "source": "python-learning"},
            callback=tracker,
        )

        # poll(0) 不阻塞，只负责及时执行已经完成的投递回调。
        producer.poll(0)
        if interval > 0:
            time.sleep(interval)

    # flush 会等待缓冲区消息完成。返回值是超时后仍未发送的消息数量。
    remaining = producer.flush(timeout=10)
    print(f"发送结束：成功={tracker.succeeded}，失败={tracker.failed}，未完成={remaining}")
    if tracker.failed or remaining:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default=DEFAULT_TOPIC, help="目标 Topic")
    parser.add_argument("--count", type=int, default=5, help="发送消息数量")
    parser.add_argument("--interval", type=float, default=0.2, help="每条消息间隔秒数")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count 必须大于 0")
    if args.interval < 0:
        parser.error("--interval 不能小于 0")
    return args


if __name__ == "__main__":
    arguments = parse_args()
    produce_messages(arguments.topic, arguments.count, arguments.interval)
