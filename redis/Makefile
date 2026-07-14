SHELL := /bin/bash

COMPOSE := docker compose -f docker-compose.yml
PYTHON := PYTHONPATH=study/scripts uv run --project .. python

.PHONY: help up down status shell quickstart reset review review-list validate data-structures expiration-eviction performance concurrency persistence replication-cluster production-ops incident-capstone all eviction-pressure crash-recovery sentinel-failover cluster-reshard special-down

help:
	@printf '%s\n' \
		'Redis 学习实验命令（实验键统一使用 lab:redis: 前缀）：' \
		'  make -C redis up                  启动并等待本地 Redis 健康' \
		'  make -C redis down                停止服务并保留持久化卷' \
		'  make -C redis quickstart          运行原有 Python 综合示例并清理' \
		'  make -C redis data-structures     运行 01 数据结构与编码实验' \
		'  make -C redis expiration-eviction 运行 02 TTL 与内存生命周期实验' \
		'  make -C redis performance         运行 03 Pipeline、热点与大 Key 实验' \
		'  make -C redis concurrency         运行 04 WATCH、Lua 与锁实验' \
		'  make -C redis persistence         运行 05 RDB/AOF 状态与重写实验' \
		'  make -C redis replication-cluster 运行 06 拓扑与槽位边界实验' \
		'  make -C redis production-ops      运行 07 容量、安全与恢复实验' \
		'  make -C redis incident-capstone   运行 08 缓存事故综合实验' \
		'  make -C redis all                 运行全部安全单节点实验' \
		'  make -C redis reset               仅删除 lab:redis: 前缀键' \
		'  make -C redis review              随机抽取三道主动回忆题' \
		'  make -C redis eviction-pressure   [显式/压力] 独立实例触发淘汰' \
		'  make -C redis crash-recovery      [显式/故障] 强杀主容器并验证 AOF 恢复' \
		'  make -C redis sentinel-failover   [显式/多节点] 独立 Sentinel 故障转移' \
		'  make -C redis cluster-reshard     [显式/多节点] 独立 Cluster 槽迁移' \
		'  make -C redis special-down        清理所有独立实验资源' \
		'  make -C redis validate            运行课程质量校验'

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

shell: up
	$(COMPOSE) exec -e REDISCLI_AUTH=redis123456 redis redis-cli

quickstart: up
	uv run --project .. python python/demo.py --cleanup

reset: up
	$(PYTHON) study/scripts/reset.py

data-structures: up
	$(PYTHON) study/labs/01-data-structures/lab.py

expiration-eviction: up
	$(PYTHON) study/labs/02-expiration-eviction/lab.py

performance: up
	$(PYTHON) study/labs/03-performance/lab.py

concurrency: up
	$(PYTHON) study/labs/04-concurrency/lab.py

persistence: up
	$(PYTHON) study/labs/05-persistence/lab.py

replication-cluster: up
	$(PYTHON) study/labs/06-replication-cluster/lab.py

production-ops: up
	$(PYTHON) study/labs/07-production-ops/lab.py

incident-capstone: up
	$(PYTHON) study/labs/08-incident-capstone/lab.py

all: data-structures expiration-eviction performance concurrency persistence replication-cluster production-ops incident-capstone

review:
	uv run --project .. python study/scripts/review.py --count 3

review-list:
	uv run --project .. python study/scripts/review.py --list-topics

eviction-pressure:
	./study/labs/02-expiration-eviction/eviction-pressure.sh

crash-recovery: up
	./study/labs/05-persistence/crash-recovery.sh

sentinel-failover:
	./study/labs/06-replication-cluster/sentinel-failover.sh

cluster-reshard:
	./study/labs/06-replication-cluster/cluster-reshard.sh

special-down:
	docker compose -p redis-study-eviction -f study/labs/02-expiration-eviction/docker-compose.eviction.yml down -v --remove-orphans
	docker compose -p redis-study-sentinel -f study/labs/06-replication-cluster/docker-compose.sentinel.yml down -v --remove-orphans
	docker compose -p redis-study-cluster -f study/labs/06-replication-cluster/docker-compose.cluster.yml down -v --remove-orphans

validate:
	python3 ../.agents/skills/build-middleware-study/scripts/validate_study.py study
