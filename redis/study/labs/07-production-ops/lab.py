#!/usr/bin/env python3
"""执行容量采样、安全检查与实验键 DUMP/RESTORE 恢复。"""

from lab_common import cleanup_prefix, redis_client


PREFIX = "lab:redis:07:"


def main() -> None:
    client = redis_client(max_connections=16)
    cleanup_prefix(client, PREFIX)
    try:
        sample_keys = [f"{PREFIX}sample:{i}" for i in range(100)]
        with client.pipeline(transaction=False) as pipe:
            for i, key in enumerate(sample_keys):
                pipe.hset(
                    key,
                    mapping={
                        "user_id": str(i),
                        "plan": "professional",
                        "payload": "x" * 256,
                    },
                )
            pipe.execute()

        usages = [int(client.memory_usage(key) or 0) for key in sample_keys]
        average = sum(usages) / len(usages)
        estimated_primary = average * 1_000_000
        planned_with_headroom_and_replica = estimated_primary * 1.5 * 2

        recovery_key = f"{PREFIX}recover:account:42"
        client.hset(
            recovery_key,
            mapping={"balance": "8800", "currency": "CNY", "version": "7"},
        )
        payload = client.dump(recovery_key)
        if payload is None:
            raise AssertionError("DUMP 未返回数据")
        client.delete(recovery_key)
        client.restore(recovery_key, 0, payload, replace=True)
        recovered = client.hgetall(recovery_key)
        if recovered.get("version") != "7" or recovered.get("balance") != "8800":
            raise AssertionError(f"恢复数据不正确：{recovered}")

        memory = client.info("memory")
        clients = client.info("clients")
        maxclients = int(client.config_get("maxclients")["maxclients"])
        identity = client.acl_whoami()
        if identity != "default":
            raise AssertionError(f"ACL 身份异常：{identity}")

        print(
            f"容量证据：样本平均={average:.1f}B；100 万同类键主节点约 "
            f"{estimated_primary / 1024 / 1024:.1f}MiB；含 50% 余量和 1 副本约 "
            f"{planned_with_headroom_and_replica / 1024 / 1024:.1f}MiB。"
        )
        print(
            f"运行证据：used_memory={memory['used_memory']}，"
            f"connected_clients={clients['connected_clients']}/{maxclients}，"
            f"ACL identity={identity}，连接池上限=16。"
        )
        print(f"恢复证据：DUMP/删除/RESTORE 后 account:42={recovered}。")
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 07 断言通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
