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

// Produce el documento de diagnóstico (POST, #442). body: {resultado, justificacion?}.
// Respuesta éxito: {ok:true, documento:{id,nombre,tipo_doc,fecha}} 200.
// Bloqueo (ya producido / incompleto sin justificación): {error, motivo?, defectos_consolidado?} 422.
export function postAnalizar(expedienteId, tareaId, body) {
  return api.post(`/api/expedientes/${expedienteId}/nodo/tarea/${tareaId}/analizar`, body)
}
