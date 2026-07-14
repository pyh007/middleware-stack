# 05 日志段、保留、压缩与吞吐

## 学习目标

- 解释 partition 目录、segment、索引、active segment 和滚动机制。
- 区分 delete retention 与 log compaction，理解 tombstone 生命周期。
- 把 batch、压缩、顺序 IO、Page Cache 与磁盘容量联系起来。

## 运行实验

```bash
make -C kafka log-storage
```

实验一创建单分区 Topic，使用 Kafka 4.3.1 允许的最小 1 MiB segment，写入 4000 条记录并进入 Broker 数据目录列出 `.log` 文件，断言至少发生一次滚动。实验二写入同 key 多版本与 tombstone，再按日志顺序重建最新逻辑状态；压缩清理本身是异步的，因此不把“旧文件立刻消失”作为断言。

## 核心机制

一个 partition 在 Broker 上对应按 offset 命名的多个 segment。active segment 接收追加；达到 `segment.bytes` 或滚动时间后关闭，保留和压缩主要处理非 active segment。`.index` 和 `.timeindex` 帮助按 offset/时间定位，日志仍以顺序追加为主。

`cleanup.policy=delete` 按时间或总大小异步删除合格 segment，保留是 segment 粒度，不是每条消息的精确 TTL。`compact` 保留每个 key 的最新值，使消费者可重建逻辑状态；tombstone 代表删除，但旧版本与 tombstone 都会在清理窗口内继续占空间。两种策略可以组合。

## 观察证据与修改变量

保存 segment 文件名、字节数、记录数和 keyed records 的物理/逻辑视图。把 `segment.bytes` 从 1 MiB 调大，预测段数；将 compact Topic 的 key 设为空，解释为什么不能得到按实体压缩。若要观察实际 cleaner，应允许足够滚动和清理时间，不能写固定睡眠后武断失败。

## 生产边界

- 容量按生产字节率 × 保留时长 × 副本数，再加索引、批次、重平衡和安全余量估算。
- 小 segment 加快删除粒度，却增加文件、索引、打开句柄和滚动开销。
- 压缩 Topic 必须有稳定 key；删除语义依赖 tombstone 和 `delete.retention.ms`。
- 磁盘接近满时先保护写入和保留证据，不能直接手工删除 Broker 数据文件。

## 完成标准

- [ ] 能从目录名和 base offset 解释一个 partition 的物理布局。
- [ ] 能说明 retention 为什么不是单条记录精确过期。
- [ ] 能用 tombstone 重建逻辑状态，并解释异步压缩边界。
- [ ] 能从业务写入率、保留与 RF 做容量估算。
