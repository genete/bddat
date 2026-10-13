/**
 * requisitos-inspector.js — Editor de condiciones anidado del CRUD de
 * requisitos documentales (#583).
 *
 * El inspector overlay NO re-ejecuta <script> embebidos en los fragmentos que
 * inyecta (ver project_inspector_vs_modal_scripts.md) — por eso esta lógica
 * vive en un fichero estático cargado una vez en listado.html, con
 * delegación de eventos a nivel document (funciona igual tras cada swap del
 * fragmento de edición).
 *
 * Contrato del fragmento (_editar_fragmento.html):
 *   [data-condiciones-editor]   contenedor
 *   [data-cond-add]             botón "Añadir condición"
 *   [data-cond-rows]            contenedor de filas
 *   template[data-cond-template] fila en blanco para clonar
 *   [data-cond-row]             una fila (variable + operador + valor + orden)
 *   [data-cond-variable]        select de variable (option con data-tipo)
 *   [data-cond-operador]        select de operador
 *   [data-cond-valor-wrap]      wrapper del input valor (se oculta en IS_NULL/NOT_NULL)
 *   [data-cond-valor]           input de valor
 *   [data-cond-remove]          botón quitar fila
 */
(function () {
  'use strict';

  var TIPO_LABELS = {
    boolean:  'verdadero/falso',
    numerico: 'número',
    texto:    'texto',
    fecha:    'AAAA-MM-DD',
    enum:     'valor del catálogo',
  };

  var SIN_VALOR = { IS_NULL: true, NOT_NULL: true };

  // Añadir o quitar una fila cambia el formulario sin que el usuario teclee nada, así que
  // no dispara input ni change. El marco del inspector (ADR-053 §A, #1042) solo enciende
  // «Guardar» al oírlos: sin este aviso, quitar una fila no se podría guardar.
  function avisarCambio(el) {
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  document.addEventListener('click', function (e) {
    var addBtn = e.target.closest('[data-cond-add]');
    if (addBtn) {
      var editor = addBtn.closest('[data-condiciones-editor]');
      var tpl = editor ? editor.querySelector('template[data-cond-template]') : null;
      var rows = editor ? editor.querySelector('[data-cond-rows]') : null;
      if (tpl && rows) {
        rows.appendChild(tpl.content.cloneNode(true));
        avisarCambio(rows);
      }
      return;
    }

    var removeBtn = e.target.closest('[data-cond-remove]');
    if (removeBtn) {
      var row = removeBtn.closest('[data-cond-row]');
      if (row) {
        var contenedor = row.parentNode;
        row.remove();
        avisarCambio(contenedor);
      }
      return;
    }
  });

  document.addEventListener('change', function (e) {
    var operSel = e.target.closest('[data-cond-operador]');
    if (operSel) {
      var row = operSel.closest('[data-cond-row]');
      var wrap = row ? row.querySelector('[data-cond-valor-wrap]') : null;
      var input = row ? row.querySelector('[data-cond-valor]') : null;
      if (wrap && input) {
        var sinValor = !!SIN_VALOR[operSel.value];
        wrap.style.display = sinValor ? 'none' : '';
        input.disabled = sinValor;
        if (sinValor) input.value = '';
      }
      return;
    }

    var varSel = e.target.closest('[data-cond-variable]');
    if (varSel) {
      var row2 = varSel.closest('[data-cond-row]');
      var hint = row2 ? row2.querySelector('[data-cond-tipo-hint]') : null;
      if (hint) {
        var opt = varSel.options[varSel.selectedIndex];
        var tipo = opt ? (opt.getAttribute('data-tipo') || '') : '';
        hint.textContent = tipo ? (TIPO_LABELS[tipo] || tipo) : '';
      }
      return;
    }
  });
})();
