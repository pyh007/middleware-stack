# 01 文档映射与分析链

## 学习目标

- 能解释 JSON 文档如何按 mapping 转成 Lucene 字段与 term，区分 `_source` 和可搜索结构。
- 能用 `_analyze` 证明 analyzer 的 character filter、tokenizer、token filter 输出。
- 能选择 `text`、`keyword`、数值、日期和 multi-field，并防止动态字段失控。
- 能说明 query context 与 filter context 的相关性、缓存和业务边界。

## 运行实验

```bash
make -C Elasticsearch documents-mappings
```

脚本重建 `lab-es-01-products`，创建严格映射和自定义英文分析器，批量写入三条文档，验证 match+term 查询，并故意写入未知字段得到 400。

## 核心机制

mapping 是索引期数据契约。`text` 经过 analyzer 变成 token 写入倒排索引，`keyword` 把整个值作为 term；数值和日期使用适合范围查询、排序和聚合的结构。`_source` 保存原 JSON 便于返回和重建，但它不是全文查询的数据来源。搜索时 query context 计算相关性分数，filter context 只做是否匹配，适合精确约束。

已有字段的类型或分析方式不能让旧 segment 原地改变；模型修复通常是建新索引、reindex、校验、追平增量并原子切换别名。

## 观察证据

- `The QUICK Runners` 被分析成 `quick`、`runners`。
- 品牌 filter 只保留 `north`，match 条件仍产生 `_score`。
- `dynamic: strict` 对 `colour` 返回 `strict_dynamic_mapping_exception`。
- 最终 mapping 只包含声明字段，脚本用断言保护这些不变量。

## 修改实验

先预测，再把 stop filter 移除，观察 `the` 是否留下；随后把 `brand` 改为 `text`，比较 term 和 match 的结果。若要保留全文与精确能力，改成带 `keyword` 子字段的 multi-field，并写出迁移方案。

## 生产边界

分析器影响召回与索引大小，修改前要用真实词表离线评估；动态模板需配字段数上限和命名规范。严格映射会拒绝新字段，应用必须监控 400 并有 schema 发布流程。reindex 会带来双份磁盘、写入追平和回滚成本。

## 完成标准

- [ ] 不看文档解释 text/keyword、`_source`、倒排索引和 mapping 不可原地改写。
- [ ] 独立预测并验证 token、命中和严格映射错误。
- [ ] 能给出动态字段治理、重建索引、校验与别名回滚方案。
- [ ] 按结论、机制、证据、边界、副作用、生产验证回答练习题。
