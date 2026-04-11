/**
 * generar_escrito.js — Flujo de generación de escritos desde tarea REDACTAR (#167 Fase 5)
 *
 * Depende de:
 *   - SelectorBusqueda (selector_busqueda.js) — ya cargado en el template
 *   - window.GE_CONFIG = { tareaId: Number }  — inyectado por el template
 *   - Bootstrap 5 (Modal, Toast)
 *
 * Flujo:
 *   1. Modal show → GET /api/escritos/plantillas → poblar SelectorBusqueda
 *   2. Selección → GET /api/escritos/preview → mostrar paso 2
 *   3. Click "Generar" → POST /api/escritos/generar → toast + reload
 */
(function () {
  'use strict';

  var config = window.GE_CONFIG;
  if (!config || !config.tareaId) return;

  // ── Elementos del DOM ──────────────────────────────────────────────
  var modal_el      = document.getElementById('modalGenerarEscrito');
  var paso1         = document.getElementById('ge-paso1');
  var paso2         = document.getElementById('ge-paso2');
  var spinner       = document.getElementById('ge-spinner');
  var contador      = document.getElementById('ge-contador');
  var preview_grid  = document.getElementById('ge-preview-campos');
  var input_nombre  = document.getElementById('ge-nombre-fichero');
  var input_ruta    = document.getElementById('ge-ruta-destino');
  var check_pool    = document.getElementById('ge-check-pool');
  var check_doc     = document.getElementById('ge-check-doc-producido');
  var check_abrir   = document.getElementById('ge-check-abrir-carpeta');
  var btn_generar   = document.getElementById('ge-btn-generar');

  if (!modal_el) return;

  // ── Estado ─────────────────────────────────────────────────────────
  var plantilla_id_seleccionada = null;
  var selector = null;

  // ── Toast helper ───────────────────────────────────────────────────
  function mostrar_toast(tipo, mensaje) {
    var iconos    = { success: 'fa-check-circle', danger: 'fa-exclamation-circle',
                      warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
    var etiquetas = { success: 'Correcto', danger: 'Error',
                      warning: 'Atención',  info: 'Información' };
    var id   = 'toast-js-' + Date.now();
    var html =
      '<div id="' + id + '" class="toast toast-' + tipo + '" role="alert"' +
      ' aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">' +
      '<div class="d-flex align-items-center p-3"><div class="flex-grow-1">' +
      '<i class="fas ' + (iconos[tipo] || iconos.info) + ' me-2"></i>' +
      '<strong>' + (etiquetas[tipo] || 'Aviso') + ':</strong> ' + mensaje +
      '</div><button type="button" class="btn-close ms-3"' +
      ' data-bs-dismiss="toast" aria-label="Cerrar"></button></div></div>';
    var container = document.querySelector('.toast-container');
    if (!container) return;
    container.insertAdjacentHTML('beforeend', html);
    var el = document.getElementById(id);
    el.classList.add('showing');
    var t = new bootstrap.Toast(el);
    t.show();
    setTimeout(function () { el.classList.remove('showing'); }, 300);
    el.addEventListener('hide.bs.toast', function () { el.classList.add('hide'); });
    el.addEventListener('click', function (e) {
      if (!e.target.closest('.btn-close')) { t.hide(); }
    });
    el.addEventListener('hidden.bs.toast', function () { el.remove(); });
  }

  // ── Inicializar SelectorBusqueda ───────────────────────────────────
  selector = new SelectorBusqueda('#ge-selector-plantilla', [], {
    placeholder: '— Seleccione una plantilla —',
    name: 'plantilla_id',
    onChange: function (v, t) {
      plantilla_id_seleccionada = v ? parseInt(v, 10) : null;
      btn_generar.disabled = !plantilla_id_seleccionada;

      if (plantilla_id_seleccionada) {
        cargar_preview(plantilla_id_seleccionada);
      } else {
        paso2.classList.add('d-none');
      }
    }
  });

  // ── Evento: modal se abre → cargar plantillas ─────────────────────
  modal_el.addEventListener('show.bs.modal', function () {
    resetear_modal();
    cargar_plantillas();
  });

  function resetear_modal() {
    plantilla_id_seleccionada = null;
    btn_generar.disabled = true;
    paso2.classList.add('d-none');
    spinner.classList.add('d-none');
    paso1.classList.remove('d-none');
    btn_generar.classList.remove('d-none');
    selector.clear();
    preview_grid.innerHTML = '';
    input_nombre.value = '';
    input_ruta.value = '';
    check_pool.checked = true;
    check_doc.checked = true;
    check_abrir.checked = false;
  }

  // ── Cargar plantillas ESFTT compatibles ────────────────────────────
  function cargar_plantillas() {
    contador.textContent = 'Cargando plantillas...';
    fetch('/api/escritos/plantillas?tarea_id=' + config.tareaId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) {
          contador.textContent = 'Error: ' + (data.error || 'desconocido');
          return;
        }
        var opciones = data.plantillas.map(function (p) {
          var texto = p.nombre;
          if (p.variante) texto += ' — ' + p.variante;
          texto += ' (' + p.especificidad + '/4)';
          return { v: String(p.id), t: texto };
        });
        selector.setOpciones(opciones);
        var n = data.plantillas.length;
        contador.textContent = n + ' plantilla' + (n !== 1 ? 's' : '') + ' disponible' + (n !== 1 ? 's' : '');
      })
      .catch(function (err) {
        contador.textContent = 'Error al cargar plantillas';
        console.error('GE: error cargando plantillas', err);
      });
  }

  // ── Cargar preview ─────────────────────────────────────────────────
  function cargar_preview(pid) {
    fetch('/api/escritos/preview?plantilla_id=' + pid + '&tarea_id=' + config.tareaId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) {
          mostrar_toast('danger', data.error || 'Error al cargar preview');
          return;
        }

        // Mostrar campos del contexto en grid
        var campos = data.campos || {};
        var html = '';
        var labels = {
          numero_at: 'N.o AT',
          titular_nombre: 'Titular',
          titular_nif: 'NIF titular',
          proyecto_titulo: 'Proyecto',
          responsable_nombre: 'Responsable',
          fecha_hoy: 'Fecha'
        };
        var claves_mostrar = ['numero_at', 'titular_nombre', 'titular_nif',
                              'proyecto_titulo', 'responsable_nombre', 'fecha_hoy'];
        for (var i = 0; i < claves_mostrar.length; i++) {
          var k = claves_mostrar[i];
          var label = labels[k] || k;
          var valor = campos[k] || '—';
          html += '<div class="col-md-6"><small class="fw-semibold">' + label +
                  ':</small> <small>' + escapeHtml(String(valor)) + '</small></div>';
        }
        preview_grid.innerHTML = html;

        input_nombre.value = data.nombre_propuesto || '';
        input_ruta.value = data.ruta_destino || '';

        paso2.classList.remove('d-none');
      })
      .catch(function (err) {
        mostrar_toast('danger', 'Error de conexión al cargar preview');
        console.error('GE: error preview', err);
      });
  }

  // ── Click "Generar" ────────────────────────────────────────────────
  btn_generar.addEventListener('click', function () {
    if (!plantilla_id_seleccionada) return;

    btn_generar.disabled = true;
    paso1.classList.add('d-none');
    paso2.classList.add('d-none');
    spinner.classList.remove('d-none');
    btn_generar.classList.add('d-none');

    var body = {
      plantilla_id: plantilla_id_seleccionada,
      tarea_id: config.tareaId,
      nombre_fichero: input_nombre.value.trim(),
      registrar_pool: check_pool.checked,
      asignar_doc_producido: check_doc.checked,
      abrir_carpeta: check_abrir.checked
    };

    fetch('/api/escritos/generar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.ok) {
          // Error: mostrar toast, volver al estado anterior
          spinner.classList.add('d-none');
          paso1.classList.remove('d-none');
          paso2.classList.remove('d-none');
          btn_generar.classList.remove('d-none');
          btn_generar.disabled = false;
          mostrar_toast('danger', data.error || 'Error desconocido al generar');
          return;
        }

        // OK: cerrar modal, toast success
        var bsModal = bootstrap.Modal.getInstance(modal_el);
        if (bsModal) bsModal.hide();

        mostrar_toast('success', 'Escrito generado: ' + escapeHtml(data.nombre_fichero));

        // Abrir carpeta si el usuario lo pidió
        if (check_abrir.checked && data.uri_explorador) {
          window.open(data.uri_explorador, '_blank');
        }

        // Recargar para reflejar cambios (doc_producido, fecha_inicio)
        setTimeout(function () { location.reload(); }, 1000);
      })
      .catch(function (err) {
        spinner.classList.add('d-none');
        paso1.classList.remove('d-none');
        paso2.classList.remove('d-none');
        btn_generar.classList.remove('d-none');
        btn_generar.disabled = false;
        mostrar_toast('danger', 'Error de conexión al generar escrito');
        console.error('GE: error generación', err);
      });
  });

  // ── Utilidad escape HTML ───────────────────────────────────────────
  function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

})();
