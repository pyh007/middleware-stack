#!/usr/bin/env python3
"""触发 RDB/AOF 后台任务并验证持久化状态。"""

from lab_common import cleanup_prefix, redis_client, wait_until


PREFIX = "lab:redis:05:"


def main() -> None:
    client = redis_client(socket_timeout=20)
    cleanup_prefix(client, PREFIX)
    try:
        with client.pipeline(transaction=False) as pipe:
            for i in range(100):
                pipe.hset(
                    f"{PREFIX}order:{i}",
                    mapping={"status": "paid", "amount": str(i * 10)},
                )
            pipe.execute()

        config = {}
        for name in ("appendonly", "appendfsync", "save"):
            config.update(client.config_get(name))
        before = client.info("persistence")
        lastsave_before = int(client.lastsave().timestamp())
        client.bgsave()
        wait_until(
            lambda: int(client.info("persistence")["rdb_bgsave_in_progress"]) == 0,
            20,
            "BGSAVE 完成",
        )
        after_rdb = client.info("persistence")
        if after_rdb["rdb_last_bgsave_status"] != "ok":
            raise AssertionError(f"RDB 失败：{after_rdb['rdb_last_bgsave_status']}")
        if int(client.lastsave().timestamp()) < lastsave_before:
            raise AssertionError("LASTSAVE 时间倒退")

        client.bgrewriteaof()
        wait_until(
            lambda: int(client.info("persistence")["aof_rewrite_in_progress"]) == 0,
            30,
            "BGREWRITEAOF 完成",
        )
        after_aof = client.info("persistence")
        if after_aof["aof_last_bgrewrite_status"] != "ok":
            raise AssertionError(
                f"AOF 重写失败：{after_aof['aof_last_bgrewrite_status']}"
            )

        print(
            "配置证据："
            f"appendonly={config['appendonly']}，appendfsync={config['appendfsync']}，"
            f"save={config['save']!r}。"
        )
        print(
            "RDB 证据："
            f"触发前 changes={before['rdb_changes_since_last_save']}，"
            f"结果={after_rdb['rdb_last_bgsave_status']}，"
            f"耗时={after_rdb['rdb_last_bgsave_time_sec']}s。"
        )
        print(
            "AOF 证据："
            f"结果={after_aof['aof_last_bgrewrite_status']}，"
            f"current_size={after_aof['aof_current_size']}，"
            f"base_size={after_aof['aof_base_size']}。"
        )
    finally:
        deleted = cleanup_prefix(client, PREFIX)
        client.close()
        print(f"模块 05 安全实验通过并清理 {deleted} 个键。")


if __name__ == "__main__":
    main()
