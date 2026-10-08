import os
import sqlite3
from collections.abc import Iterator

DEFAULT_DB_PATH = "todos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'in_progress', 'done')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
"""


def get_db_path() -> str:
    return os.environ.get("TODO_DB_PATH", DEFAULT_DB_PATH)


def connect(db_path: str) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI puede ejecutar la dependencia y el
    # endpoint en hilos distintos del threadpool; la conexión es por petición.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """Dependencia de FastAPI: una conexión por petición."""
    conn = connect(get_db_path())
    try:
        yield conn
    finally:
        conn.close()
