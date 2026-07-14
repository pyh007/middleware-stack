# 工作负载与生命周期参考答案

1. Deployment 适合可替换的无状态副本；StatefulSet 适合需要稳定序号、网络身份或独立卷的副本；DaemonSet 保证目标节点各有一个实例；Job 运行到成功完成。选择依据是身份、状态、放置范围和完成语义，不是应用名称。
2. readiness 失败通常不重启容器，但 Pod 不再 Ready，并从普通 Service 可用端点移除；liveness 连续失败由 kubelet 重启容器；startup 未成功前会抑制另外两种探针，给慢启动留窗口。
3. 依赖短暂故障会让所有应用副本同时重启，制造冷启动、连接风暴并丢失现场。liveness 应判断本进程是否不可恢复，依赖可用性通常放在 readiness 或业务降级逻辑。
4. Kubernetes 不理解订单成功率、消息兼容性和数据正确性。发布要同时验证工作负载 condition、错误率、尾延迟、容量和关键业务路径。
5. Deployment 的 PodTemplate 改变后 hash 改变，控制器用新 ReplicaSet 管理版本。容器是由声明重建的，手工修改既不可审计，也会在重建后丢失。
6. 非零退出会按策略重试，超过 backoffLimit 后 Job 失败。任务必须能识别已完成步骤或使用幂等写入，否则重试可能产生重复副作用；生产还需设置 deadline 和失败告警。
