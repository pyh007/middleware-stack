# 架构与调谐参考答案

1. 成功只表示请求通过认证、授权、准入并持久化。控制器还要创建下级对象，Scheduler 需要找到满足资源和约束的节点，kubelet 要拉取镜像、挂载存储并启动容器，探针和应用依赖也必须通过。
2. Deployment 管理发布策略和 ReplicaSet，ReplicaSet 维持指定数量的 Pod，Pod 是节点上运行容器的最小调度单位。可通过 `metadata.ownerReferences`、共同 label 和控制器创建事件证明关系。
3. 说明控制器还没有把最新期望状态处理并反映到 status。它可能只是短暂延迟，也可能因控制器或 API 故障停滞；需结合 conditions、Events 和控制器健康判断。
4. ReplicaSet 发现现实副本少于 spec 后创建替代 Pod。普通 Deployment Pod 是可替换实例，名称和 UID 会变化；需要稳定网络身份或独立存储时再评估 StatefulSet。
5. 脚本必须幂等，提交后等待可验证 condition，设置超时并在失败时保留 Events 和状态。最终一致不等于无限等待，也不等于忽略中间失败。
6. 结论应由实验支撑：spec 先变为三，generation 增加，控制器创建 Pod，observedGeneration 追平，availableReplicas 最终达到三。生产还要验证容量、PDB、流量和业务健康。
