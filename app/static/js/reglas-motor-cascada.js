/**
 * reglas-motor-cascada.js — Selector en cascada del patrón `sujeto` de
 * ReglaMotor (#170).
 *
 * A diferencia de catalogo-plazos-cascada.js (bloques mutuamente excluyentes
 * por nivel), aquí el sujeto es puramente ACUMULATIVO: el nivel elegido fija
 * cuántos segmentos tiene el patrón (assembler._compilar_sujeto añade un
 * segmento más por cada nivel — expediente/solicitud/fase/trámite), así que
 * el nivel N muestra los segmentos 0..N, no un bloque distinto por nivel.
 *
 * Delegación de eventos a nivel document — funciona igual en el modal de
 * alta y tras cada swap del fragmento de edición del inspector (el inspector
 * overlay no re-ejecuta <script> embebidos, ver
 * project_inspector_vs_modal_scripts.md).
 *
 * Contrato (_sujeto_cascada_macro.html):
 *   [data-sujeto-nivel]           select de nivel (EXPEDIENTE/SOLICITUD/FASE/TRAMITE)
 *   [data-sujeto-segmento="N"]    bloque del segmento N (0 a 3)
 */
(function () {
  'use strict';

  var NIVEL_INDICE = { EXPEDIENTE: 0, SOLICITUD: 1, FASE: 2, TRAMITE: 3 };

  function _sync(nivelSelect) {
    var form = nivelSelect.closest('form') || document;
    var maxIndice = NIVEL_INDICE.hasOwnProperty(nivelSelect.value) ? NIVEL_INDICE[nivelSelect.value] : 0;
    var segmentos = form.querySelectorAll('[data-sujeto-segmento]');
    segmentos.forEach(function (bloque) {
      var indice = parseInt(bloque.getAttribute('data-sujeto-segmento'), 10);
      var activo = indice <= maxIndice;
      bloque.style.display = activo ? '' : 'none';
      bloque.querySelectorAll('input, select').forEach(function (campo) {
        campo.disabled = !activo;
      });
    });
  }

  document.addEventListener('change', function (e) {
    var nivelSelect = e.target.closest('[data-sujeto-nivel]');
    if (nivelSelect) _sync(nivelSelect);
  });
})();
