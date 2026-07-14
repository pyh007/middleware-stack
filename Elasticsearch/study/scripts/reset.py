#!/usr/bin/env python3
"""只删除本课程的 lab-es- 前缀资源，不触碰其他索引。"""

from __future__ import annotations

from es_http import ElasticsearchError, evidence, request


def main() -> None:
    indices = request("GET", "_cat/indices/lab-es-*", params={"format": "json", "h": "index"}, expected=(200, 404))
    removed = []
    if isinstance(indices, list):
        for row in indices:
            name = row.get("index", "")
            if name.startswith("lab-es-"):
                request("DELETE", name, expected=(200, 404))
                removed.append(name)

    for user in ("lab_es_reader",):
        request("DELETE", f"_security/user/{user}", expected=(200, 404))
    for role in ("lab_es_reader",):
        request("DELETE", f"_security/role/{role}", expected=(200, 404))
    try:
        request("DELETE", "_snapshot/lab-es-repo", expected=(200, 404))
    except ElasticsearchError as exc:
        if exc.status != 500:
            raise
    evidence("已清理的实验索引", removed)
    print("reset 完成：仅处理 lab-es- 索引、课程别名、课程用户/角色和课程快照仓库。")


if __name__ == "__main__":
    main()
