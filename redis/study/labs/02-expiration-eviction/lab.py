#!/usr/bin/env python3
"""验证 TTL 状态、到期删除与内存计量。"""

import time

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:02:"


def main() -> None:
    client = redis_client()
    cleanup_prefix(client, PREFIX)
    try:
        expiring = f"{PREFIX}session"
        persistent = f"{PREFIX}profile"
        small = f"{PREFIX}value:small"
        large = f"{PREFIX}value:large"

        client.set(expiring, "token", px=900)
        client.set(persistent, "profile")
        client.set(small, "x" * 64)
        client.set(large, "x" * 4096)
        initial_ttl = client.pttl(expiring)
        if not 0 < initial_ttl <= 900:
            raise AssertionError(f"初始 PTTL 异常：{initial_ttl}")
        if client.ttl(persistent) != -1 or client.ttl("missing:key") != -2:
            raise AssertionError("TTL 的 -1/-2 状态不符合预期")

        small_memory = int(client.memory_usage(small) or 0)
        large_memory = int(client.memory_usage(large) or 0)
        if large_memory <= small_memory:
            raise AssertionError("大 Value 的内存占用没有高于小 Value")

        time.sleep(1.0)
        if client.get(expiring) is not None or client.ttl(expiring) != -2:
            raise AssertionError("过期键仍可读取")

        policy = client.config_get("maxmemory-policy")["maxmemory-policy"]
        print(
            f"TTL 证据：初始 PTTL={initial_ttl}ms，到期后 TTL=-2；"
            "持久键 TTL=-1。"
        )
        print(
            f"内存证据：64B Value 使用 {small_memory}B，4KiB Value 使用 "
            f"{large_memory}B；当前淘汰策略={policy}。"
        )
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 02 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
