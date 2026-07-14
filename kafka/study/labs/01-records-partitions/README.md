# 01 记录、主题、分区与顺序

## 学习目标

- 解释 record、topic、partition、offset、key 与 header 在数据路径中的作用。
- 用投递结果证明相同 key 的分区边界和 partition 内顺序。
- 能为订单、账户等业务选择 key，并说明扩分区带来的顺序影响。

## 运行实验

先预测三个账户会落到哪些分区，再执行：

```bash
make -C kafka records-partitions
```

脚本重建三分区 `lab_kafka_records_partitions`，写入 12 条带 key 的记录，收集 Broker 返回的 partition/offset，并断言每个 key 只落在一个 partition、同 partition 的 offset 递增。

## 核心机制

Producer 先获取 Topic 元数据，再由显式 partition 或 partitioner 选择分区。Broker 的 partition Leader 把 record batch 追加到日志，offset 是该日志中的位置。Kafka 的有序性边界是单 partition：同 key 在分区数和 partitioner 不变时通常进入同一分区，因而能按追加顺序读取；不同 partition 没有统一的先后坐标。

key 是业务设计，不只是技术参数。账户余额事件通常用 account_id，使同一账户串行；若用随机 key，会丢失账户内顺序；若所有记录用常量 key，又会形成单个热点 partition。没有 key 时分配器可能使用粘性批次策略，不能据此推导业务实体顺序。

## 观察证据与修改变量

关键证据是 delivery callback 中的 `(key, partition, offset)`，不是客户端发送循环的序号。将分区数从 3 改为 5，先预测已有 key 的映射能否稳定；再增加一个没有 key 的记录，说明为什么它不能获得账户级顺序保证。

## 生产边界

- 扩分区通常不可逆，且会改变 key 到 partition 的取模空间；需要版本化路由或接受迁移期边界。
- partition 数提高并行能力，也增加文件、Leader、Consumer assignment 和恢复成本。
- 全局顺序往往意味着单 partition，从而牺牲吞吐与可用性；先确认业务是否只需实体内顺序。
- Schema、key 规范、partitioner 版本和热点分布都应纳入变更评审。

## 完成标准

- [ ] 不看材料画出 record 从 Producer 到 partition 日志的路径。
- [ ] 能从实验输出证明顺序边界，而不是只说“Kafka 有序”。
- [ ] 能为一个真实业务选择 key，并说明热点、扩分区和空 key 的后果。
- [ ] 能回答 [练习题](exercises.md)，再与 [参考要点](answers.md) 对照。
