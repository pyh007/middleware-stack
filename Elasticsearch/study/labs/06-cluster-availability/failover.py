#!/usr/bin/env python3
"""显式故障实验：停止主分片所在节点，验证副本提升并恢复。"""

from __future__ import annotations

import subprocess

from es_http import delete_index, evidence, recreate_index, request, wait_for


INDEX = "lab-es-06-failover"
COMPOSE = [
    "docker",
    "compose",
    "-p",
    "es-study-cluster",
    "-f",
    "study/labs/06-cluster-availability/docker-compose.cluster.yml",
]


def compose(*args: str) -> None:
    subprocess.run([*COMPOSE, *args], check=True)


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "index.routing.allocation.include._name": "es-study-2,es-study-3",
            }
        },
    )
    request("PUT", INDEX + "/_doc/proof", {"message": "survive primary loss"}, params={"refresh": "wait_for"}, expected=(201,))
    wait_for("_cluster/health/" + INDEX, lambda state: state["status"] == "green")
    before = request("GET", "_cat/shards/" + INDEX, params={"format": "json", "h": "index,shard,prirep,state,node"})
    primary_node = next(row["node"] for row in before if row["prirep"] == "p")
    service_by_node = {"es-study-2": "es02", "es-study-3": "es03"}
    stopped_service = service_by_node[primary_node]
    print(f"将停止承载主分片的 {primary_node}（Compose 服务 {stopped_service}）。")
    compose("stop", stopped_service)
    try:
        yellow = wait_for("_cluster/health/" + INDEX, lambda state: state["status"] == "yellow")
        after_stop = request("GET", "_cat/shards/" + INDEX, params={"format": "json", "h": "index,shard,prirep,state,node,unassigned.reason"})
        proof = request("GET", INDEX + "/_doc/proof")
        new_primary = next(row["node"] for row in after_stop if row["prirep"] == "p" and row["state"] == "STARTED")
        assert proof["found"] is True and new_primary != primary_node, (proof, after_stop)
        evidence("停机前分片", before)
        evidence("停机后副本提升", {"stopped": primary_node, "new_primary": new_primary, "status": yellow["status"], "shards": after_stop, "document_found": proof["found"]})
    finally:
        compose("start", stopped_service)
    green = wait_for("_cluster/health/" + INDEX, lambda state: state["status"] == "green", timeout=90)
    recovered = request("GET", "_cat/shards/" + INDEX, params={"format": "json", "h": "index,shard,prirep,state,node"})
    evidence("节点恢复后的再分配", {"status": green["status"], "shards": recovered})
    delete_index(INDEX)
    print("故障节点已重启，实验索引已清理；用 make cluster-down 删除三节点卷。")


if __name__ == "__main__":
    main()
