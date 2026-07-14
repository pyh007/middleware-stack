-- 为索引和 SQL 调优模块生成确定性的 100000 行订单数据。
-- 每次执行都会重建 lab_orders，以保证实验可重复。

DROP TABLE IF EXISTS lab_orders;

CREATE TABLE lab_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '聚簇索引主键',
    order_no CHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL COMMENT '业务订单号',
    customer_id BIGINT UNSIGNED NOT NULL,
    status TINYINT UNSIGNED NOT NULL COMMENT '10待支付 20已支付 30已完成 40已取消 50已退款',
    amount DECIMAL(12, 2) NOT NULL,
    created_at DATETIME NOT NULL,
    note VARCHAR(255) NOT NULL COMMENT '模拟非索引的大字段',
    PRIMARY KEY (id),
    UNIQUE KEY uk_lab_orders_order_no (order_no),
    CONSTRAINT chk_lab_orders_status CHECK (status IN (10, 20, 30, 40, 50)),
    CONSTRAINT chk_lab_orders_amount CHECK (amount >= 0)
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

CREATE TEMPORARY TABLE lab_digits (
    n TINYINT UNSIGNED NOT NULL PRIMARY KEY
);

INSERT INTO lab_digits (n)
VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9);

-- MySQL 不允许在同一条查询中多次重开同一张临时表，因此复制为
-- 五张独立小表，再通过笛卡尔积稳定生成 0～99999。
CREATE TEMPORARY TABLE lab_digits_tens LIKE lab_digits;
CREATE TEMPORARY TABLE lab_digits_hundreds LIKE lab_digits;
CREATE TEMPORARY TABLE lab_digits_thousands LIKE lab_digits;
CREATE TEMPORARY TABLE lab_digits_ten_thousands LIKE lab_digits;

INSERT INTO lab_digits_tens SELECT n FROM lab_digits;
INSERT INTO lab_digits_hundreds SELECT n FROM lab_digits;
INSERT INTO lab_digits_thousands SELECT n FROM lab_digits;
INSERT INTO lab_digits_ten_thousands SELECT n FROM lab_digits;

INSERT INTO lab_orders (
    order_no,
    customer_id,
    status,
    amount,
    created_at,
    note
)
SELECT
    CONCAT('ORD', LPAD(sequence_no, 17, '0')),
    1 + MOD(sequence_no * 37, 10000),
    CASE
        WHEN MOD(sequence_no, 20) < 2 THEN 10
        WHEN MOD(sequence_no, 20) < 5 THEN 20
        WHEN MOD(sequence_no, 20) < 18 THEN 30
        WHEN MOD(sequence_no, 20) = 18 THEN 40
        ELSE 50
    END,
    CAST((MOD(sequence_no * 7919, 500000) + 100) / 100 AS DECIMAL(12, 2)),
    DATE_ADD('2025-01-01 00:00:00', INTERVAL sequence_no MINUTE),
    CONCAT('学习订单-', sequence_no, '-', REPEAT('x', 96))
FROM (
    SELECT
        ones.n
        + tens.n * 10
        + hundreds.n * 100
        + thousands.n * 1000
        + ten_thousands.n * 10000
        + 1 AS sequence_no
    FROM lab_digits AS ones
    CROSS JOIN lab_digits_tens AS tens
    CROSS JOIN lab_digits_hundreds AS hundreds
    CROSS JOIN lab_digits_thousands AS thousands
    CROSS JOIN lab_digits_ten_thousands AS ten_thousands
) AS numbers
ORDER BY sequence_no;

ANALYZE TABLE lab_orders;

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customer_id) AS customers,
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS last_order_at
FROM lab_orders;

SELECT status, COUNT(*) AS rows_per_status
FROM lab_orders
GROUP BY status
ORDER BY status;
