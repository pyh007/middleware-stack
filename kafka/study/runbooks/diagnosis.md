# Kafka 积压、重复与丢数声称排查 Runbook

## 1. 分级与冻结现场

记录开始时间、受影响业务、Topic/Group、积压增长率、错误率、SLO 和最近变更。确认数据保留时间是否覆盖预计恢复窗口。冻结扩分区、offset reset、Topic 删除和无序重启；这些动作会改变关键证据或放大重复风险。

## 2. 生产端证据

检查发送尝试数、delivery 成功/失败、超时、重试、缓冲队列、批次、压缩和每个 partition 的写入速率。抽取稳定 event_id 对应的 topic/partition/offset；只有应用日志“调用成功”而没有 delivery 结果时，不能证明 Broker 已确认。

## 3. Broker 与复制证据

查看 Topic 配置、Leader、RF、ISR、UnderReplicatedPartitions、OfflinePartitions、请求延迟、网络、磁盘利用率和日志目录错误。将 `acks`、`min.insync.replicas`、故障时 ISR 和非干净选举配置放在同一时间线上判断确认风险。

## 4. 消费与业务证据

逐 partition 记录 log-end-offset、committed-offset 与 lag 趋势；查看 Group 状态、成员数、assignment、rebalance 原因、poll 间隔、处理延迟、错误重试和下游连接池。对账必须区分 Kafka record 数、唯一 event_id 数、业务成功数和 DLQ 数。

## 5. 止损顺序

先处理下游超时、毒消息和资源瓶颈；再把有效实例数与 partition 数匹配，并调整已经压测的 poll/批次参数。只有稳定 event_id 和幂等处理准备完毕后才重放。积压的预计清空时间可用 `backlog / (消费速率 - 生产速率)` 粗估，分母小于等于零时必须先提高净处理能力或限流。

## 6. 验证与回滚

至少验证一个完整业务周期：lag 持续下降、rebalance 恢复基线、错误率和下游延迟正常、ISR 完整、抽样 event_id 在 Kafka/处理日志/业务库一致。变更按单 Group 或小流量灰度；回滚条件预先定义为重复副作用、错误率上升、lag 斜率恶化或 Broker 资源逼近红线。

命令语法可在本地用 `make -C kafka production-ops` 和 [综合实验](../labs/08-incident-capstone/README.md) 练习；生产环境应使用组织批准的只读平台和变更流程。
