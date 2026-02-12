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
 * Refresca la vista completa llamando al backend
 */
function refreshView() {
    const container = document.getElementById('vista3-container');
    const breadcrumb = document.getElementById('breadcrumb');
    
    // Mostrar loading
    container.innerHTML = '<div class="text-center p-5"><div class="spinner-border" role="status"><span class="visually-hidden">Cargando...</span></div></div>';
    
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
        container.innerHTML = data.html;
        breadcrumb.textContent = data.breadcrumb;
    })
    .catch(error => {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>Error:</strong> No se pudo cargar el contenido. ${error.message}
            </div>
        `;
    });
}
