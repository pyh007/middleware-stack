#!/usr/bin/env python3
"""显式恢复实验：快照后删除并恢复一个隔离索引。"""

from es_http import delete_index, evidence, recreate_index, request


INDEX = "lab-es-07-restore"
REPOSITORY = "lab-es-repo"
SNAPSHOT = "lab-es-snapshot-1"


def main() -> None:
    request("DELETE", f"_snapshot/{REPOSITORY}/{SNAPSHOT}", expected=(200, 404))
    request("DELETE", f"_snapshot/{REPOSITORY}", expected=(200, 404))
    recreate_index(INDEX, {"settings": {"number_of_shards": 1, "number_of_replicas": 0}})
    request("PUT", INDEX + "/_doc/proof", {"message": "recover me", "checksum": "es-lab-2026"}, params={"refresh": "wait_for"}, expected=(201,))
    request("PUT", f"_snapshot/{REPOSITORY}", {"type": "fs", "settings": {"location": "lab-es-repository", "compress": True}})
    snapshot = request("PUT", f"_snapshot/{REPOSITORY}/{SNAPSHOT}", {"indices": INDEX, "include_global_state": False}, params={"wait_for_completion": "true"})
    assert snapshot["snapshot"]["state"] == "SUCCESS", snapshot
    delete_index(INDEX)
    missing = request("GET", INDEX, expected=(404,))
    restored = request("POST", f"_snapshot/{REPOSITORY}/{SNAPSHOT}/_restore", {"indices": INDEX, "include_global_state": False}, params={"wait_for_completion": "true"})
    successful_shards = restored["snapshot"]["shards"]["successful"]
    assert successful_shards == 1, restored
    proof = request("GET", INDEX + "/_doc/proof")
    assert proof["_source"]["checksum"] == "es-lab-2026", proof
    evidence("快照状态与分片", snapshot["snapshot"])
    evidence("删除后的状态与恢复证据", {"delete_check": missing["error"]["type"], "successful_shards": successful_shards, "checksum": proof["_source"]["checksum"]})
    request("DELETE", f"_snapshot/{REPOSITORY}/{SNAPSHOT}")
    request("DELETE", f"_snapshot/{REPOSITORY}")
    print("恢复实验已清理快照元数据；实验索引保留，便于复核后由 make reset 清理。")


if __name__ == "__main__":
    main()
