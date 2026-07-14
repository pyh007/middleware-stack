#!/usr/bin/env python3
"""验证容量信号和索引级最小读取权限。"""

from es_http import evidence, recreate_index, request


INDEX = "lab-es-07-secure"
ROLE = "lab_es_reader"
USER = "lab_es_reader"
PASSWORD = "lab-reader-local-123"


def main() -> None:
    recreate_index(INDEX, {"settings": {"number_of_shards": 1, "number_of_replicas": 0}, "mappings": {"properties": {"message": {"type": "text"}}}})
    request("PUT", INDEX + "/_doc/1", {"message": "least privilege"}, params={"refresh": "wait_for"}, expected=(201,))
    request("PUT", "_security/role/" + ROLE, {"cluster": [], "indices": [{"names": ["lab-es-07-*"], "privileges": ["read", "view_index_metadata"]}]})
    request("PUT", "_security/user/" + USER, {"password": PASSWORD, "roles": [ROLE], "full_name": "Local lab reader"})
    try:
        readable = request("GET", INDEX + "/_search", user=USER, password=PASSWORD)
        forbidden = request("PUT", INDEX + "/_doc/2", {"message": "must fail"}, expected=(403,), user=USER, password=PASSWORD)
        assert readable["hits"]["total"]["value"] == 1
        assert forbidden["error"]["type"] == "security_exception", forbidden
    finally:
        request("DELETE", "_security/user/" + USER, expected=(200, 404))
        request("DELETE", "_security/role/" + ROLE, expected=(200, 404))
    node_stats = request("GET", "_nodes/stats/fs,jvm,indices")
    node = next(iter(node_stats["nodes"].values()))
    capacity = {
        "disk_available_bytes": node["fs"]["total"]["available_in_bytes"],
        "heap_used_percent": node["jvm"]["mem"]["heap_used_percent"],
        "index_store_bytes": node["indices"]["store"]["size_in_bytes"],
        "document_count": node["indices"]["docs"]["count"],
    }
    evidence("只读用户验证", {"read_hits": readable["hits"]["total"]["value"], "write_status": 403, "write_error": forbidden["error"]["type"]})
    evidence("容量基线", capacity)


if __name__ == "__main__":
    main()
