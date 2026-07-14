#!/usr/bin/env python3
"""验证复制角色边界、Cluster 槽位与 Hash Tag。"""

import binascii

from lab_common import redis_client


def hash_tag(key: str) -> str:
    start = key.find("{")
    if start == -1:
        return key
    end = key.find("}", start + 1)
    if end == -1 or end == start + 1:
        return key
    return key[start + 1 : end]


def slot(key: str) -> int:
    return binascii.crc_hqx(hash_tag(key).encode(), 0) % 16_384


def main() -> None:
    client = redis_client()
    try:
        replication = client.info("replication")
        cluster_enabled = client.config_get("cluster-enabled")["cluster-enabled"]
        order = "lab:redis:06:{order:42}:header"
        items = "lab:redis:06:{order:42}:items"
        other = "lab:redis:06:{order:43}:header"
        order_slot, items_slot, other_slot = slot(order), slot(items), slot(other)
        if order_slot != items_slot or order_slot == other_slot:
            raise AssertionError("Hash Tag 槽位计算不符合预期")
        if replication["role"] != "master":
            raise AssertionError(f"默认实验实例角色异常：{replication['role']}")

        print(
            f"拓扑证据：role={replication['role']}，"
            f"connected_slaves={replication['connected_slaves']}，"
            f"cluster-enabled={cluster_enabled}。"
        )
        print(
            f"槽位证据：order:42 的两个键同在 slot={order_slot}；"
            f"order:43 位于 slot={other_slot}。"
        )
        print("边界：同一 Hash Tag 支持多键原子操作，也可能制造热点槽。")
    finally:
        client.close()


if __name__ == "__main__":
    main()
