SELECT '01 InnoDB 持久性和日志关键配置' AS stage;

SHOW VARIABLES
WHERE Variable_name IN (
    'innodb_flush_log_at_trx_commit',
    'sync_binlog',
    'log_bin',
    'binlog_format',
    'transaction_isolation',
    'innodb_buffer_pool_size'
);

SELECT '02 创建实验表并确认物理组织信息' AS stage;

DROP TABLE IF EXISTS lab_innodb_records;

CREATE TABLE lab_innodb_records (
    id BIGINT UNSIGNED NOT NULL,
    value_text VARCHAR(200) NOT NULL,
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

INSERT INTO lab_innodb_records (id, value_text)
VALUES (1, 'committed-value');

SELECT
    table_name,
    engine,
    row_format,
    table_rows,
    data_length,
    index_length
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_name = 'lab_innodb_records';

SELECT '03 undo 让事务能够回滚到修改前的逻辑值' AS stage;

START TRANSACTION;
UPDATE lab_innodb_records
SET value_text = 'value-visible-inside-transaction'
WHERE id = 1;
SELECT id, value_text AS value_before_rollback FROM lab_innodb_records WHERE id = 1;
ROLLBACK;
SELECT id, value_text AS value_after_rollback FROM lab_innodb_records WHERE id = 1;

SELECT '04 buffer pool 和 redo 的累计状态；差值比单个绝对值更有意义' AS stage;

SHOW GLOBAL STATUS
WHERE Variable_name IN (
    'Innodb_buffer_pool_read_requests',
    'Innodb_buffer_pool_reads',
    'Innodb_buffer_pool_pages_dirty',
    'Innodb_buffer_pool_wait_free',
    'Innodb_log_waits',
    'Innodb_os_log_written'
);

SELECT '05 当前 binary log 位置与文件列表' AS stage;
SHOW BINARY LOG STATUS;
SHOW BINARY LOGS;
