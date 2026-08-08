// mensajes-badge.js — Badge del sobre del topbar (#28, ADR-040 §7).
//
// Un solo número, bimodal: el backend decide QUÉ cuenta según el permiso del
// rol activo (pendientes de todos + propias sin acusar, o solo lo segundo).
// Aquí no se decide nada — si el modo se calculara en el front, cambiar de rol
// dejaría el número mintiendo hasta el siguiente recargado.
//
// Mismo enfoque de polling que motor-estado.js: no hay websockets/SSE en la
// app, así que el número puede ir hasta INTERVALO_MS por detrás. Es un
// indicador, no una autorización.
(function () {
  var INTERVALO_MS = 60000;

  function pintar(el, n) {
    if (n > 0) {
      el.textContent = n > 99 ? '99+' : n;
      el.style.display = '';
    } else {
      el.style.display = 'none';
    }
  }

  function actualizar(el) {
    fetch('/api/mensajes-internos/badge', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { if (data) pintar(el, data.total || 0); })
      .catch(function () { /* red caída: se mantiene el último número conocido */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('js-mensajes-topbar-badge');
    if (!el) return;

    actualizar(el);
    setInterval(function () { actualizar(el); }, INTERVALO_MS);

    // Resolver o acusar cambia el número: refrescar sin esperar al polling.
    // El inspector emite inspector:saved tras cualquier guardado con éxito.
    document.addEventListener('inspector:saved', function () { actualizar(el); });
  });
})();
