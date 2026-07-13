"""学习 Kafka Admin API：列出、创建、查看和删除 Topic。"""

from __future__ import annotations

import argparse

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from common import DEFAULT_TOPIC, client_config


def create_topic(
    admin: AdminClient,
    topic: str,
    partitions: int = 3,
    replication_factor: int = 1,
) -> None:
    """创建 Topic，并等待 Broker 返回最终结果。

    当前 docker-compose 是单 Broker，所以副本数只能为 1。生产集群通常会使用
    多个 Broker 和更高的副本数，以便某台机器故障时数据仍然可用。
    """

    topic_definition = NewTopic(
        topic,
        num_partitions=partitions,
        replication_factor=replication_factor,
    )
    future = admin.create_topics([topic_definition])[topic]
    try:
        future.result()
        print(f"Topic 创建成功：{topic}（分区={partitions}，副本={replication_factor}）")
    except KafkaException as exc:
        error = exc.args[0]
        if isinstance(error, KafkaError) and error.code() == KafkaError.TOPIC_ALREADY_EXISTS:
            print(f"Topic 已存在，无需重复创建：{topic}")
            return
        raise


def list_topics(admin: AdminClient) -> None:
    """读取集群元数据并列出非内部 Topic。"""

    metadata = admin.list_topics(timeout=10)
    topics = sorted(name for name in metadata.topics if not name.startswith("__"))
    print(f"Cluster ID: {metadata.cluster_id or '未知'}")
    print("Topics:")
    for name in topics:
        print(f"  - {name}")
    if not topics:
        print("  （暂无用户 Topic）")


def describe_topic(admin: AdminClient, topic: str) -> None:
    """显示 Topic 的分区、Leader 和副本分配。"""

    metadata = admin.list_topics(topic=topic, timeout=10)
    topic_metadata = metadata.topics.get(topic)
    if topic_metadata is None or topic_metadata.error is not None:
        raise RuntimeError(f"Topic 不存在或元数据读取失败：{topic}")

    print(f"Topic: {topic}")
    for partition_id, partition in sorted(topic_metadata.partitions.items()):
        print(
            f"  partition={partition_id}, leader={partition.leader}, "
            f"replicas={partition.replicas}, isrs={partition.isrs}"
        )


def delete_topic(admin: AdminClient, topic: str) -> None:
    """删除 Topic。此操作同时删除其中的数据，应谨慎执行。"""

    future = admin.delete_topics([topic], operation_timeout=10)[topic]
    future.result()
    print(f"Topic 已删除：{topic}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="列出所有用户 Topic")

    create = subparsers.add_parser("create", help="创建 Topic")
    create.add_argument("--topic", default=DEFAULT_TOPIC)
    create.add_argument("--partitions", type=int, default=3)
    create.add_argument("--replication-factor", type=int, default=1)

    describe = subparsers.add_parser("describe", help="查看 Topic 分区信息")
    describe.add_argument("--topic", default=DEFAULT_TOPIC)

    delete = subparsers.add_parser("delete", help="删除 Topic 及其数据")
    delete.add_argument("--topic", default=DEFAULT_TOPIC)
    delete.add_argument("--yes", action="store_true", help="确认执行不可逆的删除操作")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    admin = AdminClient(client_config("learning-admin"))

    if args.command == "list":
        list_topics(admin)
    elif args.command == "create":
        create_topic(admin, args.topic, args.partitions, args.replication_factor)
    elif args.command == "describe":
        describe_topic(admin, args.topic)
    elif args.command == "delete":
        if not args.yes:
            raise SystemExit("删除会丢失 Topic 数据；确认后请增加 --yes")
        delete_topic(admin, args.topic)


if __name__ == "__main__":
    main()
