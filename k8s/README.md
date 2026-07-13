# Kubernetes 学习目录

`k8s/` 是与 `kafka/`、未来的 `redis/`、`mysql/` 平级的学习主题。虽然 Kubernetes 本质上是容器编排平台，但本仓库将它作为一个独立的基础设施组件进行学习。

当前示例：

- `kafka/`：使用 Namespace、ConfigMap、Service、StatefulSet、PVC、Deployment 和 Kustomize，在 Docker Desktop Kubernetes 中运行 Kafka 与 Kafka UI。

后续可以继续增加：

```text
k8s/
├── kafka/
├── redis/
└── mysql/
```

每个子目录保持独立，可以单独执行 `kubectl apply -k` 和 `kubectl delete -k`。
