// v3-breadcrumbs-acciones.js
// Menú [Acciones ▾] en Vista 3 Breadcrumbs — issue #164
//
// Convenciones en el HTML:
//   - [data-accion]      → enlace del dropdown con la acción ('iniciar', 'finalizar', 'borrar')
//   - [data-url]         → URL del endpoint POST a llamar
//   - [data-redirect]    → URL de redirección tras BORRAR (URL del nivel padre)

'use strict';

// ── Helper toast (mismo patrón que v3-tabs-main.js) ────────────────────────

function _toast_accion(mensaje, tipo) {
    const contenedor = document.querySelector('.toast-container');
    if (!contenedor) { alert(mensaje); return; }

    const iconos = {
        'success': 'fa-check-circle',
        'danger':  'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
    };
    const icono = iconos[tipo] || 'fa-info-circle';

    const el = document.createElement('div');
    el.className = `toast toast-${tipo}`;
    el.setAttribute('role', 'alert');
    el.setAttribute('data-bs-autohide', 'true');
    el.setAttribute('data-bs-delay', '8000');
    el.innerHTML = `
        <div class="d-flex align-items-center p-3">
            <div class="flex-grow-1">
                <i class="fas ${icono} me-2"></i>${mensaje}
            </div>
            <button type="button" class="btn-close ms-3"
                    data-bs-dismiss="toast" aria-label="Cerrar"></button>
        </div>`;
    contenedor.appendChild(el);
    new bootstrap.Toast(el).show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ── Handler global de clics en acciones contextuales ───────────────────────

document.addEventListener('click', async function (e) {
    const item = e.target.closest('[data-accion]');
    if (!item) return;
    e.preventDefault();

    const accion   = item.dataset.accion;
    const url      = item.dataset.url;
    const redirect = item.dataset.redirect;

    // Confirmar antes de borrar
    if (accion === 'borrar') {
        if (!confirm('¿Confirmar borrado? Esta acción no se puede deshacer.')) return;
    }

    // Deshabilitar el toggle del dropdown mientras se procesa
    const toggle = item.closest('.dropdown')?.querySelector('[data-bs-toggle="dropdown"]');
    if (toggle) toggle.disabled = true;

    try {
        const resp = await fetch(url, { method: 'POST' });
        const json = await resp.json();

        if (!json.ok) {
            // Motor bloqueó la acción o error de servidor
            _toast_accion(
                json.error + (json.norma ? ` — ${json.norma}` : ''),
                'danger'
            );
        } else {
            const mensajes_exito = {
                'iniciar':   'Elemento iniciado correctamente.',
                'finalizar': 'Elemento finalizado correctamente.',
                'borrar':    'Elemento eliminado correctamente.',
            };
            const msg_ok = mensajes_exito[accion] || 'Acción realizada.';

            if (json.nivel === 'ADVERTIR') {
                // El motor permite con advertencia: mostrar warning y ejecutar
                _toast_accion(
                    json.mensaje + (json.norma ? ` — ${json.norma}` : ''),
                    'warning'
                );
                setTimeout(() => _navegar_tras_accion(accion, redirect), 1500);
            } else {
                // Permitido sin advertencia
                _toast_accion(msg_ok, 'success');
                setTimeout(() => _navegar_tras_accion(accion, redirect), 800);
            }
        }
    } catch (_e) {
        _toast_accion('Error de comunicación con el servidor.', 'danger');
    } finally {
        if (toggle) toggle.disabled = false;
    }
});

function _navegar_tras_accion(accion, redirect) {
    if (accion === 'borrar' && redirect) {
        window.location.href = redirect;
    } else {
        window.location.reload();
    }
}
