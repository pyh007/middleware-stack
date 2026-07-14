# 交付语义、幂等处理与事务参考要点

## 1. 崩溃窗口

先提交再处理时，提交后、业务完成前崩溃会从更后位点恢复，业务可能被跳过；先处理再提交时，业务完成后、位点提交前崩溃会重新处理。结论不是绝对承诺，而是倾向的失败窗口。生产要用故障注入、稳定 event_id 和业务对账验证。

## 2. 隔离级别

事务写入和 abort 控制信息都保存在日志。read_uncommitted 返回已追加数据，因此实验看到 5 条；read_committed 根据事务状态只返回已提交的 4 条，并受最后稳定 offset 限制。旧数据不会因 abort 立即从磁盘消失，监控容量时仍要计算事务开销。

## 3. 位点事务

`send_offsets_to_transaction` 把 Consumer Group 输入进度与同一事务 Producer 的 Kafka 输出原子提交：要么输出和位点都可见，要么都回滚。它不包含外部数据库、HTTP 和非事务 Producer。生产需验证 Group metadata、事务超时、read_committed 和失败重试。

## 4. 三类幂等

幂等 Producer 针对发送重试 batch；Kafka 事务针对 Kafka 内多记录/位点的原子可见性；业务幂等针对同一业务意图被重复执行。三者可以叠加但不能互相替代。实验只证明 Kafka 边界，订单扣款仍需唯一 event_id、状态机或数据库约束。

## 5. fencing

稳定 transactional.id 让重启实例接续同一事务身份；同一 ID 不能被两个活跃实例共享。新 epoch 会 fence 旧实例，阻止“僵尸”继续提交，从而保护单写者语义。副作用是错误的 ID 分配会让正常实例互相驱逐，生产需把 ID 与实例槽位稳定绑定。

## 6. Kafka 到 MySQL

可在 MySQL 事务中用 event_id 唯一约束同时写业务结果和 inbox 处理记录，成功后再提交 Kafka offset；崩溃重试由唯一约束识别。反向发布可用 outbox。不能把数据库提交与 Kafka 提交假装成单个原子事务；必须定义重复、重试、补偿和对账证据。
