# 文档映射与分析链练习题

先闭卷口述或写下答案，再运行实验，最后查看 `answers.md`。

1. 一条 JSON 文档写入后，`_source`、mapping 和倒排索引分别承担什么职责？
2. `text` 与 `keyword` 的索引和查询行为为何不同？商品名称、品牌、订单金额应如何选择？
3. analyzer 的三个阶段是什么？为什么索引期和查询期 analyzer 不一致会改变召回？
4. query context 与 filter context 如何影响 `_score`、缓存机会和表达意图？
5. `dynamic: strict` 与动态映射各有什么故障模式？怎样支持受控扩展属性？
6. 已有字段从 `keyword` 改为 `text` 时，为什么不能只更新 mapping？写出无停机迁移步骤。
7. 面试场景：上线后字段数从 500 涨到 50,000，堆和 cluster state 恶化。你如何止损、取证、修复和验证？

加练：修改 stop filter 前先写出预期 token；修改后保存实际结果，并解释为什么这会影响索引大小、召回或精度。
