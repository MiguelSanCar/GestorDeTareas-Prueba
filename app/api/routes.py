import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.api.schemas import TodoCreate, TodoOut, TodoStatus, TodoUpdate
from app.database import repository
from app.database.connection import get_db

router = APIRouter(prefix="/api/todos", tags=["todos"])

TodoId = Path(ge=1, description="Identificador de la tarea")


def _not_found(todo_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe ninguna tarea con id {todo_id}",
    )


@router.get("", response_model=list[TodoOut])
def list_todos(
    status: TodoStatus | None = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Lista las tareas. Filtro opcional: ?status=pending|in_progress|done."""
    return repository.list_todos(conn, status.value if status else None)


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int = TodoId, conn: sqlite3.Connection = Depends(get_db)):
    todo = repository.get_todo(conn, todo_id)
    if todo is None:
        raise _not_found(todo_id)
    return todo


@router.post("", response_model=TodoOut, status_code=201)
def create_todo(data: TodoCreate, conn: sqlite3.Connection = Depends(get_db)):
    return repository.create_todo(conn, data.title, data.description, data.status.value)


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(
    data: TodoUpdate,
    todo_id: int = TodoId,
    conn: sqlite3.Connection = Depends(get_db),
):
    fields = data.model_dump(exclude_unset=True, mode="json")
    todo = repository.update_todo(conn, todo_id, fields)
    if todo is None:
        raise _not_found(todo_id)
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int = TodoId, conn: sqlite3.Connection = Depends(get_db)):
    if not repository.delete_todo(conn, todo_id):
        raise _not_found(todo_id)
    return Response(status_code=204)
