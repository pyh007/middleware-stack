#!/usr/bin/env python3
"""向隔离的 8MiB Redis 实例写入数据，观察 LRU 淘汰。"""

import os

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:02:eviction:"


def main() -> None:
    client = redis_client(
        host="127.0.0.1",
        port=int(os.getenv("EVICTION_PORT", "6389")),
        password=None,
    )
    cleanup_prefix(client, PREFIX)
    try:
        baseline = int(client.info("stats")["evicted_keys"])
        payload = "x" * 4096
        written = 0
        while written < 10_000:
            client.set(f"{PREFIX}{written}", payload)
            written += 1
            if int(client.info("stats")["evicted_keys"]) > baseline:
                break
        info = client.info()
        evicted = int(info["evicted_keys"]) - baseline
        if evicted <= 0:
            raise AssertionError("写入 10,000 个 4KiB Value 后仍未触发淘汰")
        surviving = sum(1 for _ in client.scan_iter(match=f"{PREFIX}*"))
        print(
            f"淘汰证据：写入={written}，存活={surviving}，新增 evicted_keys={evicted}，"
            f"used_memory={info['used_memory']}，maxmemory={info['maxmemory']}，"
            f"policy={info['maxmemory_policy']}。"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
