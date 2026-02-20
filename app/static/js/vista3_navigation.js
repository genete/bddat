/**
 * Vista 3 - Gestión de navegación jerárquica tipo stack
 * 
 * Stack de contextos:
 * - Nivel 0: Expediente (siempre visible)
 * - Nivel 1: Solicitudes (listado)
 * - Nivel 2: Solicitud específica
 * - Nivel 3: Fase específica
 * - Nivel 4: Trámite específico
 * - Nivel 5: Tarea específica (final, documentos sin drill-down)
 */

let navigationStack = [];
let expedienteId = null;

/**
 * Inicializa la vista con el expediente base
 */
function initVista3(expId) {
    expedienteId = expId;
    navigationStack = [{type: 'expediente', id: expId}];
}

/**
 * Expande el acordeón de solicitudes (primera interacción)
 */
function expandSolicitudes() {
    navigationStack = [
        {type: 'expediente', id: expedienteId},
        {type: 'solicitudes'}
    ];
    refreshView();
}

/**
 * Navega hacia abajo en la jerarquía (botón [...])
 */
function drillDown(type, id) {
    navigationStack.push({type: type, id: id});
    refreshView();
}

/**
 * Navega hacia arriba en la jerarquía (click en header acordeón)
 * @param {number} levelIndex - Índice del nivel al que volver
 */
function navigateToLevel(levelIndex) {
    // Cortar stack hasta el nivel indicado (inclusive)
    navigationStack = navigationStack.slice(0, levelIndex + 1);
    refreshView();
}

/**
 * Renderiza el breadcrumb clicable a partir del array de labels
 */
function renderBreadcrumb(items) {
    const list = document.getElementById('breadcrumb-list');
    if (!list) return;
    list.innerHTML = items.map((label, idx) => {
        if (idx === items.length - 1) {
            return `<li class="breadcrumb-item active" aria-current="page">${label}</li>`;
        }
        return `<li class="breadcrumb-item"><a href="#" onclick="navigateToLevel(${idx}); return false;">${label}</a></li>`;
    }).join('');
}

/**
 * Refresca la vista completa llamando al backend
 */
function refreshView() {
    const container = document.getElementById('vista3-container');

    // Fade out suave (sin borrar contenido)
    container.style.opacity = '0.5';
    container.style.transition = 'opacity 0.15s ease';

    fetch('/api/vista3/context', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({stack: navigationStack})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        // Actualizar contenido y fade in
        container.innerHTML = data.html;
        renderBreadcrumb(data.breadcrumb_items || [data.breadcrumb]);

        // Forzar reflow para que la transición funcione
        container.offsetHeight;
        container.style.opacity = '1';
    })
    .catch(error => {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>Error:</strong> No se pudo cargar el contenido. ${error.message}
            </div>
        `;
        container.style.opacity = '1';
    });
}
