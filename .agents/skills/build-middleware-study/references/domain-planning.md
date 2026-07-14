# Domain planning reference

Use these maps as starting points, not mandatory titles. Adapt them to the actual runtime, user goals, and current gaps.

## Redis

1. Data structures, encoding, and business modeling.
2. Expiration, eviction, memory accounting, and key lifecycle.
3. Pipelining, latency, hot keys, big keys, and observability.
4. Transactions, Lua, optimistic concurrency, and distributed locks.
5. RDB, AOF, rewrite, restart, and data-loss windows.
6. Replication, Sentinel, Cluster, slots, resharding, and failover.
7. Backup, capacity, security, client pools, and production operations.
8. Cache penetration, breakdown, avalanche, inconsistency, and incident capstone.

Recommended evidence includes encoding output, memory deltas, latency distributions, blocked clients, lock ownership tokens, RDB/AOF recovery, replication offsets, slot movement, and failover behavior.

## Kafka

1. Records, topics, partitions, offsets, and ordering boundaries.
2. Producer batching, compression, acknowledgements, retries, and idempotence.
3. Consumer groups, assignment, offset commits, lag, and rebalancing.
4. At-most-once, at-least-once, transactions, and end-to-end delivery semantics.
5. Log segments, retention, compaction, disk layout, and throughput.
6. Replication, ISR, leader election, KRaft, and failure behavior.
7. Capacity, quotas, security, observability, upgrades, and recovery.
8. Backlog, rebalance storms, duplicates, loss claims, and incident capstone.

Recommended evidence includes partition distribution, producer metrics, consumed offsets, lag, rebalance logs, transaction outcomes, segment files, ISR changes, and controlled broker failure.

## Elasticsearch

1. Documents, mappings, analyzers, and query versus filter context.
2. Index and shard design, routing, aliases, and lifecycle.
3. Inverted index, scoring, aggregations, pagination, and search profiling.
4. Refresh, flush, translog, optimistic concurrency, and consistency.
5. Segment merge, disk amplification, cache, heap, and garbage collection.
6. Replica shards, allocation, cluster state, failure, and recovery.
7. Snapshots, security, capacity, monitoring, upgrades, and rollover.
8. Mapping explosion, hot shards, rejected requests, data loss, and incident capstone.

Recommended evidence includes mappings, `_analyze`, query profiles, segment counts, refresh visibility, version conflicts, shard allocation, snapshot restore, and node failure.

## Relational databases

Use the existing MySQL implementation as a proven example of the architecture, not a universal topic list:

1. Schema and data types.
2. Indexes and access paths.
3. Query tuning.
4. Transactions and MVCC.
5. Locks and deadlocks.
6. Storage engine and logs.
7. Backup, recovery, and replication.
8. Production operations and incident capstone.

## Other middleware

Map the middleware to the common dimensions before naming modules. Explicitly identify:

- The data path and unit of work.
- Ordering and concurrency boundaries.
- Persistence and acknowledged-loss semantics.
- Scaling and partitioning unit.
- High-availability mechanism and split-brain risk.
- Backpressure and overload behavior.
- Native observability and recovery primitives.
- Most credible production incidents and interview questions.
