# 记录、主题、分区与顺序参考要点

## 1. 顺序边界

结论：offset 只在一个 partition 内单调增长，跨 partition 不可比较。机制是每个 partition 都是独立追加日志和 Leader 写入路径。实验中要按 partition 分组检查 offset；边界是多分区并发。若业务要求全局顺序，只能引入单分区或外部排序，副作用是吞吐、热点和可用性成本。

## 2. key 与稳定性

相同 key 在 Topic 分区数、序列化字节和 partitioner 算法不变时通常映射到同一 partition。实验输出的 key→partition 集合提供证据。扩分区、客户端 partitioner 变更或显式指定 partition 都会打破“永远不变”的说法；生产需固定客户端策略并监控 key/partition 分布。

## 3. 业务 key

选择依据是需要串行化的业务聚合根。订单状态机可用 order_id，用户级余额或额度可能用 user_id；随机 key 只追求均衡，无法保存实体内顺序。过粗 key 会形成热点，过细 key 又不能约束相关事件。上线前用真实 key 分布估算最热 partition，而不是只看平均流量。

## 4. 扩分区

常见 hash 路由包含分区数，分母改变会使同一 key 的后续记录进入新 partition，旧、新 partition 可被并行消费。可在停写窗口迁移、用路由版本让同一实体保持旧分区，或让消费者按业务版本协调。任何方案都要验证积压清空和状态机不倒退，且准备回退。

## 5. 分区成本

更多 partition 提高潜在并行度，但增加 Leader/副本日志文件、Page Cache、网络复制、Controller 元数据、再均衡和故障恢复工作。Consumer 数超过 partition 数不会继续提升同组并行度。生产决策应同时验证目标吞吐、最热分区、Broker 恢复时长和客户端 assignment 时长。

## 6. 证明顺序

`produce` 通常只入本地缓冲，网络批次和不同 partition 可并发；调用序号不是 Broker 的统一序号。应保存 delivery report 的 topic/partition/offset，并用稳定事件序号验证同 key 的消费顺序。边界是重试、事务和应用并发仍可能造成业务处理乱序，需结合幂等与处理模型验证。
