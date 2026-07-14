# 积压、重复与丢数声称综合参考要点

## 1. 统计口径

Producer 成功可能包含同一业务意图的多次发送，业务表可能按 event_id 去重，也可能有失败、DLQ 或尚未处理。实验中 20 条 Kafka records 对应 18 个 event_id，全部消费且 lag=0。结论必须先统一 record、唯一事件和业务成功口径，再谈丢失。

## 2. 证据链

从稳定 event_id/trace_id 开始，关联 Producer delivery 的 topic/partition/offset、Broker log-end/保留状态、Group committed/assignment、应用处理结果、DLQ 和业务事务 ID。partition+offset 唯一标识 Kafka 记录位置，event_id 标识业务意图。生产需保存时间窗和配置/故障变化。

## 3. 扩容条件

存在未被利用的 partition，单 Consumer 是瓶颈且下游有余量时，扩容可增加消费并行度。实例已多于 partition、热点集中单分区、瓶颈是数据库/远端接口或频繁 rebalance 时，扩容无效甚至加重故障。先比较生产率、消费率、assignment 和下游饱和度，再小步扩。

## 4. 自动提交窗口

自动提交可能在应用业务真正完成前推进 committed offset；随后进程崩溃或下游事务失败，重启从更后位置继续，lag 看似下降但业务缺失。应把提交与完成绑定，或使用幂等 inbox/事务方案。生产验证必须同时看处理成功和位点，而不是只看 lag。

## 5. 重放控制

先有稳定 event_id、唯一约束/状态机、重复结果审计和副作用评估；保存原 Group 位点与目标时间窗。用新 Group 或复制 Topic 小流量重放，对账成功、重复、失败和 DLQ，再逐步放量。出现重复扣款、错误率或下游饱和时立即停止新入口并恢复原路由。

## 6. 分阶段处置

五分钟冻结破坏证据的变更、保存分区位点与业务影响并保护保留窗口；三十分钟修复下游/再均衡瓶颈、在幂等前提下灰度追积压并持续对账；长期建立稳定 event_id、处理后提交、分区级 lag/最老年龄、rebalance 和业务成功监控，定期做故障与恢复演练。完整版本见 [案例答案](../../cases/production-incident/solution.md)。
