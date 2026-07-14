# Kafka on Kubernetes 综合事故

## 场景

单节点 Kafka StatefulSet 的期望副本为 1，但 Ready 长时间为 0，Kafka UI 可能仍显示 Running。用户反馈页面无法读取 Topic。PVC 处于 Bound，Pod 反复重启；上一实例日志包含无法创建 JVM GC 日志目录的错误。你的任务不是立即删除 Pod 或 PVC，而是形成可验证的故障链。

## 操作入口

```bash
make -C k8s kafka-status
```

该命令只读采集 StatefulSet、Pod、PVC、Service、EndpointSlice、最近 Events 和 Kafka 上一实例日志。健康时退出 0，不健康时退出 2，方便脚本和人同时识别状态。实际部署或更新必须显式执行 `make -C k8s kafka-capstone`；若旧 Pod 阻塞 StatefulSet 更新，它会重建 `kafka-0`，但不会清理 PVC。

## 事故任务

1. 写出用户影响、开始时间和最近变更，不把 UI Pod Running 当成 Kafka 可用。
2. 沿 Service → EndpointSlice → Pod condition → lastState → logs → PVC/节点资源定位第一个失败点。
3. 提出一个不删除数据的止损和恢复方案，说明风险、观察指标及回滚。
4. 恢复后验证 Kafka CLI 能列 Topic，并执行一次生产、消费或现有业务脚本。
5. 评审单节点、PLAINTEXT、固定本机 advertised listener、5Gi PVC 和单故障域的生产风险。

## 报告结构

使用“结论 → 机制 → 证据 → 边界 → 副作用 → 生产验证”表达。必须包含时间线、影响、直接根因、系统性根因、止损、数据一致性验证、回滚、长期措施、负责人和验证日期。参考分析见 [solution.md](solution.md)，应先独立完成再阅读。
