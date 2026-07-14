#!/usr/bin/env python3
"""在单节点上验证未分配副本导致 yellow，而非主分片不可用。"""

from es_http import evidence, recreate_index, request, wait_for


INDEX = "lab-es-06-availability"


def main() -> None:
    recreate_index(INDEX, {"settings": {"number_of_shards": 1, "number_of_replicas": 1}, "mappings": {"properties": {"message": {"type": "text"}}}})
    request("PUT", INDEX + "/_doc/1", {"message": "primary is available"}, params={"refresh": "wait_for"}, expected=(201,))
    yellow = wait_for("_cluster/health/" + INDEX, lambda state: state["status"] == "yellow")
    allocation = request("POST", "_cluster/allocation/explain", {"index": INDEX, "shard": 0, "primary": False})
    assert allocation["unassigned_info"]["reason"] == "INDEX_CREATED", allocation
    search = request("GET", INDEX + "/_search")
    assert search["hits"]["total"]["value"] == 1
    request("PUT", INDEX + "/_settings", {"number_of_replicas": 0})
    green = wait_for("_cluster/health/" + INDEX, lambda state: state["status"] == "green")
    evidence("副本为 1 时的索引健康", {"status": yellow["status"], "active_primary_shards": yellow["active_primary_shards"], "unassigned_shards": yellow["unassigned_shards"]})
    evidence("副本未分配原因与决策", {"reason": allocation["unassigned_info"]["reason"], "decision": allocation["allocate_explanation"]})
    evidence("调整副本后的健康", {"status": green["status"], "unassigned_shards": green["unassigned_shards"]})


if __name__ == "__main__":
    main()
