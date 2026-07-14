-- 删除本阶段创建的实验对象，不影响原有 learning_accounts 表。
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS lab_design_orders;
DROP TABLE IF EXISTS lab_design_users;
DROP TABLE IF EXISTS lab_bad_orders;
DROP TABLE IF EXISTS lab_orders;
DROP TABLE IF EXISTS lab_mvcc_accounts;
DROP TABLE IF EXISTS lab_lock_accounts;
DROP TABLE IF EXISTS lab_innodb_records;
DROP TABLE IF EXISTS lab_crash_recovery;
DROP TABLE IF EXISTS lab_recovery_items;

SET FOREIGN_KEY_CHECKS = 1;

SELECT '实验表已清理；原有 quickstart 数据未受影响。' AS result;
