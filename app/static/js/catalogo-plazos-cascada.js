/**
 * catalogo-plazos-cascada.js — Selector en cascada nivel ESFTT → tipo →
 * campo_fecha del CRUD de catálogo de plazos (#632).
 *
 * El inspector overlay NO re-ejecuta <script> embebidos en los fragmentos que
 * inyecta (ver project_inspector_vs_modal_scripts.md) — por eso esta lógica
 * vive en un fichero estático cargado una vez en listado.html, con
 * delegación de eventos a nivel document (funciona igual en el modal de alta
 * y tras cada swap del fragmento de edición).
 *
 * El bloque inicialmente visible lo decide el servidor (Jinja, ver
 * _campo_fecha_macro.html) según el nivel actual del registro (edición) o el
 * valor por defecto del select (alta) — este script solo reacciona a
 * cambios posteriores del selector de nivel, sin necesidad de enganchar
 * ningún evento de "fragmento cargado".
 *
 * Contrato (_campo_fecha_macro.html):
 *   [data-nivel-select]         select de tipo_elemento (SOLICITUD/FASE/TRAMITE/TAREA)
 *   [data-nivel-block="NIVEL"]  bloque de campos específico de ese nivel
 *
 * Al cambiar de nivel: se muestra el bloque del nivel elegido y se ocultan
 * los demás; los campos de los bloques ocultos se deshabilitan (no se
 * envían en el submit) y los del bloque visible se habilitan.
 */
(function () {
  'use strict';

  function _sync(nivelSelect) {
    var form = nivelSelect.closest('form') || document;
    var nivel = nivelSelect.value;
    var bloques = form.querySelectorAll('[data-nivel-block]');
    bloques.forEach(function (bloque) {
      var activo = bloque.getAttribute('data-nivel-block') === nivel;
      bloque.style.display = activo ? '' : 'none';
      bloque.querySelectorAll('input, select').forEach(function (campo) {
        campo.disabled = !activo;
      });
    });
  }

  document.addEventListener('change', function (e) {
    var nivelSelect = e.target.closest('[data-nivel-select]');
    if (nivelSelect) _sync(nivelSelect);
  });
})();
