// API de la isla del árbol, sobre shared/api.js (ADR-016 §16).
//
// OJO: la ruta del endpoint es PLURAL (/api/expedientes/...), confirmado en
// app/routes/api_expedientes.py:451. El plan/ADR la citan a veces en singular.
import { api } from '../shared/api.js'

// S2 (lectura): árbol completo de dominio (expediente → solicitudes → … → tareas).
export function getArbol(expedienteId) {
  return api.get(`/api/expedientes/${expedienteId}/arbol`)
}

// --- Esqueletos S3 (no usados en S2) ------------------------------------------

// Detalle lazy de un nodo para el inspector (§16). `opts` permite pasar { signal }
// para cancelar la petición anterior al cambiar de selección (AbortController).
export function getNodo(expedienteId, tipo, nodoId, opts) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`, opts)
}

// Tipos de hijo creables bajo un nodo: despensa + menú contextual (§16/§8).
export function getTiposCreables(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}/tipos-creables`)
}

// Esquema editable del nodo (editor del inspector, S3b-1).
export function getEditable(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}/editable`)
}

// Editar campos de un nodo (PATCH, S3b-1).
export function patchNodo(expedienteId, tipo, nodoId, body) {
  return api.patch(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`, body)
}

// Crear hijo bajo un nodo (POST, S3b-2). Respuesta: {ok, ids:[...], advertencia?}.
export function postHijo(expedienteId, padreTipo, padreId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/${padreTipo}/${padreId}/hijos`, body)
}

// Pool de documentos del expediente (GET, S3b-3). Respuesta: {documentos:[{id,nombre,tipo_doc,fecha}]}.
export function getPool(expedienteId) {
  return api.get(`/api/expedientes/${expedienteId}/pool`)
}

// Borrar un nodo (DELETE, S3b-4). Respuesta éxito: {ok:true} 200. Motor: {motivo,url_norma} 422.
export function deleteNodo(expedienteId, tipo, nodoId) {
  return api.delete(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`)
}

// Contenedor de la tarea ANALIZAR (#442). Respuesta: {resultado, documento_producido,
// secciones_extendidas, defectos_consolidado, completo}.
export function getAnalizar(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`)
}

// Produce el documento de diagnóstico (POST, #442/#677). body: {resultado?, justificacion?}
// — `resultado` se ignora en ANALIZAR extendido (derivado server-side, ADR-033 §3).
// Respuesta éxito: {ok:true, documento:{id,nombre,tipo_doc,fecha}} 200.
// Bloqueo (ya producido / incompleto sin justificación): {error, motivo?, defectos_consolidado?} 422.
export function postAnalizar(expedienteId, tareaId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`, body)
}

// Revierte el diagnóstico producido (DELETE, #678, ADR-033 §5): vuelve a
// "Borrador defectos". Respuesta éxito: {ok:true} 200.
// Bloqueo (422): {error, motivo, puede_escapar:false} — sin producido, o
// consumido por otra tarea (puerta cerrada, no forzable).
export function revertirDiagnostico(expedienteId, tareaId) {
  return api.delete(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`)
}

// Guarda solo `notas` de una tarea (PATCH, #677 ADR-033 §7) — fuera del ciclo
// borrador/Guardar general (ver AnalizarEditor.jsx, BloqueNotas). Respuesta: {ok:true, notas}.
export function guardarNotas(expedienteId, tareaId, notas) {
  return api.patch(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/notas`, { notas })
}

// Check documental (#495): vincula/desvincula un documento del pool a un requisito.
// Respuesta ambas: {ok:true, checklist_documental:[...]}.
export function vincularRequisitoDocumental(expedienteId, tareaId, requisitoId, documentoId) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requisitos-documentales/${requisitoId}`,
    { documento_id: documentoId },
  )
}

export function desvincularRequisitoDocumental(expedienteId, tareaId, requisitoId) {
  return api.delete(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requisitos-documentales/${requisitoId}`,
  )
}

// Check técnico (#581): registra el veredicto (texto + cubierto) de un ítem técnico.
// Respuesta: {ok:true, checklist_tecnico:[...]}.
export function guardarCoberturaTecnica(expedienteId, tareaId, itemTecnicoId, body) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/coberturas-tecnicas/${itemTecnicoId}`,
    body,
  )
}

// Selector de requerimientos (#440): estado inicial del panel shuttle (catálogo +
// selección). La selección es por solicitud (#679, ADR-033 §7) — continua entre
// vueltas de subsanación, aunque la URL cuelgue de una tarea concreta.
export function getRequerimientos(expedienteId, tareaId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos`)
}

// Sustituye la lista completa de requerimientos_tarea de la solicitud en una sola llamada.
// body: {items: [{catalogo_requerimientos_id, texto_libre, resuelto}, ...]}.
export function postRequerimientos(expedienteId, tareaId, items) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos`, { items })
}

// Crea una entrada nueva en catalogo_requerimientos desde el shuttle ("Guardar en catálogo").
export function crearRequerimientoCatalogo(expedienteId, tareaId, texto, categoria) {
  return api.post(
    `/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/requerimientos/catalogo`,
    { texto, categoria },
  )
}

// Generación de escritos (#167/#608) — Blueprint aparte (/api/escritos), no bajo
// /api/expedientes. Plantillas ESFTT compatibles con la tarea. Respuesta:
// {ok, plantillas:[{id, nombre, variante, descripcion, especificidad}]}.
export function getEscritosPlantillas(tareaId) {
  return api.get(`/api/escritos/plantillas?tarea_id=${tareaId}`)
}

// Preview de campos + nombre/ruta propuestos antes de generar.
// Respuesta: {ok, campos, nombre_propuesto, ruta_destino}.
export function getEscritosPreview(plantillaId, tareaId) {
  return api.get(`/api/escritos/preview?plantilla_id=${plantillaId}&tarea_id=${tareaId}`)
}

// Genera el .docx y lo guarda en disco + pool (#608: asignar_doc_producido siempre
// false — el .docx es un auxiliar de trabajo, no dispara cambio de estado de la
// tarea; el ciclo BORRADOR_FIRMA/firmado se gestiona aparte vía Despensa).
// Respuesta: {ok, nombre_fichero, ruta, doc_id, uri_explorador}.
export function postEscritosGenerar(plantillaId, tareaId, nombreFichero) {
  return api.post('/api/escritos/generar', {
    plantilla_id: plantillaId,
    tarea_id: tareaId,
    nombre_fichero: nombreFichero,
    registrar_pool: true,
    asignar_doc_producido: false,
  })
}
