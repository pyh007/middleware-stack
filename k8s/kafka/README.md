# Kafka Kubernetes 学习清单

这套清单面向 Docker Desktop 自带的单节点 Kubernetes，不包含 Kubernetes 集群安装步骤。它部署一个单节点 KRaft Kafka 和一个 Kafka UI，适合本地学习，不适用于生产环境。

## 资源与概念

| 文件 | Kubernetes 资源 | 学习重点 |
| --- | --- | --- |
| `namespace.yaml` | Namespace | 隔离一组中间件资源 |
| `kafka-configmap.yaml` | ConfigMap | 将非敏感配置从容器定义中分离 |
| `kafka-services.yaml` | Headless/ClusterIP Service | 稳定 DNS、服务发现和端口转发 |
| `kafka-statefulset.yaml` | StatefulSet/PVC | 稳定 Pod 名称和持久存储 |
| `kafka-ui.yaml` | Deployment/Service | 无状态应用的副本管理与访问入口 |
| `kustomization.yaml` | Kustomize 配置 | 组合并统一管理多个 YAML 文件 |

Kafka 使用 StatefulSet，Pod 名称固定为 `kafka-0`，数据写入 `kafka-data-kafka-0` PVC。Kafka UI 本身不保存关键数据，因此使用 Deployment。

## 渲染与校验

先确认当前上下文确实是 Docker Desktop，避免操作错误的集群：

下面代码块中，`#` 及其后面的内容是注释，可以连同命令一起复制到终端执行。

```bash
kubectl config current-context                              # 显示 kubectl 当前连接的集群，应输出 docker-desktop
kubectl get nodes                                          # 查看集群节点及 Ready 状态，确认 Kubernetes 可以正常工作
kubectl kustomize k8s/kafka                                # 把多个清单渲染成最终 YAML，只输出结果，不修改集群
kubectl apply --dry-run=client -k k8s/kafka                # 在客户端模拟 apply 并校验清单，不创建任何实际资源
```

## 应用与观察资源

在仓库根目录执行：

```bash
kubectl apply -k k8s/kafka                                 # 创建或更新 Kustomize 中声明的全部 Kubernetes 资源
kubectl get all,pvc,configmap -n middleware-stack           # 查看该 Namespace 中的工作负载、Service、PVC 和 ConfigMap
kubectl rollout status statefulset/kafka -n middleware-stack --timeout=300s   # 最多等待 300 秒，直到 Kafka StatefulSet 就绪
kubectl rollout status deployment/kafka-ui -n middleware-stack --timeout=300s # 最多等待 300 秒，直到 Kafka UI Deployment 就绪
```

学习排障时常用：

```bash
kubectl describe pod kafka-0 -n middleware-stack             # 查看 Kafka Pod 的状态、探针、挂载、调度信息和相关事件
kubectl logs -f kafka-0 -n middleware-stack                  # 持续跟踪 Kafka 日志；按 Ctrl+C 结束日志跟踪
kubectl logs -f deployment/kafka-ui -n middleware-stack      # 持续跟踪 Kafka UI 当前 Pod 的日志；按 Ctrl+C 结束
kubectl get events -n middleware-stack --sort-by=.lastTimestamp # 按时间顺序查看调度、拉取镜像和探针失败等事件
```

## 从宿主机访问

为避免和 Docker Compose 的 `9092`、`8080` 冲突，这里使用 `19092` 和 `18080`。端口转发命令需要保持运行：

```bash
kubectl port-forward -n middleware-stack service/kafka 19092:9092   # 本机 19092 转发到 Kafka Service 的 9092；需保持运行
kubectl port-forward -n middleware-stack service/kafka-ui 18080:8080 # 本机 18080 转发到 Kafka UI 的 8080；请另开终端运行
```

浏览器访问 <http://localhost:18080>。现有 Python 学习脚本可以通过环境变量连接 Kubernetes 中的 Kafka：

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:19092 \
  uv run python kafka/python/demo.py --topic k8s-learning-events # 仅为本次命令指定 Kafka 地址，并运行 Python 端到端示例
```

也可以在 Kafka Pod 内直接使用命令行工具：

```bash
kubectl exec -n middleware-stack kafka-0 -- \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list # 进入 Kafka Pod 执行工具并列出全部 Topic；-- 分隔 kubectl 与容器命令
```

## 更新、回滚与清理

修改清单后先查看差异，再应用：

```bash
kubectl diff -k k8s/kafka                                  # 对比本地清单与集群现状，只显示差异，不修改资源
kubectl apply -k k8s/kafka                                 # 将确认后的清单变更应用到集群
kubectl rollout history statefulset/kafka -n middleware-stack # 查看 Kafka StatefulSet 的历史修订版本
kubectl rollout undo statefulset/kafka -n middleware-stack    # 回滚 Kafka StatefulSet 到上一个修订版本
```

只删除工作负载和配置、保留 Namespace 与 Kafka PVC 数据：

```bash
kubectl delete statefulset/kafka deployment/kafka-ui -n middleware-stack # 删除 Kafka 和 Kafka UI 工作负载，但保留 StatefulSet 创建的 PVC
kubectl delete service/kafka service/kafka-headless service/kafka-ui configmap/kafka-config -n middleware-stack # 删除 Service 和 ConfigMap，不删除 Kafka 数据卷
```

如果确定不再需要 Kafka 数据，可以继续删除 PVC 和 Namespace：

```bash
kubectl delete pvc kafka-data-kafka-0 -n middleware-stack   # 永久删除 Kafka 持久卷声明，其中的 Topic 和消息将丢失
kubectl delete namespace middleware-stack                   # 删除学习用 Namespace；其中仍存在的所有资源也会被删除
```

也可以一次删除 Kustomize 管理的全部资源。因为清单中包含 Namespace，下面命令会连同 PVC 数据一起清理：

```bash
kubectl delete -k k8s/kafka                                 # 删除整套资源和 middleware-stack Namespace，属于彻底清理操作
```
