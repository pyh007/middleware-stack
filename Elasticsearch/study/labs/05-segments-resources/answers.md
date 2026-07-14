# 段合并缓存与资源参考要点

## 1. 更新与墓碑

segment 不可变，更新写入新版本并在旧版本上记录删除；只有 merge 重写段时旧数据才真正回收。`docs.deleted`、segment 与 store 共同证明，不能看到 DELETE 成功就假设磁盘立即释放。

## 2. refresh 成本

频繁 refresh 提高搜索新鲜度，却制造小段、打开搜索器、增加 merge 和缓存变化。批量导入可延长 interval，完成后受控 refresh；收益用真实写吞吐、可见延迟、segment、merge 和 P99 验证。

## 3. merge 资源

合并期间旧段仍需保留，同时写新段，所以需要额外空间并竞争 CPU/I/O；大段还影响恢复和快照读取。生产预留水位与故障空间，监控 merge current/total/throttle、磁盘、I/O 和查询尾延迟。

## 4. 缓存

request cache 常用于可复用的 size=0 聚合结果，索引 refresh 会使相关缓存失效；参数、用户权限或时间范围变化也降低复用。实验连续相同请求使 hit_count 增长，但生产应比较命中带来的 P99/heap 收益。

## 5. heap 诊断

看 GC 后基线和 old GC 时间，再按节点/请求对照 breaker、字段数、聚合桶、fielddata、cache、pending tasks 和 heap dump。单个瞬时百分比不足以下结论；先控异常请求，避免把堆无限增大导致更长停顿。

## 6. rejected

队列满说明到达率或服务时间超过处理能力。扩队列增加等待与内存，可能让超时重试更严重。限流、去除无界重试，定位慢查询、热点、merge/GC 或容量瓶颈；验证 rejected、P99、吞吐和资源同步恢复。

## 7. force merge 决策

只有索引确定只读、快照/回滚可用、临时空间和低峰充足时，在少量索引灰度；15% 余量通常风险很高，应先扩空间或迁移。监控 merge、I/O、磁盘、水位和查询，异常立刻停止后续批次。force merge 不能“撤销”，因此回滚依赖旧副本/快照或替换索引。
