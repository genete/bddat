/**
 * VISTA V3 - ACORDEÓN TRAMITACIÓN
 * 
 * PROPÓSITO:
 *   Renderizar acordeones jerárquicos desde API /api/expedientes/<id>/jerarquia
 *   Fase 2: Expediente + Proyecto (panel fijo) + Solicitudes + Fases (acordeón)
 * 
 * ESTRATEGIA DE CARGA:
 *   - Carga completa (no lazy): 1 petición HTTP al cargar página
 *   - Renderizado inmediato de toda la jerarquía
 *   - Bootstrap 5 Accordion maneja expand/collapse
 * 
 * ESTRUCTURA HTML GENERADA:
 *   <div class="panel-contexto-fijo">
 *     - Expediente (AT-X, titular, responsable)
 *     - Proyecto (título, finalidad, emplazamiento)
 *   </div>
 *   <div class="accordion" id="accordionSolicitudes">
 *     - Solicitud 1 (AAP+AAC)
 *       - Fase 1 (Registro)
 *       - Fase 2 (Admisibilidad)
 *     - Solicitud 2 (DUP)
 *   </div>
 * 
 * VERSIÓN: 1.0
 * FECHA: 2026-02-12
 */

'use strict';

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const expediente_id = getExpedienteIdFromURL();
    
    if (!expediente_id) {
        console.error('No se pudo obtener el ID del expediente de la URL');
        mostrarError('Error: No se pudo cargar el expediente');
        return;
    }
    
    cargarJerarquiaExpediente(expediente_id);
});

// =============================================================================
// OBTENER ID DEL EXPEDIENTE DESDE URL
// =============================================================================

function getExpedienteIdFromURL() {
    // URL esperada: /tramitacion/<id>
    const path = window.location.pathname;
    const match = path.match(/\/tramitacion\/(\d+)/);
    return match ? parseInt(match[1]) : null;
}

// =============================================================================
// CARGAR JERARQUÍA COMPLETA DEL EXPEDIENTE
// =============================================================================

function cargarJerarquiaExpediente(expediente_id) {
    mostrarCargando();
    
    fetch(`/api/expedientes/${expediente_id}/jerarquia`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Expediente no encontrado');
                } else if (response.status === 401) {
                    throw new Error('No autorizado. Por favor, inicia sesión.');
                } else {
                    throw new Error(`Error del servidor: ${response.status}`);
                }
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos:', data);
            renderizarVista(data);
            ocultarCargando();
        })
        .catch(error => {
            console.error('Error al cargar jerarquía:', error);
            mostrarError(`Error: ${error.message}`);
            ocultarCargando();
        });
}

// =============================================================================
// RENDERIZAR VISTA COMPLETA
// =============================================================================

function renderizarVista(data) {
    renderizarPanelContexto(data.expediente, data.proyecto);
    renderizarAcordeonSolicitudes(data.solicitudes);
}

// =============================================================================
// RENDERIZAR PANEL CONTEXTO FIJO (EXPEDIENTE + PROYECTO)
// =============================================================================

function renderizarPanelContexto(expediente, proyecto) {
    const container = document.getElementById('panel-contexto-expediente');
    if (!container) {
        console.error('Contenedor #panel-contexto-expediente no encontrado');
        return;
    }
    
    // Construir HTML del panel
    let html = '<div class="panel-contexto-fijo">';
    
    // EXPEDIENTE
    html += '<div class="expediente-info">';
    html += `<h2 class="mb-2">🗂️ Expediente ${expediente.codigo}</h2>`;
    html += '<div class="row">';
    html += '<div class="col-md-6">';
    
    if (expediente.titular) {
        html += `<p class="mb-1"><strong>Titular:</strong> ${expediente.titular.nombre}`;
        if (expediente.titular.nif) {
            html += ` (${expediente.titular.nif})`;
        }
        html += '</p>';
    }
    
    if (expediente.responsable) {
        html += `<p class="mb-1"><strong>Responsable:</strong> ${expediente.responsable.siglas} - ${expediente.responsable.nombre_completo}</p>`;
    }
    
    html += '</div>';
    html += '<div class="col-md-6 text-md-end">';
    html += '<button class="btn btn-sm btn-outline-primary me-1" title="Editar expediente">✏️</button>';
    html += '<button class="btn btn-sm btn-outline-success me-1" title="Añadir solicitud">➕</button>';
    html += '<button class="btn btn-sm btn-outline-info" title="Ver detalle">...</button>';
    html += '</div>';
    html += '</div>'; // row
    html += '</div>'; // expediente-info
    
    // PROYECTO
    if (proyecto) {
        html += '<div class="proyecto-info mt-3">';
        html += `<h3 class="mb-2 h5">🏭 Proyecto: ${proyecto.titulo || 'Sin título'}</h3>`;
        html += '<div class="row">';
        html += '<div class="col-md-8">';
        
        if (proyecto.finalidad) {
            html += `<p class="mb-1 small"><strong>Finalidad:</strong> ${proyecto.finalidad}</p>`;
        }
        
        if (proyecto.emplazamiento) {
            html += `<p class="mb-1 small"><strong>Emplazamiento:</strong> ${proyecto.emplazamiento}</p>`;
        }
        
        if (proyecto.tipo_ia) {
            html += `<p class="mb-1 small"><strong>Instrumento Ambiental:</strong> ${proyecto.tipo_ia.siglas} - ${proyecto.tipo_ia.descripcion}</p>`;
        }
        
        html += '</div>';
        html += '<div class="col-md-4 text-md-end">';
        html += '<button class="btn btn-sm btn-outline-primary me-1" title="Editar proyecto">✏️</button>';
        html += '<button class="btn btn-sm btn-outline-info" title="Ver detalle">...</button>';
        html += '</div>';
        html += '</div>'; // row
        html += '</div>'; // proyecto-info
    }
    
    html += '</div>'; // panel-contexto-fijo
    
    container.innerHTML = html;
}

