# MySQL 可重复学习实验室

这里不是 MySQL 资料收藏夹，而是一套面向面试和生产的训练系统。每个主题都必须完成：

```text
概念 → 最小实验 → 制造问题 → 查看证据 → 修复 → 面试表达 → 生产检查
```

当前基线是 MySQL 8.4。实验数据库只监听宿主机 `127.0.0.1:3306`，账号密码仅用于本地学习，不能复制到生产环境。

## 从这里开始

在仓库根目录执行：

```bash
make -C mysql help
make -C mysql up
make -C mysql quickstart
```

首轮按顺序学习：

1. [表设计与数据类型](labs/01-table-design/README.md)
2. [索引设计](labs/02-index/README.md)
3. [SQL 调优](labs/03-sql-tuning/README.md)
4. [事务、隔离级别与 MVCC](labs/04-transaction-mvcc/README.md)
5. [锁、锁等待与死锁](labs/05-lock-deadlock/README.md)
6. [InnoDB、日志与崩溃恢复](labs/06-innodb/README.md)
7. [备份恢复与主从复制](labs/07-replication-backup/README.md)
8. [生产巡检、变更与综合验收](labs/08-production-ops/README.md)

运行日常安全实验：

```bash
make -C mysql all
```

`all` 会运行八周中不主动中断容器、不额外启动主从的实验。崩溃恢复和独立主从需要显式执行：

```bash
make -C mysql crash-recovery
make -C mysql replication
make -C mysql replication-down
```

`index`、`tuning` 和 `production` 会先重建 10 万行订单数据，保证执行计划可以重复观察。实验表统一使用 `lab_` 前缀，可随时清理：

```bash
make -C mysql reset
```

## 学习地图

| 模块 | 面试目标 | 实验目标 | 生产目标 | 状态 |
|---|---|---|---|---|
| 表设计 | 解释主键、类型、字符集和范式取舍 | 设计用户与订单表 | 避免精度、时间和约束问题 | 可学习 |
| 索引 | 解释 B+Tree、联合索引、回表、覆盖索引 | 对比全表扫描与索引扫描 | 控制慢查询和写放大 | 可学习 |
| SQL 调优 | 读懂执行计划并给出优化顺序 | 验证函数、分页等典型问题 | 建立慢 SQL 排查流程 | 可学习 |
| 事务与 MVCC | 解释隔离级别和可见性 | 双连接对比 RC/RR | 选择正确事务边界 | 可学习 |
| 锁与死锁 | 解释记录锁、间隙锁、临键锁 | 观察阻塞链并制造死锁 | 定位并缓解锁冲突 | 可学习 |
| InnoDB | 解释 buffer pool、redo、undo、binlog | 回滚、状态与崩溃恢复 | 理解性能和持久性取舍 | 可学习 |
| 复制与恢复 | 解释复制、GTID、RPO、RTO | 误删恢复和独立主从 | 制定备份恢复方案 | 可学习 |
| 生产运维 | 解释容量、监控、安全 | 巡检与综合事故 | 编写可执行 Runbook | 可学习 |

具体进度和掌握等级记录在 [ROADMAP.md](ROADMAP.md)，核心结论集中在 [CHEATSHEET.md](CHEATSHEET.md)。

## 一次标准学习会话

建议每次 45～60 分钟：

1. 先用 10 分钟闭卷回答 `exercises.md`。
2. 用 10～15 分钟阅读模块 `README.md`。
3. 用 20～30 分钟运行并修改 `lab.sql`。
4. 用 10 分钟记录自己的解释、实验结果和疑问。

不要只看实验输出。至少修改一次查询条件或索引顺序，并预测新的执行计划。

## 忘记之后如何回来

只有 15 分钟时：

1. 看 [CHEATSHEET.md](CHEATSHEET.md) 恢复知识地图。
2. 执行 `make -C mysql review`，先口述再看答案。
3. 重跑最薄弱模块的实验。
4. 在 [ROADMAP.md](ROADMAP.md) 更新掌握等级和下次复习日期。

复习节奏及题库使用方式见 [review/README.md](review/README.md)。生产排查入口放在 [runbooks](runbooks)，综合故障案例放在 [cases](cases)。

## 目录约定

每个正式模块包含：

- `README.md`：原理、学习顺序和完成标准。
- `lab.sql`、`lab.py` 或实验脚本：可观察证据的实验。
- `exercises.md`：先做后看的主动回忆题。
- `answers.md`：参考答案及生产取舍，不是背诵模板。

实验 SQL 主要负责暴露数据库行为；Python 用于造数、并发和自动验证，避免驱动或 ORM 隐藏 MySQL 原理。
