# Gestor de tareas

API REST (FastAPI + SQLite con `sqlite3`, sin ORM) y panel web para gestionar tareas en local.

## Estructura

```
app/
  main.py            # aplicación FastAPI, sirve el panel en "/"
  database/          # conexión SQLite y consultas SQL (repository)
  api/               # rutas y modelos pydantic
  static/            # panel visual (HTML + CSS + JS)
tests/               # pytest + TestClient
```

## Uso

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app.main:app --reload   # panel en http://127.0.0.1:8000 · docs en /docs
pytest
```

La base de datos se crea en `todos.db`; cambia la ruta con la variable `TODO_DB_PATH`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/todos?status=pending\|in_progress\|done` | Lista (filtro opcional) |
| GET | `/api/todos/{id}` | Detalle |
| POST | `/api/todos` | Crea (`title` obligatorio, `description` opcional) |
| PATCH | `/api/todos/{id}` | Actualiza `title`, `description` y/o `status` |
| DELETE | `/api/todos/{id}` | Elimina (204) |