// =============================================================================
// RENDERIZAR ACORDEÓN DE SOLICITUDES
// =============================================================================

function renderizarAcordeonSolicitudes(solicitudes) {
    const container = document.getElementById('acordeon-solicitudes');
    if (!container) {
        console.error('Contenedor #acordeon-solicitudes no encontrado');
        return;
    }
    
    if (!solicitudes || solicitudes.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No hay solicitudes en este expediente.</div>';
        return;
    }
    
    let html = '<div class="accordion" id="accordionSolicitudes">';
    
    solicitudes.forEach((solicitud, index) => {
        const solicitud_id = `solicitud-${solicitud.id}`;
        const es_primera = index === 0;
        
        html += '<div class="accordion-item">';
        
        // CABECERA SOLICITUD
        html += `<h2 class="accordion-header" id="heading-${solicitud_id}">`;
        html += `<button class="accordion-button ${es_primera ? '' : 'collapsed'}" type="button" `;
        html += `data-bs-toggle="collapse" data-bs-target="#collapse-${solicitud_id}" `;
        html += `aria-expanded="${es_primera}" aria-controls="collapse-${solicitud_id}">`;
        
        // Columnas personalizadas en cabecera
        html += '<div class="d-flex justify-content-between w-100 align-items-center">';
        html += `<span class="fw-bold">${solicitud.codigo}: ${solicitud.tipos}</span>`;
        html += `<span class="badge bg-secondary ms-2">Fases: ${solicitud.num_fases}</span>`;
        
        // Badge estado
        let badge_class = 'bg-info';
        if (solicitud.estado === 'RESUELTA') badge_class = 'bg-success';
        if (solicitud.estado === 'EN_TRAMITE') badge_class = 'bg-primary';
        if (solicitud.estado === 'ARCHIVADA') badge_class = 'bg-secondary';
        
        html += `<span class="badge ${badge_class} ms-2">${solicitud.estado}</span>`;
        html += '</div>';
        html += '</button>';
        html += '</h2>';
        
        // CUERPO SOLICITUD (colapsable)
        html += `<div id="collapse-${solicitud_id}" `;
        html += `class="accordion-collapse collapse ${es_primera ? 'show' : ''}" `;
        html += `aria-labelledby="heading-${solicitud_id}" data-bs-parent="#accordionSolicitudes">`;
        html += '<div class="accordion-body">';
        
        // Detalles de la solicitud
        html += '<div class="detalle-solicitud mb-3">';
        html += '<div class="row">';
        html += '<div class="col-md-8">';
        
        if (solicitud.fecha_solicitud) {
            html += `<p class="mb-1"><strong>Fecha solicitud:</strong> ${formatearFecha(solicitud.fecha_solicitud)}</p>`;
        }
        
        if (solicitud.fecha_fin) {
            html += `<p class="mb-1"><strong>Fecha fin:</strong> ${formatearFecha(solicitud.fecha_fin)}</p>`;
        }
        
        html += '</div>';
        html += '<div class="col-md-4 text-md-end">';
        html += '<button class="btn btn-sm btn-outline-primary me-1" title="Editar solicitud">✏️</button>';
        html += '<button class="btn btn-sm btn-outline-success me-1" title="Añadir fase">➕</button>';
        html += '<button class="btn btn-sm btn-outline-info" title="Ver detalle">...</button>';
        html += '</div>';
        html += '</div>'; // row
        html += '</div>'; // detalle-solicitud
        
        // ACORDEÓN ANIDADO DE FASES
        if (solicitud.fases && solicitud.fases.length > 0) {
            html += renderizarAcordeonFases(solicitud.fases, solicitud.id);
        } else {
            html += '<div class="alert alert-secondary small">No hay fases en esta solicitud.</div>';
        }
        
        html += '</div>'; // accordion-body
        html += '</div>'; // collapse
        html += '</div>'; // accordion-item
    });
    
    html += '</div>'; // accordion
    
    container.innerHTML = html;
}

