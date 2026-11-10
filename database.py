
import sqlite3
import os

DB_NAME = "office.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                staff TEXT,
                details TEXT,
                priority TEXT DEFAULT '中',
                status TEXT DEFAULT '未着手',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 既存のtasksテーブルに不足している列を追加
        columns = [
            row[1] for row in
            con.execute("PRAGMA table_info(tasks)").fetchall()
        ]

        if "details" not in columns:
            con.execute(
                "ALTER TABLE tasks ADD COLUMN details TEXT"
            )

        if "priority" not in columns:
            con.execute(
                "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT '中'"
            )

        con.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT DEFAULT '下書き',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_tasks():
    with connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def get_articles():
    with connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM articles ORDER BY id DESC"
        ).fetchall()
        return [dict(row) for row in rows]


def add_task(title, staff, details="", priority="中"):
    with connect() as con:
        con.execute(
            """
            INSERT INTO tasks (title, staff, details, priority)
            VALUES (?, ?, ?, ?)
            """,
            (title, staff, details, priority)
        )


def update_task_status(task_id, status):
    with connect() as con:
        con.execute(
            """
            UPDATE tasks
            SET status = ?
            WHERE id = ?
            """,
            (status, task_id)
        )


def delete_task(task_id):
    with connect() as con:
        con.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )


def add_article(title, body):
    with connect() as con:
        con.execute(
            """
            INSERT INTO articles (title, body, status)
            VALUES (?, ?, ?)
            """,
            (title, body, "下書き")
        )


def update_article(article_id, title, body):
    with connect() as con:
        con.execute(
            """
            UPDATE articles
            SET title = ?, body = ?
            WHERE id = ?
            """,
            (title, body, article_id)
        )
