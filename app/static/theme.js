"use strict";

// Se carga en <head> y es síncrono para aplicar el tema antes de pintar (sin parpadeo).
(function () {
  const KEY = "theme";

  function stored() {
    try { return localStorage.getItem(KEY); } catch { return null; }
  }

  function preferred() {
    return stored() || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }

  function apply(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.textContent = theme === "dark" ? "☀️" : "🌙";
      btn.title = theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
      btn.setAttribute("aria-label", btn.title);
    }
  }

  apply(preferred());

  document.addEventListener("DOMContentLoaded", () => {
    apply(preferred());
    document.getElementById("theme-toggle").addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      try { localStorage.setItem(KEY, next); } catch { /* sin almacenamiento: solo dura la sesión */ }
      apply(next);
    });
  });
})();
