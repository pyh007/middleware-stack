# Kafka 可运行、可复习学习体系

这不是资料索引，而是一套用真实 Broker 行为证明结论的训练系统：既能准备 Kafka 面试，也能练习生产中的积压、重复、故障切换和恢复判断。当前实验基线为 Apache Kafka 4.3.1、KRaft 模式。

## 从这里开始

在仓库根目录执行：

```bash
make -C kafka help
make -C kafka up
make -C kafka records-partitions
```

Kafka 监听 `127.0.0.1:9092`，Kafka UI 监听 `127.0.0.1:8080`。默认环境使用 PLAINTEXT 且没有业务账号，只允许本机学习，不能作为生产安全示例。原有快速示例仍可运行：

```bash
make -C kafka quickstart
```

## 学习路线

1. [记录、主题、分区与顺序](labs/01-records-partitions/README.md)
2. [生产者批处理、压缩与可靠性](labs/02-producer-reliability/README.md)
3. [消费组、位点、延迟与再均衡](labs/03-consumer-groups/README.md)
4. [交付语义、幂等处理与事务](labs/04-delivery-semantics/README.md)
5. [日志段、保留、压缩与吞吐](labs/05-log-storage/README.md)
6. [复制、ISR、Leader 与 KRaft](labs/06-replication-kraft/README.md)
7. [容量、可观测性、安全与恢复](labs/07-production-ops/README.md)
8. [积压、重复与丢数声称综合事故](labs/08-incident-capstone/README.md)

每个模块都按以下闭环学习：

```text
先预测 → 运行最小实验 → 制造状态变化 → 保存证据 → 解释边界 → 修改变量 → 形成面试表达
```

## 命令与风险

日常安全全量实验只重建 `lab_kafka_` 前缀 Topic，并使用同前缀 Consumer Group：

```bash
make -C kafka all
make -C kafka reset
```

`reset` 不删除数据卷，也不会触碰其他前缀的 Topic 或 Group。`all` 不停止 Broker、不删除卷、不启动额外集群。

三节点与故障实验必须显式运行：

```bash
make -C kafka cluster-up        # 额外占用 19092、19093、19094 和三个数据卷
make -C kafka cluster-down      # 删除独立集群及其三个实验卷
make -C kafka cluster-failover  # 停止 Topic Leader，验证选举/ISR，结束后自动清理
```

`cluster-failover` 只影响项目名 `kafka-study-cluster` 的独立容器，不中断默认 `kafka` 容器。它会创建并删除额外数据卷，不能改成默认依赖。

## 一次标准学习会话

建议每次 45～60 分钟：先闭卷回答 `exercises.md`，再读模块原理；运行命令并保存 partition、offset、lag、ISR 或文件大小等证据；修改一个参数并先写预测；最后用“结论 → 机制 → 证据 → 边界 → 副作用 → 生产验证”口述答案。

综合案例见 [生产事故题](cases/production-incident/README.md)，操作步骤见 [生产排查 Runbook](runbooks/diagnosis.md) 与 [恢复 Runbook](runbooks/recovery.md)。

## 忘记后 15 分钟回来

1. 用 [CHEATSHEET.md](CHEATSHEET.md) 恢复数据路径和故障边界。
2. 运行 `make -C kafka review`，先口述再看参考要点。
3. 重跑最薄弱模块的一个实验。
4. 在 [ROADMAP.md](ROADMAP.md) 记录等级、证据和下次复习日。

复习间隔与记录方式见 [主动回忆说明](review/README.md)。
