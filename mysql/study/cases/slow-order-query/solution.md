# 慢订单查询参考方案

先完成自己的分析。这里给的是一个候选方案，不是唯一正确答案。

## SQL 改写

```sql
SELECT id, order_no, customer_id, amount, created_at
FROM lab_orders
WHERE status = 30
  AND created_at >= '2025-02-15 00:00:00'
  AND created_at <  '2025-02-16 00:00:00'
ORDER BY created_at DESC
LIMIT 50;
```

半开区间避免对索引列逐行执行 `DATE()`，也不依赖字段时间精度；明确列名减少不需要的数据读取和传输。

## 候选索引

```sql
CREATE INDEX idx_lab_orders_status_created
    ON lab_orders (status, created_at DESC);
```

`status` 是等值条件，`created_at` 是范围和排序列。尽管状态单列选择性不高，与时间范围组成联合索引后仍可以显著缩小目标范围并按需要的顺序取前 50 行。

如果该查询极高频且回表成为瓶颈，可评估更宽的覆盖索引，但不应未经数据验证把所有返回列都加入索引。`order_no`、`customer_id`、`amount` 会增加索引空间和每次写入成本。

## 验证要点

- 在加索引前后分别保存 `EXPLAIN ANALYZE`，比较实际行数和时间。
- 将原 SQL 与新 SQL 的结果写入临时表，双向做差或比较主键序列。
- 使用多天、不同状态和无数据日期测试，避免只优化一个参数。
- 上线关注写入延迟、buffer pool、磁盘、复制延迟和目标接口尾延迟。
- 回滚通常是恢复旧 SQL 并在确认安全窗口后删除新索引；删除索引本身也需评估 DDL 风险。
