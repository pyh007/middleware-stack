#!/usr/bin/env python3
"""显式资源实验：只对隔离索引执行只读后的 force merge。"""

from es_http import bulk, evidence, recreate_index, request


INDEX = "lab-es-05-force-merge"


def segment_count() -> int:
    return request("GET", INDEX + "/_stats/segments")["indices"][INDEX]["total"]["segments"]["count"]


def main() -> None:
    recreate_index(INDEX, {"settings": {"number_of_shards": 1, "number_of_replicas": 0, "refresh_interval": "-1"}})
    for batch in range(5):
        bulk(sum(([{"index": {"_index": INDEX, "_id": f"{batch}-{n}"}}, {"batch": batch, "value": n}] for n in range(10)), []))
        request("POST", INDEX + "/_refresh")
    before = segment_count()
    request("PUT", INDEX + "/_settings", {"index.blocks.write": True})
    request("POST", INDEX + "/_forcemerge", params={"max_num_segments": 1}, timeout=120)
    after = segment_count()
    assert after <= before and after == 1, (before, after)
    evidence("force merge 前后段数量", {"before": before, "after": after, "write_block": True})
    print("该操作会产生磁盘 I/O；生产中仅对不再写入的索引评估后执行。")


if __name__ == "__main__":
    main()
