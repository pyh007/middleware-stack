#!/usr/bin/env python3
"""比较逐条请求与 Pipeline，并收集热点/大 Key 诊断证据。"""

import time

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:03:"
COUNT = 600


def elapsed_ms(operation) -> float:
    started = time.perf_counter()
    operation()
    return (time.perf_counter() - started) * 1000


def main() -> None:
    client = redis_client()
    cleanup_prefix(client, PREFIX)
    try:
        direct_prefix = f"{PREFIX}direct:"
        pipeline_prefix = f"{PREFIX}pipeline:"

        direct_ms = elapsed_ms(
            lambda: [client.set(f"{direct_prefix}{i}", i) for i in range(COUNT)]
        )

        def pipeline_write() -> None:
            with client.pipeline(transaction=False) as pipe:
                for i in range(COUNT):
                    pipe.set(f"{pipeline_prefix}{i}", i)
                results = pipe.execute()
            if not all(results):
                raise AssertionError("Pipeline 中存在失败命令")

        pipeline_ms = elapsed_ms(pipeline_write)
        if client.mget(
            f"{pipeline_prefix}0", f"{pipeline_prefix}{COUNT - 1}"
        ) != ["0", str(COUNT - 1)]:
            raise AssertionError("Pipeline 写入结果不完整")

        hot_key = f"{PREFIX}hot"
        big_key = f"{PREFIX}big-hash"
        client.set(hot_key, "value")
        for _ in range(2000):
            client.get(hot_key)
        client.hset(big_key, mapping={f"field:{i}": "x" * 128 for i in range(800)})

        stats = client.info("stats")
        commandstats = client.info("commandstats")
        big_memory = int(client.memory_usage(big_key) or 0)
        if big_memory < 80_000:
            raise AssertionError(f"大 Key 样本过小：{big_memory} bytes")
        get_calls = int(commandstats.get("cmdstat_get", {}).get("calls", 0))

        print(
            f"往返证据：逐条 SET {COUNT} 次耗时={direct_ms:.2f}ms；"
            f"单 Pipeline 耗时={pipeline_ms:.2f}ms。耗时只作本机对照，不作 SLA。"
        )
        print(
            f"诊断证据：hot key 已读 2000 次，服务累计 GET calls={get_calls}；"
            f"big-hash MEMORY USAGE={big_memory}B，字段数=800。"
        )
        print(
            "运行态证据："
            f"blocked_clients={client.info('clients')['blocked_clients']}，"
            f"expired_keys={stats['expired_keys']}，slowlog_len={client.slowlog_len()}。"
        )
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 03 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
