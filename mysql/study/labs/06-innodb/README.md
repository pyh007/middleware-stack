# 06 InnoDB、日志与崩溃恢复

## 学习目标

- 解释 buffer pool、redo log、undo log、binlog 的职责与协作关系。
- 理解 WAL、脏页、checkpoint 和崩溃恢复的基本过程。
- 说明 `innodb_flush_log_at_trx_commit` 与 `sync_binlog` 的持久性取舍。
- 区分 redo 与 binlog，理解两阶段提交要解决的问题。

## 基础实验

```bash
make -C mysql innodb
```

实验会观察当前持久性配置、表物理信息、事务回滚、buffer pool/redo 状态和 binary log 位置。

状态变量是实例启动以来的累计值。排查时应在相同时间窗口采集两次计算速率或命中率，而不是只对一个绝对值下结论。例如逻辑读请求很多并不等于磁盘读很多，应结合 `Innodb_buffer_pool_reads` 的增量分析。

## 崩溃恢复实验

下面的命令会先提交一条唯一标记，再使用 `SIGKILL` 强制终止本地学习容器，随后启动并验证标记仍然存在：

```bash
make -C mysql crash-recovery
```

这会短暂中断本仓库的本地 MySQL，只能在学习环境主动执行，不能照搬到共享或生产实例。

## 四类核心组件

- buffer pool：缓存数据页和索引页，修改通常先发生在内存页中。
- redo log：记录页修改的物理变化，用 WAL 保证已提交修改可在崩溃后重放。
- undo log：保存构造旧版本和回滚所需的信息，也支撑 MVCC。
- binlog：Server 层逻辑变更日志，用于复制、审计链路和基于时间点恢复。

redo 与 binlog 属于不同层、服务不同目标。提交时需要协调两者，避免崩溃后出现“存储已提交但复制日志没有”或相反的不一致状态。

## 完成标准

- 能画出一次 `UPDATE` 从 buffer pool、redo、binlog 到提交响应的主要步骤。
- 能解释已提交事务和未提交事务在崩溃恢复中的处理差异。
- 能说明修改刷盘参数可能丢失什么、换来什么。
- 能根据状态增量判断 buffer pool 是否产生明显物理读压力。
