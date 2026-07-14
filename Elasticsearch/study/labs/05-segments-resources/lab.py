#!/usr/bin/env python3
"""观察段数量、请求缓存、JVM、线程池和文件系统指标。"""

from es_http import bulk, evidence, recreate_index, request


INDEX = "lab-es-05-events"


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "-1"},
            "mappings": {"properties": {"service": {"type": "keyword"}, "latency_ms": {"type": "integer"}, "message": {"type": "text"}}},
        },
    )
    for batch in range(3):
        actions = []
        for offset in range(10):
            number = batch * 10 + offset
            actions.extend([{"index": {"_index": INDEX, "_id": str(number)}}, {"service": "api" if number % 2 == 0 else "worker", "latency_ms": number, "message": f"event number {number}"}])
        bulk(actions)
        request("POST", INDEX + "/_refresh")
    stats_before = request("GET", INDEX + "/_stats/segments,request_cache")["indices"][INDEX]["total"]
    query = {"size": 0, "query": {"term": {"service": "api"}}, "aggs": {"avg_latency": {"avg": {"field": "latency_ms"}}}}
    request("POST", INDEX + "/_search", query, params={"request_cache": "true"})
    request("POST", INDEX + "/_search", query, params={"request_cache": "true"})
    stats_after = request("GET", INDEX + "/_stats/segments,request_cache")["indices"][INDEX]["total"]
    assert stats_after["request_cache"]["hit_count"] > stats_before["request_cache"]["hit_count"], (stats_before, stats_after)
    nodes = request("GET", "_nodes/stats/jvm,fs,thread_pool")
    node = next(iter(nodes["nodes"].values()))
    compact = {
        "heap_used_percent": node["jvm"]["mem"]["heap_used_percent"],
        "gc_old_collection_count": node["jvm"]["gc"]["collectors"]["old"]["collection_count"],
        "fs_available_bytes": node["fs"]["total"]["available_in_bytes"],
        "search_queue": node["thread_pool"]["search"]["queue"],
        "search_rejected": node["thread_pool"]["search"]["rejected"],
    }
    evidence("段与缓存命中", {"segments": stats_after["segments"]["count"], "cache_before": stats_before["request_cache"], "cache_after": stats_after["request_cache"]})
    evidence("节点资源信号", compact)


if __name__ == "__main__":
    main()
