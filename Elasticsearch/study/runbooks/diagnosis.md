# Elasticsearch 生产诊断 Runbook

## 1. 判断影响和紧急程度

记录开始时间、受影响 API/租户/索引、错误率、P50/P95/P99、吞吐、数据新鲜度和最近变更。明确读不可用、写被拒绝、搜索变慢、结果不完整或恢复变慢中的哪一种；为每种现象指定业务负责人。先定义止损成功条件，避免把“集群变绿”误当成业务恢复。

## 2. 保存现场

按同一时间窗保存：客户端超时/重试/连接池，入口 QPS 和大请求；`_cluster/health?level=indices`、`_cat/nodes`、`_cat/shards`、`_cluster/pending_tasks`、`_tasks`、allocation explain；节点 JVM/GC、线程池 queue/rejected、磁盘水位、I/O、CPU、网络；索引 mapping/settings/segments/merge/cache；慢日志和 Elasticsearch 日志；发布、模板、ILM、路由与容量变更。敏感字段和凭据进入受控事故存储，不贴到公开聊天。

## 3. 定位顺序

1. **范围**：全部请求还是某索引、分片、节点或租户；比较健康与异常分组。
2. **可用性**：red 主分片、yellow 副本、master/pending task、节点离线和分配原因。
3. **背压**：客户端重试是否放大；search/write queue 与 rejected；长任务和大聚合。
4. **资源**：heap/GC、磁盘与水位、merge/throttle、CPU、I/O、文件句柄和网络。
5. **数据模型**：字段数、分片尺寸/偏斜、routing、segment 数、删除比例和查询 fan-out。
6. **请求**：用慢日志和代表性请求 `profile`；确认 query/filter、分页、聚合桶和返回字段。
7. **变更**：把异常拐点与 mapping、模板、refresh、replica、ILM、版本或客户端发布对齐。

单次 `profile` 会增加请求开销，只对代表性请求受控采样。allocation explain 应指定一个未分配分片，并保存 decider 结论，不要只看摘要。

## 4. 止损与修复

- 入口按租户/请求类型限流，禁止无界重试；保护核心查询和关键写入。
- 暂停造成动态字段、超大 bulk、深分页或高基数聚合的来源；保留可重放队列。
- 有证据时回滚最近 mapping/template/refresh/routing/客户端变更。
- 磁盘水位先按审批释放明确过期数据或扩容；不要关闭保护阈值掩盖风险。
- 分片故障先恢复节点/网络/磁盘，再观察自动恢复；手工 reroute 前记录命令与数据丢失风险。
- 只有在不可变索引、空间充足和低峰验证后才考虑 force merge。

每一步只改变一个主要变量，记录执行人、时间、命令、预期、实际和撤销方法。

## 5. 验证、灰度与回滚

业务验证包括错误率、延迟、结果完整性、写入新鲜度和关键文档 checksum；平台验证包括 health、unassigned、rejected、GC、heap、磁盘、merge、恢复速率和客户端重试。先镜像或小租户，再 1%/10%/50%/100% 灰度。任一 SLO 反弹、数据校验失败、磁盘继续恶化或恢复估时越界就回滚并重新限流。

事故结束前保存根因证据、遗漏的告警、容量余量、长期 owner 和截止时间，并用 [综合事故题](../cases/production-incident/README.md) 复盘。
