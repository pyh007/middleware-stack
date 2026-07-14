# 消费组、位点、延迟与再均衡参考要点

## 1. 三个位点

position 是 Consumer 下一次 fetch/返回的位置，poll 后前进；committed offset 保存在 Group 状态中，是故障恢复起点；log-end-offset 是 Broker 分区日志末端。实验先处理 5 条后可见 committed 与 log-end 差 7。生产应逐分区采样三者及其变化率，避免只看一个总数。

## 2. reset 策略

earliest/latest 是“找不到有效 committed offset 时”的起点策略，不是每次启动的强制开关。同一 Group 已提交后会继续从 committed 开始。若要重放，应使用经过审批的 offset reset 或新 Group，并先验证幂等、保存原位点和定义回滚，不能只改 earliest。

## 3. lag 口径

总 lag 不包含生产/消费速率、记录处理成本和保留窗口。100 条大消息或一个热点分区可能比平均分散的 100 条更危险。应看逐分区 lag、增长斜率、最老消息年龄、生产/消费率、处理延迟、错误/DLQ 和预计清空时间，再映射业务影响。

## 4. 实例与分区

同一 Group 中一个 partition 同时只归一个 Consumer，12 个 partition 最多让 12 个成员获得分配，其余空闲。多余实例仍参与协调，部署抖动时可能增加 rebalance。生产并行度规划还要考虑热点、单实例可承载分区数、故障余量与扩分区成本。

## 5. 再均衡风暴

成员加入/退出、心跳或 session 超时、超过 max poll interval、订阅/分区变化都会触发。若处理变慢导致超时，rebalance 暂停处理又进一步积压，成员恢复后再次加入，便形成正反馈。证据是 Group 状态、assignment、poll 间隔、处理时长和部署时间线。

## 6. 长处理

可缩小单次拉取、把 poll 与有界 worker 解耦、按 partition 暂停/恢复，并在 revoke 前处理或放弃在途任务；提交必须与任务完成绑定。调大 poll interval 只是扩大故障检测窗口。生产需压测队列上限、最坏处理时长、关闭流程和重复处理行为。
