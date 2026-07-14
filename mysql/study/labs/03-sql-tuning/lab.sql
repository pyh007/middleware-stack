SELECT '01 为时间范围和稳定排序建立索引' AS stage;

CREATE INDEX idx_lab_orders_created_id
    ON lab_orders (created_at, id);

ANALYZE TABLE lab_orders;

SELECT '02 对索引列使用函数：需要扫描整棵时间索引再计算 DATE' AS stage;

EXPLAIN ANALYZE
SELECT COUNT(*)
FROM lab_orders
WHERE DATE(created_at) = '2025-02-15';

SELECT '03 改写为半开范围：[当天零点, 次日零点)' AS stage;

EXPLAIN ANALYZE
SELECT COUNT(*)
FROM lab_orders
WHERE created_at >= '2025-02-15 00:00:00'
  AND created_at <  '2025-02-16 00:00:00';

SELECT '04 深分页：即使走索引，也要跳过前 90000 行' AS stage;

EXPLAIN ANALYZE
SELECT id, created_at
FROM lab_orders
ORDER BY created_at, id
LIMIT 90000, 20;

SELECT '05 游标分页：客户端已持有上一页最后一个排序键' AS stage;

-- 造数规则保证每分钟只有一条数据；真实业务通常使用 (created_at, id)
-- 作为联合游标，以处理 created_at 相同的记录。
EXPLAIN ANALYZE
SELECT id, created_at
FROM lab_orders
WHERE created_at > DATE_ADD('2025-01-01 00:00:00', INTERVAL 90000 MINUTE)
ORDER BY created_at, id
LIMIT 20;

SELECT '06 覆盖索引：只覆盖核心高频查询需要的列' AS stage;

CREATE INDEX idx_lab_orders_customer_status_created_amount
    ON lab_orders (customer_id, status, created_at DESC, amount);

ANALYZE TABLE lab_orders;

EXPLAIN
SELECT id, created_at, amount
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

EXPLAIN
SELECT *
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

SELECT '07 慢日志演示：主动产生一条仅用于学习的慢查询' AS stage;

SELECT SLEEP(0.25) AS simulated_slow_query;

SELECT
    start_time,
    query_time,
    rows_examined,
    LEFT(CONVERT(sql_text USING utf8mb4), 120) AS sql_text
FROM mysql.slow_log
WHERE start_time >= NOW() - INTERVAL 5 MINUTE
ORDER BY start_time DESC
LIMIT 5;
