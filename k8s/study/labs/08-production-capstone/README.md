# 08 生产审计与 Kafka 综合项目

## 学习目标

把工作负载、网络、配置、存储、资源、安全和可观测性串成一次生产评审；能区分 Kubernetes 控制器健康、Kafka 进程健康和 Kafka 数据可靠性；形成带止损、验证、回滚、RPO/RTO 的事故报告。

## 安全审计实验

```bash
make -C k8s capstone-audit
```

实验渲染根目录 Kafka Kustomize 清单，断言 StatefulSet、PVC 模板、资源和三类探针，拒绝 `latest` 镜像，并执行服务端 dry-run。它不会创建、更新或删除实际资源。先从清单画出 `Kafka UI → Service → kafka-0 → PVC`，再运行审计核对。

## 真实综合案例

现有 Kafka 使用 `middleware-stack` Namespace 和持久数据，部署属于显式重资源操作：

```bash
make -C k8s kafka-status
make -C k8s kafka-capstone
```

第一条只读采集状态，第二条应用根目录清单、在旧 revision 阻塞更新时重建 `kafka-0`、等待 Kafka 与 UI 就绪并执行 Kafka CLI 验证。它不会自动删除 PVC，也不在 `make all` 中。具体事故任务、报告结构和参考解法见 [Kafka 综合事故](../../cases/kafka-incident/README.md)。

## 生产边界

单节点 Kafka 只用于学习，不能证明 Broker 复制、KRaft quorum、ISR、跨故障域和滚动升级。Kubernetes 让 Pod 重建，不会自动保证 Kafka 无数据损失。生产评审还需镜像 digest、NetworkPolicy、Secret、PodDisruptionBudget、反亲和、容量、备份、监控、升级兼容和恢复演练。

## 完成标准

能在十五分钟内完成清单风险审计；能从 Pod lastState、日志、PVC、Events 和节点资源定位启动失败；能说明恢复动作对数据和可用性的影响；能提交包含时间线、根因、止损、恢复验证、回滚和长期措施的综合报告。
