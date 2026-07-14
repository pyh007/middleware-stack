# 04 交付语义、幂等处理与事务

## 学习目标

- 用故障时间线解释至多一次、至少一次与 Kafka exactly-once 语义。
- 实际 abort 一笔事务，比较 `read_uncommitted` 与 `read_committed`。
- 原子提交 Kafka 输出和输入 offset，并说明跨数据库边界。

## 运行实验

```bash
make -C kafka delivery-semantics
```

实验向单分区输入写 4 条。处理器先产生一条输出并发送输入 offset，随后主动 abort 并 seek 回原位置；第二次在一个事务内完成 4 条输出和 offset 提交。最终 `read_uncommitted` 看到 5 条数据记录，`read_committed` 只看到 4 条已提交记录，处理 Group 的 committed offset 为 4。

## 核心机制

先提交 offset 再执行业务，崩溃窗口可能跳过未完成业务，倾向至多一次；先执行业务再提交，崩溃窗口会重做，倾向至少一次。Kafka 事务让事务 Producer 写入的多个 partition 原子可见，并通过 `send_offsets_to_transaction` 把输入进度放进同一提交边界；`read_committed` Consumer 跳过 aborted 数据。

“Exactly once”必须写清系统边界。Kafka 事务无法回滚普通数据库、HTTP 调用或邮件。常用方案是业务唯一键/幂等状态机、数据库 outbox 后可靠发布，或把结果继续留在 Kafka 事务拓扑内。

## 观察证据与修改变量

关键证据是相同输出 Topic 在两种 isolation level 下的可见记录数，以及 Group committed offset。把验证 Consumer 改成 `read_uncommitted`，预测为何会看到 abort 输出；再思考处理后数据库提交、offset 提交前进程崩溃的结果。

## 生产边界

- `transactional.id` 必须稳定且每个并发实例唯一，否则会发生 fencing。
- 长事务增加未决数据、协调状态和 read_committed 等待，受事务超时限制。
- 业务幂等需要稳定 event_id、唯一约束、状态转移校验和可观察的冲突结果。
- 重放前先评估外部副作用；低 lag 不代表业务结果 exactly-once。

## 完成标准

- [ ] 能画出提交前后崩溃窗口并判定重复或跳过。
- [ ] 能解释 abort 数据为何仍占日志但对 read_committed 不可见。
- [ ] 能说明 Kafka 内 EOS 与跨数据库一致性的边界。
- [ ] 能为一个业务设计幂等键、失败记录和重放验证。
