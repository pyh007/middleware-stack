# 08 积压、重复与丢数声称综合事故

## 学习目标

- 建立 Producer delivery、Broker partition/offset、Group committed 和业务 event_id 的证据链。
- 区分积压、Kafka 记录重复、业务事件重复、处理跳过与真实 Broker 丢失。
- 用 Runbook 给出止损、恢复、验证、灰度、回滚与长期治理。

## 运行实验

```bash
make -C kafka incident-capstone
```

实验写入 20 条 Kafka records，其中只有 18 个唯一 event_id。消费者先处理 7 条并退出，断言 lag=13；同 Group 重启处理剩余 13 条，最终断言 lag=0、总 records=20、唯一业务事件=18、重复=2。由此证明“业务表只有 18 个 ID”不能直接推出 Kafka 丢了两条。

## 事故方法

第一步冻结改变证据的动作：offset reset、扩分区、删除 Group/Topic 和无序重启。第二步统一统计口径，保存每个 delivery report 的 topic/partition/offset，读取各 partition log-end 和 Group committed，再用稳定 event_id 对账处理日志、DLQ 与业务库。第三步把时间线与 ISR、rebalance、下游超时和最近变更关联。

积压处置先判断净消费能力是否为正。扩 Consumer 只有在有未分配 partition 且瓶颈不在下游时有效；盲目扩容可能加重数据库、风控或 Group 再均衡。重放必须在幂等完成后使用新 Group 或受控位点，小流量验证副作用。

## 修改变量

把第一阶段处理数从 7 改成 4，先计算 lag；再删除稳定 event_id 或改为每次重试生成新 ID，说明为什么业务层无法识别重复。最后独立完成 [生产事故题](../../cases/production-incident/README.md)，再对照答案。

## 生产边界与完成标准

- Kafka 正常保留记录不等于业务没有丢失，自动提交、过滤、异常吞掉和下游事务都可能造成结果缺口。
- Kafka 中 record 数大于业务唯一事件数也不等于 Broker 重复写入，可能是上游业务重试。
- 任何恢复都应定义 RPO/RTO、幂等、对账范围和回滚条件。
- [ ] 能在 10 分钟内形成完整证据表和假设优先级。
- [ ] 能用六段式回答“Kafka 是否丢数”。
- [ ] 能执行 [排查 Runbook](../../runbooks/diagnosis.md) 并给出生产级处置。
