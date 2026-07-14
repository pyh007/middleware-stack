# 段合并缓存与资源练习题

先闭卷作答，再运行安全和显式实验。

1. 为什么 Lucene 更新文档会留下删除墓碑，磁盘不会立刻下降？
2. refresh 频率怎样影响 segment 数、merge、缓存、写吞吐和搜索新鲜度？
3. merge 为什么需要临时磁盘，它如何影响搜索与恢复？
4. request cache 适合哪些查询？段变化和请求参数如何影响命中？
5. heap 使用率高时如何区分正常缓存、聚合压力、字段膨胀和泄漏？
6. search/write rejected 出现时，为什么扩大 queue 通常不是根治？
7. 面试场景：只读历史索引小段很多、查询慢、磁盘余量 15%。是否 force merge？如何灰度与验证？

加练：把每批 refresh 改成每条 refresh，保存 segment、耗时和 cache 输出，再解释本机自动 merge 给实验造成的波动。
