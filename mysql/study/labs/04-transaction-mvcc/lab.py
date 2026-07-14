"""用两个真实连接复现 READ COMMITTED 与 REPEATABLE READ 的可见性差异。"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


MYSQL_CONFIG: dict[str, Any] = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "study"),
    "user": os.getenv("MYSQL_USER", "study_user"),
    "password": os.getenv("MYSQL_PASSWORD", "study123456"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": False,
}


def connect() -> Connection:
    return pymysql.connect(**MYSQL_CONFIG)


def setup() -> None:
    connection = connect()
    connection.autocommit(True)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS lab_mvcc_accounts (
                    id BIGINT UNSIGNED NOT NULL,
                    balance DECIMAL(12, 2) NOT NULL,
                    version INT UNSIGNED NOT NULL DEFAULT 0,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB
                """
            )
            cursor.execute(
                """
                INSERT INTO lab_mvcc_accounts (id, balance, version)
                VALUES (1, 100.00, 0)
                ON DUPLICATE KEY UPDATE balance = 100.00, version = 0
                """
            )
    finally:
        connection.close()


def read_balance(connection: Connection, *, locking: bool = False) -> Decimal:
    suffix = " FOR UPDATE" if locking else ""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT balance FROM lab_mvcc_accounts WHERE id = 1{suffix}")
        row = cursor.fetchone()
    assert row is not None
    return row["balance"]


def add_balance(connection: Connection, amount: Decimal) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE lab_mvcc_accounts
            SET balance = balance + %s, version = version + 1
            WHERE id = 1
            """,
            (amount,),
        )
    connection.commit()


def reset_balance() -> None:
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE lab_mvcc_accounts SET balance = 100.00, version = 0 WHERE id = 1"
            )
        connection.commit()
    finally:
        connection.close()


def demonstrate_read_committed() -> None:
    reset_balance()
    reader = connect()
    writer = connect()
    try:
        with reader.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        reader.begin()
        first = read_balance(reader)

        add_balance(writer, Decimal("50.00"))
        second = read_balance(reader)

        print("场景 1：READ COMMITTED 每次一致性读创建新的 Read View")
        print(f"  事务 A 第一次读取：{first}")
        print("  事务 B 将余额增加 50 并提交")
        print(f"  事务 A 第二次读取：{second}")
        assert first == Decimal("100.00") and second == Decimal("150.00")
    finally:
        reader.rollback()
        reader.close()
        writer.close()


def demonstrate_repeatable_read() -> None:
    reset_balance()
    reader = connect()
    writer = connect()
    try:
        with reader.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        reader.begin()
        first = read_balance(reader)

        add_balance(writer, Decimal("50.00"))
        snapshot_second = read_balance(reader)
        current_read = read_balance(reader, locking=True)

        print("场景 2：REPEATABLE READ 的快照读与当前读")
        print(f"  事务 A 第一次快照读：{first}")
        print("  事务 B 将余额增加 50 并提交")
        print(f"  事务 A 第二次快照读：{snapshot_second}")
        print(f"  事务 A 使用 FOR UPDATE 当前读：{current_read}")
        assert first == Decimal("100.00")
        assert snapshot_second == Decimal("100.00")
        assert current_read == Decimal("150.00")
    finally:
        reader.rollback()
        reader.close()
        writer.close()


def main() -> None:
    setup()
    demonstrate_read_committed()
    demonstrate_repeatable_read()
    print("实验通过：隔离级别、快照读和当前读均符合预期。")


if __name__ == "__main__":
    main()
