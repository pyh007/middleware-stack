# Kafka 综合事故参考分析

## 结论与证据链

StatefulSet Ready=0 表明控制器未获得可用 Kafka Pod；UI Running 只说明 UI 进程本身存活。若 PVC Bound、镜像已拉取、容器进入 Running 后以退出码 1 终止，而 `logs --previous` 指向 `/opt/kafka/logs` 无法创建，应把直接根因定位为 Kafka JVM 运行时日志目录不可写或空间不足，而不是探针或 Service。

恢复应优先保留 `/var/lib/kafka/data` PVC。课程清单把可丢失的 GC 日志放到受限的内存型 `emptyDir`。修复后还要继续验证探针：Pod 内 CLI 应走 INTERNAL `29092`，且 advertised 地址必须使用 `publishNotReadyAddresses` 的 Headless Pod DNS；若返回普通 Service，未 Ready Pod 没有可用 Endpoint，会形成启动闭环。副作用是 GC 日志占用 Pod 内存且随 Pod 删除消失；生产应接入标准输出或持久日志采集，并对节点磁盘、inode 和 emptyDir 使用量告警。

## 生产边界

单 Broker/Controller 没有副本与 quorum 冗余，Kubernetes 重建 Pod 不能等价于 Kafka 高可用。长期措施至少包括多节点 KRaft、反亲和与拓扑分散、ISR/under-replicated partitions 监控、容量水位、认证加密、NetworkPolicy、备份恢复和滚动升级演练。RPO 要由 ack、min ISR、副本和磁盘故障组合定义；RTO 要通过真实恢复演练测量。

## 验证与回滚

验证顺序是 Broker STARTED、INTERNAL listener CLI、Pod Ready、Service EndpointSlice、消息生产消费、消费者 offset、业务指标和告警恢复。若新清单引入内存压力，应回滚 StatefulSet PodTemplate，并把日志改到具有容量与采集策略的专用卷；任何回滚都不得删除既有 PVC。
