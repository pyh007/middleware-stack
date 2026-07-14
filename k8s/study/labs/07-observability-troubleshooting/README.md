# 07 可观测性与标准排障路径

## 学习目标

建立从业务症状到 Kubernetes 对象、节点和应用的证据链；熟练使用 get、describe、Events、logs、`--previous`、EndpointSlice 和临时调试容器，并理解日志、指标、追踪和审计各自回答的问题。

## 核心机制

status/conditions 描述当前对象状态，Events 是有保留期限的离散线索，容器日志来自标准输出和错误，指标描述时间序列，追踪串联请求路径。Kubernetes 不把容器日志永久保存；容器重启后常需 `logs --previous`，节点或 Pod 消失后依赖集中日志。排障应从用户影响和最近变化出发，先定位故障层次，再做最小验证。

## 实验

```bash
make -C k8s observability
```

实验发出真实 Service 请求，断言业务响应，并同时收集 Deployment/Pod 状态、Service/EndpointSlice、按时间排序 Events 和应用访问日志。执行前先写下你认为“请求成功”至少需要的五个证据点，再与输出比较。

## 标准诊断顺序

确认范围与时间线；检查 Deployment condition 和 Pod phase；查看 describe 与 Events；按容器和前一实例读取日志；检查 Service/EndpointSlice 与依赖；最后看节点资源和控制平面。止损动作前先保存短生命周期证据，变更后必须验证业务指标并准备回滚。完整流程见 [生产排障 Runbook](../../runbooks/production-troubleshooting.md)。

## 生产边界与完成标准

生产需集中日志、指标告警、分布式追踪、审计和明确保留周期，同时控制标签基数和成本。完成本模块应能在十分钟内形成时间线，区分应用、配置、网络、调度、存储和节点故障，给出止损、验证、回滚与长期改进，而不只是执行一次重启。
