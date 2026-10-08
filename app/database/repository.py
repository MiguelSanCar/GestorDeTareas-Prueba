import sqlite3
from typing import Any

_UPDATABLE_COLUMNS = {"title", "description", "status"}


def _to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else dict(row)


def list_todos(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        rows = conn.execute("SELECT * FROM todos ORDER BY id").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status = ? ORDER BY id", (status,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_todo(conn: sqlite3.Connection, todo_id: int) -> dict[str, Any] | None:
    return _to_dict(conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone())


def create_todo(
    conn: sqlite3.Connection,
    title: str,
    description: str | None,
    status: str = "pending",
) -> dict[str, Any]:
    cursor = conn.execute(
        "INSERT INTO todos (title, description, status) VALUES (?, ?, ?)",
        (title, description, status),
    )
    conn.commit()
    return get_todo(conn, cursor.lastrowid)


def update_todo(
    conn: sqlite3.Connection, todo_id: int, fields: dict[str, Any]
) -> dict[str, Any] | None:
    """Actualiza solo las columnas indicadas. Devuelve None si no existe."""
    unknown = set(fields) - _UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"Columnas no actualizables: {sorted(unknown)}")

    # Los nombres de columna salen de la lista blanca de arriba, nunca del usuario.
    assignments = ", ".join(f"{col} = ?" for col in fields)
    cursor = conn.execute(
        f"UPDATE todos SET {assignments}, "
        "updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
        (*fields.values(), todo_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        return None
    return get_todo(conn, todo_id)


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    return cursor.rowcount > 0
