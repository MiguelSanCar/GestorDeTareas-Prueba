"use strict";

const API = "/api/todos";
const STATUS_LABELS = { pending: "Pendiente", in_progress: "En progreso", done: "Completada" };

const STATUS_ORDER = ["pending", "in_progress", "done"];

const errorBox = document.getElementById("error");
let editingId = null;
let draggedTodo = null;

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

// Convierte la respuesta de error de FastAPI (string o lista de errores de validación) en texto legible.
function formatDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => e.msg).join("; "); // el servidor ya devuelve mensajes en español
  }
  return "Error inesperado";
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor");
  }
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(formatDetail(body.detail));
  return body;
}

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  node.append(...children);
  return node;
}

function renderCard(todo) {
  if (todo.id === editingId) return renderEditCard(todo);

  const index = STATUS_ORDER.indexOf(todo.status);
  const moveBtn = (offset, symbol, title) => {
    const target = STATUS_ORDER[index + offset];
    const btn = el("button", {
      type: "button",
      className: "btn btn-primary move",
      textContent: symbol,
      title: target ? `${title}: ${STATUS_LABELS[target]}` : title,
      disabled: !target,
    });
    btn.addEventListener("click", () => act(() => update(todo.id, { status: target })));
    return btn;
  };
  const moveLeft = moveBtn(-1, "←", "Mover a la izquierda");
  const moveRight = moveBtn(1, "→", "Mover a la derecha");

  const editBtn = el("button", { className: "btn btn-sm btn-outline-secondary", textContent: "Editar" });
  editBtn.addEventListener("click", () => { editingId = todo.id; load(); });

  const deleteBtn = el("button", { className: "btn btn-sm btn-outline-danger", textContent: "Eliminar" });
  deleteBtn.addEventListener("click", () => {
    if (confirm(`¿Eliminar "${todo.title}"?`)) act(() => request(`${API}/${todo.id}`, { method: "DELETE" }));
  });

  const body = el("div", { className: "card-body" }, el("h3", { className: "card-title h6", textContent: todo.title }));
  if (todo.description) body.append(el("p", { className: "card-text text-body-secondary small", textContent: todo.description }));
  body.append(el("div", { className: "actions" },
    moveLeft, el("div", { className: "center-actions" }, editBtn, deleteBtn), moveRight));
  const card = el("li", { className: "card shadow-sm", draggable: true }, body);

  card.addEventListener("dragstart", (event) => {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(todo.id));
    draggedTodo = todo;
    // setTimeout: el navegador captura la imagen del arrastre antes de aplicar el estilo.
    setTimeout(() => card.classList.add("dragging"), 0);
  });
  card.addEventListener("dragend", () => {
    draggedTodo = null;
    card.classList.remove("dragging");
    document.querySelectorAll(".column.drag-over").forEach((c) => c.classList.remove("drag-over"));
  });
  return card;
}

function renderEditCard(todo) {
  // Sin `required`: la validación (y su mensaje en español) la hace el servidor.
  const title = el("input", { className: "form-control", value: todo.title, maxLength: 200 });
  const description = el("textarea", { className: "form-control", value: todo.description || "", maxLength: 2000, rows: 3 });
  const cancel = el("button", { type: "button", className: "btn btn-sm btn-outline-secondary", textContent: "Cancelar" });
  cancel.addEventListener("click", () => { editingId = null; load(); });

  const form = el("form", { className: "d-grid gap-2" }, title, description,
    el("div", { className: "d-flex justify-content-end gap-2" },
      cancel, el("button", { type: "submit", className: "btn btn-sm btn-primary", textContent: "Guardar" })));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    act(async () => {
      await update(todo.id, { title: title.value, description: description.value || null });
      editingId = null;
    });
  });
  return el("li", { className: "card shadow-sm" }, el("div", { className: "card-body" }, form));
}

function update(id, fields) {
  return request(`${API}/${id}`, { method: "PATCH", body: JSON.stringify(fields) });
}

// Ejecuta una acción, muestra el error si falla y recarga el tablero.
async function act(fn) {
  try {
    showError("");
    await fn();
  } catch (err) {
    showError(err.message);
  }
  await load();
}

async function load() {
  try {
    const todos = await request(API);
    for (const column of document.querySelectorAll(".column")) {
      const items = todos.filter((t) => t.status === column.dataset.status);
      column.querySelector(".count").textContent = `(${items.length})`;
      column.querySelector("ul").replaceChildren(...items.map(renderCard));
    }
  } catch (err) {
    showError(err.message);
  }
}

// Las columnas son fijas, así que los listeners de soltado se registran una sola vez.
// La zona de soltado es el carril (.lane), que ocupa todo el alto de la pantalla,
// mientras que la caja (.column) solo mide lo que su contenido.
for (const lane of document.querySelectorAll(".lane")) {
  const column = lane.querySelector(".column");
  lane.addEventListener("dragover", (event) => {
    if (!draggedTodo) return;
    event.preventDefault(); // necesario para permitir el drop
    event.dataTransfer.dropEffect = "move";
    column.classList.add("drag-over");
  });
  lane.addEventListener("dragleave", (event) => {
    if (!lane.contains(event.relatedTarget)) column.classList.remove("drag-over");
  });
  lane.addEventListener("drop", (event) => {
    event.preventDefault();
    column.classList.remove("drag-over");
    const todo = draggedTodo;
    const status = column.dataset.status;
    if (todo && todo.status !== status) act(() => update(todo.id, { status }));
  });
}

const createDialog = document.getElementById("create-dialog");
const createForm = document.getElementById("create-form");
const createError = document.getElementById("create-error");

function setCreateError(message) {
  createError.textContent = message;
  createError.hidden = !message;
}

document.getElementById("open-create").addEventListener("click", () => {
  createForm.reset();
  setCreateError("");
  createDialog.showModal();
  document.getElementById("new-title").focus();
});
document.getElementById("close-create").addEventListener("click", () => createDialog.close());
document.getElementById("cancel-create").addEventListener("click", () => createDialog.close());
// Clic en el fondo oscuro (fuera del cuadro) también cierra.
createDialog.addEventListener("click", (event) => {
  if (event.target === createDialog) createDialog.close();
});

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setCreateError("");
  try {
    await request(API, {
      method: "POST",
      body: JSON.stringify({
        title: document.getElementById("new-title").value,
        description: document.getElementById("new-description").value || null,
        status: document.getElementById("new-status").value,
      }),
    });
  } catch (err) {
    setCreateError(err.message); // el diálogo sigue abierto para corregir
    return;
  }
  createDialog.close();
  showError("");
  await load();
});

load();
