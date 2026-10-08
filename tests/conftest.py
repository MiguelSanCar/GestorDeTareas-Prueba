import pytest
from fastapi.testclient import TestClient

from app.database.connection import connect, get_db, init_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    """Cliente con una base de datos SQLite temporal y aislada por test."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)

    def override_get_db():
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    # Sin `with`: no se ejecuta el lifespan, que crearía la BD real (todos.db).
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_todo(client):
    def _make(title="Tarea de prueba", **extra):
        response = client.post("/api/todos", json={"title": title, **extra})
        assert response.status_code == 201
        return response.json()

    return _make
