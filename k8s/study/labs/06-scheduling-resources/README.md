# 06 调度、资源与可靠性

## 学习目标

理解 requests、limits、QoS、ResourceQuota、LimitRange 与调度的关系；掌握 nodeSelector、亲和性、污点容忍、拓扑分布、PDB 和 HPA 各自解决的问题及边界。

## 核心机制

Scheduler 主要用 requests 与节点可分配资源、约束和优先级决定放置，并不按实时使用率直接调度。CPU 超过 limit 通常被节流，内存超过 limit 可能 OOMKilled。requests 与 limits 的组合影响 Guaranteed、Burstable、BestEffort QoS，在节点压力下影响驱逐顺序。ResourceQuota 控制 Namespace 总量，LimitRange 提供默认值或约束单个对象。

## 实验

```bash
make -C k8s scheduling
```

实验创建 LimitRange、ResourceQuota 和显式资源的 Deployment，断言调度节点、Burstable QoS 及 CPU 请求/上限。不可调度场景是显式故障实验：

```bash
make -C k8s pending-failure
```

它创建远超节点容量的请求，等待 `PodScheduled=False/Unschedulable`，打印调度 Events 后清理。

## 生产边界

requests 太低会造成节点超卖、争抢和驱逐，太高会降低装箱率并制造 Pending；limits 太紧会节流或 OOM。HPA 依赖可用、可信的指标与合理 requests，PDB 只约束自愿中断，不能阻止节点突然故障。生产容量要同时考虑常态、峰值、滚动升级 surge、节点故障余量和扩容延迟。

## 完成标准

能从 Events 解释 Pending；能根据业务内存和延迟基线给出 requests/limits 起点及验证方法；能区分调度约束、运行时限制和 Namespace 配额；能设计多副本拓扑分散、PDB 与扩容策略并说明不可用边界。
