"""Kafka 学习脚本共用的配置、序列化和输出函数。"""

from __future__ import annotations

import json
import os
import socket
from typing import Any


# 脚本运行在宿主机，因此连接 docker-compose.yml 暴露出来的 9092 端口。
# 如果以后连接远程 Kafka，可以在命令前设置：
# KAFKA_BOOTSTRAP_SERVERS=host1:9092,host2:9092 uv run ...
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
DEFAULT_TOPIC = os.getenv("KAFKA_TOPIC", "learning-events")


def client_config(client_name: str) -> dict[str, Any]:
    """生成所有客户端共享的最小配置。

    client.id 只用于 Broker 日志和监控，便于区分不同学习脚本；它不会影响
    Consumer Group 的消费进度，消费进度由 consumer 的 group.id 决定。
    """

    return {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "client.id": f"{client_name}-{socket.gethostname()}",
        # 网络或 Broker 暂时不可用时，不让学习脚本无限等待。
        "socket.timeout.ms": 10_000,
    }


def json_to_bytes(value: Any) -> bytes:
    """把 Python 对象编码为 UTF-8 JSON，作为 Kafka 消息体。"""

    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def bytes_to_value(value: bytes | None) -> Any:
    """把 Kafka 消息体还原为 Python 对象；空值代表 tombstone 消息。"""

    if value is None:
        return None
    try:
        return json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # 并不是所有 Kafka 消息都必须是 JSON。解析失败时用 repr 保留原始信息。
        return repr(value)


def decode_key(value: bytes | None) -> str | None:
    """安全解码消息键。消息键通常用于决定分区。"""

    return value.decode("utf-8", errors="replace") if value is not None else None
