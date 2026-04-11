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
    // Resetear form y re-habilitar submit por si quedó disabled de una apertura anterior
    const form = modalEl.querySelector('.form-nueva-entidad');
    if (form) {
        form.reset();
        const btnSubmit = form.querySelector('[type=submit]');
        if (btnSubmit) btnSubmit.disabled = false;
    }
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
});

// Submit de formulario de creación → POST → inyección dinámica en DOM
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
        bootstrap.Modal.getInstance(modalEl)?.hide();
        if (data.advertencia) mostrarAdvertencia(data.advertencia.mensaje);
        await _insertarNuevoTab(nivel, data.id, parentId);
    } catch (err) {
        mostrarError('Error de red: ' + err.message);
        if (btnSubmit) btnSubmit.disabled = false;
    }
});


// ── Cancelar edición al cambiar de tab ────────────────────────────────────────

document.addEventListener('hide.bs.tab', (e) => {
    const panelId = e.target.dataset.bsTarget;
    if (!panelId) return;
    const panel = document.querySelector(panelId);
    if (!panel) return;
    panel.querySelectorAll('.card').forEach(card => {
        if (card.querySelector('[data-modo-editar]:not(.d-none)')) {
            const form = card.querySelector('form');
            if (form) form.reset();
            _toggleModoEditar(card, false);
        }
    });
});


// ── Toggle edición inline ─────────────────────────────────────────────────────

document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-editar-entidad')) {
        const card = e.target.closest('.card');
        if (card) _toggleModoEditar(card, true);
    }
    if (e.target.closest('.btn-cancelar-edicion')) {
        const card = e.target.closest('.card');
        if (card) {
            const form = card.querySelector('form');
            if (form) form.reset();
            _toggleModoEditar(card, false);
        }
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
        const card = form.closest('.card');
        _aplicarCambiosAVista(card);
        _toggleModoEditar(card, false);
        _actualizarTabIcon(nivel, entidadId, card);
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
            'EN_TRAMITE': ['bi bi-file-earmark-text',  'text-primary'],
            'RESUELTA':   ['bi bi-file-earmark-check', 'text-success'],
            'DESISTIDA':  ['bi bi-file-earmark-x',     'text-danger'],
            'ARCHIVADA':  ['bi bi-file-earmark',       'text-secondary'],
        };
        [icono, color] = map[est] || map['EN_TRAMITE'];
    } else if (nivel === 'tarea') {
        // Icono por tipo (semántico), color por estado
        const tipoCodigo = tabBtn.dataset.tipoCodigo || '';
        const tipoIconos = {
            'ANALISIS':      'bi bi-person-gear',
            'REDACTAR':      'bi bi-pencil',
            'FIRMAR':        'bi bi-pen',
            'NOTIFICAR':     'bi bi-send',
            'PUBLICAR':      'bi bi-megaphone',
            'ESPERAR_PLAZO': 'bi bi-hourglass-split',
            'INCORPORAR':    'bi bi-box-arrow-in-down',
        };
        icono = tipoIconos[tipoCodigo] || 'bi bi-square';
        if (fechaFinEl?.value)    color = 'text-success';
        else if (fechaInicioEl?.value) color = 'text-warning';
    } else {
        const tieneFin    = fechaFinEl?.value;
        const tieneInicio = fechaInicioEl?.value;
        const finIcons = { fase: 'bi bi-diagram-3',      tramite: 'bi bi-clipboard-check' };
        const curIcons = { fase: 'bi bi-diagram-3-fill', tramite: 'bi bi-clipboard-pulse' };
        const penIcons = { fase: 'bi bi-diagram-3',      tramite: 'bi bi-clipboard' };
        if (tieneFin) {
            icono = finIcons[nivel] || 'bi bi-file-earmark'; color = 'text-success';
        } else if (tieneInicio) {
            icono = curIcons[nivel] || 'bi bi-file-earmark'; color = 'text-warning';
        } else {
            icono = penIcons[nivel] || 'bi bi-file-earmark';
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

/** Localiza el tabList y tabContent del contenedor padre según nivel y parentId. */
function _encontrarContenedorTab(nivel, parentId) {
    const parentNivelMap = { solicitud: null, fase: 'solicitud', tramite: 'fase', tarea: 'tramite' };
    const parentNivel = parentNivelMap[nivel];
    const container = parentNivel
        ? document.getElementById(`panel-${parentNivel}-${parentId}`)
        : document.querySelector('.tabs-nivel-1');
    if (!container) return {};
    return {
        tabList:    container.querySelector('.tramitacion-tabs'),
        tabContent: container.querySelector('.tab-content'),
    };
}

/**
 * Hace fetch de la página, extrae el tab+panel del nuevo elemento
 * e los inyecta en el DOM sin recargar la página.
 */
async function _insertarNuevoTab(nivel, id, parentId) {
    const respHtml = await fetch(location.href);
    const html = await respHtml.text();
    const tempDoc = new DOMParser().parseFromString(html, 'text/html');

    const newLi    = tempDoc.getElementById(`tab-${nivel}-${id}`)?.closest('li');
    const newPanel = tempDoc.getElementById(`panel-${nivel}-${id}`);
    if (!newLi || !newPanel) { location.reload(); return; }

    // Quitar active/show: se activará manualmente
    newLi.querySelector('.nav-link')?.classList.remove('active');
    newPanel.classList.remove('active', 'show');

    const { tabList, tabContent } = _encontrarContenedorTab(nivel, parentId);
    if (!tabList || !tabContent) { location.reload(); return; }

    // Insertar antes del botón "+"
    const plusLi = tabList.querySelector('.btn-nueva-entidad')?.closest('li');
    tabList.insertBefore(document.adoptNode(newLi), plusLi || null);
    tabContent.appendChild(document.adoptNode(newPanel));

    // Activar el nuevo tab y desplazar hasta él
    const newBtn = document.getElementById(`tab-${nivel}-${id}`);
    if (newBtn) {
        new bootstrap.Tab(newBtn).show();
        newBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Re-inicializar tooltips en el nuevo panel
    document.getElementById(`panel-${nivel}-${id}`)
        ?.querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach(el => new bootstrap.Tooltip(el));
}

// Inicializar tooltips al cargar
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
});
