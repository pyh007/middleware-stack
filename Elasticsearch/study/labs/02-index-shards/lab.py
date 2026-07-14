#!/usr/bin/env python3
"""验证路由缩小搜索分片范围，以及别名原子切换。"""

from es_http import bulk, evidence, recreate_index, request


V1 = "lab-es-02-orders-v1"
V2 = "lab-es-02-orders-v2"
ALIAS = "lab-es-orders"


def definition() -> dict:
    return {
        "settings": {"number_of_shards": 2, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "tenant_id": {"type": "keyword"},
                "order_id": {"type": "keyword"},
                "amount": {"type": "double"},
            }
        },
    }


def main() -> None:
    recreate_index(V1, definition())
    recreate_index(V2, definition())
    actions = []
    for number in range(12):
        tenant = "tenant-a" if number < 6 else "tenant-b"
        actions.extend(
            [
                {"index": {"_index": V1, "_id": str(number), "routing": tenant}},
                {"tenant_id": tenant, "order_id": f"o-{number:02d}", "amount": number + 0.5},
            ]
        )
    bulk(actions)
    request("POST", V1 + "/_refresh")

    all_shards = request("GET", V1 + "/_search_shards")
    routed_shards = request("GET", V1 + "/_search_shards", params={"routing": "tenant-a"})
    assert len(all_shards["shards"]) == 2, all_shards
    assert len(routed_shards["shards"]) == 1, routed_shards

    request("POST", "_aliases", {"actions": [{"add": {"index": V1, "alias": ALIAS, "is_write_index": True}}]})
    request("POST", ALIAS + "/_doc/from-alias", {"tenant_id": "tenant-a", "order_id": "from-alias", "amount": 99}, params={"routing": "tenant-a"}, expected=(201,))
    request(
        "POST",
        "_aliases",
        {"actions": [{"remove": {"index": V1, "alias": ALIAS}}, {"add": {"index": V2, "alias": ALIAS, "is_write_index": True}}]},
    )
    alias_state = request("GET", "_alias/" + ALIAS)
    assert list(alias_state) == [V2], alias_state
    request("POST", ALIAS + "/_doc/new-version", {"tenant_id": "tenant-a", "order_id": "v2", "amount": 101}, expected=(201,))
    v2_doc = request("GET", V2 + "/_doc/new-version")
    assert v2_doc["found"] is True
    shard_rows = request("GET", "_cat/shards/" + V1, params={"format": "json", "h": "index,shard,prirep,state,docs,node"})
    evidence("无路由与 tenant-a 路由涉及的分片组数", {"all": len(all_shards["shards"]), "routed": len(routed_shards["shards"])})
    evidence("V1 分片分布", shard_rows)
    evidence("原子切换后的别名", alias_state)


if __name__ == "__main__":
    main()
