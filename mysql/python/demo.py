"""MySQL 端到端学习示例：CRUD、事务、回滚和索引执行计划。"""

from __future__ import annotations

import argparse
import os
import uuid
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


# 脚本运行在宿主机，因此连接 docker-compose.yml 暴露出来的 3306 端口。
# 连接其他 MySQL 时，可以通过 MYSQL_HOST、MYSQL_PORT 等环境变量覆盖默认值。
MYSQL_CONFIG: dict[str, Any] = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "study"),
    "user": os.getenv("MYSQL_USER", "study_user"),
    "password": os.getenv("MYSQL_PASSWORD", "study123456"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    # 关闭自动提交，便于明确观察 commit 和 rollback 的作用。
    "autocommit": False,
    "connect_timeout": 5,
}


def create_table(connection: Connection) -> None:
    """创建学习表；IF NOT EXISTS 让脚本可以安全地重复运行。"""

    sql = """
        CREATE TABLE IF NOT EXISTS learning_accounts (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
            run_id CHAR(36) NOT NULL COMMENT '每次脚本运行的唯一标识',
            owner VARCHAR(50) NOT NULL COMMENT '账户名称',
            balance DECIMAL(12, 2) NOT NULL COMMENT '账户余额',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            INDEX idx_learning_accounts_run_id (run_id)
        ) ENGINE=InnoDB
          DEFAULT CHARACTER SET utf8mb4
          COLLATE utf8mb4_0900_ai_ci
          COMMENT='MySQL Python 学习账户表'
    """
    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.commit()
    print("步骤 1/6：学习表已准备好。")


def insert_accounts(connection: Connection, run_id: str) -> None:
    """使用参数化 SQL 批量插入，避免手工拼接造成 SQL 注入。"""

    sql = """
        INSERT INTO learning_accounts (run_id, owner, balance)
        VALUES (%s, %s, %s)
    """
    accounts = [
        (run_id, "张三", Decimal("1000.00")),
        (run_id, "李四", Decimal("500.00")),
    ]
    with connection.cursor() as cursor:
        affected = cursor.executemany(sql, accounts)
    connection.commit()
    print(f"步骤 2/6：参数化批量插入完成，写入 {affected} 个账户。")


def query_accounts(connection: Connection, run_id: str) -> list[dict[str, Any]]:
    """查询本轮创建的账户。"""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, run_id, owner, balance, created_at
            FROM learning_accounts
            WHERE run_id = %s
            ORDER BY id
            """,
            (run_id,),
        )
        return list(cursor.fetchall())


def print_accounts(accounts: list[dict[str, Any]]) -> None:
    for account in accounts:
        print(
            f"  id={account['id']} owner={account['owner']} "
            f"balance={account['balance']} created_at={account['created_at']}"
        )


def transfer(
    connection: Connection,
    run_id: str,
    sender: str,
    receiver: str,
    amount: Decimal,
) -> None:
    """在一个事务内完成转账，任何一步失败都会回滚全部修改。"""

    connection.begin()
    try:
        with connection.cursor() as cursor:
            # balance >= amount 把余额检查和扣款放在同一条 SQL 中，避免并发超扣。
            cursor.execute(
                """
                UPDATE learning_accounts
                SET balance = balance - %s
                WHERE run_id = %s AND owner = %s AND balance >= %s
                """,
                (amount, run_id, sender, amount),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"{sender} 余额不足或账户不存在")

            cursor.execute(
                """
                UPDATE learning_accounts
                SET balance = balance + %s
                WHERE run_id = %s AND owner = %s
                """,
                (amount, run_id, receiver),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"{receiver} 账户不存在")
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()


def explain_query(connection: Connection, run_id: str) -> None:
    """使用 EXPLAIN 观察 WHERE run_id 查询是否命中索引。"""

    with connection.cursor() as cursor:
        cursor.execute(
            "EXPLAIN SELECT * FROM learning_accounts WHERE run_id = %s",
            (run_id,),
        )
        plan = cursor.fetchone()

    assert plan is not None
    print(
        "步骤 5/6：EXPLAIN 执行计划："
        f"type={plan['type']} key={plan['key']} rows={plan['rows']} "
        f"Extra={plan['Extra']}"
    )


def cleanup(connection: Connection, run_id: str) -> None:
    """只删除本轮数据，不影响之前运行留下的学习记录。"""

    with connection.cursor() as cursor:
        deleted = cursor.execute(
            "DELETE FROM learning_accounts WHERE run_id = %s",
            (run_id,),
        )
    connection.commit()
    print(f"步骤 6/6：已清理本轮 {deleted} 条数据。")


def run_demo(should_cleanup: bool) -> None:
    run_id = str(uuid.uuid4())
    print(
        "连接 MySQL："
        f"{MYSQL_CONFIG['user']}@{MYSQL_CONFIG['host']}:"
        f"{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )

    connection = pymysql.connect(**MYSQL_CONFIG)
    try:
        create_table(connection)
        insert_accounts(connection, run_id)

        print("步骤 3/6：查询刚插入的数据：")
        print_accounts(query_accounts(connection, run_id))

        transfer(connection, run_id, "张三", "李四", Decimal("100.00"))
        print("步骤 4/6：事务提交成功，张三向李四转账 100：")
        print_accounts(query_accounts(connection, run_id))

        try:
            transfer(connection, run_id, "张三", "李四", Decimal("9999.00"))
        except ValueError as exc:
            print(f"  预期中的失败：{exc}；事务已回滚，余额保持不变。")
        else:
            raise AssertionError("余额不足的转账不应成功")

        explain_query(connection, run_id)

        if should_cleanup:
            cleanup(connection, run_id)
        else:
            print(
                "步骤 6/6：本轮数据已保留。重建容器后再次查询，可验证数据卷持久化。"
            )
        print(f"演示完成，本轮 run_id={run_id}")
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="演示完成后删除本轮数据；默认保留以便观察持久化",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        run_demo(arguments.cleanup)
    except pymysql.MySQLError as exc:
        raise SystemExit(
            "MySQL 操作失败。请先执行 "
            "docker compose -f mysql/docker-compose.yml up -d，"
            f"然后重试。原始错误：{exc}"
        ) from exc
