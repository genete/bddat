// motor-estado.js — Polling del semáforo del modo global del motor (#479).
// No hay infraestructura de push (websockets/SSE) en la app; esto da un
// "broadcast" aproximado — hasta INTERVALO_MS de retraso, no instantáneo.
(function () {
  var INTERVALO_MS = 60000;
  var CLASES = ['text-bg-success', 'text-bg-warning', 'text-bg-danger', 'text-bg-secondary'];

  function actualizar(el) {
    fetch('/configuracion-motor/estado', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        CLASES.forEach(function (c) { el.classList.remove(c); });
        el.classList.add('text-bg-' + data.clase);
        el.title = 'Modo global del motor: ' + data.etiqueta;
        el.innerHTML = '<i class="bi bi-shield-check"></i> ' + data.etiqueta;
      })
      .catch(function () { /* red caída: se mantiene el último estado conocido */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var el = document.getElementById('js-motor-estado');
    if (!el) return;
    setInterval(function () { actualizar(el); }, INTERVALO_MS);
  });
})();
