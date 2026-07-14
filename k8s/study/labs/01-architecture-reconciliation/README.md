# 01 集群架构、API 与控制器调谐

## 学习目标

理解 API Server 是资源操作入口，etcd 保存集群状态，Controller Manager 持续调谐，Scheduler 为未绑定 Pod 选择节点，kubelet 驱动容器运行时并回写状态。能区分声明的 `spec`、观察到的 `status`、对象版本和事件，而不是把 Kubernetes 理解成一组 `kubectl` 命令。

## 核心机制

`kubectl apply` 把期望状态提交给 API Server；Deployment 控制器观察对象并创建 ReplicaSet，ReplicaSet 再维持 Pod 数量。控制器通过幂等循环缩小期望与现实的差距。`metadata.generation` 在期望状态变化时增加，`status.observedGeneration` 表示控制器已经处理到哪个版本；两者相等且可用副本达到目标，才是比“命令执行成功”更强的证据。

## 实验

```bash
make -C k8s architecture
```

实验创建一个副本的 Deployment，再把期望副本改为两个，断言 generation、observedGeneration 和 availableReplicas。执行前先预测会出现几个 ReplicaSet、Pod 名称为何不稳定。显式故障实验会删除一个 Pod，验证控制器使用新 UID 恢复副本：

```bash
make -C k8s pod-failure
```

## 观察与生产边界

查看 `Deployment → ReplicaSet → Pod` 的 ownerReferences、conditions 和 Events。API Server 接受对象只代表语法和准入通过，不代表镜像、调度、探针或应用已经成功。生产发布应等待明确 condition，设置超时并同时观察业务指标；控制器能恢复数量，不保证应用数据正确，也不能替代容量与依赖检查。

## 完成标准

能画出一次 apply 到容器运行的数据路径；能解释 generation 与 resourceVersion 的区别；能从 ownerReferences 找到对象所有者；运行实验后修改 replicas 并预测调谐结果；面试时能说明控制器为何采用声明式、幂等循环。
