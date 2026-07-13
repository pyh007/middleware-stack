"""Redis 端到端学习示例：数据结构、过期时间、事务和发布订阅。"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from typing import Any

import redis
from redis.client import Redis


# 脚本运行在宿主机，所以默认连接 Compose 暴露出来的 localhost:6379。
# 连接其他 Redis 时可通过 REDIS_HOST、REDIS_PORT、REDIS_PASSWORD、REDIS_DB 覆盖。
REDIS_CONFIG: dict[str, Any] = {
    "host": os.getenv("REDIS_HOST", "127.0.0.1"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "password": os.getenv("REDIS_PASSWORD", "redis123456"),
    "db": int(os.getenv("REDIS_DB", "0")),
    # Redis 默认返回 bytes；学习示例开启自动 UTF-8 解码，输出更直观。
    "decode_responses": True,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
}


def show_server_info(client: Redis) -> None:
    """检查连接并显示服务端版本、运行模式和持久化配置。"""

    if not client.ping():
        raise RuntimeError("Redis PING 未返回 PONG")

    server = client.info("server")
    persistence = client.info("persistence")
    print(
        "步骤 1/7：连接成功："
        f"Redis {server['redis_version']}，mode={server['redis_mode']}，"
        f"AOF={persistence['aof_enabled']}"
    )


def learn_strings(client: Redis, prefix: str) -> list[str]:
    """演示 String、原子计数器和 TTL。"""

    message_key = f"{prefix}:message"
    counter_key = f"{prefix}:counter"
    session_key = f"{prefix}:session"

    client.set(message_key, "你好，Redis")
    client.set(counter_key, 0)
    counter = client.incr(counter_key)
    # EX 使键在 60 秒后自动删除，常用于登录会话、验证码和缓存。
    client.set(session_key, "temporary-token", ex=60)

    print(
        "步骤 2/7：String："
        f"message={client.get(message_key)!r}，counter={counter}，"
        f"session TTL={client.ttl(session_key)} 秒"
    )
    return [message_key, counter_key, session_key]


def learn_hash(client: Redis, prefix: str) -> str:
    """演示 Hash：一个 Redis Key 下保存多个字段。"""

    user_key = f"{prefix}:user:1001"
    client.hset(
        user_key,
        mapping={
            "name": "张三",
            "age": 20,
            "city": "上海",
        },
    )
    client.hincrby(user_key, "age", 1)
    print(f"步骤 3/7：Hash：{client.hgetall(user_key)}")
    return user_key


def learn_collections(client: Redis, prefix: str) -> list[str]:
    """演示 List、Set 和 Sorted Set 三种集合结构。"""

    queue_key = f"{prefix}:task-queue"
    tags_key = f"{prefix}:tags"
    ranking_key = f"{prefix}:ranking"

    # List 保持插入顺序，可用于简单队列；LPUSH + RPOP 是先进先出。
    client.rpush(queue_key, "任务A", "任务B", "任务C")
    # Set 自动去重，不保证顺序。
    client.sadd(tags_key, "python", "redis", "python")
    # Sorted Set 为每个成员保存 score，适合排行榜和延迟队列。
    client.zadd(ranking_key, {"张三": 88, "李四": 95, "王五": 91})

    print(f"步骤 4/7：List={client.lrange(queue_key, 0, -1)}")
    print(f"           Set={sorted(client.smembers(tags_key))}")
    print(
        "           Sorted Set="
        f"{client.zrevrange(ranking_key, 0, -1, withscores=True)}"
    )
    return [queue_key, tags_key, ranking_key]


def learn_transaction(client: Redis, prefix: str) -> list[str]:
    """通过 Pipeline 的 transaction=True 演示 MULTI/EXEC 原子执行。"""

    inventory_key = f"{prefix}:inventory"
    order_count_key = f"{prefix}:order-count"
    client.set(inventory_key, 10)
    client.set(order_count_key, 0)

    # execute 前命令只进入队列；EXEC 后两条命令不会被其他客户端写操作插入。
    with client.pipeline(transaction=True) as pipeline:
        pipeline.decr(inventory_key)
        pipeline.incr(order_count_key)
        results = pipeline.execute()

    print(
        "步骤 5/7：事务执行结果="
        f"{results}，库存={client.get(inventory_key)}，"
        f"订单数={client.get(order_count_key)}"
    )
    return [inventory_key, order_count_key]


def learn_pubsub(client: Redis, prefix: str) -> None:
    """在一个脚本中演示订阅、发布和接收实时消息。"""

    channel = f"{prefix}:notifications"
    payload = {"event": "order.created", "order_id": 10001}

    with client.pubsub() as subscriber:
        subscriber.subscribe(channel)

        # 等待订阅确认，确保后续 publish 时订阅者已经就绪。
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            confirmation = subscriber.get_message(timeout=0.2)
            if confirmation and confirmation["type"] == "subscribe":
                break
        else:
            raise RuntimeError("等待 Redis 订阅确认超时")

        receivers = client.publish(channel, json.dumps(payload, ensure_ascii=False))
        message = subscriber.get_message(
            ignore_subscribe_messages=True,
            timeout=2,
        )
        if message is None:
            raise RuntimeError("发布后未收到 Redis Pub/Sub 消息")

    print(
        "步骤 6/7：Pub/Sub："
        f"订阅者数量={receivers}，收到={json.loads(message['data'])}"
    )


def cleanup(client: Redis, keys: list[str]) -> None:
    """只删除本轮演示创建的键，不影响其他学习数据。"""

    deleted = client.delete(*keys)
    print(f"步骤 7/7：已清理本轮 {deleted} 个键。")


def run_demo(should_cleanup: bool) -> None:
    run_id = str(uuid.uuid4())
    prefix = f"learning:{run_id}"
    print(
        "连接 Redis："
        f"{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/"
        f"{REDIS_CONFIG['db']}"
    )

    client = redis.Redis(**REDIS_CONFIG)
    created_keys: list[str] = []
    try:
        show_server_info(client)
        created_keys.extend(learn_strings(client, prefix))
        created_keys.append(learn_hash(client, prefix))
        created_keys.extend(learn_collections(client, prefix))
        created_keys.extend(learn_transaction(client, prefix))
        learn_pubsub(client, prefix)

        if should_cleanup:
            cleanup(client, created_keys)
        else:
            print(
                "步骤 7/7：本轮数据已保留。重建容器后读取这些键，"
                "可验证 AOF/RDB 持久化。"
            )
        print(f"演示完成，本轮 Key 前缀={prefix}")
    finally:
        client.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="演示结束后删除本轮键；默认保留以便观察持久化",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        run_demo(arguments.cleanup)
    except redis.RedisError as exc:
        raise SystemExit(
            "Redis 操作失败。请先执行 "
            "docker compose -f redis/docker-compose.yml up -d，"
            f"然后重试。原始错误：{exc}"
        ) from exc
