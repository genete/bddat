/**
 * plantillas-inspector.js — comportamientos del inspector de plantillas (ADR-023 / #545).
 *
 * El inspector overlay NO re-ejecuta los <script> de sus fragmentos (inyecta por
 * innerHTML). Por eso el JS de los fragmentos de edición/lectura de plantillas se
 * delega aquí, a nivel document, cargado una vez desde el listado:
 *
 *   [data-pl-copy]        — copia al portapapeles el valor de [data-pl-copy-target]
 *                           (o de data-pl-copy-value); feedback visual en el icono.
 *
 * (El explorador de ficheros del servidor y su botón «Cambiar fichero» se retiraron en #1009:
 * el fichero de una plantilla o fragmento se sube desde el navegador.)
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

})();
