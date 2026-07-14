# Elasticsearch 15 分钟找回速查

这不是第二本教材。忘记后先恢复地图，再抽题、跑一个实验、记一个薄弱点。

## 0～3 分钟：数据路径

```text
JSON 文档 → mapping/analyzer → primary shard → translog + indexing buffer
→ refresh 生成可搜索 segment → replica → merge → snapshot repository
查询 → 协调节点 scatter → shard query → fetch/aggregate → reduce → 客户端
```

- `text` 分析后检索，`keyword` 保留整体值用于过滤、排序和聚合。
- primary shard 数决定索引的基础并行与路由空间；replica 提供读取副本和故障冗余。
- 写入成功、实时 GET 可见、搜索可见、flush 持久化边界是不同事件。
- segment 不可变；删除先记墓碑，merge 才真正回收，代价是磁盘 I/O 和临时空间。

## 3～7 分钟：八个关键问题

1. 映射是长期数据契约；动态字段必须有模板或上限。[实验 01](labs/01-documents-mappings/README.md)
2. 自定义 routing 能减少 fan-out，也能制造热点和迁移约束。[实验 02](labs/02-index-shards/README.md)
3. query 计算相关性，filter 表达布尔约束；慢查询用 profile 证明耗时位置。[实验 03](labs/03-search-profile/README.md)
4. refresh 影响搜索可见与段生成，flush 影响 Lucene commit/translog，不应混为一谈。[实验 04](labs/04-write-consistency/README.md)
5. cache hit 只有在请求和段稳定时有意义；同时看 heap、GC、磁盘、线程池和负载。[实验 05](labs/05-segments-resources/README.md)
6. yellow 常表示副本未分配但主分片可用；red 才表示至少一个主分片未分配。[实验 06](labs/06-cluster-availability/README.md)
7. 快照是增量的段级备份；成功状态必须配合恢复演练和业务校验。[实验 07](labs/07-snapshot-operations/README.md)
8. 映射爆炸、热点分片和 rejected 往往互相放大，先控流和冻结变更，再定位资源等待。[实验 08](labs/08-incident-capstone/README.md)

## 7～11 分钟：最小诊断集

```bash
curl -u elastic:elastic-local-123 '127.0.0.1:9200/_cluster/health?pretty'
curl -u elastic:elastic-local-123 '127.0.0.1:9200/_cat/nodes?v&h=name,roles,heap.percent,ram.percent,cpu,load_1m,disk.avail'
curl -u elastic:elastic-local-123 '127.0.0.1:9200/_cat/shards?v&h=index,shard,prirep,state,docs,store,node,unassigned.reason'
curl -u elastic:elastic-local-123 '127.0.0.1:9200/_nodes/stats/jvm,fs,indices,thread_pool?pretty'
curl -u elastic:elastic-local-123 '127.0.0.1:9200/_tasks?detailed=true&actions=*search*,*write*'
```

顺序是业务影响与时间线 → 集群/索引范围 → 分片分配 → 节点资源与队列 → 慢请求画像/日志 → 最近变更。完整操作见 [诊断 Runbook](runbooks/diagnosis.md)。

## 11～15 分钟：主动证明

```bash
make -C Elasticsearch review
make -C Elasticsearch write-consistency
```

最后在 [ROADMAP.md](ROADMAP.md) 写下：最弱问题、实际证据、下次复习日期。若涉及丢失或恢复，先定义 RPO/RTO，再按 [恢复 Runbook](runbooks/recovery.md) 演练。

## 高风险提醒

- 不为“变绿”盲目把副本设为 0；先确认冗余和故障域。
- 不在写入活跃索引上随意 force merge；它会竞争 I/O 并需要临时磁盘。
- 不用删除索引、重启全部节点或清空数据目录代替根因分析。
- 不把单节点、本地默认密码、HTTP 明文和 `elastic` 超级用户作为生产配置。
- 不以快照任务成功代替恢复成功，恢复后必须校验文档、时间范围、别名、权限和应用读写。
