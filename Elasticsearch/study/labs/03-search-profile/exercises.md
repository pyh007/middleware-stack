# 倒排索引搜索评分与聚合练习题

先闭卷作答，再运行实验验证。

1. 倒排索引如何从查询 term 找到文档？term dictionary、postings 与 `_source` 各做什么？
2. BM25 分数受哪些主要因素影响？为什么不同索引或不同查询的分数不宜直接比较？
3. bool 的 must、should、filter、must_not 应如何表达业务意图？
4. 一个搜索请求在多个分片上的 query、fetch 和 reduce 路径是什么？
5. terms 聚合为什么可能耗尽堆？怎样限制和观测风险？
6. 深 `from/size`、`search_after`、scroll 和 PIT 分别适合什么场景？
7. 面试场景：某查询平均 80 ms、P99 8 s。你如何选择样本、使用慢日志/profile、验证优化并回滚？

加练：移除唯一 tie-breaker，插入相同价格数据；解释为何游标分页可能出现重复或遗漏，并设计修复。
