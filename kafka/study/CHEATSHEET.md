# Kafka 15 分钟重返速查

这张图只恢复知识坐标；结论必须回到实验验证。

## 数据路径

```text
Producer record(key,value,headers)
  → metadata/partitioner → client batch/compress → partition Leader append
  → ISR replicate → acks response → Consumer fetch → business process → commit next offset
```

- Topic 是逻辑流，partition 是有序追加日志和并行单位，offset 只在单 partition 内有意义。
- key 决定相关事件能否进入同一顺序边界；扩分区可能改变 key 映射，不能承诺全局顺序。
- Leader 处理读写，Follower 追赶；ISR 是当前足够同步的副本集合，不是永久成员名单。

## 生产与可靠性

- `acks=all` 等待当前 ISR，不代表一定有三份；结合 RF 与 `min.insync.replicas` 才能描述容错。
- 幂等 Producer 抑制单会话内因重试产生的日志重复，不等于业务请求天然幂等。
- `linger.ms`、`batch.size`、压缩通常提高吞吐和网络效率，也增加等待、内存与 CPU 成本。
- delivery report 是 Broker 确认，不是消费者处理成功或业务落库成功。

## 消费组与语义

- 同一 Group 内一个 partition 同时只分给一个成员；并行度上限受 partition 数限制。
- `lag = log-end-offset - committed-offset`，要逐 partition 看趋势；低 lag 也不证明业务正确。
- 先提交后处理倾向至多一次；先处理后提交倾向至少一次；故障窗口必须用时间线解释。
- Kafka 事务可原子提交 Kafka 输出和输入位点；跨数据库仍需 outbox、幂等键或补偿。

## 存储与复制

- partition 由多个 segment 组成；保留按时间/大小清理，清理是异步的。
- compact 保留每个 key 的最新逻辑状态，tombstone 表示删除；它不保证旧值立即物理消失。
- KRaft 管理集群元数据；Controller quorum 与数据分区副本是两类不同状态。
- 非干净 Leader 选举可能换可用性但带来已确认数据风险，生产默认应谨慎。

## 事故排查

```text
业务影响/时间窗 → 生产成功证据 → partition log-end → Group committed/lag
→ assignment/rebalance → Broker/ISR/磁盘/网络 → event_id 业务对账
```

- 不要在证据不完整时 reset offset、扩分区、删除 Topic 或反复重启消费者。
- 积压先判断“生产变快”还是“消费变慢”；再看热点分区、错误重试、下游延迟和再均衡。
- “条数不一致”先统一口径：Kafka records、唯一 event_id、成功业务结果、DLQ 各是不同集合。

关键入口：[事务实验](labs/04-delivery-semantics/README.md)、[故障切换](labs/06-replication-kraft/README.md)、[生产排查](runbooks/diagnosis.md)、[恢复](runbooks/recovery.md)、[综合事故](cases/production-incident/README.md)。
