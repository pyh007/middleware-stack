"""Redis 学习实验的连接、清理与等待工具。"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import redis
from redis.client import Redis


LAB_PREFIX = "lab:redis:"


def redis_client(**overrides: Any) -> Redis:
    config: dict[str, Any] = {
        "host": os.getenv("REDIS_HOST", "127.0.0.1"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", "redis123456"),
        "db": int(os.getenv("REDIS_DB", "0")),
        "decode_responses": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
    }
    config.update(overrides)
    client = redis.Redis(**config)
    if not client.ping():
        raise RuntimeError("Redis PING 未返回 PONG")
    return client


def cleanup_prefix(client: Redis, prefix: str = LAB_PREFIX) -> int:
    """使用 SCAN 分批删除实验前缀，不触碰其他业务键。"""

    if not prefix.startswith(LAB_PREFIX):
        raise ValueError(f"拒绝清理非实验前缀：{prefix}")
    deleted = 0
    batch: list[str] = []
    for key in client.scan_iter(match=f"{prefix}*", count=200):
        batch.append(key)
        if len(batch) == 200:
            deleted += int(client.unlink(*batch))
            batch.clear()
    if batch:
        deleted += int(client.unlink(*batch))
    return deleted


def wait_until(
    predicate: Callable[[], bool], timeout: float, description: str
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise RuntimeError(f"等待超时：{description}")
