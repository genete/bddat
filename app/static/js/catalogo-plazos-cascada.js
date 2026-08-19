/**
 * catalogo-plazos-cascada.js — Selector en cascada nivel ESFTT → tipo →
 * campo_fecha del CRUD de catálogo de plazos (#632, #788).
 *
 * El inspector overlay NO re-ejecuta <script> embebidos en los fragmentos que
 * inyecta (ver project_inspector_vs_modal_scripts.md) — por eso esta lógica
 * vive en un fichero estático cargado una vez en listado.html, con
 * delegación de eventos a nivel document (funciona igual en el modal de alta
 * y tras cada swap del fragmento de edición). Por la misma razón, el mapa de
 * tipos de documento (window.CATALOGO_PLAZOS_TIPODOC_MAP) se embebe como JSON
 * en el <script> inicial de listado.html, no en el fragmento de edición.
 *
 * El bloque inicialmente visible lo decide el servidor (Jinja, ver
 * _campo_fecha_macro.html) según el nivel actual del registro (edición) o el
 * valor por defecto del select (alta) — este script solo reacciona a
 * cambios posteriores del selector de nivel, sin necesidad de enganchar
 * ningún evento de "fragmento cargado".
 *
 * Contrato (_campo_fecha_macro.html):
 *   [data-nivel-select]         select de tipo_elemento (SOLICITUD/TAREA, #788)
 *   [data-nivel-block="NIVEL"]  bloque de campo_fecha específico de ese nivel
 *   [data-camino-seg="N"]       segmento N del camino SFTT (#785), 1..5
 *   [data-camino-req="N"]       asterisco de obligatorio del segmento N
 *   [data-tipodoc-source="X"]   selects que alimentan el filtro de tipo_documento
 *                                (X: tramite/tarea/rol — camino_tramite,
 *                                camino_tarea, campo_fecha_rol)
 *   [data-tipodoc-target]       select de campo_fecha_tipo_documento a repoblar
 *
 * Al cambiar de nivel:
 *   - campo_fecha: se muestra el bloque del nivel elegido y se ocultan los demás;
 *     los campos ocultos se deshabilitan (no viajan en el submit).
 *   - camino (#785): se muestran los segmentos 1..N del nivel elegido y se
 *     ocultan los de más profundidad. El último visible es la hoja: obligatorio
 *     y sin opción «Cualquiera», porque es el tipo del elemento evaluado y
 *     siempre se conoce. Los anteriores son ancestros y admiten ANY.
 *
 * Al cambiar trámite, tarea o rol (nivel TAREA, #788 §2.3): el desplegable de
 * tipo_documento se repuebla con las opciones de
 * CATALOGO_PLAZOS_TIPODOC_MAP["<tramite>|<tarea>|<rol>"] — mismo mapa que
 * pintó Jinja en el primer render, para que el JS solo tenga que reaccionar a
 * cambios posteriores. Sin trámite concreto (ANY o sin elegir) no hay
 * combinación que buscar y el desplegable queda solo con «Sin especificar».
 */
(function () {
  'use strict';

  var SEGMENTOS_POR_NIVEL = { SOLICITUD: 2, TAREA: 5 };

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

  function _syncTipoDocumento(form) {
    var target = form.querySelector('[data-tipodoc-target]');
    if (!target) return;

    var fuente = function (nombre) {
      var sel = form.querySelector('[data-tipodoc-source="' + nombre + '"]');
      return sel ? sel.value : '';
    };
    var clave = fuente('tramite') + '|' + fuente('tarea') + '|' + (fuente('rol') || 'CONSUMIDO');
    var mapa = window.CATALOGO_PLAZOS_TIPODOC_MAP || {};
    var opciones = mapa[clave] || [];
    var valorPrevio = target.value;

    target.innerHTML = '';
    var optSinEspecificar = document.createElement('option');
    optSinEspecificar.value = '';
    optSinEspecificar.textContent = '— Sin especificar —';
    target.appendChild(optSinEspecificar);
    opciones.forEach(function (opt) {
      var el = document.createElement('option');
      el.value = opt.codigo;
      el.textContent = opt.nombre;
      target.appendChild(el);
    });
    target.value = opciones.some(function (o) { return o.codigo === valorPrevio; }) ? valorPrevio : '';
  }

  function _sync(nivelSelect) {
    var form = nivelSelect.closest('form') || document;
    var nivel = nivelSelect.value;
    _syncCampoFecha(form, nivel);
    _syncCamino(form, nivel);
    _syncTipoDocumento(form);
  }

  document.addEventListener('change', function (e) {
    var nivelSelect = e.target.closest('[data-nivel-select]');
    if (nivelSelect) _sync(nivelSelect);

    var tipodocSource = e.target.closest('[data-tipodoc-source]');
    if (tipodocSource) {
      var form = tipodocSource.closest('form') || document;
      _syncTipoDocumento(form);
    }
  });
})();
