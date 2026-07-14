# 交付语义、幂等处理与事务练习

1. 先提交 offset 再处理，与先处理再提交，分别有哪些崩溃窗口？
2. `read_uncommitted` 为什么能看到 aborted 数据，`read_committed` 如何判断？
3. `send_offsets_to_transaction` 解决了什么原子性，未解决什么？
4. 幂等 Producer、Kafka 事务、业务幂等三者有什么不同？
5. `transactional.id` 为什么要稳定且实例间唯一，fencing 有什么意义？
6. 消费 Kafka 后写 MySQL，怎样避免重复扣款或“位点已走但数据库没写”？
