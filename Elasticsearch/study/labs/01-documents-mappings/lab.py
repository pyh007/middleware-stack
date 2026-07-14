#!/usr/bin/env python3
"""验证映射、分析链、严格动态字段，以及 query/filter 上下文。"""

from es_http import bulk, evidence, recreate_index, request


INDEX = "lab-es-01-products"


def main() -> None:
    recreate_index(
        INDEX,
        {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "lab_english": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"],
                        }
                    }
                },
            },
            "mappings": {
                "dynamic": "strict",
                "properties": {
                    "name": {"type": "text", "analyzer": "lab_english"},
                    "brand": {"type": "keyword"},
                    "price": {"type": "scaled_float", "scaling_factor": 100},
                    "created_at": {"type": "date"},
                },
            },
        },
    )
    analyzed = request(
        "POST", INDEX + "/_analyze", {"analyzer": "lab_english", "text": "The QUICK Runners"}
    )
    tokens = [token["token"] for token in analyzed["tokens"]]
    assert tokens == ["quick", "runners"], tokens

    actions = []
    for doc_id, doc in {
        "1": {"name": "Quick running shoes", "brand": "north", "price": 399.0, "created_at": "2026-01-01"},
        "2": {"name": "Quick trail jacket", "brand": "north", "price": 699.0, "created_at": "2026-01-02"},
        "3": {"name": "City walking shoes", "brand": "south", "price": 299.0, "created_at": "2026-01-03"},
    }.items():
        actions.extend([{"index": {"_index": INDEX, "_id": doc_id}}, doc])
    bulk(actions)
    request("POST", INDEX + "/_refresh")

    result = request(
        "POST",
        INDEX + "/_search",
        {
            "query": {
                "bool": {
                    "must": [{"match": {"name": "quick shoes"}}],
                    "filter": [{"term": {"brand": "north"}}],
                }
            }
        },
    )
    assert result["hits"]["total"]["value"] == 2, result["hits"]
    strict_failure = request(
        "POST",
        INDEX + "/_doc/strict-failure",
        {"name": "unknown field", "brand": "north", "price": 1, "created_at": "2026-01-04", "colour": "red"},
        expected=(400,),
    )
    assert strict_failure["error"]["type"] == "strict_dynamic_mapping_exception", strict_failure
    mapping = request("GET", INDEX + "/_mapping")
    evidence("分析器 token", tokens)
    evidence("命中 ID、分数与精确过滤", [{"id": h["_id"], "score": h["_score"]} for h in result["hits"]["hits"]])
    evidence("严格映射拒绝未知字段", strict_failure["error"]["type"])
    evidence("最终映射", mapping[INDEX]["mappings"])


if __name__ == "__main__":
    main()
