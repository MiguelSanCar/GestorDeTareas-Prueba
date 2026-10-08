import pytest


# --- POST /api/todos -------------------------------------------------------

def test_create_todo(client):
    response = client.post(
        "/api/todos", json={"title": "  Comprar leche  ", "description": "Entera"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] >= 1
    assert body["title"] == "Comprar leche"  # se recortan espacios
    assert body["description"] == "Entera"
    assert body["status"] == "pending"
    assert body["created_at"] and body["updated_at"]


def test_create_todo_without_description(client):
    response = client.post("/api/todos", json={"title": "Solo título"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_todo_with_initial_status(client):
    response = client.post("/api/todos", json={"title": "Ya empezada", "status": "in_progress"})
    assert response.status_code == 201
    assert response.json()["status"] == "in_progress"


@pytest.mark.parametrize(
    "payload",
    [
        {},  # falta título
        {"description": "sin título"},
        {"title": ""},
        {"title": "   "},
        {"title": None},
        {"title": 123},
        {"title": "x" * 201},
        {"title": "ok", "description": "d" * 2001},
        {"title": "ok", "status": "inventado"},
        {"title": "ok", "status": None},
        {"title": "ok", "campo_basura": 1},
    ],
)
def test_create_todo_rejects_invalid_payload(client, payload):
    response = client.post("/api/todos", json=payload)
    assert response.status_code == 422
    assert client.get("/api/todos").json() == []


def test_create_todo_rejects_malformed_json(client):
    response = client.post(
        "/api/todos", content="{no es json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "method, url, payload, expected",
    [
        ("post", "/api/todos", {}, "El campo «título» es obligatorio"),
        ("post", "/api/todos", {"title": "   "}, "El campo «título» no puede estar vacío"),
        ("post", "/api/todos", {"title": "x" * 201}, "no puede superar los 200 caracteres"),
        ("post", "/api/todos", {"title": "a", "status": "x"}, "valores permitidos: pending"),
        ("post", "/api/todos", {"title": "a", "zzz": 1}, "El campo «zzz» no está permitido"),
        ("patch", "/api/todos/1", {}, "indica al menos un campo"),
        ("patch", "/api/todos/1", {"title": None}, "no puede ser null"),
    ],
)
def test_validation_errors_are_in_spanish(client, make_todo, method, url, payload, expected):
    make_todo("existente")
    response = getattr(client, method)(url, json=payload)
    assert response.status_code == 422
    messages = [e["msg"] for e in response.json()["detail"]]
    assert any(expected in m for m in messages), messages
    assert not any("Field required" in m or "Value error" in m for m in messages)


def test_validation_error_for_malformed_json_is_in_spanish(client):
    response = client.post(
        "/api/todos", content="{roto", headers={"Content-Type": "application/json"}
    )
    assert response.json()["detail"][0]["msg"] == "El cuerpo de la petición no es un JSON válido"


def test_validation_error_for_invalid_id_is_in_spanish(client):
    response = client.get("/api/todos/0")
    assert "mayor o igual que 1" in response.json()["detail"][0]["msg"]


# --- GET /api/todos --------------------------------------------------------

def test_list_todos_empty(client):
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_returns_all(client, make_todo):
    make_todo("A")
    make_todo("B")
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["A", "B"]


def test_list_todos_filter_by_status(client, make_todo):
    make_todo("pendiente")
    done = make_todo("hecha")
    client.patch(f"/api/todos/{done['id']}", json={"status": "done"})

    response = client.get("/api/todos", params={"status": "done"})
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["hecha"]

    response = client.get("/api/todos", params={"status": "in_progress"})
    assert response.json() == []


def test_list_todos_invalid_status_filter(client):
    response = client.get("/api/todos", params={"status": "inventado"})
    assert response.status_code == 422


# --- GET /api/todos/{id} ---------------------------------------------------

def test_get_todo(client, make_todo):
    todo = make_todo("Buscar")
    response = client.get(f"/api/todos/{todo['id']}")
    assert response.status_code == 200
    assert response.json() == todo


def test_get_todo_not_found(client):
    response = client.get("/api/todos/999")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


@pytest.mark.parametrize("bad_id", ["abc", "0", "-1"])
def test_get_todo_invalid_id(client, bad_id):
    assert client.get(f"/api/todos/{bad_id}").status_code == 422


# --- PATCH /api/todos/{id} -------------------------------------------------

def test_update_todo_all_fields(client, make_todo):
    todo = make_todo("Viejo", description="vieja")
    response = client.patch(
        f"/api/todos/{todo['id']}",
        json={"title": "Nuevo", "description": "nueva", "status": "in_progress"},
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["title"], body["description"], body["status"]) == (
        "Nuevo",
        "nueva",
        "in_progress",
    )
    assert client.get(f"/api/todos/{todo['id']}").json() == body


def test_update_todo_partial_keeps_other_fields(client, make_todo):
    todo = make_todo("Título", description="Descripción")
    response = client.patch(f"/api/todos/{todo['id']}", json={"status": "done"})
    body = response.json()
    assert body["status"] == "done"
    assert body["title"] == "Título"
    assert body["description"] == "Descripción"


def test_update_todo_can_clear_description(client, make_todo):
    todo = make_todo("Título", description="Descripción")
    response = client.patch(f"/api/todos/{todo['id']}", json={"description": None})
    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_todo_not_found(client):
    response = client.patch("/api/todos/999", json={"status": "done"})
    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},  # nada que actualizar
        {"title": ""},
        {"title": None},
        {"status": None},
        {"status": "inventado"},
        {"id": 5},  # no se puede cambiar el id
        {"created_at": "2000-01-01"},
        {"campo_basura": True},
    ],
)
def test_update_todo_rejects_invalid_payload(client, make_todo, payload):
    todo = make_todo("Intacta")
    response = client.patch(f"/api/todos/{todo['id']}", json=payload)
    assert response.status_code == 422
    assert client.get(f"/api/todos/{todo['id']}").json() == todo


# --- DELETE /api/todos/{id} ------------------------------------------------

def test_delete_todo(client, make_todo):
    todo = make_todo("Borrar")
    response = client.delete(f"/api/todos/{todo['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/todos/{todo['id']}").status_code == 404


def test_delete_todo_not_found(client):
    response = client.delete("/api/todos/999")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


# --- Frontend --------------------------------------------------------------

def test_index_serves_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Gestor de tareas" in response.text
