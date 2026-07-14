# Kubernetes 15 分钟重返地图

## 先恢复一条主线

客户端把期望状态提交给 API Server；对象持久化后，控制器持续比较 `spec` 与现实，Scheduler 为未绑定 Pod 选择节点，kubelet 让容器在节点上运行并回写 `status`。排障不要从“重启试试”开始，而要沿着对象关系寻找第一个不满足的条件。

```text
请求 → Service/DNS → EndpointSlice → Ready Pod → 容器端口 → 应用
声明 → API Server → 控制器 → Scheduler → kubelet → 容器运行时
数据 → VolumeMount → PVC → PV/StorageClass → 底层存储
身份 → ServiceAccount → RBAC → API 授权结果
```

## 十条高频检查

```bash
kubectl config current-context
kubectl get nodes
kubectl get deploy,rs,pod -n <ns> -o wide
kubectl describe pod <pod> -n <ns>
kubectl get events -n <ns> --sort-by=.lastTimestamp
kubectl logs <pod> -n <ns> --all-containers
kubectl logs <pod> -n <ns> --previous
kubectl get service,endpointslice -n <ns>
kubectl auth can-i <verb> <resource> --as=<identity> -n <ns>
kubectl get pvc,pv,storageclass
```

## 高频判断

- Deployment 管理无状态副本和滚动更新；StatefulSet 提供稳定序号、网络身份和独立存储，但不自动让应用获得数据高可用。
- readiness 失败会让 Pod 退出 Service 端点；liveness 连续失败会重启容器；startup 成功前会抑制另外两种探针。
- Service selector 必须匹配 Pod label；Service 存在不代表 EndpointSlice 一定有可用端点。
- requests 参与调度，limits 约束运行时；内存超过 limit 常见结果是 OOMKilled，CPU 超限通常被节流。
- PVC 只是申请；是否可绑定、能否扩容、删除后底层数据是否保留，取决于 StorageClass、访问模式和回收策略。
- ConfigMap/Secret 变更是否进入运行中容器取决于注入方式；环境变量不会自动刷新，卷投影也不是瞬时一致。

## 15 分钟动作

1. 用 3 分钟口述上面的两条数据路径。
2. 执行 `make -C k8s review`，先说答案再看提示。
3. 用 7 分钟重跑最薄弱模块，保存一条真实证据。
4. 在 [ROADMAP.md](ROADMAP.md) 更新等级、证据和下一次复习日。
