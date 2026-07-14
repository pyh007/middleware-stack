# Kafka 数据与状态恢复 Runbook

## 恢复目标

先为每类流定义 RPO/RTO：支付等不可丢事件可能要求 RPO=0；可重算指标可接受更大 RPO。确认恢复对象是 Broker 日志、Topic 配置、ACL、Schema、Consumer Group 位点，还是下游物化结果；它们不是同一份状态。

## 备份与演练

跨集群复制或对象存储导出必须同时保存消息 key、value、headers、timestamp、原 partition/offset 证据，以及 Topic 配置、ACL 和 Schema 版本。Consumer Group 位点要独立记录。Broker 数据目录不能在运行中简单复制后声称可恢复；文件、元数据与一致性边界必须由受支持方案保证。

## 受控恢复

1. 隔离目标环境并验证容量、版本、认证与网络。
2. 重建 Topic 的 partition、RF、cleanup/retention 和 `min.insync.replicas`。
3. 先恢复小时间窗到新 Topic，核对条数、key 分布、校验值和业务不变量。
4. 用新 Group 从明确位点试消费，验证幂等和下游副作用。
5. 灰度切换生产/消费入口，持续对账；保留旧环境直到超过回退窗口。

## 回滚与验收

恢复过程中不覆盖唯一可信副本。回滚是停止新入口、恢复旧路由和原 Group 位点，而不是再次无依据 reset。验收必须给出恢复记录数、唯一 event_id 数、首尾时间、失败/DLQ 数、Topic 配置差异和实际 RTO/RPO。

本地 [应用级导出恢复实验](../labs/07-production-ops/README.md) 会故意删除并重建隔离 Topic；它只证明业务 payload 可重放，不代表完整 Kafka 灾备。
