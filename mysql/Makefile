SHELL := /bin/sh

COMPOSE := docker compose -f docker-compose.yml
MYSQL_ROOT_PASSWORD ?= root123456
MYSQL := $(COMPOSE) exec -T -e MYSQL_PWD=$(MYSQL_ROOT_PASSWORD) mysql \
	mysql --protocol=tcp -uroot --default-character-set=utf8mb4 study

.PHONY: help up down status shell quickstart reset seed table-design index tuning mvcc locks innodb crash-recovery backup-restore replication replication-down production all review review-list

help:
	@printf '%s\n' \
		'MySQL 学习实验命令：' \
		'  make -C mysql up            启动并等待 MySQL 健康' \
		'  make -C mysql quickstart    运行原有 CRUD/事务快速示例' \
		'  make -C mysql table-design  运行 01 表设计实验' \
		'  make -C mysql index         重新造数并运行 02 索引实验' \
		'  make -C mysql tuning        重新造数并运行 03 SQL 调优实验' \
		'  make -C mysql mvcc          运行 04 事务与 MVCC 双连接实验' \
		'  make -C mysql locks         运行 05 锁等待与死锁并发实验' \
		'  make -C mysql innodb        运行 06 InnoDB 与日志实验' \
		'  make -C mysql crash-recovery 强制终止本地容器并验证崩溃恢复' \
		'  make -C mysql backup-restore 运行 07 备份、误删与恢复实验' \
		'  make -C mysql replication   启动独立 GTID 主从并验证复制' \
		'  make -C mysql replication-down 清理独立主从和数据卷' \
		'  make -C mysql production    运行 08 生产巡检实验' \
		'  make -C mysql all           运行除崩溃和独立主从外的全部实验' \
		'  make -C mysql review        随机抽取三道复习题' \
		'  make -C mysql review-list   查看题库主题' \
		'  make -C mysql shell         进入 MySQL 交互终端' \
		'  make -C mysql reset         删除所有 lab_ 前缀的实验表'

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

shell: up
	$(COMPOSE) exec -e MYSQL_PWD=$(MYSQL_ROOT_PASSWORD) mysql \
		mysql --protocol=tcp -uroot --default-character-set=utf8mb4 study

quickstart: up
	uv run --project .. python study/python/demo.py --cleanup

reset: up
	$(MYSQL) < study/scripts/reset.sql

seed: up
	$(MYSQL) < study/scripts/seed-orders.sql

table-design: up
	$(MYSQL) < study/labs/01-table-design/lab.sql

index: up
	$(MYSQL) < study/scripts/seed-orders.sql
	$(MYSQL) < study/labs/02-index/lab.sql

tuning: up
	$(MYSQL) < study/scripts/seed-orders.sql
	$(MYSQL) < study/labs/03-sql-tuning/lab.sql

mvcc: up
	uv run --project .. python study/labs/04-transaction-mvcc/lab.py

locks: up
	uv run --project .. python study/labs/05-lock-deadlock/lab.py

innodb: up
	$(MYSQL) < study/labs/06-innodb/lab.sql

crash-recovery:
	./study/labs/06-innodb/crash-recovery.sh

backup-restore:
	./study/labs/07-replication-backup/backup-restore.sh

replication:
	./study/labs/07-replication-backup/setup-replication.sh

replication-down:
	docker compose -p mysql-study-replication \
		-f study/labs/07-replication-backup/docker-compose.yml down -v

production: up
	$(MYSQL) < study/scripts/seed-orders.sql
	$(MYSQL) < study/labs/08-production-ops/lab.sql

all: table-design index tuning mvcc locks innodb backup-restore production

review:
	uv run --project .. python study/scripts/review.py --count 3

review-list:
	uv run --project .. python study/scripts/review.py --list-topics
