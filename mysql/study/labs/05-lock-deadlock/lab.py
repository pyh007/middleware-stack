"""真实复现 InnoDB 行锁等待和死锁，并验证正确恢复方式。"""

from __future__ import annotations

import os
import threading
import time
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


MYSQL_CONFIG: dict[str, Any] = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "study"),
    "user": os.getenv("MYSQL_ADMIN_USER", "root"),
    "password": os.getenv("MYSQL_ROOT_PASSWORD", "root123456"),
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
                CREATE TABLE IF NOT EXISTS lab_lock_accounts (
                    id BIGINT UNSIGNED NOT NULL,
                    balance DECIMAL(12, 2) NOT NULL,
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB
                """
            )
            cursor.execute("DELETE FROM lab_lock_accounts")
            cursor.executemany(
                "INSERT INTO lab_lock_accounts (id, balance) VALUES (%s, %s)",
                [(1, Decimal("100.00")), (2, Decimal("100.00"))],
            )
    finally:
        connection.close()


def demonstrate_lock_wait() -> None:
    holder = connect()
    waiter = connect()
    inspector = connect()
    waiter_started = threading.Event()
    waiter_result: list[str] = []

    def wait_for_same_row() -> None:
        try:
            with waiter.cursor() as cursor:
                cursor.execute("SET SESSION innodb_lock_wait_timeout = 5")
            waiter.begin()
            waiter_started.set()
            with waiter.cursor() as cursor:
                cursor.execute(
                    "UPDATE lab_lock_accounts SET balance = balance + 1 WHERE id = 1"
                )
            waiter.commit()
            waiter_result.append("committed")
        except Exception:
            waiter.rollback()
            raise

    try:
        holder.begin()
        with holder.cursor() as cursor:
            cursor.execute(
                "UPDATE lab_lock_accounts SET balance = balance + 10 WHERE id = 1"
            )

        thread = threading.Thread(target=wait_for_same_row, name="lock-waiter")
        thread.start()
        waiter_started.wait(timeout=2)

        wait_row: dict[str, Any] | None = None
        for _ in range(40):
            with inspector.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        REQUESTING_ENGINE_TRANSACTION_ID AS requesting_trx,
                        BLOCKING_ENGINE_TRANSACTION_ID AS blocking_trx
                    FROM performance_schema.data_lock_waits
                    LIMIT 1
                    """
                )
                wait_row = cursor.fetchone()
            if wait_row:
                break
            time.sleep(0.05)

        print("场景 1：两个事务更新同一行")
        print("  事务 A 已更新 id=1 但未提交，持有排他记录锁")
        print(f"  performance_schema.data_lock_waits：{wait_row}")
        assert wait_row is not None, "未观察到预期的行锁等待"

        holder.rollback()
        thread.join(timeout=5)
        assert not thread.is_alive(), "等待事务没有在锁释放后结束"
        assert waiter_result == ["committed"]
        print("  事务 A 回滚释放锁后，事务 B 成功提交")
    finally:
        holder.rollback()
        holder.close()
        waiter.close()
        inspector.close()


def reset_balances() -> None:
    connection = connect()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE lab_lock_accounts SET balance = 100.00")
        connection.commit()
    finally:
        connection.close()


def demonstrate_deadlock() -> None:
    reset_balances()
    barrier = threading.Barrier(2)
    results: dict[str, tuple[str, int | None]] = {}
    result_lock = threading.Lock()

    def worker(name: str, first_id: int, second_id: int) -> None:
        connection = connect()
        outcome: tuple[str, int | None]
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET SESSION innodb_lock_wait_timeout = 5")
            connection.begin()
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE lab_lock_accounts SET balance = balance + 10 WHERE id = %s",
                    (first_id,),
                )
                barrier.wait(timeout=3)
                cursor.execute(
                    "UPDATE lab_lock_accounts SET balance = balance + 10 WHERE id = %s",
                    (second_id,),
                )
            connection.commit()
            outcome = ("committed", None)
        except pymysql.MySQLError as exc:
            connection.rollback()
            outcome = ("deadlock" if exc.args[0] == 1213 else "error", exc.args[0])
        finally:
            connection.close()
        with result_lock:
            results[name] = outcome

    first = threading.Thread(target=worker, args=("事务 A", 1, 2))
    second = threading.Thread(target=worker, args=("事务 B", 2, 1))
    first.start()
    second.start()
    first.join(timeout=8)
    second.join(timeout=8)

    print("场景 2：反向加锁制造死锁")
    for name, outcome in sorted(results.items()):
        print(f"  {name}：{outcome}")

    outcomes = [outcome[0] for outcome in results.values()]
    assert sorted(outcomes) == ["committed", "deadlock"], results

    inspector = connect()
    try:
        with inspector.cursor() as cursor:
            cursor.execute("SHOW ENGINE INNODB STATUS")
            row = cursor.fetchone()
        assert row is not None
        status = row["Status"]
        marker = "LATEST DETECTED DEADLOCK"
        start = status.find(marker)
        excerpt = status[start : start + 1400] if start >= 0 else "未找到死锁片段"
        print("  InnoDB 最近死锁报告节选：")
        print(excerpt)
    finally:
        inspector.close()

    print("实验通过：一个完整事务成为死锁牺牲者，另一个事务成功提交。")


def main() -> None:
    setup()
    demonstrate_lock_wait()
    demonstrate_deadlock()


if __name__ == "__main__":
    main()
