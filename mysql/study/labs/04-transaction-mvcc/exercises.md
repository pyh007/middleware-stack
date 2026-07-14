# 事务与 MVCC 练习题

1. ACID 四个特性分别是什么？InnoDB 中哪些机制主要支撑它们？
2. `READ COMMITTED` 与 `REPEATABLE READ` 创建 Read View 的时机有什么差异？
3. 普通 `SELECT` 与 `SELECT ... FOR UPDATE` 为什么可能读到不同版本？
4. MVCC 是否意味着读操作永远不加锁？
5. MySQL 默认 `REPEATABLE READ` 是否意味着业务一定不会出现幻读？
6. 为什么事务中不应调用耗时的第三方接口？
7. 两个事务都先读库存 1，再各自写入库存 0，可能出现什么问题？如何修复？
8. 发生死锁后只重试失败的最后一条 SQL 是否正确？
