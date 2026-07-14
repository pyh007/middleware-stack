SELECT '01 表设计实验：错误设计可以写入无效语义' AS stage;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS lab_design_orders;
DROP TABLE IF EXISTS lab_design_users;
DROP TABLE IF EXISTS lab_bad_orders;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE lab_bad_orders (
    id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(255),
    amount FLOAT,
    status VARCHAR(50),
    created_at VARCHAR(50),
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4;

INSERT INTO lab_bad_orders (id, customer_name, amount, status, created_at)
VALUES
    ('order-1', '张三', 0.1, 'anything-is-accepted', '2025-99-99'),
    ('order-2', '李四', 199.99, 'PAID', 'not-a-date');

SELECT
    id,
    amount,
    CAST(amount AS DECIMAL(30, 18)) AS float_internal_approximation,
    status,
    created_at
FROM lab_bad_orders
ORDER BY id;

SELECT '02 正确类型和约束把业务规则落入数据库' AS stage;

CREATE TABLE lab_design_users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '稳定、较短的聚簇索引键',
    email VARCHAR(254) CHARACTER SET ascii COLLATE ascii_general_ci NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    status TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1正常 2冻结 3注销',
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_lab_design_users_email (email),
    CONSTRAINT chk_lab_design_users_status CHECK (status IN (1, 2, 3))
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE lab_design_orders (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_no CHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    status TINYINT UNSIGNED NOT NULL COMMENT '10待支付 20已支付 30已完成 40已取消',
    created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    paid_at DATETIME(3) NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_lab_design_orders_order_no (order_no),
    KEY idx_lab_design_orders_user_created (user_id, created_at DESC),
    CONSTRAINT fk_lab_design_orders_user
        FOREIGN KEY (user_id) REFERENCES lab_design_users (id),
    CONSTRAINT chk_lab_design_orders_amount CHECK (amount >= 0),
    CONSTRAINT chk_lab_design_orders_status CHECK (status IN (10, 20, 30, 40))
) ENGINE = InnoDB
  DEFAULT CHARACTER SET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

INSERT INTO lab_design_users (email, nickname)
VALUES ('learner@example.com', '学习者');

INSERT INTO lab_design_orders (order_no, user_id, amount, status)
VALUES ('ORD00000000000000001', 1, 199.99, 10);

SELECT
    o.id,
    o.order_no,
    u.email,
    o.amount,
    o.status,
    o.created_at
FROM lab_design_orders AS o
JOIN lab_design_users AS u ON u.id = o.user_id;

SELECT '03 数据库拒绝非法状态；应用校验不能替代最终约束' AS stage;

DROP PROCEDURE IF EXISTS lab_try_invalid_status;

DELIMITER //
CREATE PROCEDURE lab_try_invalid_status()
BEGIN
    DECLARE constraint_rejected BOOLEAN DEFAULT FALSE;
    BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET constraint_rejected = TRUE;
        INSERT INTO lab_design_orders (order_no, user_id, amount, status)
        VALUES ('ORD00000000000000002', 1, 100.00, 99);
    END;

    SELECT
        IF(
            constraint_rejected,
            '符合预期：CHECK 约束拒绝了 status=99',
            '异常：非法状态被写入'
        ) AS constraint_result;
END//
DELIMITER ;

CALL lab_try_invalid_status();
DROP PROCEDURE lab_try_invalid_status;

SELECT '04 查看真实列定义和索引，而不是只看建表 SQL' AS stage;

SELECT
    table_name,
    column_name,
    column_type,
    is_nullable,
    column_key,
    column_default,
    collation_name
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name IN ('lab_bad_orders', 'lab_design_users', 'lab_design_orders')
ORDER BY table_name, ordinal_position;

SHOW INDEX FROM lab_design_orders;
