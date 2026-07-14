# Kubernetes 生产排障 Runbook

## 触发与目标

适用于发布失败、Pod 不就绪、重启、Service 不通、Pending、存储挂载失败和节点资源异常。目标是先控制用户影响并保留证据，再定位第一个失败层，恢复后验证业务与数据，不以“Pod 重新 Running”作为结束条件。

## 现场保护

记录告警时间、影响范围、当前版本和最近变更；导出相关对象 YAML、describe、Events、当前及上一实例日志。不要先删除 Namespace、PVC 或批量重启。输出可能包含 Secret、Token、环境变量和业务数据，归档前必须脱敏并遵守保留权限。

## 诊断顺序

1. 业务：成功率、错误码、尾延迟、积压和关键路径是否受影响。
2. 发布：Deployment/StatefulSet condition、generation、observedGeneration、修订和副本数。
3. Pod：phase、PodScheduled/Ready、container waiting/lastState、restartCount 和探针。
4. 事件与日志：describe、按时间 Events、当前日志、`--previous` 和相关 sidecar。
5. 网络：DNS、Service port/targetPort、selector、EndpointSlice、NetworkPolicy 和应用监听。
6. 存储：PVC Bound、挂载 Events、StorageClass、节点拓扑、容量和只读错误。
7. 节点与控制面：Ready、Pressure、allocatable、运行时、API 延迟和控制器积压。

## 止损、验证与回滚

止损可以是停止发布、回滚已验证版本、摘除坏端点、限流或扩容，但每项都要写出影响和撤销方法。变更后同时验证 Kubernetes condition、应用接口、业务指标、数据一致性和告警；观察至少覆盖一个业务峰值或明确窗口。回滚前确认配置、数据格式和数据库变更是否向后兼容。

## 升级与复盘

若故障涉及容量，记录 requests/limits、节点余量、surge 和扩容耗时；涉及状态，定义实际 RPO/RTO 并执行恢复；涉及权限，审计身份和授权变化。复盘包含时间线、影响、检测缺口、直接与系统性根因、长期措施、负责人和可验证截止日期。
