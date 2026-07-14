# 生产者批处理、压缩与可靠性参考要点

## 1. 两个成功边界

`produce()` 成功通常只表示进入客户端缓冲；队列满、序列化失败或参数错误可能同步失败。delivery callback 成功表示 Broker 按 `acks` 条件确认，并给出 partition/offset。实验用 120 个坐标和 high watermark 交叉验证。它仍不证明下游处理，生产要把投递和业务完成指标分开。

## 2. `acks=all`

它等待当时 ISR 中的副本，而不是固定“三台”。RF=1 时也会成功。要描述单机容错，通常需 RF≥3、`min.insync.replicas≥2`、Producer `acks=all`，并避免非干净选举。副作用是 ISR 不足时写入失败；生产应监控 ISR shrink、UnderReplicatedPartitions 和错误率。

## 3. 批处理取舍

linger 给更多 record 聚批时间，较大 batch 降低请求开销，压缩对重复数据尤其有效；代价是排队延迟、缓冲内存、压缩 CPU 和更大的失败重试单位。证据应是固定负载下的请求数、batch size、发送字节、CPU、P50/P99 与错误，而不是只看吞吐。

## 4. 幂等边界

幂等 Producer 能让 Broker 根据 Producer ID 和序号过滤同一会话、同一 partition 的重试 batch。业务请求重放、两个 Producer 实例、超过状态生命周期或下游重复副作用不在这个保证内。业务仍需稳定 event_id、唯一约束或幂等状态机，并对冲突结果可观测。

## 5. 性能验证

100 条小样本可能没有填满 batch，缓存预热和单次网络抖动会支配结果。应使用代表性 key/value 大小与压缩率，分阶段预热，多轮比较吞吐、端到端延迟、delivery error、请求/batch 指标、CPU、网络与 Broker 写入。还要验证故障和队列满时的尾延迟。

## 6. 重试与背压

无限或高并发重试会增加请求、占满内存并放大 Broker/网络故障，形成重试风暴。客户端应设置总体 delivery deadline、指数退避、有限缓冲和明确失败出口；上游需限流或降级。恢复后逐步放量，并验证错误率、队列深度和 ISR，而不是同时释放全部积压。
