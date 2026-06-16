/**
 * plantillas-inspector.js — comportamientos del inspector de plantillas (ADR-023 / #545).
 *
 * El inspector overlay NO re-ejecuta los <script> de sus fragmentos (inyecta por
 * innerHTML). Por eso el JS de los fragmentos de edición/lectura de plantillas se
 * delega aquí, a nivel document, cargado una vez desde el listado:
 *
 *   [data-pl-copy]        — copia al portapapeles el valor de [data-pl-copy-target]
 *                           (o de data-pl-copy-value); feedback visual en el icono.
 *   [data-pl-explorador]  — abre el explorador de ficheros como modal grande
 *                           (capa 3) con onSaved no-op para NO refrescar el
 *                           inspector al cerrar y así no perder la edición en curso.
 */
(function () {
  'use strict';

  // ── Copiar al portapapeles ────────────────────────────────────────────────
  function _fallbackCopy(valor) {
    var tmp = document.createElement('textarea');
    tmp.value = valor;
    tmp.style.position = 'fixed';
    tmp.style.opacity = '0';
    document.body.appendChild(tmp);
    tmp.focus();
    tmp.select();
    try { document.execCommand('copy'); } catch (e) { /* ignore */ }
    document.body.removeChild(tmp);
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-pl-copy]');
    if (!btn) return;
    var sel   = btn.getAttribute('data-pl-copy-target');
    var src   = sel ? document.querySelector(sel) : null;
    var valor = src ? src.value : (btn.getAttribute('data-pl-copy-value') || '');
    if (!valor) return;

    function feedback() {
      var icon = btn.querySelector('i');
      if (!icon) return;
      var prev = icon.className;
      icon.className = 'fas fa-check text-success';
      setTimeout(function () { icon.className = prev; }, 1500);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(valor).then(feedback).catch(function () {
        _fallbackCopy(valor); feedback();
      });
    } else {
      _fallbackCopy(valor); feedback();
    }
  });

  // ── Abrir el explorador de ficheros como modal grande ─────────────────────
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-pl-explorador]');
    if (!btn) return;
    var url = btn.getAttribute('data-pl-explorador-url');
    if (url && window.AppModalLarge) {
      // onSaved no-op: al cerrar el modal NO se refresca el inspector (la edición sigue viva).
      AppModalLarge.open(url, { title: 'Seleccionar fichero del servidor', onSaved: function () {} });
    }
  });

})();
