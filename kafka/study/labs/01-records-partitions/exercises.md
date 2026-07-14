# 记录、主题、分区与顺序练习

先闭卷画图或口述，再查看 `answers.md`。

1. Kafka 为什么只能保证 partition 内顺序，offset 能否跨 partition 比较？
2. 消息 key 如何影响分区？相同 key 是否在任何条件下都永远落到同一分区？
3. 订单事件应该用 order_id、user_id 还是随机值做 key？给出选择标准。
4. 扩分区为什么可能破坏同一业务实体的连续顺序？如何迁移？
5. partition 越多是否一定越好？列出至少四类成本。
6. Producer 调用 `produce` 的先后顺序为什么不能单独证明 Broker 中的全局顺序？生产如何验证？
