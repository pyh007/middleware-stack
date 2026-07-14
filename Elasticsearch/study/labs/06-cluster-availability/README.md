# 06 副本分配与集群可用性

## 学习目标

- 能解释 master、cluster state、主分片、in-sync 副本、分配和恢复。
- 能区分 green/yellow/red，并用 allocation explain 找到 decider，而非盲目改副本。
- 能在独立三节点环境停止主分片节点，证明副本提升、业务可读和再分配。
- 能识别故障域、磁盘水位、allocation filter 与容量对可用性的限制。

## 运行实验

```bash
# 默认安全实验：单节点副本边界
make -C Elasticsearch cluster-availability

# 显式多节点与停机故障，默认 all 不包含
make -C Elasticsearch cluster-failover
make -C Elasticsearch cluster-down
```

安全实验创建 1 主 1 副本索引，在单节点上断言 yellow、搜索仍成功，并读取副本未分配原因；只对实验索引把副本改为 0 后验证 green。故障实验在独立三节点集群把主副本限制到两个数据节点，停止主分片节点，记录新主和文档可读，再重启并等待 green。

## 核心机制

master 维护 cluster state 和分片分配，数据请求由主/副本执行。副本不能与同一分片主本放在同节点；yellow 表示主可用但至少一个副本缺失，red 表示至少一个主分片缺失。主节点故障时，符合 in-sync 条件的副本可被提升；恢复速度受分片大小、磁盘、网络、并发限制和故障域影响。

## 观察证据

- 单节点时 active primary=1、unassigned replica=1，allocation explain 原因是创建索引且无其他节点。
- 降低实验索引副本后 green 只证明当前索引配置满足，不代表生产更安全。
- 故障实验记录旧主节点、新主节点、停机后 yellow、文档 found，以及节点恢复后的两个 STARTED copies。

## 修改实验

把显式实验副本从 1 改为 2，预测停一节点后的状态；再移除 allocation include，观察主分片可能落到哪个节点。记录恢复耗时，并说明小文档结果为何不能代表 TB 级分片。

## 生产边界

副本必须跨节点、机架或可用区规划；三节点不自动等于容灾。全局/索引 allocation filter、磁盘水位、节点角色和版本会阻止分配。手工 reroute 可能接受陈旧数据，必须先定义数据损失和回滚。故障演练需在容量和变更窗口内审批。

## 完成标准

- [ ] 能从 health 到 cat shards 再到 allocation explain 完成诊断。
- [ ] 能解释 yellow 为什么仍可搜及降副本的副作用。
- [ ] 能运行显式故障实验并指出旧主、新主、业务证据和恢复时间。
- [ ] 能把可用性设计与故障域、容量、RPO/RTO 联系起来。
