# 06 复制、ISR、Leader 与 KRaft

## 学习目标

- 区分数据 partition 的 Leader/Replica/ISR 与 KRaft metadata quorum。
- 说明 RF、`min.insync.replicas`、acks 和非干净选举共同决定的故障边界。
- 在独立三节点集群停止 Leader，观察选举、继续写入、记录完整与 ISR 恢复。

## 安全单节点实验

```bash
make -C kafka replication-kraft
```

该命令只在默认单 Broker 创建隔离 Topic，运行 `kafka-metadata-quorum describe --status`，并断言三个 partition 都是 RF=1、ISR={1}。它揭示一个常见误区：RF=1 时 `acks=all` 仍只有一份数据。

## 显式三节点故障实验

```bash
make -C kafka cluster-failover
```

该命令额外启动三个 combined broker/controller，绑定 `127.0.0.1:19092～19094`，使用三个独立数据卷。脚本创建 RF=3、min ISR=2 的单分区 Topic，写入两条后停止实际 Leader，等待新 Leader，用剩余两个 ISR 继续 `acks=all` 写两条，从头验证四条完整，再重启旧 Leader 等待 ISR 恢复。无论成功或失败都会删除额外集群与数据卷。

若需要手工观察：

```bash
make -C kafka cluster-up
make -C kafka cluster-down
```

`cluster-up` 属于额外多节点资源，必须显式清理。

## 核心机制

partition Leader 接受读写，Follower 拉取复制；ISR 是当前追赶在允许范围内的副本。Leader 故障后从合格副本中选新 Leader，客户端刷新元数据后继续。`min.insync.replicas` 是写入时最小 ISR 门槛，与 Producer `acks=all` 共同工作。

KRaft quorum 保存 Broker 注册、Topic/partition 和配置等集群元数据。Controller Leader 的选举不等同于每个数据 partition 的 Leader 选举；生产应分别监控 quorum 健康和数据副本健康。

## 生产边界与完成标准

- 机架感知决定副本是否真正跨故障域；三副本同机不等于三机容灾。
- ISR 缩小时继续写还是失败是可用性/持久性取舍，必须从业务 RPO 推导。
- 非干净选举可能恢复可用但丢失已确认尾部，不能无条件开启。
- [ ] 能用实际 Leader/ISR 输出解释停机时间线。
- [ ] 能说明停两台后 min ISR=2 为何拒绝写入。
- [ ] 能区分 Controller quorum 和数据复制状态。
