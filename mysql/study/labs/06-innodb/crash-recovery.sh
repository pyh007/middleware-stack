#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MYSQL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
COMPOSE_FILE="$MYSQL_DIR/docker-compose.yml"
MARKER="committed-before-crash-$(date +%s)-$$"

compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}

mysql_exec() {
    compose exec -T -e MYSQL_PWD=root123456 mysql \
        mysql --protocol=tcp -uroot --default-character-set=utf8mb4 study "$@"
}

ensure_running() {
    compose up -d --wait >/dev/null 2>&1 || true
}

trap ensure_running EXIT INT TERM

compose up -d --wait
mysql_exec -e "
CREATE TABLE IF NOT EXISTS lab_crash_recovery (
    marker VARCHAR(100) NOT NULL PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;
INSERT INTO lab_crash_recovery (marker) VALUES ('$MARKER');
"

echo "已提交标记：$MARKER"
echo "使用 SIGKILL 模拟 mysqld 非正常退出……"
compose kill --signal SIGKILL mysql
compose up -d --wait

RECOVERED=$(mysql_exec -N -e \
    "SELECT COUNT(*) FROM lab_crash_recovery WHERE marker='$MARKER';")

if [ "$RECOVERED" != "1" ]; then
    echo "崩溃恢复验证失败：没有找到已提交标记" >&2
    exit 1
fi

echo "崩溃恢复成功：重启后仍能读取已提交标记 $MARKER"
trap - EXIT INT TERM
