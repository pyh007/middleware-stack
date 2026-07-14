#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="mysql-study-replication"

compose() {
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" "$@"
}

primary_mysql() {
    compose exec -T -e MYSQL_PWD=root123456 mysql-primary \
        mysql --protocol=tcp -uroot --default-character-set=utf8mb4 "$@"
}

replica_mysql() {
    compose exec -T -e MYSQL_PWD=root123456 mysql-replica \
        mysql --protocol=tcp -uroot --default-character-set=utf8mb4 "$@"
}

compose up -d --wait

primary_mysql -e "
CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED WITH caching_sha2_password BY 'repl123456';
ALTER USER 'repl'@'%' IDENTIFIED WITH caching_sha2_password BY 'repl123456';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
"

replica_mysql -e "
SET GLOBAL super_read_only=OFF;
SET GLOBAL read_only=OFF;
STOP REPLICA;
RESET REPLICA ALL;
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST='mysql-primary',
    SOURCE_PORT=3306,
    SOURCE_USER='repl',
    SOURCE_PASSWORD='repl123456',
    SOURCE_AUTO_POSITION=1,
    GET_SOURCE_PUBLIC_KEY=1;
START REPLICA;
SET GLOBAL read_only=ON;
SET GLOBAL super_read_only=ON;
"

primary_mysql -e "
DROP TABLE IF EXISTS study.lab_replication_events;
CREATE TABLE study.lab_replication_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    event_text VARCHAR(100) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO study.lab_replication_events (event_text)
VALUES ('written-on-primary'), ('replicated-by-gtid');
"

REPLICATED=""
for _ in $(seq 1 30); do
    if REPLICATED=$(replica_mysql -N -e \
        "SELECT COUNT(*) FROM study.lab_replication_events;" 2>/dev/null); then
        if [ "$REPLICATED" = "2" ]; then
            break
        fi
    fi
    sleep 1
done

if [ "$REPLICATED" != "2" ]; then
    echo "复制验证失败：副本记录数为 ${REPLICATED:-不可读}" >&2
    replica_mysql -e "SHOW REPLICA STATUS\G" || true
    exit 1
fi

echo "主库写入、副本读取验证成功："
replica_mysql -e \
    "SELECT id, event_text, created_at FROM study.lab_replication_events ORDER BY id;"

echo "复制线程状态："
replica_mysql -e "
SELECT CHANNEL_NAME, SERVICE_STATE, LAST_ERROR_NUMBER, LAST_ERROR_MESSAGE
FROM performance_schema.replication_connection_status;
SELECT CHANNEL_NAME, SERVICE_STATE
FROM performance_schema.replication_applier_status;
"

echo "主库端口 3307，副本端口 3308。学习结束后执行 make -C mysql replication-down。"
