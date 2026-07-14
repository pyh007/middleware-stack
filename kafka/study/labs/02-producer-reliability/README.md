# 02 生产者批处理、压缩与可靠性

## 学习目标

- 解释 Producer 缓冲、batch、压缩、请求、Broker 追加与 delivery report 的路径。
- 区分 `acks`、重试、幂等 Producer 和业务幂等各自解决的问题。
- 能在吞吐、延迟、CPU、内存与数据风险之间选择参数。

## 运行实验

```bash
make -C kafka producer-reliability
```

实验使用 `acks=all`、幂等 Producer、`linger.ms=50`、每批最多 20 条和 gzip，异步写入 120 条可压缩记录；随后断言 120 个唯一 partition/offset 坐标都收到确认，并用各分区 high watermark 验证 Broker 端总记录数。

## 核心机制

`produce()` 通常只是把 record 放进客户端 accumulator。sender 线程按 partition 聚合 batch，压缩后发给 Leader；只有 delivery callback 成功才说明 Broker 按当前 `acks` 条件确认。`acks=0/1/all` 分别把确认边界放在“不等待”、Leader 追加和当前 ISR 确认，但实际耐故障能力还取决于 RF、ISR、`min.insync.replicas` 与选举策略。

幂等 Producer 使用 Producer ID 和 partition sequence，让 Broker 识别同一会话因网络重试产生的重复 batch；它不识别用户点击两次或服务重启后重新生成的业务事件。事务在幂等基础上原子写多个 partition，并可与消费位点绑定，详见模块 04。

## 观察证据与修改变量

观察 delivery report 数、partition high watermark、逻辑 payload 字节及客户端统计。分别把 `linger.ms` 改为 0、压缩改为 `none`，在相同记录数下比较总耗时、请求批次、CPU 和发送字节；不要只用一次小样本下结论。

## 生产边界

- 增大 linger/batch 往往提升吞吐，也增加单条等待和进程内未发送数据量。
- 压缩降低网络与磁盘写入，代价由算法、数据可压缩性和 Broker 解压路径决定。
- 无限重试会放大过载；必须结合 delivery timeout、退避、队列上限和降级策略。
- delivery 成功不等于消费者成功、数据库提交或最终业务完成。

## 完成标准

- [ ] 能画出异步发送与 callback 的时间线。
- [ ] 能用 RF/ISR/min ISR 补全 `acks=all` 的保证边界。
- [ ] 能解释幂等 Producer 为什么不等于业务 exactly-once。
- [ ] 能根据延迟 SLO 与吞吐数据给出参数和生产验证方法。
