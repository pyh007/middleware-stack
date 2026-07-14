# 复制、ISR、Leader 与 KRaft 参考要点

## 1. 副本集合

AR 是分配给 partition 的全部 replicas，ISR 是其中当前与 Leader 足够同步、可参与正常选举的集合；ISR 变化是复制状态，不等同于机器存活。实验 `Replicas` 与 `Isr` 字段提供证据。生产还要结合 replica lag、网络、磁盘和 Leader 分布判断根因。

## 2. 一台与两台故障

三副本、min ISR=2、acks=all 时，停一台后剩余两份同步副本可以选 Leader 并继续写，实验验证四条完整；再停一台使 ISR 低于门槛，写入应失败以保护 RPO。代价是可用性下降。恢复后必须等 ISR 追齐再认为冗余恢复。

## 3. RF=1

`acks=all` 的 all 指当前 ISR，单副本 ISR 只有 Leader 自己；确认后没有第二份复制。Broker/磁盘永久损坏仍会丢失数据。单节点实验明确输出 RF=1 和 ISR={1}。生产可靠性描述必须把 acks、RF、min ISR、故障域和备份放在一起。

## 4. 非干净选举

若没有 ISR 副本，允许落后的非 ISR 成为 Leader 可更快恢复分区可用，但其日志缺少旧 Leader 已确认的尾部，可能造成数据丢失或历史截断。是否接受取决于 RPO；关键事件通常宁可短暂不可用。变更前要保存位点、评估数据差异并准备回滚。

## 5. 两类 Leader

KRaft Controller Leader 通过 quorum 管理集群元数据和变更决策；每个 Topic partition 另有负责该数据日志读写的 Leader。Controller 切换不意味着所有数据 Leader 同时切换，反之亦然。监控需分别覆盖 quorum voter/epoch 和 Offline/UnderReplicated partitions。

## 6. 故障域

同机架、同电源或同可用区的三个副本可能在一次故障中同时失效，RF 只是份数不是独立性。生产应配置 rack/zone 标识，检查 replica assignment 跨域，模拟单域故障并验证 Leader、ISR、客户端和恢复时长，同时评估跨域网络延迟与费用。
