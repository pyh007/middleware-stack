#!/usr/bin/env python3
"""综合复现映射字段上限、路由热点与搜索诊断信号。"""

from es_http import bulk, evidence, recreate_index, request


INDEX = "lab-es-08-incident"


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {"number_of_shards": 3, "number_of_replicas": 0, "mapping.total_fields.limit": 8},
            "mappings": {"properties": {"tenant_id": {"type": "keyword"}, "service": {"type": "keyword"}, "status": {"type": "integer"}, "message": {"type": "text"}, "event_time": {"type": "date"}}},
        },
    )
    actions = []
    for number in range(40):
        tenant = "tenant-hot" if number < 30 else f"tenant-{number}"
        actions.extend([{"index": {"_index": INDEX, "_id": str(number), "routing": tenant}}, {"tenant_id": tenant, "service": "checkout", "status": 500 if number % 7 == 0 else 200, "message": f"request {number}", "event_time": "2026-07-14T08:00:00Z"}])
    bulk(actions)
    request("POST", INDEX + "/_refresh")
    explosion = request("POST", INDEX + "/_doc/explosion", {"tenant_id": "bad", "service": "api", "status": 200, "message": "too many dynamic fields", "event_time": "2026-07-14T08:00:00Z", "field_a": 1, "field_b": 2, "field_c": 3, "field_d": 4}, expected=(400,))
    assert explosion["error"]["type"] == "document_parsing_exception", explosion
    assert explosion["error"]["caused_by"]["type"] == "illegal_argument_exception", explosion
    shards = request("GET", "_cat/shards/" + INDEX, params={"format": "json", "h": "shard,prirep,state,docs,node"})
    primary_docs = [int(row.get("docs") or 0) for row in shards if row["prirep"] == "p"]
    assert max(primary_docs) > min(primary_docs), primary_docs
    profiled = request("POST", INDEX + "/_search", {"profile": True, "query": {"bool": {"filter": [{"term": {"tenant_id": "tenant-hot"}}, {"term": {"status": 500}}]}}})
    assert profiled["hits"]["total"]["value"] > 0
    nodes = request("GET", "_nodes/stats/thread_pool")
    node = next(iter(nodes["nodes"].values()))
    thread_pool = {name: {"active": node["thread_pool"][name]["active"], "queue": node["thread_pool"][name]["queue"], "rejected": node["thread_pool"][name]["rejected"]} for name in ("search", "write")}
    evidence("映射爆炸被字段上限阻止", {"status": 400, "type": explosion["error"]["type"], "cause": explosion["error"]["caused_by"]["type"], "reason": explosion["error"]["caused_by"]["reason"]})
    evidence("热点路由导致的主分片文档数", {"docs_per_primary": primary_docs, "rows": shards})
    evidence("热点租户 500 查询与线程池", {"hits": profiled["hits"]["total"]["value"], "thread_pool": thread_pool})
    print("事故推理：先止住动态字段写入和异常流量，再依据分片、线程池、堆与磁盘证据决定拆索引或改路由。")


if __name__ == "__main__":
    main()
