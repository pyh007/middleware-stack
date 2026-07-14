# 复制、ISR、Leader 与 KRaft 练习

1. Replica、ISR、AR 各是什么？ISR 是否等于“健康机器列表”？
2. RF=3、min ISR=2、acks=all 时，停一台和停两台分别会怎样？
3. RF=1 时 `acks=all` 为什么仍可能因机器故障丢失可用数据？
4. 非干净 Leader 选举换来了什么，又可能丢失什么？
5. KRaft Controller Leader 与 Topic partition Leader 有什么区别？
6. 三个副本放在同一机架为何不满足机架故障容灾？生产如何验证？
