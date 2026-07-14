SHELL := /bin/bash

COMPOSE := docker compose -f docker-compose.yml
PYTHON := PYTHONPATH=study/scripts uv run --project .. python

.PHONY: help up down status shell quickstart reset records-partitions producer-reliability consumer-groups delivery-semantics log-storage replication-kraft production-ops incident-capstone all review review-list cluster-up cluster-failover cluster-down validate

help:
	@printf '%s\n' \
		'Kafka 学习实验命令（实验资源统一使用 lab_kafka_ 前缀）：' \
		'  make -C kafka up                   启动单节点 KRaft 与 Kafka UI' \
		'  make -C kafka down                 停止服务并保留数据卷' \
		'  make -C kafka quickstart           运行原有 Python 端到端示例' \
		'  make -C kafka records-partitions   运行 01 记录、分区与顺序实验' \
		'  make -C kafka producer-reliability 运行 02 批处理、压缩与可靠性实验' \
		'  make -C kafka consumer-groups      运行 03 位点、Lag 与再均衡实验' \
		'  make -C kafka delivery-semantics   运行 04 事务与交付语义实验' \
		'  make -C kafka log-storage          运行 05 日志段与压缩语义实验' \
		'  make -C kafka replication-kraft    运行 06 单节点 KRaft 观察实验' \
		'  make -C kafka production-ops       运行 07 巡检与受控恢复实验' \
		'  make -C kafka incident-capstone    运行 08 积压、重复与丢数声称案例' \
		'  make -C kafka all                  运行全部安全、单节点实验' \
		'  make -C kafka review               随机抽取三道主动回忆题' \
		'  make -C kafka reset                仅删除 lab_kafka_ 前缀 Topic/Group' \
		'  make -C kafka cluster-up           [显式/多节点] 启动独立三节点集群' \
		'  make -C kafka cluster-failover     [显式/故障] 停 Leader、验证选举并清理' \
		'  make -C kafka cluster-down         清理独立三节点集群及其数据卷' \
		'  make -C kafka validate             运行课程质量校验'

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

shell: up
	$(COMPOSE) exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

quickstart: up
	uv run --project .. python python/demo.py --topic lab_kafka_quickstart --count 5

reset: up
	./study/scripts/reset.sh

records-partitions: up
	$(PYTHON) study/labs/01-records-partitions/lab.py

producer-reliability: up
	$(PYTHON) study/labs/02-producer-reliability/lab.py

consumer-groups: up
	$(PYTHON) study/labs/03-consumer-groups/lab.py
	$(PYTHON) study/labs/03-consumer-groups/rebalance.py

delivery-semantics: up
	$(PYTHON) study/labs/04-delivery-semantics/lab.py

log-storage: up
	$(PYTHON) study/labs/05-log-storage/lab.py

replication-kraft: up
	./study/labs/06-replication-kraft/lab.sh

production-ops: up
	$(PYTHON) study/labs/07-production-ops/lab.py
	$(PYTHON) study/labs/07-production-ops/recovery.py

incident-capstone: up
	$(PYTHON) study/labs/08-incident-capstone/lab.py

all: records-partitions producer-reliability consumer-groups delivery-semantics log-storage replication-kraft production-ops incident-capstone

review:
	uv run --project .. python study/scripts/review.py --count 3

review-list:
	uv run --project .. python study/scripts/review.py --list-topics

cluster-up:
	docker compose -p kafka-study-cluster -f study/labs/06-replication-kraft/docker-compose.yml up -d --wait

cluster-failover:
	./study/labs/06-replication-kraft/failover.sh

cluster-down:
	docker compose -p kafka-study-cluster -f study/labs/06-replication-kraft/docker-compose.yml down -v --remove-orphans

validate:
	python3 ../.agents/skills/build-middleware-study/scripts/validate_study.py study
