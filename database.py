
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "office.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        # タスク管理テーブル
        con.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            staff TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '未着手',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 既存データベースの列を確認
        columns = [
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        ]

        # 詳細列を追加
        if "details" not in columns:
            con.execute("""
                ALTER TABLE tasks
                ADD COLUMN details TEXT NOT NULL DEFAULT ''
            """)

        # 優先度列を追加
        if "priority" not in columns:
            con.execute("""
                ALTER TABLE tasks
                ADD COLUMN priority TEXT NOT NULL DEFAULT '中'
            """)

        # 記事管理テーブル
        con.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '下書き',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)


def get_tasks():
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def get_articles():
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM articles ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def add_task(title, staff, details="", priority="中"):
    with connect() as con:
        con.execute("""
            INSERT INTO tasks (
                title,
                staff,
                details,
                priority
            )
            VALUES (?, ?, ?, ?)
        """, (title, staff, details, priority))


def update_task_status(task_id, status):
    with connect() as con:
        con.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
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
