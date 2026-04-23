// v3-breadcrumbs-crear.js
// Modales de creación de entidades hijas en Vista 3 Breadcrumbs — issue #165
//
// Convenciones en el HTML:
//   - .form-nueva-bc [data-url]  → formulario dentro del modal con URL del endpoint POST
//   - .alert-crear               → div de error dentro del modal body

'use strict';

// ── Helper toast (mismo patrón que v3-breadcrumbs-acciones.js) ─────────────

function _toast_crear(mensaje, tipo) {
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
    el.setAttribute('data-bs-delay', '6000');
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

// ── Submit de formularios de creación ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.form-nueva-bc').forEach(function (form) {
        const modal_el   = form.closest('.modal');
        const alert_el   = form.querySelector('.alert-crear');
        const submit_btn = form.querySelector('[type="submit"]');

        // Limpiar errores y restablecer el form al abrir el modal
        if (modal_el) {
            modal_el.addEventListener('show.bs.modal', function () {
                form.reset();
                if (alert_el) alert_el.classList.add('d-none');
                if (submit_btn) {
                    submit_btn.disabled = false;
                    submit_btn.innerHTML = '<i class="fa-solid fa-plus me-1"></i> Crear';
                }
            });
        }

        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const url = form.dataset.url;
            if (!url) return;

            // Validar campos EntradaFecha (hidden con clase ef-hidden)
            const campos_ef = form.querySelectorAll('input.ef-hidden');
            for (const campo of campos_ef) {
                if (!campo.value) {
                    if (alert_el) {
                        alert_el.textContent = 'La fecha es obligatoria.';
                        alert_el.classList.remove('d-none');
                    }
                    return;
                }
            }

            // Deshabilitar submit para evitar doble envío
            if (submit_btn) {
                submit_btn.disabled = true;
                submit_btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Creando…';
            }
            if (alert_el) alert_el.classList.add('d-none');

            try {
                const resp = await fetch(url, { method: 'POST', body: new FormData(form) });
                const json = await resp.json();

                if (!json.ok) {
                    // Mostrar error dentro del modal (sin cerrarlo)
                    if (alert_el) {
                        alert_el.innerHTML = json.error + (json.url_norma ? ` (<a href="${json.url_norma}" target="_blank">ver norma</a>)` : '');
                        alert_el.classList.remove('d-none');
                    }
                    if (submit_btn) {
                        submit_btn.disabled = false;
                        submit_btn.innerHTML = '<i class="fa-solid fa-plus me-1"></i> Crear';
                    }
                } else {
                    // Cerrar modal + toast + recargar listado
                    if (modal_el) bootstrap.Modal.getInstance(modal_el)?.hide();

                    if (json.advertencia) {
                        _toast_crear(json.advertencia.mensaje, 'warning');
                    } else {
                        _toast_crear('Elemento creado correctamente.', 'success');
                    }

                    window.location.reload();
                }
            } catch (_e) {
                if (alert_el) {
                    alert_el.textContent = 'Error de comunicación con el servidor.';
                    alert_el.classList.remove('d-none');
                }
                if (submit_btn) {
                    submit_btn.disabled = false;
                    submit_btn.innerHTML = '<i class="fa-solid fa-plus me-1"></i> Crear';
                }
            }
        });
    });

});
