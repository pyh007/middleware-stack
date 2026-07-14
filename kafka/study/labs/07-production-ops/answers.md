# 容量、可观测性、安全与恢复参考要点

## 1. 诊断顺序

先确认业务、Topic/Group、时间窗、SLO 和变更；再比较生产/消费速率与逐分区 lag；随后看 Group/rebalance/处理延迟，最后下钻 Broker 请求、ISR、磁盘和网络。顺序把症状映射到数据路径。生产取证应保存快照，避免重启或 reset 先改变现场。

## 2. 分区级 lag

总 lag 会隐藏一个热点 partition、位点不均或最老消息年龄；低 lag 也可能是自动提交早于业务成功。实验总 lag=12，还能看到每分区 committed/log-end。生产要结合 lag 增长率、生产/消费率、assignment、处理成功和 DLQ，才能判断影响与清空时间。

## 3. 容量余量

需要压缩后的真实字节率、索引和 segment、事务/compaction 膨胀、重分配双写、Follower 追赶、操作系统水位、故障失去一台后的承载，以及最热 Broker/partition。还应验证网络与恢复时长。保留变更前做峰值和故障场景演算，并设置磁盘分级告警。

## 4. 安全控制

网络只开放必要 listener；TLS 加密并验证身份；SASL/平台身份使用短期凭据；ACL 按 Topic/Group/事务 ID 最小授权；管理操作单独角色并审计。还需配额、密钥轮换、证书过期监控和应急吊销。实验 PLAINTEXT 仅因 loopback 隔离，不能复制到生产。

## 5. 升级

先核对 Broker/客户端协议与配置兼容，备份配置并定义回退版本；按故障域逐台滚动，观察 Controller、Offline/UnderReplicated partitions、ISR、请求错误、P99 和业务对账。进程存活不代表副本追齐或客户端正常。指标恶化即暂停并回滚本批，而非继续完成计划。

## 6. 恢复验收

应用导出可能遗漏 key/headers/timestamp、partition/offset、Topic 配置、ACL、Schema、Group 位点和事务状态。恢复前定义 RPO/RTO；恢复后校验记录数、唯一 event_id、首尾时间、哈希/业务不变量、配置与权限，并用新 Group 灰度消费。保留旧副本直至超过回退窗口。
