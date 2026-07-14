# 05 存储、PVC 与有状态工作负载

## 学习目标

理解 Volume、PV、PVC、StorageClass、访问模式、绑定时机和回收策略；能区分“Pod 重建后数据仍在”和“应用已经具备高可用、备份与灾难恢复”。理解 StatefulSet 提供的稳定身份与存储语义。

## 核心机制

PVC 描述工作负载对容量、访问模式和存储类别的申请，StorageClass 决定动态制备器、绑定模式、扩容能力和默认参数，PV 表示实际供应的存储。`ReadWriteOnce` 描述卷可被单节点读写，不等于只能挂载给一个 Pod。删除 PVC 后底层卷是否保留取决于 PV reclaimPolicy；卷快照、应用一致性备份和跨区域恢复是不同层次的问题。

## 实验

```bash
make -C k8s storage
```

实验创建 PVC，由 writer Job 写入确定内容，再由另一个 reader Pod 挂载同一 PVC 并读取，断言 PVC 为 Bound、数据跨工作负载可见。执行前先预测 `WaitForFirstConsumer` StorageClass 下 PVC 何时绑定，并查看 PV 的 StorageClass 与 reclaimPolicy。

## 生产边界

课程 reset 会删除整个隔离 Namespace，其中 PVC 及底层数据可能随 `Delete` 策略消失。生产删除 PVC、StatefulSet 缩容、StorageClass 迁移前必须确认保留策略、备份、恢复演练、RPO/RTO 和权限。StatefulSet 不理解数据库复制、Kafka ISR 或文件系统一致性，应用级冗余仍需单独设计。

## 完成标准

能沿着 Pod → volumeMount → PVC → PV → StorageClass 找到真实存储；能解释访问模式和回收策略；能在不删除数据的前提下替换消费者工作负载；能为生产状态服务写出备份、恢复、容量、监控与删除保护方案。
