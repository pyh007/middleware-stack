# 调度与资源参考答案

1. Scheduler 根据 Pod requests、节点 allocatable、已有请求、亲和性、污点容忍、拓扑和优先级等做可行性与打分，不直接用瞬时 CPU 使用率决定。排查应先读 PodScheduled condition 和调度 Events。
2. requests 影响调度和资源份额，limits 由运行时约束。CPU 超限一般被 throttling，延迟可能上升；内存超过限制常被 OOMKill。还应结合工作集、GC、尾延迟和重启原因验证。
3. 每个容器 CPU/内存 request 等于 limit 时可成为 Guaranteed；有部分声明通常是 Burstable；均无声明是 BestEffort。节点压力时 QoS、优先级和实际超额共同影响驱逐，但不能把 QoS 当绝对存活保证。
4. Quota 限制 Namespace 总请求、上限、对象数等，LimitRange 给容器默认值并约束最小最大。组合后既防止对象漏填资源，也限制团队总体消耗。
5. 不能。PDB 约束 drain、部分升级等自愿驱逐允许同时减少多少可用副本，不阻止机器断电、内核崩溃等非自愿故障。仍需副本和拓扑分散。
6. 指标采集和扩容有延迟，新 Pod 还需调度、拉镜像和预热；资源不足、最大副本、依赖瓶颈或错误 requests 也会限制效果。需要容量余量、压测和过载保护。
