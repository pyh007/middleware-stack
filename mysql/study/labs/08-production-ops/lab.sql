SELECT '01 关键配置基线：生产变更前必须保存实际值' AS stage;

SHOW VARIABLES
WHERE Variable_name IN (
    'max_connections',
    'max_user_connections',
    'wait_timeout',
    'interactive_timeout',
    'sql_mode',
    'performance_schema',
    'slow_query_log',
    'long_query_time'
);

SELECT '02 连接与失败累计状态：实际排查应比较时间窗口增量' AS stage;

SHOW GLOBAL STATUS
WHERE Variable_name IN (
    'Threads_connected',
    'Threads_running',
    'Max_used_connections',
    'Connections',
    'Aborted_connects',
    'Aborted_clients'
);

SELECT
    COALESCE(PROCESSLIST_USER, 'internal') AS user_name,
    COALESCE(PROCESSLIST_DB, '-') AS database_name,
    PROCESSLIST_COMMAND AS command_name,
    COUNT(*) AS connection_count
FROM performance_schema.threads
WHERE TYPE = 'FOREGROUND'
GROUP BY PROCESSLIST_USER, PROCESSLIST_DB, PROCESSLIST_COMMAND
ORDER BY connection_count DESC;

SELECT '03 语句摘要：按总耗时而不是只按单次最慢排序' AS stage;

SELECT
    LEFT(DIGEST_TEXT, 100) AS digest_text,
    COUNT_STAR AS executions,
    ROUND(SUM_TIMER_WAIT / 1000000000000, 3) AS total_seconds,
    SUM_ROWS_EXAMINED AS rows_examined,
    SUM_ROWS_SENT AS rows_sent
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME = DATABASE()
  AND DIGEST_TEXT IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;

SELECT '04 容量基线：information_schema 的行数是 InnoDB 估算值' AS stage;

SELECT
    table_name,
    table_rows,
    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
    ROUND(index_length / 1024 / 1024, 2) AS index_mb,
    ROUND(data_free / 1024 / 1024, 2) AS data_free_mb
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY data_length + index_length DESC;

SELECT '05 查看当前未被统计到使用的索引；不能据此立即删除' AS stage;

SELECT
    object_name AS table_name,
    index_name
FROM sys.schema_unused_indexes
WHERE object_schema = DATABASE()
ORDER BY table_name, index_name;

SELECT '06 最小权限：只读账号不应拥有写入和管理权限' AS stage;

DROP USER IF EXISTS 'lab_readonly'@'%';
CREATE USER 'lab_readonly'@'%' IDENTIFIED BY 'local-study-only-123456';
GRANT SELECT ON study.* TO 'lab_readonly'@'%';
SHOW GRANTS FOR 'lab_readonly'@'%';
DROP USER 'lab_readonly'@'%';

SELECT '生产巡检实验完成：配置、连接、语句、容量和权限均已采集。' AS result;
