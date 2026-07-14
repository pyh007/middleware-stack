# 日志段、保留、压缩与吞吐练习

1. active segment 为什么通常不立即参与 retention 删除？
2. `retention.ms=1h` 是否保证每条记录在第 60 分钟精确消失？
3. log compaction 保证什么，不保证什么？没有 key 会怎样？
4. tombstone 为什么不会立刻从物理日志消失？消费者如何解释它？
5. 将 segment 调得非常小会带来哪些收益与成本？
6. 已知峰值 100 MB/s、保留 3 天、RF=3，容量评估还要考虑什么？
