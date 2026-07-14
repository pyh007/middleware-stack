# Elasticsearch 可重复学习实验室

这套课程面向“能讲清机制、能用证据诊断、能在生产边界内做决策”三个目标。八个模块使用 Elasticsearch 原生 REST API 复现分析链、分片路由、搜索画像、写入可见性、段与缓存、副本恢复、快照恢复和综合事故；脚本对关键结论直接断言，退出码为零不再是唯一成功标准。

## 从这里开始

```bash
make -C Elasticsearch help
make -C Elasticsearch preflight
make -C Elasticsearch up
make -C Elasticsearch documents-mappings
make -C Elasticsearch review
```

本地地址为 `http://127.0.0.1:9200`。默认账号 `elastic`、密码 `elastic-local-123` 只用于本机学习；可以通过 `ES_PASSWORD` 覆盖，不能把该凭据或单节点配置复制到生产。

为兼容磁盘空间较小的 Docker Desktop 虚拟盘，本地 Compose 使用绝对剩余空间水位，默认 low/high/flood-stage 为 1536MB/1GB/512MB，merge 高水位为 512MB；保护机制仍然启用。`preflight` 同时检查宿主机和可检测到的 Docker 虚拟盘空间。生产必须按容量、增长和故障模型重新设计水位并预留 merge、恢复和节点故障空间。

默认 `up` 只启动 Elasticsearch；需要可视化界面时使用 `make -C Elasticsearch up-kibana`，Kibana 仅绑定 `127.0.0.1:5601`。`stop` 保留容器、网络和卷，`down` 删除容器与网络但保留卷。

## 学习路线

1. [文档映射与分析链](labs/01-documents-mappings/README.md)：字段如何进入倒排索引，为什么映射是数据契约。
2. [索引分片路由与别名](labs/02-index-shards/README.md)：扩展单位、路由边界和无停机切换。
3. [倒排索引搜索评分与聚合](labs/03-search-profile/README.md)：相关性、过滤、聚合、画像与深分页。
4. [刷新事务日志与并发控制](labs/04-write-consistency/README.md)：写入确认、搜索可见、持久化和冲突检测。
5. [段合并缓存与资源](labs/05-segments-resources/README.md)：不可变段、合并成本、堆、缓存与线程池。
6. [副本分配与集群可用性](labs/06-cluster-availability/README.md)：yellow/red、分配决策和主分片故障。
7. [快照安全容量与生产运维](labs/07-snapshot-operations/README.md)：恢复证明、最小权限、容量与升级边界。
8. [事故诊断与面试综合](labs/08-incident-capstone/README.md)：映射爆炸、热点分片和拒绝请求的联合推理。

每个模块先闭卷完成 `exercises.md`，再阅读原理、运行实验、解释证据，最后修改指定变量。掌握度和复习证据记录到 [ROADMAP.md](ROADMAP.md)，15 分钟找回路径见 [CHEATSHEET.md](CHEATSHEET.md)。

## 命令与风险分层

| 类型 | 命令 | 影响与清理 |
|---|---|---|
| 安全 | `make -C Elasticsearch all` | 重建八组 `lab-es-` 索引；不停止节点、不删卷 |
| 安全 | `make -C Elasticsearch reset` | 只删 `lab-es-` 索引、课程别名、课程账号和快照仓库 |
| 资源操作 | `make -C Elasticsearch force-merge` | 仅合并 `lab-es-05-force-merge`，产生磁盘 I/O |
| 恢复 | `make -C Elasticsearch snapshot-restore` | 仅删除并恢复 `lab-es-07-restore` |
| 多节点故障 | `make -C Elasticsearch cluster-failover` | 启动独立三节点、停止一个数据节点并重新启动 |
| 删除 | `make -C Elasticsearch destroy-lab-data CONFIRM=destroy` | 永久删除根课程的 ES、快照与 Kibana 卷，不删除 `elastic-start-local` 文件和卷 |

三节点实验结束后运行 `make -C Elasticsearch cluster-down`。默认 `all` 不依赖任何资源操作、数据删除、故障注入或额外集群命令。

## 生产迁移

- 先定义业务 SLO、写入确认语义、RPO/RTO，再选择分片、副本、刷新和快照策略。
- 修改映射、分片数、路由或生命周期前，评估重建成本、磁盘峰值、客户端兼容和回滚路径。
- 排障时保存 `_cluster/health`、`_cat/shards`、allocation explain、节点资源、线程池、任务、慢日志和最近变更；不要先做 force merge 或无证据重启。
- 快照成功不等于可恢复，必须在隔离环境周期性恢复并校验业务文档与权限。

生产情境从 [综合事故题](cases/production-incident/README.md) 开始，操作顺序参考 [诊断 Runbook](runbooks/diagnosis.md)、[恢复 Runbook](runbooks/recovery.md) 和 [安全容量 Runbook](runbooks/security-capacity.md)。
