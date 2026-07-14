# 架构与调谐练习题

先闭卷回答，再运行 `make -C k8s architecture` 保存证据。

1. API Server 返回创建成功，为什么 Pod 仍可能无法运行？列出至少四个后续环节。
2. Deployment、ReplicaSet 和 Pod 的职责分别是什么，怎样从对象关系证明？
3. `metadata.generation` 与 `status.observedGeneration` 不相等意味着什么？
4. 手工删除 Deployment 管理的 Pod 后，为什么会出现新 Pod，而 Pod 名称和 UID 为什么不能当作稳定身份？
5. Kubernetes 的“声明式”和“最终一致”对发布脚本有什么要求？
6. 修改实验副本数为三个，预测 API 对象和 status 会如何变化，再实际验证。
