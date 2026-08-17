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
 *   [data-nivel-block="NIVEL"]  bloque de campo_fecha específico de ese nivel
 *   [data-camino-seg="N"]       segmento N del camino SFTT (#785), 1..5
 *   [data-camino-req="N"]       asterisco de obligatorio del segmento N
 *
 * Al cambiar de nivel:
 *   - campo_fecha: se muestra el bloque del nivel elegido y se ocultan los demás;
 *     los campos ocultos se deshabilitan (no viajan en el submit).
 *   - camino (#785): se muestran los segmentos 1..N del nivel elegido y se
 *     ocultan los de más profundidad. El último visible es la hoja: obligatorio
 *     y sin opción «Cualquiera», porque es el tipo del elemento evaluado y
 *     siempre se conoce. Los anteriores son ancestros y admiten ANY.
 */
(function () {
  'use strict';

  var SEGMENTOS_POR_NIVEL = { SOLICITUD: 2, FASE: 3, TRAMITE: 4, TAREA: 5 };

  function _syncCampoFecha(form, nivel) {
    form.querySelectorAll('[data-nivel-block]').forEach(function (bloque) {
      var activo = bloque.getAttribute('data-nivel-block') === nivel;
      bloque.style.display = activo ? '' : 'none';
      bloque.querySelectorAll('input, select').forEach(function (campo) {
        campo.disabled = !activo;
      });
    });
  }

  function _syncCamino(form, nivel) {
    var total = SEGMENTOS_POR_NIVEL[nivel] || 2;

    form.querySelectorAll('[data-camino-seg]').forEach(function (bloque) {
      var n = parseInt(bloque.getAttribute('data-camino-seg'), 10);
      var visible = n <= total;
      var esHoja = n === total;

      bloque.style.display = visible ? '' : 'none';

      bloque.querySelectorAll('select').forEach(function (select) {
        select.disabled = !visible;
        // La hoja no admite «Cualquiera»: se oculta la opción ANY y, si estaba
        // seleccionada, se deja el select vacío para forzar una elección real.
        var optAny = select.querySelector('option[value="ANY"]');
        if (optAny) {
          optAny.hidden = esHoja;
          optAny.disabled = esHoja;
          if (esHoja && select.value === 'ANY') select.selectedIndex = -1;
          if (!esHoja && select.selectedIndex === -1) select.value = 'ANY';
        }
        select.required = esHoja;
      });
    });

    form.querySelectorAll('[data-camino-req]').forEach(function (marca) {
      var n = parseInt(marca.getAttribute('data-camino-req'), 10);
      marca.style.display = n === total ? '' : 'none';
    });
  }

  function _sync(nivelSelect) {
    var form = nivelSelect.closest('form') || document;
    var nivel = nivelSelect.value;
    _syncCampoFecha(form, nivel);
    _syncCamino(form, nivel);
  }

  document.addEventListener('change', function (e) {
    var nivelSelect = e.target.closest('[data-nivel-select]');
    if (nivelSelect) _sync(nivelSelect);
  });
})();
