# 消费组、位点、延迟与再均衡练习

1. position、committed offset 和 log-end-offset 分别在哪里、何时变化？
2. `auto.offset.reset=earliest` 为什么对已有提交位点的 Group 不生效？
3. 总 lag 为 100 是否足以判断影响？还需要哪些分区和速率证据？
4. 12 个 partition 配 24 个同组 Consumer 会发生什么？
5. 哪些事件会触发 rebalance？它为何可能形成“再均衡风暴”？
6. 耗时处理如何避免超过 poll 间隔，又不把无限任务塞进内存？
