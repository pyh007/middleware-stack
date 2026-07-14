# 网络与服务发现练习题

1. Service 对象存在且有 ClusterIP，为什么访问仍可能超时或拒绝连接？
2. selector、Pod label、EndpointSlice 三者怎样关联？先查哪一个最有效？
3. `port`、`targetPort`、`containerPort` 和 NodePort 分别是什么？
4. readiness 失败为什么会影响 Service 流量，但直接访问 Pod IP 可能仍有响应？
5. Headless Service 与普通 ClusterIP Service 的 DNS 结果和使用场景有什么差别？
6. Namespace 是否提供默认网络隔离？NetworkPolicy 落地前需要验证哪些前提？
