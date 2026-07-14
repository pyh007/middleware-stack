# 04 刷新事务日志与并发控制

## 学习目标

- 区分写入确认、实时 GET、搜索可见、refresh、flush 和 translog 恢复边界。
- 能用 `_seq_no` 与 `_primary_term` 做乐观并发控制并正确处理 409。
- 能解释 refresh interval 对新鲜度、段数量、merge 和写吞吐的取舍。
- 能把 acknowledgment、副本、客户端超时与 RPO 结合起来，而非宣称绝对不丢。

## 运行实验

```bash
make -C Elasticsearch write-consistency
```

实验把 `refresh_interval` 设为 `-1`，写入后证明实时 GET 可见而搜索 count 为 0；手动 refresh 后搜索可见。随后带序号/任期成功更新一次，再复用旧条件得到 409，最后观察 flush 前后 translog 指标。

## 核心机制

主分片接收写入并记录操作，translog 支持未提交操作的恢复；内存中的索引内容经 refresh 形成可搜索 segment，但这不是完整 Lucene commit。flush 提交 Lucene 并开启新的 translog generation。写返回成功的持久性还取决于副本、durability、活跃分片和故障组合。

序号标识操作顺序，primary term 标识主分片任期。客户端以读到的二者作为更新前提，可拒绝陈旧写；冲突后的业务合并不能被“无限自动重试”替代。

## 观察证据

- 写入后实时 GET 为 true，而 refresh 前 `_count` 为 0，refresh 后为 1。
- 第一次条件写更新 seq_no，旧条件写返回 `version_conflict_engine_exception` 409。
- translog 输出 operations、size 和 uncommitted 状态，flush 后状态变化。

## 修改实验

把 refresh interval 改为 `1s`，不手动 refresh，测量搜索可见延迟；再批量写 100 条并分别使用每条 `refresh=wait_for` 和批后一次 refresh，比较段、耗时和 merge 信号。修改前写下业务新鲜度假设。

## 生产边界

更频繁 refresh 以写放大和小段换新鲜度。客户端超时不能证明失败，重试需稳定 ID/幂等键。冲突率升高可能是热点文档或错误并发模型。生产要定义 RPO、确认级别、恢复源和对账机制，并用节点故障/恢复演练验证。

## 完成标准

- [ ] 能画出写入到 refresh/flush/merge 的状态变化。
- [ ] 能解释 GET 与 search 可见性差异并复现实验。
- [ ] 能用 seq_no/primary_term 防止静默覆盖并处理 409。
- [ ] 能把 refresh、吞吐、新鲜度、RPO 和副作用一起回答。
