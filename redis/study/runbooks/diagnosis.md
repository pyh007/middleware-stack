# Redis 生产排查 Runbook

## 1. 定义影响与冻结现场

记录开始时间、接口、租户、错误码、P50/P95/P99、吞吐、正确性影响和最近发布；指定事件指挥者，冻结非必要发布。先确认是单应用、单机房、单分片还是全局。禁止先执行 `FLUSHALL`、`KEYS *`、无界 Lua、全量重启或大规模预热。

## 2. 分层保存证据

应用侧保存连接池使用/等待、超时、重试率、命中率、回源量和命令分布；网络侧检查 DNS、握手、丢包和跨区；Redis 保存 `INFO server/clients/stats/memory/persistence/replication/commandstats`、`SLOWLOG GET`、`LATENCY LATEST`、`CLIENT LIST` 摘要；主机保存 CPU、RSS、磁盘延迟、网络和容器限制。Cluster 记录 `CLUSTER NODES/SHARDS/INFO`，Sentinel 记录当前 master 和事件日志。所有证据带同一时区时间戳。

## 3. 从症状到根等待

1. 错误率与超时先区分拒绝连接、命令错误、MOVED/ASK、只读和真正慢响应。
2. `blocked_clients`、连接池等待和 `maxclients` 判断连接/阻塞问题；先抑制无界重试。
3. `instantaneous_ops_per_sec`、网络吞吐、CPU、SLOWLOG 和 commandstats 判断热命令或高复杂度命令。
4. `used_memory`、`mem_fragmentation_ratio`、`evicted_keys`、`expired_keys` 判断容量、碎片和命中率反馈。
5. AOF/RDB 进行中、fork 延迟、磁盘延迟判断持久化暂停。
6. 复制 offset、lag、link 状态、failover 日志和客户端目标判断拓扑分叉。
7. 对可疑键用 `SCAN` 采样、`MEMORY USAGE` 和类型长度命令；避免在生产对全库运行阻塞扫描。

## 4. 止损与修复

止损按可逆性排序：应用限流/降级、关闭放大重试、短时读取陈旧值、隔离重命令、定点延长热点 TTL、限速小批预热、扩容或迁移槽。修改淘汰策略、提升内存、故障转移和重启前，必须确认可淘汰集合、持久化状态、复制健康和回滚命令。数据正确性事故先停止错误写入，再从权威数据源对账回填。

## 5. 验证、灰度与回滚

预先写出成功条件：业务错误率/P99 回到基线、数据库低于安全水位、命中率恢复、Redis CPU/内存/淘汰稳定、复制链路健康、版本倒退为零。按单实例或 1% 流量灰度，观察至少一个业务峰值窗口。回滚要能恢复客户端路由、配置、限流和旧数据路径；恢复步骤见 [恢复 Runbook](recovery.md)，容量和权限检查见 [安全容量清单](security-capacity.md)。

