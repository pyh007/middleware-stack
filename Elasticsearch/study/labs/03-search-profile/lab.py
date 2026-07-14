#!/usr/bin/env python3
"""验证相关性评分、filter、聚合、profile 与 search_after。"""

from es_http import bulk, evidence, recreate_index, request


INDEX = "lab-es-03-catalog"


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "category": {"type": "keyword"},
                    "price": {"type": "double"},
                }
            },
        },
    )
    docs = [
        ("a", "quick brown fox", "book", 10.0),
        ("b", "quick search handbook", "book", 20.0),
        ("c", "brown leather bag", "bag", 30.0),
        ("d", "distributed search quick guide", "book", 40.0),
        ("e", "search operations", "book", 50.0),
    ]
    actions = []
    for doc_id, title, category, price in docs:
        actions.extend([{"index": {"_index": INDEX, "_id": doc_id}}, {"doc_id": doc_id, "title": title, "category": category, "price": price}])
    bulk(actions)
    request("POST", INDEX + "/_refresh")

    profiled = request(
        "POST",
        INDEX + "/_search",
        {
            "profile": True,
            "query": {"bool": {"must": [{"match": {"title": "quick search"}}], "filter": [{"term": {"category": "book"}}]}},
            "aggs": {"price_stats": {"stats": {"field": "price"}}},
        },
    )
    assert profiled["hits"]["total"]["value"] == 4, profiled["hits"]
    assert profiled["aggregations"]["price_stats"]["count"] == 4
    profile_types = [child["type"] for child in profiled["profile"]["shards"][0]["searches"][0]["query"]]

    first = request("POST", INDEX + "/_search", {"size": 2, "query": {"match_all": {}}, "sort": [{"price": "asc"}, {"doc_id": "asc"}]})
    after = first["hits"]["hits"][-1]["sort"]
    second = request("POST", INDEX + "/_search", {"size": 2, "query": {"match_all": {}}, "sort": [{"price": "asc"}, {"doc_id": "asc"}], "search_after": after})
    first_ids = [h["_id"] for h in first["hits"]["hits"]]
    second_ids = [h["_id"] for h in second["hits"]["hits"]]
    assert not set(first_ids) & set(second_ids), (first_ids, second_ids)
    evidence("评分顺序", [{"id": h["_id"], "score": h["_score"]} for h in profiled["hits"]["hits"]])
    evidence("聚合统计", profiled["aggregations"])
    evidence("profile 查询节点类型", profile_types)
    evidence("search_after 两页", {"first": first_ids, "cursor": after, "second": second_ids})


if __name__ == "__main__":
    main()
