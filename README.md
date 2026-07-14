# Middleware Stack 学习实验室

这个仓库用于系统学习 MySQL、Redis、Kafka、Elasticsearch 和 Kubernetes，目标同时覆盖：

- 面试：能用自己的话解释机制、边界和取舍。
- 实践：每个结论都有可重复运行的实验和证据。
- 生产：能定位故障、评估风险、设计上线与回滚方案。
- 复习：遗忘后能在 15 分钟内找到知识地图和核心实验。

## 学习模型

每个中间件都按同一个闭环建设：

```text
知识地图
→ 最小实验
→ 制造问题
→ 收集指标和证据
→ 修复并验证
→ 面试表达
→ 生产 Runbook
→ 间隔复习
```

掌握度分为：能解释（L1）、能验证（L2）、能诊断（L3）、能决策（L4）。看完文档不算掌握，至少独立跑通实验并解释结果后才达到 L2。

## 当前入口

| 中间件 | 当前内容 | 学习入口 |
|---|---|---|
| MySQL | 八周完整课程：设计、调优、并发、InnoDB、恢复、复制、生产运维 | [mysql/study/README.md](mysql/study/README.md) |
| Redis | 八模块完整课程：数据建模、生命周期、性能、并发、持久化、高可用、运维、缓存事故 | [redis/study/README.md](redis/study/README.md) |
| Kafka | 八模块完整课程：分区、生产消费、语义、存储、KRaft、高可用和生产事故 | [kafka/study/README.md](kafka/study/README.md) |
| Elasticsearch | 八模块完整课程：映射、分片、搜索、写入一致性、段资源、高可用、快照运维和生产事故 | [Elasticsearch/study/README.md](Elasticsearch/study/README.md) |

MySQL、Redis、Kafka 和 Elasticsearch 均使用同一学习闭环与验收标准，但课程主题、实验和生产边界按各自领域设计。

## 推荐起点

```bash
make -C mysql help
make -C mysql quickstart
make -C redis help
make -C redis all
make -C Elasticsearch help
make -C Elasticsearch all
```

完整 MySQL 学习路线、复习方法和实验命令见 [MySQL 可重复学习实验室](mysql/study/README.md)。

## 通用模块约定

每个中间件把运行环境放在模块根目录，把学习内容统一收进 `study/`：

```text
middleware/
├── docker-compose.yml  运行环境
├── Makefile            统一命令入口
└── study/
    ├── README.md       总入口和知识地图
    ├── ROADMAP.md      掌握等级、最近与下次复习日期
    ├── CHEATSHEET.md   15 分钟快速找回
    ├── labs/           可重复实验
    ├── cases/          综合故障案例
    ├── interview/      主动回忆题库
    ├── runbooks/       生产排查与恢复手册
    └── scripts/        造数、重置和自动验证
```

所有实验应满足：环境可启动、数据可重建、命令可重复、预期证据明确、清理不误伤非实验数据。

## 可复用 Skill

跨中间件课程使用 [build-middleware-study](.agents/skills/build-middleware-study/SKILL.md) 统一生成和审计。它包含：

- 课程架构、质量门禁和 Redis/Kafka/Elasticsearch 主题规划参考。
- `study/` 初始化模板和主动回忆脚本。
- 初始化器与课程质量校验器。

验证一个已经完成的课程：

```bash
python .agents/skills/build-middleware-study/scripts/validate_study.py mysql/study
```

该 Skill 位于 Codex 正式支持的仓库级发现目录 `.agents/skills/`，随仓库共享，无需个人安装副本。
