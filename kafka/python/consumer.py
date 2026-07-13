"""学习 Kafka Consumer：订阅 Topic、读取消息并手动提交 Offset。"""

from __future__ import annotations

import argparse

from confluent_kafka import Consumer, KafkaException, Message

from common import DEFAULT_TOPIC, bytes_to_value, client_config, decode_key


def print_message(message: Message) -> None:
    """完整打印消息位置、键、头和 JSON 内容。"""

    # offset 只在一个 partition 内递增；Kafka 不保证不同 partition 之间的全局顺序。
    print(
        f"\n收到消息：topic={message.topic()} partition={message.partition()} "
        f"offset={message.offset()} timestamp={message.timestamp()[1]}"
    )
    print(f"  key: {decode_key(message.key())}")
    print(f"  headers: {message.headers() or []}")
    print(f"  value: {bytes_to_value(message.value())}")


def consume(topic: str, group_id: str, from_beginning: bool, max_messages: int) -> None:
    config = client_config("learning-consumer")
    config.update(
        {
            # 同一 group.id 下的多个 Consumer 会分担分区，而不是每人收到全部消息。
            "group.id": group_id,
            # earliest/latest 只在该消费者组没有已提交 Offset 时生效。
            "auto.offset.reset": "earliest" if from_beginning else "latest",
            # 关闭自动提交，处理成功后由代码明确提交，便于理解至少一次消费语义。
            "enable.auto.commit": False,
        }
    )
    consumer = Consumer(config)
    received = 0

    try:
        # subscribe 是“订阅”：Broker 会根据消费者组成员变化自动分配分区。
        consumer.subscribe([topic])
        print(
            f"开始订阅 topic={topic} group={group_id}。"
            "按 Ctrl+C 停止；可以另开终端运行 producer.py。"
        )

        while max_messages == 0 or received < max_messages:
            # poll 会同时完成心跳、组协调和拉取消息。None 表示本次等待期间没有新消息。
            message = consumer.poll(timeout=1.0)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())

            print_message(message)

            # 实际项目应先完成业务处理，再提交 Offset。若处理失败则不要提交，重启后可重试。
            consumer.commit(message=message, asynchronous=False)
            print(f"  已提交下一消费位置：offset={message.offset() + 1}")
            received += 1
    except KeyboardInterrupt:
        print("\n收到停止信号，准备安全退出。")
    finally:
        # close 会退出消费者组并触发再均衡；务必放在 finally 中执行。
        consumer.close()
        print(f"Consumer 已关闭，本次共处理 {received} 条消息。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument("--group", default="learning-group", help="消费者组 ID")
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="新消费者组从最早消息开始；已有组仍从其已提交 Offset 继续",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=0,
        help="消费指定数量后退出；0 表示持续订阅",
    )
    args = parser.parse_args()
    if args.max_messages < 0:
        parser.error("--max-messages 不能小于 0")
    return args


if __name__ == "__main__":
    arguments = parse_args()
    consume(arguments.topic, arguments.group, arguments.from_beginning, arguments.max_messages)
