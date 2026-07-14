# Redis 15 分钟核心速查

这是一张重新进入问题空间的地图，不代替模块原理和实验。

## 数据结构与建模

- Redis 类型决定命令语义，内部编码决定常数和内存；小 Hash/ZSet 会在阈值后转为哈希表/跳表。[编码实验](labs/01-data-structures/README.md)
- 先按访问模式选择 String、Hash、Set、ZSet、Stream，再估算单键大小、元素数、过期和热点风险。
- 多个逻辑对象塞进一个大 Key 会减少键开销，却放大阻塞、迁移和恢复成本。

## 生命周期与内存

- `TTL=-1` 是无过期，`TTL=-2` 是键不存在；到期删除由访问触发和后台采样共同完成。[TTL 实验](labs/02-expiration-eviction/README.md)
- `used_memory` 不等于数据净大小，还包含字典、过期表、缓冲区、复制积压和碎片。
- 淘汰是达到 `maxmemory` 后按策略回收，不是过期的同义词；生产切策略前先算可淘汰集合。

## 性能与观测

- Pipeline 减少网络往返，不减少命令执行量；批次过大增加队头阻塞和客户端缓冲。[性能实验](labs/03-performance/README.md)
- 顺序看业务延迟与错误率，再看 `INFO clients/stats/memory/commandstats`、SLOWLOG、LATENCY、CPU/网络。
- 热 Key 看请求集中度，大 Key 看 `MEMORY USAGE`、元素数和单命令复杂度；两者治理不同。

## 并发与一致性

- `MULTI/EXEC` 保证排队命令连续执行，但不自动回滚业务错误；WATCH 提供乐观冲突检测。[并发实验](labs/04-concurrency/README.md)
- Lua 在单实例内原子执行，长脚本会阻塞事件循环；Cluster 多键脚本要求同槽。
- 锁需 `SET NX PX`、唯一令牌、Lua 比较删除；仍要考虑超时、续租、主从切换和 fencing token。

## 持久化与恢复

- RDB 恢复快但损失窗口取决于快照频率；AOF 损失窗口取决于 fsync 策略，重写不会消除已确认窗口。[持久化实验](labs/05-persistence/README.md)
- `appendfsync everysec` 通常意味着故障时可能损失约 1 秒写入，不是零丢失承诺。
- 备份成功不等于可恢复；必须隔离恢复、核对业务记录并记录实际 RPO/RTO。

## 复制、Sentinel 与 Cluster

- 复制通常异步，偏移接近不等于业务已经端到端确认；读副本要接受陈旧读。[拓扑实验](labs/06-replication-cluster/README.md)
- Sentinel 发现主、协商选主、提升副本并重配旧主；客户端必须重新发现，quorum 不能只有教学环境的 1。
- Cluster 用 16384 槽分片；Hash Tag 让多键同槽，也可能制造热点槽；槽迁移期间客户端要处理 MOVED/ASK。

## 生产运维

- 容量从真实样本 `MEMORY USAGE` 出发，加键数量、增长、碎片、复制/AOF 缓冲和安全余量。[运维实验](labs/07-production-ops/README.md)
- 连接池上限必须结合应用实例数与 Redis `maxclients`；拒绝连接时先抑制重连风暴。
- 网络最小暴露、ACL 最小权限、Secret 轮换、TLS 和审计应一起设计；本地密码不是生产模板。

## 缓存事故

- 穿透：不存在数据反复回源；击穿：热点失效并发回源；雪崩：大量键同窗失效；三者证据与治理不同。[综合实验](labs/08-incident-capstone/README.md)
- 空值缓存/布隆过滤器、互斥重建/逻辑过期、TTL 抖动分别有一致性、复杂度和容量副作用。
- 先止损回源、保护源站，再修缓存；不能在源站已过载时直接全量预热。

## 生产排查顺序

```text
定义业务影响与时间线 → 冻结变更和保存现场 → 客户端/网络/Redis/主机分层
→ 找到资源或等待 → 小范围止损 → 验证正确性和延迟 → 灰度长期修复 → 演练回滚
```

详细命令见 [生产排查](runbooks/diagnosis.md)、[恢复演练](runbooks/recovery.md) 和 [容量安全检查](runbooks/security-capacity.md)。

