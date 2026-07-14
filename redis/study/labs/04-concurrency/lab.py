#!/usr/bin/env python3
"""复现丢失更新，并用 WATCH、Lua 和所有权令牌修复。"""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import redis

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:04:"
WORKERS = 8
INCREMENTS = 20


def naive_lost_update(key: str) -> int:
    client = redis_client()
    barrier = naive_lost_update.barrier
    try:
        current = int(client.get(key) or 0)
        barrier.wait(timeout=5)
        client.set(key, current + 1)
        return current
    finally:
        client.close()


naive_lost_update.barrier = threading.Barrier(WORKERS)


def watched_increment(key: str) -> int:
    client = redis_client()
    retries = 0
    try:
        for _ in range(INCREMENTS):
            while True:
                try:
                    with client.pipeline() as pipe:
                        pipe.watch(key)
                        current = int(pipe.get(key) or 0)
                        pipe.multi()
                        pipe.set(key, current + 1)
                        pipe.execute()
                    break
                except redis.WatchError:
                    retries += 1
        return retries
    finally:
        client.close()


def main() -> None:
    client = redis_client()
    cleanup_prefix(client, PREFIX)
    naive_key = f"{PREFIX}naive-counter"
    watch_key = f"{PREFIX}watch-counter"
    stock_key = f"{PREFIX}stock"
    lock_key = f"{PREFIX}lock:order:42"
    try:
        client.set(naive_key, 0)
        naive_lost_update.barrier = threading.Barrier(WORKERS)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            list(executor.map(lambda _: naive_lost_update(naive_key), range(WORKERS)))
        naive_result = int(client.get(naive_key) or 0)
        if naive_result != 1:
            raise AssertionError(f"丢失更新复现不确定：期望 1，实际 {naive_result}")

        client.set(watch_key, 0)
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            retries = sum(executor.map(lambda _: watched_increment(watch_key), range(WORKERS)))
        watched_result = int(client.get(watch_key) or 0)
        expected = WORKERS * INCREMENTS
        if watched_result != expected:
            raise AssertionError(f"WATCH 结果错误：{watched_result} != {expected}")

        client.set(stock_key, 2)
        decrement_if_available = """
        local stock = tonumber(redis.call('GET', KEYS[1]) or '-1')
        if stock <= 0 then return {0, stock} end
        local remaining = redis.call('DECR', KEYS[1])
        return {1, remaining}
        """
        lua_results = [client.eval(decrement_if_available, 1, stock_key) for _ in range(3)]
        if lua_results != [[1, 1], [1, 0], [0, 0]]:
            raise AssertionError(f"Lua 库存结果异常：{lua_results}")

        token = str(uuid.uuid4())
        if not client.set(lock_key, token, nx=True, px=10_000):
            raise AssertionError("获取实验锁失败")
        release = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
          return redis.call('DEL', KEYS[1])
        end
        return 0
        """
        wrong_release = client.eval(release, 1, lock_key, "other-owner")
        correct_release = client.eval(release, 1, lock_key, token)
        if (wrong_release, correct_release) != (0, 1):
            raise AssertionError("锁所有权令牌校验失败")

        print(f"丢失更新证据：{WORKERS} 个并发写最终仅为 {naive_result}。")
        print(
            f"WATCH 证据：最终={watched_result}，冲突重试={retries}；"
            f"Lua 三次扣库存={lua_results}。"
        )
        print("锁证据：错误令牌不能解锁，持有者令牌成功删除锁。")
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 04 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
