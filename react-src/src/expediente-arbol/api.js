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

// Detalle lazy de un nodo para el inspector (§16). El endpoint backend aún NO
// existe (S1 entregó arbol + tipos-creables); se implementa en S3.
export function getNodo(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}`)
}

// Tipos de hijo creables bajo un nodo: despensa + menú contextual (§16/§8).
export function getTiposCreables(expedienteId, tipo, nodoId) {
  return api.get(`/api/expedientes/${expedienteId}/nodo/${tipo}/${nodoId}/tipos-creables`)
}
