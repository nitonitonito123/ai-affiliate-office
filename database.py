import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "office.db"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            staff TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '未着手',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
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
        rows = con.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def get_articles():
    with connect() as con:
        rows = con.execute("SELECT * FROM articles ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]

def add_task(title, staff):
    with connect() as con:
        con.execute("INSERT INTO tasks(title, staff) VALUES (?, ?)", (title, staff))
