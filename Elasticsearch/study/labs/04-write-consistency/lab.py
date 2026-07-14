#!/usr/bin/env python3
"""验证实时 GET、refresh 可见性、translog 与乐观并发控制。"""

from es_http import evidence, recreate_index, request


INDEX = "lab-es-04-accounts"


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "-1"},
            "mappings": {"properties": {"owner": {"type": "keyword"}, "balance": {"type": "integer"}}},
        },
    )
    created = request("PUT", INDEX + "/_doc/1", {"owner": "alice", "balance": 100}, expected=(201,))
    realtime = request("GET", INDEX + "/_doc/1")
    before_refresh = request("GET", INDEX + "/_count")
    assert realtime["found"] is True and before_refresh["count"] == 0
    request("POST", INDEX + "/_refresh")
    after_refresh = request("GET", INDEX + "/_count")
    assert after_refresh["count"] == 1

    current = request("GET", INDEX + "/_doc/1")
    seq_no, primary_term = current["_seq_no"], current["_primary_term"]
    updated = request(
        "PUT",
        INDEX + "/_doc/1",
        {"owner": "alice", "balance": 80},
        params={"if_seq_no": seq_no, "if_primary_term": primary_term},
    )
    conflict = request(
        "PUT",
        INDEX + "/_doc/1",
        {"owner": "alice", "balance": 60},
        params={"if_seq_no": seq_no, "if_primary_term": primary_term},
        expected=(409,),
    )
    assert conflict["error"]["type"] == "version_conflict_engine_exception", conflict
    translog_before = request("GET", INDEX + "/_stats/translog")["indices"][INDEX]["total"]["translog"]
    request("POST", INDEX + "/_flush")
    translog_after = request("GET", INDEX + "/_stats/translog")["indices"][INDEX]["total"]["translog"]
    evidence("refresh 前后搜索计数与实时 GET", {"created_result": created["result"], "realtime_get": realtime["found"], "before": before_refresh["count"], "after": after_refresh["count"]})
    evidence("成功更新与陈旧写冲突", {"new_seq_no": updated["_seq_no"], "stale_status": 409, "error": conflict["error"]["type"]})
    evidence("flush 前后 translog", {"before": translog_before, "after": translog_after})


if __name__ == "__main__":
    main()