// =============================================================================
// RENDERIZAR ACORDEÓN ANIDADO DE FASES
// =============================================================================

function renderizarAcordeonFases(fases, solicitud_id) {
    const accordion_id = `accordionFases-${solicitud_id}`;
    
    let html = `<div class="accordion accordion-anidado" id="${accordion_id}">`;
    
    fases.forEach((fase, index) => {
        const fase_id = `fase-${fase.id}`;
        const es_primera = index === 0;
        
        html += '<div class="accordion-item">';
        
        // CABECERA FASE
        html += `<h3 class="accordion-header" id="heading-${fase_id}">`;
        html += `<button class="accordion-button ${es_primera ? '' : 'collapsed'}" type="button" `;
        html += `data-bs-toggle="collapse" data-bs-target="#collapse-${fase_id}" `;
        html += `aria-expanded="${es_primera}" aria-controls="collapse-${fase_id}">`;
        
        // Columnas personalizadas
        html += '<div class="d-flex justify-content-between w-100 align-items-center">';
        html += `<span><strong>${fase.codigo}</strong>: ${fase.nombre}</span>`;
        
        // Badge estado fase
        const badge_fase = fase.estado === 'completada' ? 'bg-success' : 'bg-warning text-dark';
        const texto_estado = fase.estado === 'completada' ? '✓ Completada' : '🔄 En curso';
        html += `<span class="badge ${badge_fase} ms-2">${texto_estado}</span>`;
        html += '</div>';
        
        html += '</button>';
        html += '</h3>';
        
        // CUERPO FASE
        html += `<div id="collapse-${fase_id}" `;
        html += `class="accordion-collapse collapse ${es_primera ? 'show' : ''}" `;
        html += `aria-labelledby="heading-${fase_id}" data-bs-parent="#${accordion_id}">`;
        html += '<div class="accordion-body">';
        
        // Detalles de la fase
        if (fase.fecha_inicio) {
            html += `<p class="mb-1 small"><strong>Inicio:</strong> ${formatearFecha(fase.fecha_inicio)}</p>`;
        }
        
        if (fase.fecha_fin) {
            html += `<p class="mb-1 small"><strong>Fin:</strong> ${formatearFecha(fase.fecha_fin)}</p>`;
        }
        
        if (fase.observaciones) {
            html += `<p class="mb-1 small"><strong>Observaciones:</strong> ${fase.observaciones}</p>`;
        }
        
        html += '<div class="mt-2">';
        html += '<button class="btn btn-sm btn-outline-primary me-1" title="Editar fase">✏️</button>';
        html += '<button class="btn btn-sm btn-outline-info" title="Ver detalle">...</button>';
        html += '</div>';
        
        html += '</div>'; // accordion-body
        html += '</div>'; // collapse
        html += '</div>'; // accordion-item
    });
    
    html += '</div>'; // accordion
    
    return html;
}

// =============================================================================
// UTILIDADES
// =============================================================================

function formatearFecha(fecha_iso) {
    if (!fecha_iso) return 'N/A';
    
    const fecha = new Date(fecha_iso);
    const dia = String(fecha.getDate()).padStart(2, '0');
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const anio = fecha.getFullYear();
    
    return `${dia}/${mes}/${anio}`;
}

function mostrarCargando() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        loading.style.display = 'block';
    }
}

function ocultarCargando() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        loading.style.display = 'none';
    }
}

function mostrarError(mensaje) {
    const container = document.getElementById('acordeon-solicitudes');
    if (container) {
        container.innerHTML = `<div class="alert alert-danger">${mensaje}</div>`;
    }
}
