/**
 * pool_acciones.js — acciones del inspector de un documento del pool: «Borrar» y «Sustituir
 * fichero» (#881, ADR-053 §F).
 *
 * El inspector inyecta su fragmento con `innerHTML`, así que los `<script>` del fragmento no se
 * ejecutan (ADR-023): los botones se enganchan aquí, por delegación a nivel `document`. El modal
 * de sustituir vive en la página (`_pool_modal_sustituir.html`) y lo abre el propio botón del
 * fragmento con `data-bs-toggle="modal"`, que le pasa `data-doc-id` y `data-doc-nombre`.
 *
 * Avisa a la página de que el pool cambió con el evento `pool:cambiado` (borrar); tras sustituir
 * se recarga la página entera, que reabre el inspector por `?sel=` y refresca las extensiones del
 * filtro (el nombre del fichero nuevo puede traer una que antes no había).
 *
 * Depende de: bootstrap y de los globales `AppInspector`, `mostrar_toast` y `quitar_comprimidos`.
 */
(function () {
  'use strict';

  var CFG = document.getElementById('pool-config').dataset;

  // ================================================================
  // BORRAR
  // ================================================================
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-pool-borrar]');
    if (!btn) return;
    if (!confirm('¿Borrar este registro del pool?\nEl fichero del servidor NO se eliminará.')) return;
    btn.disabled = true;
    fetch(btn.dataset.url, { method: 'POST' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        mostrar_toast('info', 'Registro eliminado del pool.');
        if (window.AppInspector) AppInspector.close();
        document.dispatchEvent(new CustomEvent('pool:cambiado'));
      } else {
        btn.disabled = false;
        mostrar_toast('danger', data.error || 'No se pudo borrar el documento.');
      }
    })
    .catch(function () {
      btn.disabled = false;
      mostrar_toast('danger', 'Error de red al borrar.');
    });
  });

  // ================================================================
  // SUSTITUIR FICHERO (ADR-050 §F, #1007)
  // ================================================================
  var modal = document.getElementById('modal-sustituir');
  var fichero = document.getElementById('sustituir-fichero');
  var motivo  = document.getElementById('sustituir-motivo');
  var boton   = document.getElementById('btn-sustituir');
  var error   = document.getElementById('sustituir-error');

  function actualizar_boton_sustituir() {
    boton.disabled = !(fichero.files.length > 0 && motivo.value.trim() !== '');
  }

  // Al abrirse desde el botón del fragmento: id y nombre del documento, y el formulario limpio.
  modal.addEventListener('show.bs.modal', function (e) {
    var origen = e.relatedTarget;
    if (origen && origen.dataset.docId) {
      document.getElementById('sustituir-doc-id').value       = origen.dataset.docId;
      document.getElementById('sustituir-nombre').textContent = origen.dataset.docNombre;
    }
    fichero.value = '';
    motivo.value  = '';
    error.classList.add('d-none');
    actualizar_boton_sustituir();
  });

  fichero.addEventListener('change', function (e) {
    quitar_comprimidos(e.target);
    actualizar_boton_sustituir();
  });
  motivo.addEventListener('input', actualizar_boton_sustituir);

  window.enviar_sustitucion = function () {
    var doc_id = document.getElementById('sustituir-doc-id').value;
    if (!fichero.files[0]) return;

    var formData = new FormData();
    formData.append('fichero', fichero.files[0]);
    formData.append('motivo', motivo.value.trim());

    boton.disabled = true;
    error.classList.add('d-none');
    fetch(CFG.urlBase + '/' + doc_id + '/sustituir', { method: 'POST', body: formData })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        bootstrap.Modal.getInstance(modal).hide();
        mostrar_toast('success', 'Fichero sustituido: el documento ahora es «' + data.nombre + '».');
        setTimeout(function () { window.location.reload(); }, 1500);
      } else {
        error.textContent = data.error || 'No se pudo sustituir el fichero.';
        error.classList.remove('d-none');
        boton.disabled = false;
      }
    })
    .catch(function () {
      error.textContent = 'Error de red.';
      error.classList.remove('d-none');
      boton.disabled = false;
    });
  };

}());
