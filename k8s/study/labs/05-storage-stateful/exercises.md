# 存储与有状态练习题

1. PVC 长时间 Pending 时，按什么顺序检查 StorageClass、绑定模式、容量和调度？
2. `ReadWriteOnce` 是否意味着只能被一个 Pod 使用？它真正约束什么？
3. 删除 StatefulSet、Pod、PVC、PV 对数据的影响为什么不同？
4. StatefulSet 能提供哪些稳定性，又不能替应用解决哪些一致性和高可用问题？
5. 动态制备卷的 reclaimPolicy 为 Delete 时，误删 PVC 的风险是什么？
6. 卷快照为什么不一定等于数据库可恢复备份，怎样验证 RPO/RTO？
