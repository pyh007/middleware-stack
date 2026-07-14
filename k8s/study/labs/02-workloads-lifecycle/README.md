# 02 工作负载与生命周期

## 学习目标

根据业务生命周期选择 Pod、Deployment、StatefulSet、DaemonSet、Job 和 CronJob；理解滚动更新、修订记录、重启策略、优雅终止及 startup/readiness/liveness 三类探针的不同职责。

## 核心机制

Deployment 用新的 PodTemplate hash 创建 ReplicaSet，并按照 strategy 控制新旧副本比例。Job 关注成功完成次数，不要求进程永久运行。startupProbe 保护慢启动应用；readinessProbe 决定是否进入 Service 端点；livenessProbe 只处理进程失活，连续失败会触发容器重启。把依赖故障写进 liveness 可能造成级联重启。

## 实验

```bash
make -C k8s workloads
```

实验同时运行 Deployment 和一次性 Job，通过修改环境变量触发真实 rollout，断言修订增加和 Job 完成。执行前预测新旧 ReplicaSet 数量以及 Job Pod 的最终 phase。探针故障必须显式运行：

```bash
make -C k8s probe-failure
```

它把 readiness 路径改错，保存未就绪和 Events 证据，再恢复配置。

## 生产边界

rollout 成功只说明 Kubernetes 条件满足，不代表业务错误率、延迟和数据兼容性满足发布标准。生产还需合理的 `terminationGracePeriodSeconds`、preStop、连接摘除、数据库变更兼容、灰度指标和可执行回滚。探针超时和阈值应根据启动与尾延迟分布设置，不能照抄固定数字。

## 完成标准

能为 HTTP 服务、批处理任务、节点代理和有状态节点选择控制器；能解释三类探针失败后的不同结果；能通过 rollout history、ReplicaSet 和 Events 诊断发布；能设计包含成功指标、终止指标和回滚验证的上线步骤。
