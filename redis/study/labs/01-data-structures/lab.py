#!/usr/bin/env python3
"""观察 Redis 类型、内部编码与业务建模边界。"""

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:01:"


def encoding(client, key: str) -> str:
    value = client.object("ENCODING", key)
    return str(value)


def main() -> None:
    client = redis_client()
    cleanup_prefix(client, PREFIX)
    try:
        integer = f"{PREFIX}counter"
        short = f"{PREFIX}short"
        long_value = f"{PREFIX}long"
        small_hash = f"{PREFIX}user:1"
        large_hash = f"{PREFIX}user:2"
        small_zset = f"{PREFIX}rank:small"
        large_zset = f"{PREFIX}rank:large"
        queue = f"{PREFIX}queue"

        client.set(integer, 42)
        client.set(short, "redis")
        client.set(long_value, "x" * 256)
        client.hset(small_hash, mapping={"name": "Ada", "level": "L2"})
        client.hset(large_hash, mapping={f"field:{i}": str(i) for i in range(600)})
        client.zadd(small_zset, {f"u{i}": float(i) for i in range(8)})
        client.zadd(large_zset, {f"u{i}": float(i) for i in range(200)})
        client.rpush(queue, "order-1", "order-2", "order-3")

        evidence = {
            "string-int": encoding(client, integer),
            "string-short": encoding(client, short),
            "string-long": encoding(client, long_value),
            "hash-small": encoding(client, small_hash),
            "hash-large": encoding(client, large_hash),
            "zset-small": encoding(client, small_zset),
            "zset-large": encoding(client, large_zset),
        }
        if evidence["hash-small"] == evidence["hash-large"]:
            raise AssertionError(f"Hash 编码未发生预期转换：{evidence}")
        if evidence["zset-small"] == evidence["zset-large"]:
            raise AssertionError(f"ZSet 编码未发生预期转换：{evidence}")
        popped = client.lpop(queue)
        if popped != "order-1":
            raise AssertionError(f"队列顺序异常：{popped}")

        print("内部编码证据：")
        for name, value in evidence.items():
            print(f"  {name:14s} -> {value}")
        print(
            "业务语义证据：List 按插入顺序弹出 order-1；"
            f"大 Hash 内存={client.memory_usage(large_hash)} bytes。"
        )
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 01 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
