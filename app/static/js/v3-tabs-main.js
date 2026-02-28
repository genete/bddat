/**
 * v3-tabs-main.js — Tabs dinámicos V3 (issue #150)
 *
 * Responsabilidades:
 *   - Creación de entidad hija via modal → reload
 *   - Edición inline (toggle ver/editar) → actualización DOM
 *   - Borrado → eliminación DOM (tab + panel)
 *   - Toasts de error/advertencia
 */

'use strict';

// ── Helpers toast ─────────────────────────────────────────────────────────────

function mostrarToast(mensaje, tipo) {
    const contenedor = document.querySelector('.toast-container');
    if (!contenedor) { alert(mensaje); return; }
    const el = document.createElement('div');
    el.className = `toast toast-${tipo}`;
    el.setAttribute('role', 'alert');
    el.setAttribute('data-bs-autohide', 'true');
    el.setAttribute('data-bs-delay', '8000');
    el.innerHTML = `
        <div class="d-flex align-items-center p-3">
            <div class="flex-grow-1">
                <i class="fas fa-exclamation-circle me-2"></i>${mensaje}
            </div>
            <button type="button" class="btn-close ms-3" data-bs-dismiss="toast" aria-label="Cerrar"></button>
        </div>`;
    contenedor.appendChild(el);
    new bootstrap.Toast(el).show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}

function mostrarError(msg)       { mostrarToast(msg, 'danger'); }
function mostrarAdvertencia(msg) { mostrarToast(msg, 'warning'); }


// ── Creación de entidad hija ──────────────────────────────────────────────────
//    Clic en .btn-nueva-entidad → actualiza data-parent-id del modal y lo abre

document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-nueva-entidad');
    if (!btn) return;
    const nivel    = btn.dataset.nivel;
    const parentId = btn.dataset.parentId;
    const modalEl  = document.getElementById(`modal-nueva-${nivel}`);
    if (!modalEl) return;
    modalEl.dataset.parentId = parentId;
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
});

// Submit de formulario de creación → POST → location.reload()
document.addEventListener('submit', async (e) => {
    if (!e.target.classList.contains('form-nueva-entidad')) return;
    e.preventDefault();
    const form     = e.target;
    const nivel    = form.dataset.nivel;
    const modalEl  = form.closest('.modal');
    const parentId = modalEl.dataset.parentId;
    const endpoint = _buildCrearEndpoint(nivel, parentId);
    if (!endpoint) return;

    const btnSubmit = form.querySelector('[type=submit]');
    if (btnSubmit) btnSubmit.disabled = true;

    try {
        const resp = await fetch(endpoint, {
            method: 'POST',
            body: new FormData(form),
        });
        const data = await resp.json();
        if (!data.ok) {
            mostrarError(data.error || 'Error al crear');
            if (btnSubmit) btnSubmit.disabled = false;
            return;
        }
        // Cerrar modal y recargar la página para mostrar el nuevo elemento
        bootstrap.Modal.getInstance(modalEl)?.hide();
        if (data.advertencia) mostrarAdvertencia(data.advertencia.mensaje);
        location.reload();
    } catch (err) {
        mostrarError('Error de red: ' + err.message);
        if (btnSubmit) btnSubmit.disabled = false;
    }
});


// ── Toggle edición inline ─────────────────────────────────────────────────────

document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-editar-entidad')) {
        const panel = e.target.closest('.tab-pane');
        if (panel) _toggleModoEditar(panel, true);
    }
    if (e.target.closest('.btn-cancelar-edicion')) {
        const panel = e.target.closest('.tab-pane');
        if (panel) _toggleModoEditar(panel, false);
    }
});

function _toggleModoEditar(panel, editar) {
    panel.querySelectorAll('[data-modo-ver]').forEach(el =>
        el.classList.toggle('d-none', editar));
    panel.querySelectorAll('[data-modo-editar]').forEach(el =>
        el.classList.toggle('d-none', !editar));
    // Campos sin wrapper data-modo-* (textareas compartidas)
    panel.querySelectorAll(
        'textarea:not([data-modo-ver]):not([data-modo-editar])'
    ).forEach(el => {
        if (!el.dataset.siempreDeshabilitado) el.readOnly = !editar;
    });
}


// ── Guardar edición inline ────────────────────────────────────────────────────

document.addEventListener('submit', async (e) => {
    if (!e.target.classList.contains('form-editar-entidad')) return;
    e.preventDefault();
    const form      = e.target;
    const nivel     = form.dataset.nivel;
    const entidadId = form.dataset.entidadId;
    const endpoint  = `/api/vista3/${nivel}/${entidadId}/editar`;

    const btnSubmit = form.querySelector('[type=submit]');
    if (btnSubmit) btnSubmit.disabled = true;

    try {
        const resp = await fetch(endpoint, {
            method: 'POST',
            body: new FormData(form),
        });
        const data = await resp.json();
        if (!data.ok) {
            mostrarError(data.error || 'Error al guardar');
            if (btnSubmit) btnSubmit.disabled = false;
            return;
        }
        // Actualizar campos de vista y volver a modo ver
        const panel = form.closest('.tab-pane');
        _aplicarCambiosAVista(panel);
        _toggleModoEditar(panel, false);
        _actualizarTabIcon(nivel, entidadId, panel);
        if (data.advertencia) mostrarAdvertencia(data.advertencia.mensaje);
    } catch (err) {
        mostrarError('Error de red: ' + err.message);
    } finally {
        if (btnSubmit) btnSubmit.disabled = false;
    }
});

