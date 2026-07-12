// motor-estado.js — Polling del semáforo del modo global del motor (#479).
// No hay infraestructura de push (websockets/SSE) en la app; esto da un
// "broadcast" aproximado — hasta INTERVALO_MS de retraso, no instantáneo.
// Nota: el retraso es solo de visualización — la autorización real la
// re-evalúa siempre en vivo el endpoint de mutación (#618).
(function () {
  var INTERVALO_MS = 60000;
  var CLASES = ['text-bg-success', 'text-bg-warning', 'text-bg-danger', 'text-bg-secondary'];

  function actualizar(el, estado) {
    fetch('/configuracion-motor/estado', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        CLASES.forEach(function (c) { el.classList.remove(c); });
        el.classList.add('text-bg-' + data.clase);
        el.title = 'Modo global del motor: ' + data.etiqueta;
        el.innerHTML = '<i class="bi bi-shield-check"></i> ' + data.etiqueta;
        if (data.modo !== estado.modo) {
          estado.modo = data.modo;
          // Notifica a islas React (p. ej. la despensa del árbol, #618) para que
          // invaliden cachés de tipos-creables calculadas con el modo anterior.
          window.dispatchEvent(new CustomEvent('bddat:motor-modo-cambio', { detail: data }));
        }
      })
      .catch(function () { /* red caída: se mantiene el último estado conocido */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('js-motor-estado');
    if (!el) return;
    var estado = { modo: el.dataset.modo || null };
    setInterval(function () { actualizar(el, estado); }, INTERVALO_MS);
  });
})();
