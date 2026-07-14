# 03 网络、Service 与服务发现

## 学习目标

理解 Pod IP、Service 虚拟入口、EndpointSlice、集群 DNS 和端口映射的数据路径；能区分“DNS 不通”“Service 没后端”“端口不匹配”“Pod 未 Ready”和应用自身错误。

## 核心机制

Pod 获得集群可路由 IP，但生命周期内地址可能变化。Service 用 selector 找到 Pod，控制器把地址写入 EndpointSlice，数据面再把 Service 流量转到可用端点。DNS 通常解析为 Service ClusterIP；`port` 是客户端访问 Service 的端口，`targetPort` 是后端容器接收端口。Namespace 本身不是网络隔离，隔离取决于 CNI 和 NetworkPolicy。

## 实验

```bash
make -C k8s networking
```

实验创建两个 HTTP Pod、一个 Service 和一个客户端，断言 DNS 全名、两个 EndpointSlice 地址以及真实响应。先预测 Service selector 与 Pod label 不匹配时哪些对象仍存在。然后显式注入并修复错误 selector：

```bash
make -C k8s service-failure
```

## 诊断顺序与边界

从调用方确认错误和 DNS，再检查 Service 端口、selector、EndpointSlice、Pod Ready、容器监听地址及 NetworkPolicy。`kubectl port-forward` 适合本地诊断，不是生产入口；Ingress 或 Gateway 只解决七层入口的一部分，还需 TLS、认证、限流、健康检查和负载均衡器容量。NetworkPolicy 的实际支持能力要在目标 CNI 上验证。

## 完成标准

能画出 `client → DNS → Service → EndpointSlice → Pod:targetPort`；能在五分钟内定位空端点；能说明 Headless Service 的 DNS 行为和典型用途；修改实验 label 或端口后，能根据证据恢复服务。
