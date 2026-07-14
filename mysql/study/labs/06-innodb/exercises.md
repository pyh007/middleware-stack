# InnoDB 与日志练习题

1. 为什么修改数据页前通常先写 redo，而不是每次提交都同步刷完整数据页？
2. redo log 和 binlog 有什么区别？
3. undo log 除了回滚事务，还服务什么机制？
4. 什么是脏页？脏页多是否一定代表异常？
5. `innodb_flush_log_at_trx_commit=1` 与 `sync_binlog=1` 提供什么保证？
6. 两阶段提交要避免什么不一致？
7. buffer pool 命中率很高是否一定没有 IO 问题？
8. 长事务为什么可能让 undo 历史版本长期无法清理？
9. mysqld 被强制终止后，InnoDB 大致如何处理已提交和未提交事务？
