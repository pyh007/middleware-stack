# Kubernetes 可持续学习实验室

这不是 YAML 清单收藏夹，而是一套面向面试与生产使用的训练系统。每个模块遵循：

```text
原理 → 预测 → 最小实验 → 证据 → 故障注入 → 修复 → 面试表达 → 生产边界
```

## 学习入口

先确认当前集群是本地实验环境，然后运行安全实验：

```bash
make -C k8s up
make -C k8s all
```

`all` 只操作 `k8s-study-*` Namespace。Pod 删除、错误探针、错误 Service selector、不可调度 Pod 和 Kafka 部署必须使用 `make -C k8s help` 中列出的显式命令。Kafka 使用独立的 `middleware-stack` Namespace 和 PVC，不属于安全全量任务。

## 八个模块

1. [集群架构、API 与控制器调谐](labs/01-architecture-reconciliation/README.md)
2. [工作负载与生命周期](labs/02-workloads-lifecycle/README.md)
3. [网络、Service 与服务发现](labs/03-networking-discovery/README.md)
4. [配置、身份、RBAC 与安全边界](labs/04-config-security/README.md)
5. [存储、PVC 与有状态工作负载](labs/05-storage-stateful/README.md)
6. [调度、资源与可靠性](labs/06-scheduling-resources/README.md)
7. [可观测性与标准排障路径](labs/07-observability-troubleshooting/README.md)
8. [生产审计与 Kafka 综合项目](labs/08-production-capstone/README.md)

前七个模块属于工作负载主线；控制平面、etcd、节点升级和多节点高可用属于集群运维扩展线。当前环境可以观察控制平面对象，但不会在共享 Docker Desktop 集群上执行节点中断或 etcd 恢复。

## 一次学习会话

建议每次 45～60 分钟：先闭卷回答 `exercises.md`，再读机制并运行 `lab.sh`；执行前预测对象的 `spec/status`、事件或网络端点；执行后修改一个变量，记录命令、证据和边界。达到 L2 必须能独立复现实验，达到 L3 必须能从 Events、状态、日志或 EndpointSlice 定位故障。

忘记后先读 [CHEATSHEET.md](CHEATSHEET.md)，执行 `make -C k8s review`，重跑最薄弱模块，再在 [ROADMAP.md](ROADMAP.md) 更新证据和复习日期。生产排障入口在 [runbooks](runbooks/production-troubleshooting.md)，综合事故在 [cases](cases/kafka-incident/README.md)。

## 环境与安全

- 默认上下文固定为 `docker-desktop`；其他本地上下文必须显式设置 `K8S_STUDY_ALLOWED_CONTEXTS`。
- 课程统一使用缓存友好的 `busybox:1.37`，避免用框架隐藏 Kubernetes 行为。
- reset 只删除名称前缀和课程标签同时匹配的 Namespace。
- Secret 示例值仅供本地实验；生产需使用外部密钥管理、轮换、审计和静态加密。
- `down` 只清理课程资源，不关闭用户的 Kubernetes 集群。