/** Copia los valores de los campos de edición a los campos de visualización. */
function _aplicarCambiosAVista(panel) {
    panel.querySelectorAll('[data-display-for]').forEach(displayEl => {
        const nombre  = displayEl.dataset.displayFor;
        const editEl  = panel.querySelector(`[name="${nombre}"]`);
        if (!editEl) return;

        if (editEl.tagName === 'SELECT') {
            const sel = editEl.options[editEl.selectedIndex];
            displayEl.value = sel ? sel.text : '';
        } else if (editEl.type === 'date' && editEl.value) {
            const [y, m, d] = editEl.value.split('-');
            displayEl.value = d ? `${d}/${m}/${y}` : '';
        } else {
            displayEl.value = editEl.value;
        }
    });
    // Textareas con data-display-for (observaciones, notas)
    panel.querySelectorAll('textarea[data-display-for]').forEach(displayEl => {
        const editEl = panel.querySelector(`[name="${displayEl.dataset.displayFor}"]`);
        if (editEl) displayEl.value = editEl.value;
    });
}

/** Actualiza el icono del tab según el estado derivado de los campos del panel. */
function _actualizarTabIcon(nivel, id, panel) {
    const tabBtn = document.getElementById(`tab-${nivel}-${id}`);
    if (!tabBtn) return;
    const iconEl = tabBtn.querySelector('.tab-icon i');
    if (!iconEl) return;

    const fechaInicioEl = panel?.querySelector('[name="fecha_inicio"]');
    const fechaFinEl    = panel?.querySelector('[name="fecha_fin"]');
    const estadoEl      = panel?.querySelector('[name="estado"]');

    let icono = '', color = 'text-secondary';

    if (nivel === 'solicitud') {
        const est = estadoEl?.value || 'EN_TRAMITE';
        const map = {
            'EN_TRAMITE': ['fa-solid fa-file-contract',      'text-warning'],
            'RESUELTA':   ['fa-solid fa-file-circle-check',  'text-success'],
            'DESISTIDA':  ['fa-solid fa-file-circle-xmark',  'text-secondary'],
            'ARCHIVADA':  ['fa-regular fa-file',             'text-secondary'],
        };
        [icono, color] = map[est] || map['EN_TRAMITE'];
    } else {
        const tieneFin    = fechaFinEl?.value;
        const tieneInicio = fechaInicioEl?.value;
        const finIcons   = { fase: 'fa-solid fa-sitemap',       tramite: 'fa-solid fa-clipboard-check', tarea: 'fa-solid fa-square-check' };
        const curIcons   = { fase: 'fa-solid fa-sitemap',       tramite: 'fa-solid fa-clipboard-list',  tarea: 'fa-solid fa-pen-to-square' };
        const penIcons   = { fase: 'fa-solid fa-sitemap',       tramite: 'fa-regular fa-clipboard',     tarea: 'fa-regular fa-square' };
        if (tieneFin) {
            icono = finIcons[nivel] || 'fa-regular fa-file'; color = 'text-success';
        } else if (tieneInicio) {
            icono = curIcons[nivel] || 'fa-regular fa-file'; color = 'text-warning';
        } else {
            icono = penIcons[nivel] || 'fa-regular fa-file';
        }
    }
    iconEl.className = `${icono} ${color}`;
}


// ── Borrado ───────────────────────────────────────────────────────────────────

document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.btn-borrar-entidad');
    if (!btn) return;
    if (!confirm('¿Eliminar este elemento? Esta acción no se puede deshacer.')) return;

    const nivel = btn.dataset.nivel;
    const id    = btn.dataset.id;

    try {
        const resp = await fetch(`/api/vista3/${nivel}/${id}/borrar`, {
            method: 'POST',
        });
        const data = await resp.json();
        if (!data.ok) {
            mostrarError(data.error || 'No se pudo eliminar');
            return;
        }
        // Activar tab anterior o siguiente antes de eliminar
        const tabBtn  = document.getElementById(`tab-${nivel}-${id}`);
        const panelEl = document.getElementById(`panel-${nivel}-${id}`);
        const liEl    = tabBtn?.closest('li');
        const prevLi  = liEl?.previousElementSibling;
        const nextLi  = liEl?.nextElementSibling;
        const targetBtn = prevLi?.querySelector('button.nav-link:not(.btn-nueva-entidad)')
                       || nextLi?.querySelector('button.nav-link:not(.btn-nueva-entidad)');
        if (targetBtn) new bootstrap.Tab(targetBtn).show();
        liEl?.remove();
        panelEl?.remove();
    } catch (err) {
        mostrarError('Error de red: ' + err.message);
    }
});


// ── Helpers ───────────────────────────────────────────────────────────────────

function _buildCrearEndpoint(nivel, parentId) {
    const map = {
        solicitud: `/api/vista3/expediente/${parentId}/solicitudes/nueva`,
        fase:      `/api/vista3/solicitud/${parentId}/fases/nueva`,
        tramite:   `/api/vista3/fase/${parentId}/tramites/nuevo`,
        tarea:     `/api/vista3/tramite/${parentId}/tareas/nueva`,
    };
    return map[nivel] || null;
}

// Inicializar tooltips de Bootstrap en toda la página
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
});
