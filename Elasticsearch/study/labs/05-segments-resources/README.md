# 05 段合并缓存与资源

## 学习目标

- 能解释不可变 segment、删除墓碑、merge 和磁盘放大的关系。
- 能区分 request/query 缓存的命中条件，不把低命中率简单归咎于配置。
- 能联合 heap/GC、文件系统、merge、线程池 queue/rejected 和业务延迟诊断。
- 能说明 force merge 只适合不再写入索引，并评估临时磁盘与 I/O。

## 运行实验

```bash
make -C Elasticsearch segments-resources
# 显式资源操作，默认 all 不包含
make -C Elasticsearch force-merge
```

安全实验分三批写入并各自 refresh，观察 segment 与 request cache；同一 size=0 聚合执行两次后断言 cache hit 增长，并采集 JVM、GC、磁盘和 search 线程池。显式实验把隔离索引设为只读后合并到一个段。

## 核心机制

Lucene segment 一旦写成即不可变，更新本质是新增版本并标记旧文档删除。后台 merge 读多个旧段、写新段、回收删除，需要 CPU、I/O 和临时磁盘；refresh 过频会产生更多小段。请求缓存以分片结果为单位，通常更适合重复的 size=0 查询；段变化、请求变化和低复用都会降低命中。

heap 高并不自动等于泄漏，必须看 GC 后基线、停顿、breaker 和请求形状。线程池 rejected 是背压信号，扩大队列通常只延迟失败并占更多堆。

## 观察证据

- 三批 refresh 后存在可观察 segment；重复聚合让 request cache hit_count 增长。
- 节点证据包含 heap 使用率、old GC 次数、可用磁盘、search queue/rejected。
- 显式 force merge 前后段数下降到 1，且写 block 已设置。

## 修改实验

把每批 10 条改为每条都 refresh，先预测 segment 与耗时；再让查询每次带不同值，观察缓存命中。不要把 force merge 加入安全 `all`，并解释为何本地小索引的耗时不能代表生产。

## 生产边界

活跃索引 merge 由系统管理；手工 force merge 可能使超大段难以继续合并、占满磁盘并恶化快照/恢复。缓存优化要与新鲜度、段稳定、heap 和请求复用一起评估。任何资源调优都需业务 P99、吞吐、错误率和数据正确性共同验收。

## 完成标准

- [ ] 能画出 refresh 产生段、更新留墓碑、merge 回收的过程。
- [ ] 能证明一次 cache hit，并解释何时不会命中。
- [ ] 能从多种资源信号给出诊断顺序。
- [ ] 能写出 force merge 的适用条件、影响、验证与回滚/停止条件。
