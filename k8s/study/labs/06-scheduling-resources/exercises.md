# 调度与资源练习题

1. Pod Pending 时为什么不能只看节点当前 CPU 使用率？Scheduler 主要看什么？
2. requests 和 limits 分别影响哪些阶段，CPU 与内存超限后的典型现象有何不同？
3. Guaranteed、Burstable、BestEffort 如何形成，在节点压力下有什么意义？
4. ResourceQuota 与 LimitRange 分别控制什么，为什么两者常组合使用？
5. PDB 能否阻止节点宕机导致副本减少？它真正约束哪类中断？
6. HPA 已经启用，为什么仍可能无法应对突发流量？
