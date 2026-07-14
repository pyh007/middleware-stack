SHELL := /bin/bash

-include .env

ES_VERSION ?= 9.4.3-arm64
ES_PORT ?= 9200
ES_PASSWORD ?= elastic-local-123
ES_JAVA_OPTS ?= -Xms512m -Xmx512m
ES_REQUIRED_DISK_GB ?= 1
KIBANA_PORT ?= 5601
KIBANA_SYSTEM_PASSWORD ?= kibana-local-123
KIBANA_ENCRYPTION_KEY ?= local-kibana-encryption-key-32-chars

export ES_VERSION ES_PORT ES_PASSWORD ES_JAVA_OPTS ES_REQUIRED_DISK_GB
export KIBANA_PORT KIBANA_SYSTEM_PASSWORD KIBANA_ENCRYPTION_KEY

COMPOSE := docker compose -f docker-compose.yml
PYTHON := ES_URL=$${ES_URL:-http://127.0.0.1:$(ES_PORT)} ES_USER=$${ES_USER:-elastic} ES_PASSWORD=$${ES_PASSWORD:-$(ES_PASSWORD)} PYTHONPATH=study/scripts python3
CLUSTER_COMPOSE := docker compose -p es-study-cluster -f study/labs/06-cluster-availability/docker-compose.cluster.yml
ES_IMAGE := docker.elastic.co/elasticsearch/elasticsearch:$(ES_VERSION)
KIBANA_IMAGE := docker.elastic.co/kibana/kibana:$(ES_VERSION)

.PHONY: help preflight preflight-kibana up up-kibana stop down status reset review review-list documents-mappings index-shards search-profile write-consistency segments-resources cluster-availability snapshot-operations incident-capstone all force-merge snapshot-restore cluster-up cluster-failover cluster-down destroy-lab-data remove-images validate

help:
	@printf '%s\n' \
		'Elasticsearch 学习实验命令（实验资源统一使用 lab-es- 前缀）：' \
		'  make -C Elasticsearch preflight            检查 Docker、端口与宿主机/虚拟盘空间' \
		'  make -C Elasticsearch up                   启动本地安全单节点并等待健康' \
		'  make -C Elasticsearch up-kibana            [可选] 启动 Elasticsearch 与 Kibana' \
		'  make -C Elasticsearch stop                 仅停止容器，保留容器、网络和数据卷' \
		'  make -C Elasticsearch down                 删除容器和网络，保留数据卷' \
		'  make -C Elasticsearch status               只读查看容器与集群健康，不自动启动' \
		'  make -C Elasticsearch documents-mappings   运行 01 映射、分析器与查询上下文' \
		'  make -C Elasticsearch index-shards         运行 02 分片、路由与别名切换' \
		'  make -C Elasticsearch search-profile       运行 03 评分、聚合与搜索画像' \
		'  make -C Elasticsearch write-consistency    运行 04 refresh、translog 与并发控制' \
		'  make -C Elasticsearch segments-resources   运行 05 段、缓存、堆与线程池观察' \
		'  make -C Elasticsearch cluster-availability 运行 06 单节点副本与分配边界' \
		'  make -C Elasticsearch snapshot-operations  运行 07 容量与最小权限实验' \
		'  make -C Elasticsearch incident-capstone    运行 08 映射爆炸与热点综合事故' \
		'  make -C Elasticsearch all                  运行全部安全单节点实验' \
		'  make -C Elasticsearch reset                仅清理 lab-es- 实验资源' \
		'  make -C Elasticsearch review               随机抽取三道主动回忆题' \
		'  make -C Elasticsearch force-merge          [显式/资源操作] 对隔离索引执行合并' \
		'  make -C Elasticsearch snapshot-restore     [显式/恢复] 删除并恢复隔离索引' \
		'  make -C Elasticsearch cluster-up           [显式/多节点] 启动独立三节点集群' \
		'  make -C Elasticsearch cluster-failover     [显式/故障] 停主分片节点并验证提升' \
		'  make -C Elasticsearch cluster-down         清理独立集群及数据卷' \
		'  make -C Elasticsearch destroy-lab-data CONFIRM=destroy  [显式/删除] 删除课程卷' \
		'  make -C Elasticsearch remove-images CONFIRM=remove-images [显式/删除] 删除本地镜像' \
		'  make -C Elasticsearch validate             运行课程质量校验'

preflight:
	./scripts/preflight.sh

preflight-kibana:
	CHECK_KIBANA_PORT=1 ./scripts/preflight.sh

up: preflight
	$(COMPOSE) up -d --wait

up-kibana: preflight-kibana
	$(COMPOSE) --profile kibana up -d --wait

stop:
	$(COMPOSE) --profile kibana stop

down:
	$(COMPOSE) --profile kibana down

status:
	$(COMPOSE) --profile kibana ps -a
	@if [ "$$(docker inspect -f '{{.State.Running}}' es-study-single 2>/dev/null || true)" = "true" ]; then \
		curl -fsS -u "$${ES_USER:-elastic}:$${ES_PASSWORD:-$(ES_PASSWORD)}" "http://127.0.0.1:$(ES_PORT)/_cluster/health?pretty"; \
	else \
		printf '%s\n' 'es-study-single 未运行；status 不会自动启动服务。'; \
	fi

reset: up
	$(PYTHON) study/scripts/reset.py

documents-mappings: up
	$(PYTHON) study/labs/01-documents-mappings/lab.py

index-shards: up
	$(PYTHON) study/labs/02-index-shards/lab.py

search-profile: up
	$(PYTHON) study/labs/03-search-profile/lab.py

write-consistency: up
	$(PYTHON) study/labs/04-write-consistency/lab.py

segments-resources: up
	$(PYTHON) study/labs/05-segments-resources/lab.py

cluster-availability: up
	$(PYTHON) study/labs/06-cluster-availability/lab.py

snapshot-operations: up
	$(PYTHON) study/labs/07-snapshot-operations/lab.py

incident-capstone: up
	$(PYTHON) study/labs/08-incident-capstone/lab.py

all: documents-mappings index-shards search-profile write-consistency segments-resources cluster-availability snapshot-operations incident-capstone

review:
	python3 study/scripts/review.py --count 3

review-list:
	python3 study/scripts/review.py --list-topics

force-merge: up
	$(PYTHON) study/labs/05-segments-resources/force_merge.py

snapshot-restore: up
	$(PYTHON) study/labs/07-snapshot-operations/snapshot_restore.py

cluster-up:
	$(CLUSTER_COMPOSE) up -d --wait

cluster-failover: cluster-up
	ES_URL=http://127.0.0.1:19200 PYTHONPATH=study/scripts python3 study/labs/06-cluster-availability/failover.py

cluster-down:
	$(CLUSTER_COMPOSE) down -v --remove-orphans

destroy-lab-data:
	@if [ "$(CONFIRM)" != "destroy" ]; then \
		printf '%s\n' \
			'拒绝执行：该命令会永久删除 es-study-data、es-study-backup 和可选 Kibana 数据卷。' \
			'确认影响后使用：make -C Elasticsearch destroy-lab-data CONFIRM=destroy'; \
		exit 2; \
	fi
	@printf '%s\n' \
		'即将停止根目录课程环境，并永久删除 Elasticsearch、快照和 Kibana 课程卷。' \
		'不影响 Elasticsearch/elastic-start-local/ 的文件或其 dev-elasticsearch/dev-kibana 卷。'
	$(COMPOSE) --profile kibana down -v --remove-orphans

remove-images:
	@if [ "$(CONFIRM)" != "remove-images" ]; then \
		printf '%s\n' \
			'拒绝执行：该命令会删除根课程使用的 Elasticsearch/Kibana 本地镜像。' \
			'这些镜像也可能被 elastic-start-local 引用；删除后旧环境需要重新拉取。' \
			'先运行 make -C Elasticsearch down，再使用 CONFIRM=remove-images。'; \
		exit 2; \
	fi
	@if [ -n "$$($(COMPOSE) --profile kibana ps -a -q)" ]; then \
		printf '%s\n' '仍存在根课程容器，请先执行 make -C Elasticsearch down。'; \
		exit 2; \
	fi
	@for image in "$(ES_IMAGE)" "$(KIBANA_IMAGE)"; do \
		if docker image inspect "$$image" >/dev/null 2>&1; then docker image rm "$$image"; \
		else printf '%s\n' "镜像不存在，跳过：$$image"; fi; \
	done

validate:
	python3 ../.agents/skills/build-middleware-study/scripts/validate_study.py study
