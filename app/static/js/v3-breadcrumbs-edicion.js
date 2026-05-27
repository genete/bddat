// v3-breadcrumbs-edicion.js
// Gestión de edición inline en Vista 3 Breadcrumbs — válido para todos los niveles ESFTT
//
// Convenciones en el HTML:
//   - [data-bc-editable]       → contenedor del card editable (generalmente .bc-card-nodo)
//   - [data-modo-ver]          → elementos visibles solo en modo ver
//   - [data-modo-editar]       → elementos visibles solo en modo editar
//   - [data-ef-name][data-ef-value] → contenedores para EntradaFecha
//   - #form-bc-<nivel>         → el formulario de edición, con data-url apuntando al endpoint
//   - #disp-<campo>            → spans de visualización actualizables tras guardar
//   - #alert-edicion           → div para mensajes de error/advertencia

document.addEventListener('DOMContentLoaded', function () {

  const contenedor = document.querySelector('[data-bc-editable]');
  if (!contenedor) return;

  const btn_editar   = contenedor.querySelector('.btn-editar-bc');
  const btn_cancelar = contenedor.querySelector('.btn-cancelar-bc');
  const btn_guardar  = contenedor.querySelector('.btn-guardar-bc');
  const form         = contenedor.querySelector('form[data-url]');
  const alert_el     = document.getElementById('alert-edicion');

  if (!btn_editar || !form) return;

  // ── 1. Inicializar EntradaFecha en todos los campos [data-ef-name] ────────
  const instancias_ef = {};
  contenedor.querySelectorAll('[data-ef-name]').forEach(el => {
    const ef = new EntradaFecha('#' + el.id, { name: el.dataset.efName });
    if (el.dataset.efValue) ef.setValue(el.dataset.efValue);
    instancias_ef[el.dataset.efName] = ef;
  });

  // ── 2. Toggle ver ↔ editar ────────────────────────────────────────────────
  function activar_modo_editar() {
    contenedor.querySelectorAll('[data-modo-ver]').forEach(el => el.classList.add('d-none'));
    contenedor.querySelectorAll('[data-modo-editar]').forEach(el => el.classList.remove('d-none'));
    _ocultar_alert();
  }

  function activar_modo_ver() {
    contenedor.querySelectorAll('[data-modo-editar]').forEach(el => el.classList.add('d-none'));
    contenedor.querySelectorAll('[data-modo-ver]').forEach(el => el.classList.remove('d-none'));
  }

  btn_editar.addEventListener('click', activar_modo_editar);
  btn_cancelar.addEventListener('click', activar_modo_ver);

  // ── 3. Submit AJAX ────────────────────────────────────────────────────────
  btn_guardar.addEventListener('click', async function () {
    const url   = form.dataset.url;
    const datos = new FormData(form);

    btn_guardar.disabled = true;
    btn_guardar.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Guardando…';

    try {
      const resp = await fetch(url, { method: 'POST', body: datos });
      const json = await resp.json();

      if (!json.ok) {
        _mostrar_alert('danger', (json.motivo ? json.motivo + ' ' : '') + json.error + (json.url_norma ? ` (<a href="${json.url_norma}" target="_blank">ver norma</a>)` : ''));
      } else {
        _actualizar_display(datos);
        activar_modo_ver();
        form.dispatchEvent(new CustomEvent('bc:guardado', { bubbles: false }));
        if (json.advertencia) {
          _mostrar_alert('warning', (json.advertencia.motivo ? json.advertencia.motivo + ' ' : '') + (json.advertencia.norma_compilada || ''));
        }
      }
    } catch (_e) {
      _mostrar_alert('danger', 'Error de comunicación con el servidor.');
    } finally {
      btn_guardar.disabled = false;
      btn_guardar.innerHTML = '<i class="fas fa-save me-1"></i> Guardar';
    }
  });

  // ── 4. Actualizar display tras guardar ────────────────────────────────────
  function _actualizar_display(datos) {
    // Campos EntradaFecha: actualizar span de visualización
    Object.entries(instancias_ef).forEach(([nombre, ef]) => {
      const span = document.getElementById('disp-' + nombre);
      if (!span) return;
      const iso = ef.getValue();
      span.textContent = iso ? _iso_a_dmy(iso) : '—';
    });

    // Estado (select con badge de color — caso especial)
    const estado = datos.get('estado');
    if (estado) {
      const span = document.getElementById('disp-estado');
      if (span) {
        span.textContent = _label_estado(estado);
        span.className   = 'badge ' + _clase_estado(estado);
      }
    }

    // Selects genéricos: actualizar #disp-{name} con el texto de la opción seleccionada
    form.querySelectorAll('select').forEach(sel => {
      if (sel.name === 'estado') return; // ya tratado arriba
      const span = document.getElementById('disp-' + sel.name);
      if (!span) return;
      const opcion = sel.options[sel.selectedIndex];
      span.textContent = (opcion && opcion.value) ? opcion.text : '—';
    });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function _iso_a_dmy(iso) {
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
  }

  function _label_estado(estado) {
    const mapa = {
      'EN_TRAMITE': 'En trámite',
      'RESUELTA':   'Resuelta',
      'DESISTIDA':  'Desistida',
      'ARCHIVADA':  'Archivada'
    };
    return mapa[estado] || estado;
  }

  function _clase_estado(estado) {
    const mapa = {
      'EN_TRAMITE': 'bg-primary',
      'RESUELTA':   'bg-success',
      'DESISTIDA':  'bg-warning text-dark',
      'ARCHIVADA':  'bg-secondary'
    };
    return mapa[estado] || 'bg-secondary';
  }

  function _mostrar_alert(tipo, texto) {
    if (!alert_el) return;
    alert_el.className = `alert alert-${tipo} mt-2 py-2 mb-0`;
    alert_el.innerHTML = texto;
    alert_el.classList.remove('d-none');
  }

  function _ocultar_alert() {
    if (alert_el) alert_el.classList.add('d-none');
  }

});
