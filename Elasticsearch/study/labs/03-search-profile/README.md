# 03 倒排索引搜索评分与聚合

## 学习目标

- 能从 term dictionary/postings 解释全文检索与 BM25 相关性，不把分数当业务真理。
- 能组织 bool query 的 must/filter，使用聚合并识别高基数内存风险。
- 能阅读 search profile 的 shard、rewrite/query、collector，而不是凭感觉优化。
- 能说明 `from/size`、`search_after` 和 PIT 的分页取舍。

## 运行实验

```bash
make -C Elasticsearch search-profile
```

实验索引五个商品文档，执行带 category filter 的全文查询和价格统计，输出分数与 profile 类型；再用 `price + doc_id` 的稳定唯一排序键执行两页 `search_after`，断言页面不重复。

## 核心机制

倒排索引从 term 找到包含它的文档列表，BM25 综合词频、逆文档频率和字段长度产生分数。filter 不参与分数，能更清楚表达权限、租户、状态等硬约束。协调节点向各相关分片发 query phase，再 fetch 文档并 reduce 聚合；分片数量、返回字段、桶数和候选集都会影响成本。

深 `from/size` 要每个分片保留更大候选集。`search_after` 使用上一页 sort 值继续，适合顺序遍历但不支持随意跳页；并发刷新下需要 PIT 固定搜索视图，并管理 keep_alive 资源。

## 观察证据

- 四条 book 文档匹配，分数按词项匹配不同。
- price stats 的 count 与命中数一致。
- profile 暴露 bool、term 或相关底层查询节点。
- 两页 ID 无交集，游标就是上一页最后一条的 sort 数组。

## 修改实验

删除 category filter，预测命中和聚合变化；把 must 改为 should 并调整 `minimum_should_match`。随后插入相同 price 的文档，删除 `doc_id` tie-breaker，观察排序为何不再保证稳定。

## 生产边界

profile 有额外开销，只对代表性慢请求采样；高基数 terms 聚合、脚本评分、大返回 `_source` 和跨大量分片都可能成为瓶颈。优化必须同时验证正确性、P95/P99、CPU/heap、线程池和 cache，且保留查询回滚。

## 完成标准

- [ ] 能解释 BM25 是相对分数及其输入。
- [ ] 能从 profile 指出查询和 collector 的成本，而非只看总耗时。
- [ ] 能实现稳定 `search_after` 并解释 PIT 生命周期。
- [ ] 能给出慢搜索的证据收集、灰度与回滚步骤。
