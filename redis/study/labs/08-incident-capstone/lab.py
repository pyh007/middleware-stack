#!/usr/bin/env python3
"""复现穿透、击穿、雪崩和乱序回填，并验证治理手段。"""

import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:08:"
WORKERS = 10


class Backend:
    def __init__(self) -> None:
        self.calls = 0
        self.guard = threading.Lock()

    def load(self, value: str | None) -> str | None:
        with self.guard:
            self.calls += 1
        time.sleep(0.02)
        return value


def penetration(client) -> tuple[int, int]:
    key = f"{PREFIX}missing:user:404"
    backend = Backend()
    for _ in range(8):
        if client.get(key) is None:
            backend.load(None)
    without_null_cache = backend.calls

    backend.calls = 0
    for _ in range(8):
        value = client.get(key)
        if value is None:
            result = backend.load(None)
            client.set(key, "__NULL__" if result is None else result, ex=30)
    with_null_cache = backend.calls
    return without_null_cache, with_null_cache


def breakdown(client) -> tuple[int, int]:
    key = f"{PREFIX}hot-product"
    barrier = threading.Barrier(WORKERS)
    naive_backend = Backend()

    def naive_worker() -> None:
        local = redis_client()
        try:
            if local.get(key) is None:
                barrier.wait(timeout=5)
                local.set(key, naive_backend.load("product-v1"), ex=30)
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        list(executor.map(lambda _: naive_worker(), range(WORKERS)))
    naive_calls = naive_backend.calls

    client.delete(key)
    protected_backend = Backend()
    lock_key = f"{key}:rebuild-lock"
    release = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
      return redis.call('DEL', KEYS[1])
    end
    return 0
    """

    def protected_worker() -> None:
        local = redis_client()
        token = str(uuid.uuid4())
        try:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if local.get(key) is not None:
                    return
                if local.set(lock_key, token, nx=True, px=2000):
                    try:
                        if local.get(key) is None:
                            local.set(key, protected_backend.load("product-v1"), ex=30)
                    finally:
                        local.eval(release, 1, lock_key, token)
                    return
                time.sleep(0.005)
            raise RuntimeError("等待缓存重建超时")
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        list(executor.map(lambda _: protected_worker(), range(WORKERS)))
    return naive_calls, protected_backend.calls


def avalanche(client) -> tuple[int, int, int]:
    rng = random.Random(42)
    ttls = [60 + rng.randint(0, 30) for _ in range(100)]
    with client.pipeline(transaction=False) as pipe:
        for index, ttl in enumerate(ttls):
            pipe.set(f"{PREFIX}avalanche:{index}", "value", ex=ttl)
        pipe.execute()
    observed = [client.ttl(f"{PREFIX}avalanche:{index}") for index in range(100)]
    return min(observed), max(observed), len(set(observed))


def consistency(client) -> tuple[int, int, str]:
    key = f"{PREFIX}account:42"
    client.hset(key, mapping={"value": "new", "version": "2"})
    versioned_write = """
    local current = tonumber(redis.call('HGET', KEYS[1], 'version') or '-1')
    local incoming = tonumber(ARGV[1])
    if incoming <= current then return 0 end
    redis.call('HSET', KEYS[1], 'version', ARGV[1], 'value', ARGV[2])
    return 1
    """
    stale = int(client.eval(versioned_write, 1, key, 1, "old"))
    fresh = int(client.eval(versioned_write, 1, key, 3, "newest"))
    return stale, fresh, str(client.hget(key, "value"))


def main() -> None:
    client = redis_client()
    cleanup_prefix(client, PREFIX)
    try:
        penetration_before, penetration_after = penetration(client)
        naive_calls, protected_calls = breakdown(client)
        min_ttl, max_ttl, ttl_buckets = avalanche(client)
        stale, fresh, final_value = consistency(client)

        if (penetration_before, penetration_after) != (8, 1):
            raise AssertionError("空值缓存没有抑制穿透")
        if naive_calls != WORKERS or protected_calls != 1:
            raise AssertionError(
                f"互斥重建结果异常：naive={naive_calls}, protected={protected_calls}"
            )
        if ttl_buckets < 10 or max_ttl - min_ttl < 20:
            raise AssertionError("TTL 抖动分布不足")
        if (stale, fresh, final_value) != (0, 1, "newest"):
            raise AssertionError("版本化回填未拒绝旧值")

        print(
            f"穿透证据：后端访问 {penetration_before} -> {penetration_after}；"
            "短 TTL 空值缓存生效。"
        )
        print(
            f"击穿证据：并发回源 {naive_calls} -> {protected_calls}；"
            "带所有权令牌的互斥重建生效。"
        )
        print(
            f"雪崩证据：100 个键 TTL 分布 {min_ttl}..{max_ttl}s，"
            f"可见桶数={ttl_buckets}。"
        )
        print(
            f"一致性证据：旧版本写入={stale}，新版本写入={fresh}，"
            f"最终值={final_value}。"
        )
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 08 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
