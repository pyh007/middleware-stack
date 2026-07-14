# 生产审计与综合项目练习题

1. Kafka StatefulSet Ready=0 时，如何区分调度、存储、镜像、配置、探针和进程故障？
2. Kafka Pod 被 Kubernetes 重建，为什么不代表消息一定没有丢失？
3. 单节点 Kafka 即使有 PVC，仍缺少哪些生产可用性与数据可靠性能力？
4. ConfigMap 变更后 Kafka 为什么可能仍使用旧配置，怎样安全发布和回滚？
5. 清单使用固定 tag 后，为什么生产仍可能要求固定 digest？
6. 一次中间件事故恢复完成前，至少要验证哪些 Kubernetes、应用和业务证据？
