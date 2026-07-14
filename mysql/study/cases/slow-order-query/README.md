# 综合作业：慢订单查询

先独立完成，再查看 [solution.md](solution.md)。

## 场景

订单后台需要查询 2025-02-15 当天已完成的订单。当前 SQL 在数据增长后变慢：

```sql
SELECT *
FROM lab_orders
WHERE status = 30
  AND DATE(created_at) = '2025-02-15'
ORDER BY created_at DESC
LIMIT 50;
```

接口只需要 `id、order_no、customer_id、amount、created_at`。表每天持续写入，状态分布明显不均匀，其中已完成订单最多。

## 准备环境

```bash
make -C mysql seed
make -C mysql shell
```

## 任务

1. 保存原 SQL 的 `EXPLAIN` 和 `EXPLAIN ANALYZE`。
2. 记录返回行数、估算扫描行数、实际扫描行数和耗时。
3. 改写 SQL，但必须保持“当天已完成订单”的语义。
4. 设计至多一个新索引，并解释每列的顺序。
5. 验证优化前后前 50 行完全一致。
6. 说明新索引对订单写入、磁盘和缓存的影响。
7. 写出上线监控指标和回滚方法。

## 限制

- 不能使用 `FORCE INDEX` 作为最终方案。
- 不能修改业务语义或少返回应有数据。
- 不能只说“执行计划走了索引”，必须比较实际扫描和耗时。
- 必须考虑数据增长和状态分布变化。

## 验收报告

```text
问题现象：
原计划与实际扫描：
根因：
SQL 改写：
索引设计：
结果一致性验证：
优化前后数据：
写入和容量副作用：
上线监控：
回滚方案：
```
