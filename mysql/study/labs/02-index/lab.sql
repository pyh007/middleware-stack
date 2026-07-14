SELECT '01 基线：只有主键和订单号唯一索引' AS stage;

EXPLAIN
SELECT id, customer_id, status, amount, created_at
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

EXPLAIN ANALYZE
SELECT id, customer_id, status, amount, created_at
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

SELECT '02 联合索引同时服务等值过滤和排序' AS stage;

CREATE INDEX idx_lab_orders_customer_status_created
    ON lab_orders (customer_id, status, created_at DESC);

ANALYZE TABLE lab_orders;

EXPLAIN
SELECT id, customer_id, status, amount, created_at
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

EXPLAIN ANALYZE
SELECT id, customer_id, status, amount, created_at
FROM lab_orders
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

SELECT '03 左侧前缀：比较三种查询，不预设优化器一定选什么' AS stage;

EXPLAIN SELECT id FROM lab_orders WHERE customer_id = 42;
EXPLAIN SELECT id FROM lab_orders WHERE customer_id = 42 AND status = 30;
EXPLAIN SELECT id FROM lab_orders WHERE status = 30;

SELECT '04 范围条件：观察 key_len、rows 和是否额外排序' AS stage;

EXPLAIN
SELECT id, customer_id, status, created_at
FROM lab_orders
WHERE customer_id = 42
  AND status >= 20
ORDER BY created_at DESC
LIMIT 20;

SELECT '05 覆盖索引与回表：FORCE INDEX 只用于教学对照' AS stage;

CREATE INDEX idx_lab_orders_covering
    ON lab_orders (customer_id, status, created_at DESC, amount);

ANALYZE TABLE lab_orders;

-- id 是主键，已经隐含在 InnoDB 二级索引叶子节点中。
EXPLAIN
SELECT id, amount, created_at
FROM lab_orders FORCE INDEX (idx_lab_orders_covering)
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

-- note 不在索引中，需要访问聚簇索引。
EXPLAIN
SELECT id, amount, created_at, note
FROM lab_orders FORCE INDEX (idx_lab_orders_covering)
WHERE customer_id = 42
  AND status = 30
ORDER BY created_at DESC
LIMIT 20;

SELECT '06 查看索引定义；思考前两个联合索引是否都值得保留' AS stage;
SHOW INDEX FROM lab_orders;

SELECT
    table_name,
    index_length,
    data_length,
    table_rows
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name = 'lab_orders';
