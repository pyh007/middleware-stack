# 06 复制、Sentinel 与 Redis Cluster

## 学习目标

- 解释异步复制、offset、陈旧读和故障转移中的数据缺口。
- 跑通 Sentinel 提升副本与旧主回归，理解 quorum 和客户端发现边界。
- 计算槽与 Hash Tag，实际迁移 slot 0 并验证键仍可读取。

## 运行实验

```bash
make -C redis replication-cluster  # 安全单节点边界与槽位计算
make -C redis sentinel-failover    # 显式：1 主 1 从 1 Sentinel
make -C redis cluster-reshard      # 显式：3 主 0 从并迁移 1 槽
```

两个多节点实验使用独立 Compose 项目，不映射宿主机端口，结束自动删除容器、网络和卷。教学 Sentinel 使用 quorum=1、教学 Cluster 没有副本，均不是生产拓扑，也不属于 `all`。

## 核心机制

副本通过全量/部分同步追随主节点，正常写入通常异步传播；offset 接近只说明复制流进度，不等于业务写已经跨系统确认。Sentinel 监控主节点，多数判断客观下线后协商领导者，选择副本提升，并重配置其他节点。客户端必须支持 Sentinel 发现和重新连接，否则可能继续指向旧主。

Cluster 把键的 CRC16 映射到 16384 个槽，槽归某个主节点。`{...}` Hash Tag 只哈希花括号内容，使相关键同槽并支持多键操作，也可能把热点集中到一个槽。reshard 迁移槽和其中键，客户端在稳定/迁移状态处理 MOVED/ASK。

## 观察证据与修改

安全实验输出角色、从节点数、cluster-enabled 和两组槽。Sentinel 实验输出主从 offset、提升后的主地址和旧主回归角色。Cluster 实验断言 state=ok、slot 0 所有者改变且 marker 值不丢。把 Hash Tag 从 `order:42` 删除，先预测两个键槽位；把 Sentinel down-after 调大，测量 RTO 变化。

## 生产边界与完成标准

生产至少 3 Sentinel 分布于独立故障域，副本选择考虑 lag、优先级和数据中心；Cluster 每主应有副本并设置迁槽带宽/延迟水位。故障转移必须验证客户端路由、写入缺口、脑裂旧主和回滚，不能只看节点 role。

- [ ] 能解释复制 offset 与业务确认的区别。
- [ ] 能根据输出重建一次 Sentinel 时间线。
- [ ] 能说明同槽、热点槽、迁槽重定向和生产拓扑边界。

