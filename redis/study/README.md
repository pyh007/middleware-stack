# Redis 可重复学习实验室

这套课程把 Redis 的数据路径、并发边界、持久化、高可用和缓存事故连接到可重复证据，目标是既能回答机制与取舍，也能按 Runbook 定位和恢复生产问题。

## 从这里开始

```bash
make -C redis help
make -C redis up
make -C redis all
make -C redis review
```

`all` 约需 1～2 分钟，只运行安全的单节点实验。每个实验先清理自己的 `lab:redis:<模块>:` 前缀，结束后再次清理；不会执行 `FLUSHDB` 或删除数据卷。

## 八模块路线

1. [数据结构与业务建模](labs/01-data-structures/README.md)：类型、编码转换与建模成本。
2. [过期淘汰与内存生命周期](labs/02-expiration-eviction/README.md)：TTL 状态、内存计量与淘汰策略。
3. [性能热点与可观测性](labs/03-performance/README.md)：往返、Pipeline、热点、大 Key 与诊断信号。
4. [并发事务 Lua 与分布式锁](labs/04-concurrency/README.md)：丢失更新、WATCH、Lua 和锁所有权。
5. [持久化重写与恢复窗口](labs/05-persistence/README.md)：RDB、AOF、重写与崩溃恢复。
6. [复制 Sentinel 与 Cluster](labs/06-replication-cluster/README.md)：复制偏移、选主、槽位和迁移。
7. [容量安全备份与生产运维](labs/07-production-ops/README.md)：容量采样、连接、ACL 和恢复演练。
8. [缓存事故综合实战](labs/08-incident-capstone/README.md)：穿透、击穿、雪崩和乱序回填。

辅助入口包括 [综合事故题](cases/production-incident/README.md)、[面试题库](interview/questions.json)、[主动回忆方法](review/README.md) 和 [生产排查 Runbook](runbooks/diagnosis.md)。

## 学习闭环

每个模块按同一顺序学习：先闭卷回答 `exercises.md`，预测实验结果，运行命令，解释输出断言，修改一个变量重跑，最后用 `answers.md` 的“结论 → 机制 → 证据 → 边界 → 副作用 → 生产验证”校准表达。只有能独立复现并解释证据才达到 L2。

## 安全边界

- 默认实例只映射 `127.0.0.1:6379`，密码 `redis123456` 仅供本地学习，不能复用到生产。
- `make -C redis reset` 通过 `SCAN` + `UNLINK` 仅删除 `lab:redis:*`，不会清空数据库。
- `eviction-pressure` 使用 `127.0.0.1:6389` 的 8 MiB 临时实例；结束自动删除。
- `crash-recovery` 会强杀默认 Redis，造成短时不可用，但保留命名卷并自动拉起。
- `sentinel-failover`、`cluster-reshard` 使用不暴露端口的独立拓扑，结束自动清理。
- 以上四个显式命令不属于 `all`。遗留资源可用 `make -C redis special-down` 清理。

## 遗忘后的 15 分钟回归

用 [CHEATSHEET.md](CHEATSHEET.md) 在 3 分钟恢复地图，运行 `make -C redis review` 闭卷回答三题，用 7 分钟重跑最薄弱模块，再用 5 分钟把输出和掌握等级登记到 [ROADMAP.md](ROADMAP.md)。复习日约为第 1、3、7、14、30、90 天。

