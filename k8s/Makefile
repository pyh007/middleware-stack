SHELL := /bin/sh

.PHONY: help up down reset review review-list architecture workloads networking config-security storage scheduling observability capstone-audit all pod-failure probe-failure service-failure pending-failure kafka-capstone kafka-status validate

help:
	@printf '%s\n' \
		'Kubernetes 学习实验命令：' \
		'  make -C k8s up               校验 kubectl、上下文和集群连通性' \
		'  make -C k8s architecture     运行 01 架构与调谐实验' \
		'  make -C k8s workloads        运行 02 工作负载与生命周期实验' \
		'  make -C k8s networking       运行 03 网络与服务发现实验' \
		'  make -C k8s config-security  运行 04 配置与安全实验' \
		'  make -C k8s storage          运行 05 存储与有状态实验' \
		'  make -C k8s scheduling       运行 06 调度与资源治理实验' \
		'  make -C k8s observability    运行 07 可观测性实验' \
		'  make -C k8s capstone-audit   运行 08 Kafka 清单与现场审计' \
		'  make -C k8s all              运行八个非破坏性、隔离实验' \
		'  make -C k8s review           随机抽取三道复习题' \
		'  make -C k8s reset            仅删除带课程标签的 k8s-study-* Namespace' \
		'  make -C k8s down             清理课程 Namespace，不停止 Docker Desktop' \
		'显式故障/重资源命令（不会被 all 调用）：' \
		'  make -C k8s pod-failure      删除课程 Pod，验证控制器调谐' \
		'  make -C k8s probe-failure    注入错误探针并恢复' \
		'  make -C k8s service-failure  注入错误 Service selector 并恢复' \
		'  make -C k8s pending-failure  创建不可调度 Pod，采集证据后清理' \
		'  make -C k8s kafka-capstone   应用 Kafka 清单，必要时重建旧 Pod（保留 PVC）' \
		'  make -C k8s kafka-status      只读诊断现有 Kafka 状态' \
		'  make -C k8s validate          运行课程质量校验'

up:
	./study/scripts/preflight.sh

down:
	./study/scripts/reset.sh

reset:
	./study/scripts/reset.sh

architecture: up
	./study/labs/01-architecture-reconciliation/lab.sh

workloads: up
	./study/labs/02-workloads-lifecycle/lab.sh

networking: up
	./study/labs/03-networking-discovery/lab.sh

config-security: up
	./study/labs/04-config-security/lab.sh

storage: up
	./study/labs/05-storage-stateful/lab.sh

scheduling: up
	./study/labs/06-scheduling-resources/lab.sh

observability: up
	./study/labs/07-observability-troubleshooting/lab.sh

capstone-audit: up
	./study/labs/08-production-capstone/lab.sh

all: architecture workloads networking config-security storage scheduling observability capstone-audit

pod-failure: architecture
	./study/labs/01-architecture-reconciliation/pod-failure.sh

probe-failure: workloads
	./study/labs/02-workloads-lifecycle/probe-failure.sh

service-failure: networking
	./study/labs/03-networking-discovery/service-failure.sh

pending-failure: scheduling
	./study/labs/06-scheduling-resources/pending-failure.sh

kafka-capstone: up
	./study/cases/kafka-incident/capstone.sh

kafka-status: up
	./study/cases/kafka-incident/diagnose.sh

review:
	python3 study/scripts/review.py --count 3

review-list:
	python3 study/scripts/review.py --list-topics

validate:
	python3 ../.agents/skills/build-middleware-study/scripts/validate_study.py study
