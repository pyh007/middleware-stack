# 日志段、保留、压缩与吞吐参考要点

## 1. active segment

active segment 持续追加，删除它会破坏当前写入路径；Broker 通常先滚动为 closed segment，再根据保留或 cleaner 条件处理。实验用 1 MiB 段和确定性数据产生多个段，文件名 base offset 是证据。生产修改滚动参数要同时评估删除粒度、文件数和恢复扫描成本。

## 2. retention 精度

retention 是后台、segment 粒度的策略：要先滚动，整个 segment 达到时间/大小条件，再等待清理检查。因此单条记录不会在精确第 60 分钟删除。容量应按最坏清理延迟和 active segment 余量规划；合规删除要求还需验证实际文件与备份生命周期。

## 3. compaction

compaction 让稳定 key 的最新记录最终保留，支持重建最新逻辑状态；它不保证只剩一条、不保证立即清理，也不提供按时间完整历史。空 key 无法参与正常按 key 压缩。生产要验证 key 非空率、重复版本、cleaner lag 和下游重放语义。

## 4. tombstone

key 非空、value 为空的记录表示删除。消费者按顺序应用时移除该 key；Broker 需先保留 tombstone 足够时间，让离线消费者看见删除，再由 cleaner 清理旧值与 tombstone。窗口过短可能让长期离线消费者重建出已删除状态，需结合最大离线时间设置。

## 5. 小 segment

小段能更快滚动，使 retention/compaction 更快获得处理单元，也缩小单次删除粒度；代价是更多 `.log/.index/.timeindex`、文件句柄、元数据、滚动和恢复工作。实验段数变化只是局部证据，生产还要在真实吞吐与保留下测磁盘、CPU 和恢复时间。

## 6. 容量

裸数据约为 `100 MB/s × 259200s × 3`，已经是巨大规模；还需使用压缩后的真实字节率，并加索引、segment/文件系统、重分配双写、复制追赶、事务/compact 膨胀和水位安全余量。还要按 Broker/机架分布、最热分区和补副本速度验证，而非只算集群总盘。
