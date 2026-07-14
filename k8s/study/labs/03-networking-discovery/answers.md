# 网络与服务发现参考答案

1. DNS、selector、端点就绪、端口映射、进程监听、NetworkPolicy、节点网络和应用依赖任一环节都可能失败。ClusterIP 只证明 Service 已分配虚拟地址。
2. Service selector 匹配 Pod label，EndpointSlice 控制器据此生成后端，并结合 Ready 条件标记可用性。通常先看 EndpointSlice 是否有地址，再反查 selector/label 或 Pod readiness，证据链最短。
3. `port` 是 Service 暴露端口，`targetPort` 是后端接收端口或命名端口，`containerPort` 主要是 Pod 模板中的端口声明，本身不开放网络；NodePort 在每个节点分配外部可访问端口。
4. readiness 失败时端点会被标为不就绪或从可用流量中排除，但进程可能仍监听端口，所以绕过 Service 直连 Pod 可能成功。这个差异能帮助定位是流量摘除还是进程死亡。
5. 普通 Service DNS 解析到稳定 ClusterIP；Headless Service 不分配 ClusterIP，DNS 返回后端地址，适合客户端发现、StatefulSet 稳定身份等场景，但负载与故障处理责任可能转移给客户端。
6. Namespace 只是逻辑边界。NetworkPolicy 还依赖 CNI 实现、默认拒绝规则、双向策略、DNS 放行和实际连通性测试；不能只看策略对象创建成功。
