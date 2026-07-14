# Middleware Stack 学习实验室

这是一个面向中间件与基础设施学习的本地实验仓库。项目不以“看完文档”为目标，而是通过可重复实验，把原理、故障证据、面试表达和生产边界连接起来。

当前包含 MySQL、Redis、Kafka、Elasticsearch 和 Kubernetes 五条学习路线，适合用于：

- 系统补齐核心原理，而不是零散记忆结论；
- 通过原生客户端、脚本或清单复现真实行为；
- 练习从执行计划、指标、日志和对象状态中定位问题；
- 沉淀面试答案、生产 Runbook 和间隔复习记录。

## 项目入口

| 主题 | 课程内容 | 本地运行方式 | 学习入口 |
|---|---|---|---|
| MySQL | 表设计、索引、SQL 调优、MVCC、锁、InnoDB、恢复与复制、生产运维 | Docker Compose | [MySQL 学习实验室](mysql/study/README.md) |
| Redis | 数据建模、过期淘汰、性能、并发、持久化、Sentinel/Cluster、生产运维、缓存事故 | Docker Compose | [Redis 学习实验室](redis/study/README.md) |
| Kafka | 分区与顺序、生产消费、交付语义、日志存储、KRaft、高可用、生产事故 | Docker Compose | [Kafka 学习实验室](kafka/study/README.md) |
| Elasticsearch | 映射、分片、搜索、写入一致性、段与资源、副本、快照、综合事故 | Docker Compose | [Elasticsearch 学习实验室](Elasticsearch/study/README.md) |
| Kubernetes | 控制器调谐、工作负载、网络、安全、存储、调度、可观测性、生产审计 | 本机 Docker Desktop Kubernetes | [Kubernetes 学习实验室](k8s/study/README.md) |

五条路线都采用相同的学习闭环和验收标准，但课程主题、实验方式和生产边界按各自领域设计。

## 环境要求

- Docker 与 Docker Compose：运行 MySQL、Redis、Kafka 和 Elasticsearch 实验；
- Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)：运行 Python 实验和复习脚本；
- `kubectl` 与已启用的 Docker Desktop Kubernetes：仅 Kubernetes 路线需要；
- GNU Make：提供统一命令入口。

先在仓库根目录安装 Python 依赖：

```bash
uv sync
```

具体镜像、端口、凭据和资源要求以各主题的 `study/README.md` 与 `make help` 输出为准。本地示例凭据只用于学习，不能复用到生产环境。

## 快速开始

先选择一个主题查看可用命令和风险说明：

```bash
make -C mysql help
make -C redis help
make -C kafka help
make -C Elasticsearch help
make -C k8s help
```

再启动环境并运行第一个实验，例如：

```bash
make -C mysql up
make -C mysql table-design

make -C redis up
make -C redis data-structures

make -C kafka up
make -C kafka records-partitions

make -C Elasticsearch preflight
make -C Elasticsearch documents-mappings

make -C k8s up
make -C k8s architecture
```

每个主题的常用入口保持一致：

| 命令 | 作用 |
|---|---|
| `make -C <主题> help` | 查看模块命令、风险和清理方式 |
| `make -C <主题> up` | 启动或检查默认本地环境 |
| `make -C <主题> all` | 运行默认安全实验集 |
| `make -C <主题> review` | 随机抽取主动回忆题 |
| `make -C <主题> reset` | 仅清理课程命名空间内的实验数据 |
| `make -C <主题> down` | 停止默认环境或清理课程资源 |

`<主题>` 可替换为 `mysql`、`redis`、`kafka`、`Elasticsearch` 或 `k8s`。不同主题的 `up`、`down` 语义略有差异，执行前请先查看对应的 `help`。

## 学习方式

每个模块都围绕同一个闭环组织：

```text
原理 → 预测 → 最小实验 → 状态变化或故障 → 收集证据
    → 修复并验证 → 面试表达 → 生产边界 → 间隔复习
```

掌握度使用 L0～L4 记录：

- L0：无法可靠解释；
- L1：能用自己的话解释；
- L2：能独立复现实验并解释证据；
- L3：能根据计划、指标、日志或状态完成诊断；
- L4：能选择方案并说明取舍、风险和验证方式。

建议每次先闭卷完成模块的 `exercises.md`，再阅读原理并运行实验；至少修改一个变量、预测结果并解释新证据。参考答案位于 `answers.md`，用于校准机制和边界，不是背诵模板。

遗忘后可先阅读对应主题的 `CHEATSHEET.md`，运行 `make -C <主题> review`，重跑最薄弱的实验，再在 `ROADMAP.md` 中登记掌握等级、证据和下次复习日期。

## 目录约定

运行环境和统一命令入口位于主题根目录，课程内容统一放在 `study/`：

```text
middleware/
├── docker-compose.yml  # 本地运行环境；Kubernetes 主题除外
├── Makefile            # 统一命令入口
└── study/
    ├── README.md       # 学习入口与主题地图
    ├── ROADMAP.md      # L0～L4 进度、证据与复习日期
    ├── CHEATSHEET.md   # 15 分钟快速找回
    ├── labs/           # 原理、练习、答案与可运行实验
    ├── cases/          # 综合故障案例
    ├── interview/      # 主动回忆题库
    ├── review/         # 复习方法
    ├── runbooks/       # 生产诊断与恢复手册
    └── scripts/        # 造数、重置、复习等辅助脚本
```

## 安全边界

- 默认安全实验集 `all` 不包含强杀容器、删除数据卷、故障转移、额外集群或高负载实验；
- 破坏性、故障注入、多节点和资源密集型实验必须通过 `make help` 中标注的显式命令运行；
- MySQL 实验表、Redis 键、Kafka Topic/Group、Elasticsearch 索引和 Kubernetes Namespace 都使用课程专属命名范围；
- `reset` 只清理课程资源，不应触碰同一环境中的其他数据；
- 多节点或故障实验结束后，按对应主题文档执行专用清理命令。

## 课程校验

仓库级 [build-middleware-study Skill](.agents/skills/build-middleware-study/SKILL.md) 定义了课程架构、质量门禁、初始化模板和校验脚本。可以在仓库根目录校验全部学习路线：

```bash
for target in mysql redis kafka Elasticsearch k8s; do
  python3 .agents/skills/build-middleware-study/scripts/validate_study.py "$target/study"
done
```

结构校验通过不等于实验结论成立。课程内容变更后，还需要实际运行相关实验，并记录计划、锁、偏移量、Lag、分片状态、恢复结果或 Kubernetes 对象状态等可观察证据。
