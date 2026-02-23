/**
 * acordeon_lazy.js — Componente genérico de acordeón con lazy loading.
 *
 * Lee toda la configuración de atributos data-* del HTML.
 * No conoce el modelo SFTT; válido para cualquier jerarquía.
 *
 * Uso en templates:
 *   <div id="mi-container" data-expediente-id="{{ expediente.id }}" class="accordion vista3-acordeon">
 *     <div class="accordion-item" data-endpoint="/api/..." data-loaded="false">
 *       ...
 *       <div class="hijos-container accordion vista3-acordeon"></div>
 *     </div>
 *   </div>
 *   <script>
 *     document.addEventListener('DOMContentLoaded', function() {
 *       initAcordeonLazy('mi-container');
 *     });
 *   </script>
 */

// Escucha global: show.bs.collapse bubblea hasta document
document.addEventListener('show.bs.collapse', function (e) {
    const item = e.target.closest('[data-endpoint]');
    if (!item || item.dataset.loaded !== 'false') return;

    // Marcar como cargado antes del fetch para evitar doble petición
    item.dataset.loaded = 'true';

    const container = item.querySelector('.hijos-container');
    if (container) {
        cargarHijos(item.dataset.endpoint, container);
    }
});

/**
 * Carga hijos AJAX e inyecta el HTML en el contenedor.
 * @param {string} endpoint - URL que devuelve {html, count}
 * @param {HTMLElement} container - Elemento .hijos-container donde inyectar
 */
function cargarHijos(endpoint, container) {
    container.innerHTML =
        '<div class="text-center py-3">' +
        '<div class="spinner-border spinner-border-sm text-success" role="status">' +
        '<span class="visually-hidden">Cargando...</span>' +
        '</div></div>';

    fetch(endpoint, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (data) {
            container.innerHTML = data.html || '';
            // Inicializar tooltips Bootstrap si los hubiera en el HTML inyectado
            container.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
                new bootstrap.Tooltip(el);
            });
        })
        .catch(function (err) {
            console.error('[acordeon_lazy] Error cargando ' + endpoint + ':', err);
            container.innerHTML =
                '<div class="alert alert-danger m-2 py-1 px-2">' +
                '<small><i class="fas fa-exclamation-triangle me-1"></i>Error al cargar. ' +
                '<a href="#" onclick="location.reload()">Recargar página</a></small></div>';
        });
}

/**
 * Llama al endpoint /arbol, inyecta el árbol completo y expande todos los acordeones.
 * @param {HTMLElement} rootContainer - Elemento con data-expediente-id
 */
function expandirTodo(rootContainer) {
    const expId = rootContainer.dataset.expedienteId;
    if (!expId) {
        console.warn('[acordeon_lazy] expandirTodo: falta data-expediente-id en el container');
        return;
    }

    rootContainer.style.opacity = '0.5';
    rootContainer.style.transition = 'opacity 0.2s';

    fetch('/api/vista3/expediente/' + expId + '/arbol', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function (data) {
            rootContainer.innerHTML = data.html || '';
            rootContainer.style.opacity = '1';

            // Expandir todos los acordeones tras un pequeño retraso para asegurar el renderizado
            setTimeout(function () {
                rootContainer.querySelectorAll('.accordion-collapse').forEach(function (el) {
                    var collapse = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
                    collapse.show();
                });
            }, 50);
        })
        .catch(function (err) {
            console.error('[acordeon_lazy] Error en expandirTodo:', err);
            rootContainer.style.opacity = '1';
        });
}

/**
 * Colapsa todos los acordeones del container sin descargar los datos.
 * @param {HTMLElement} rootContainer
 */
function colapsarTodo(rootContainer) {
    rootContainer.querySelectorAll('.accordion-collapse.show').forEach(function (el) {
        var collapse = bootstrap.Collapse.getInstance(el);
        if (collapse) collapse.hide();
    });
}

/**
 * Registra los botones de expandir/colapsar todo.
 * @param {string} containerId - ID del elemento raíz del acordeón
 */
function initAcordeonLazy(containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn('[acordeon_lazy] initAcordeonLazy: no se encontró #' + containerId);
        return;
    }

    const btnExpandir = document.getElementById('btn-expandir-todo');
    if (btnExpandir) {
        btnExpandir.addEventListener('click', function () { expandirTodo(container); });
    }

    const btnColapsar = document.getElementById('btn-colapsar-todo');
    if (btnColapsar) {
        btnColapsar.addEventListener('click', function () { colapsarTodo(container); });
    }
}
