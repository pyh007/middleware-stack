# 文档映射与分析链参考要点

## 1. 文档数据路径

结论：`_source` 保存原始 JSON，mapping 定义字段解释，Lucene 结构支持检索。机制：写入按 mapping 解析，分析后的 term 进入倒排索引，数值/keyword 等还可有 doc values。证据：实验同时输出 mapping、token 与查询命中。边界：关闭或裁剪 `_source` 会影响更新、调试和 reindex，生产先验证恢复需求。

## 2. 类型选择

`text` 用于全文相关性，`keyword` 用于精确匹配、排序、聚合；金额用数值类型。品牌既要搜索又要聚合时可用 `text` 加 `keyword` 子字段。multi-field 增加磁盘和写成本，应通过真实查询验证收益。

## 3. 分析器

character filter 先规范字符，tokenizer 切 token，token filter 再小写、停用词或词干化。实验的 standard tokenizer + lowercase + stop 去掉 `the`。索引和查询分析不兼容会使查询 term 找不到索引 term；用 `_analyze` 与代表性语料回归。

## 4. query/filter

需要相关性排序的条件放 query，状态、租户、权限等布尔约束放 filter。filter 不计算分数并可能受益于缓存，但缓存不是保证；段频繁变化、低复用请求会降低收益。用 profile、cache stats 和 P99 验证。

## 5. 动态字段

严格模式把 schema 漂移变成显式 400，动态模式方便但可能 mapping explosion。受控方案包括 schema 审批、dynamic template、字段上限、`flattened` 和拒绝率告警；`flattened` 会牺牲部分类型化查询能力。

## 6. 映射迁移

旧 segment 已按旧类型编码，更新 mapping 不能重写。建 V2 索引和模板，reindex 历史数据，双写或重放增量，比较数量/时间水位/checksum/查询，再原子切别名；保留 V1 只读作为回滚，确认后按保留策略清理。

## 7. 字段爆炸事故

先暂停产生动态字段的来源并限流，保存 mapping 大小、字段增长、master/pending tasks、heap/GC、写拒绝与发布记录。短期用模板/严格模式阻止新增，长期重建到预定义或 flattened 模型。验证业务 SLO、字段数、堆、cluster state、400 比例和关键查询，灰度失败时回切旧别名。
