#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MYSQL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
COMPOSE_FILE="$MYSQL_DIR/docker-compose.yml"
TMP_DIR=$(mktemp -d)
BACKUP_FILE="$TMP_DIR/lab_recovery_items.sql"

compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}

mysql_exec() {
    compose exec -T -e MYSQL_PWD=root123456 mysql \
        mysql --protocol=tcp -uroot --default-character-set=utf8mb4 study "$@"
}

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT INT TERM

compose up -d --wait
mysql_exec -e "
DROP TABLE IF EXISTS lab_recovery_items;
CREATE TABLE lab_recovery_items (
    id BIGINT UNSIGNED NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB;
INSERT INTO lab_recovery_items (id, item_name)
VALUES (1, 'backup-a'), (2, 'backup-b'), (3, 'backup-c');
"

compose exec -T -e MYSQL_PWD=root123456 mysql \
    mysqldump --protocol=tcp -uroot --single-transaction --skip-add-locks \
    study lab_recovery_items > "$BACKUP_FILE"

echo "逻辑备份已生成：$(wc -c < "$BACKUP_FILE" | tr -d ' ') 字节"

mysql_exec -e "DELETE FROM lab_recovery_items;"
DELETED_COUNT=$(mysql_exec -N -e "SELECT COUNT(*) FROM lab_recovery_items;")
if [ "$DELETED_COUNT" != "0" ]; then
    echo "故障模拟失败：表中仍有数据" >&2
    exit 1
fi
echo "已模拟误删：表中记录数为 0"

mysql_exec < "$BACKUP_FILE"
RESTORED=$(mysql_exec -N -e \
    "SELECT CONCAT(COUNT(*), ':', GROUP_CONCAT(item_name ORDER BY id)) FROM lab_recovery_items;")

if [ "$RESTORED" != "3:backup-a,backup-b,backup-c" ]; then
    echo "恢复验证失败：$RESTORED" >&2
    exit 1
fi

echo "恢复成功并完成业务校验：$RESTORED"
