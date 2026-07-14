# 工作负载与生命周期练习题

1. Deployment、StatefulSet、DaemonSet、Job 分别适合什么生命周期？
2. readiness 失败和 liveness 失败对容器、Pod Ready 与 Service 端点有什么不同影响？
3. 为什么把数据库暂时不可达作为 liveness 检查条件可能扩大事故？
4. Deployment rollout 完成后，为什么仍要观察业务指标和依赖兼容性？
5. 修改环境变量为何会产生新 ReplicaSet，直接修改运行中容器为何不可持续？
6. Job 的容器退出码非零时，restartPolicy、backoffLimit 和幂等性如何共同影响结果？
