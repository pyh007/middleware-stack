# 倒排索引搜索评分与聚合参考要点

## 1. 倒排结构

term dictionary 定位词项，postings 记录文档 ID、频率或位置，查询据此求交并评分；`_source` 主要在 fetch 阶段返回原 JSON。stored fields/doc values 还有不同读取方向。实验的 match 命中来自分析后的 term，不是扫描 `_source`。

## 2. BM25

主要受词频、逆文档频率、字段长度和参数影响，分数只在当前查询/索引统计上下文内排序。分片局部统计、文档集合变化和 boost 都会改变分数；业务排序常需结合明确特征并用离线相关性集和线上指标验证。

## 3. bool 语义

must 是必须匹配且计分，filter 是必须匹配但不计分，must_not 排除，should 根据是否有 must/filter 与 `minimum_should_match` 决定可选或必须。权限、租户、状态通常放 filter，全文意图放 must/should。

## 4. 分布式搜索

协调节点向目标分片发 query，各分片返回局部 top K/聚合中间态；协调节点归并后 fetch 文档。分片 fan-out、候选 K、桶数和返回字段会放大 CPU、堆与网络。routing 可缩小目标，但有热点边界。

## 5. 聚合风险

高基数 terms 需要各分片维护候选桶，再由协调节点归并，可能触发 circuit breaker。限制 size/shard_size、预聚合或重建模型；监控 heap、breaker、GC、线程池、请求耗时和结果误差。

## 6. 分页

深 from/size 适合浅随机页；search_after 适合稳定顺序浏览，需唯一排序键；PIT 固定视图但占段资源；scroll 主要用于批量遍历而非用户分页。实验的 tie-breaker 避免同价文档游标歧义。

## 7. 尾延迟诊断

按租户、分片、请求形状和节点分组，保存慢日志、profile 少量异常/正常对照、fan-out、queue/rejected、GC/磁盘/merge。最小化返回、修正 filter/分页/聚合或 routing 后小流量灰度；同时验证结果正确、P99 和资源，超阈值立即回滚查询版本。
