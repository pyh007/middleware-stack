# 03 消费组、位点、延迟与再均衡

## 学习目标

- 解释 Group Coordinator、成员、assignment、fetch position 与 committed offset。
- 量化分区级 lag，并证明已有提交位点时 `auto.offset.reset` 不生效。
- 观察成员加入/离开触发的真实再均衡，判断实例数和分区数的关系。

## 运行实验

```bash
make -C kafka consumer-groups
```

第一个脚本在三个分区写入 12 条，先处理并同步提交 5 条，断言总 lag=7；新 Consumer 使用同一 Group 继续处理剩余 7 条，断言 lag=0。第二个脚本让两个真实 Consumer 先后加入同一 Group，保存 assignment history 并验证分区发生重新分配。

## 核心机制

同一 Group 对一个 partition 同时只分配一个成员，Group 通过 Coordinator 维护成员和已提交的“下一消费位置”。Consumer 本地 position 会随 poll 前进，committed offset 只有提交后才成为重启恢复点。`auto.offset.reset=earliest/latest` 只在没有有效提交位点或位点越界时选择起点。

成员加入、退出、心跳超时、订阅变化或超过 poll 间隔都可能触发 rebalance。经典 eager 协议可能先撤销较多分区；协作式协议可渐进迁移，但应用仍要处理 revoke、在途任务和提交时序。

## 观察证据与修改变量

保存每个 partition 的 high watermark、committed offset、lag 和两名成员的分配历史。把第一阶段消费数改成 2，预测各 partition lag；再把两个成员同时启动，比较分配历史。不要只看总 lag，热点 partition 可能被平均值掩盖。

## 生产边界

- 同组实例数超过 partition 数会有空闲成员，却仍增加协调和发布成本。
- lag 是日志进度，不是业务成功率；自动提交可能让 lag 很低但业务处理尚未完成。
- 长处理应与 poll/心跳模型匹配，或把拉取与有界工作队列解耦。
- 再均衡期间要处理在途任务、提交失败和重复，不能只调大超时掩盖问题。

## 完成标准

- [ ] 能区分 position、committed offset 和 log-end-offset。
- [ ] 能逐 partition 计算 lag，并解释 earliest/latest 的触发条件。
- [ ] 能从 assignment history 解释再均衡，而不是把它等同于负载均衡。
- [ ] 能为给定 partition 数选择 Consumer 数和 poll 参数。
