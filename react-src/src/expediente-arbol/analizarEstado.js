// analizarEstado.js — El estado del análisis de una tarea ANALIZAR, compartido entre las piezas
// del inspector (#1043, ADR-053 §C).
//
// El inspector pinta el ANALIZAR en dos zonas del cuerpo: las tarjetas de datos (secciones, borrador
// de defectos o resultado; en lectura y en edición) y la acción de producir el diagnóstico (solo en
// edición). Las dos leen lo mismo, `GET …/tarea/<id>/analizar`, que solo exige poder ver el
// expediente; este store lo guarda para que la tarjeta lo cargue al montarse y la acción lo
// recargue tras producir, sin depender de que el inspector se vuelva a montar.
//
// `tareaId` dice de qué tarea es `payload`: al cambiar de tarea se descarta, pero al recargar la
// misma (tras una vinculación, un guardado o producir) se conserva y no parpadea.
import { create } from 'zustand'
import { getAnalizar } from './api.js'

export const useAnalisisTarea = create((set, get) => ({
  tareaId: null,
  payload: null,
  error: null,

  cargar: async (expedienteId, tareaId) => {
    if (get().tareaId !== tareaId) set({ tareaId, payload: null, error: null })
    try {
      const payload = await getAnalizar(expedienteId, tareaId)
      if (get().tareaId === tareaId) set({ payload, error: null })
    } catch (e) {
      if (get().tareaId === tareaId) {
        set({ error: (e && e.message) || 'No se pudo cargar el diagnóstico' })
      }
    }
  },
}))

// ¿Falta producir el diagnóstico de esta tarea? Lo usa el inspector para saber si pinta la zona de
// acciones propias.
export function useDiagnosticoPendiente(tareaId) {
  return useAnalisisTarea(
    (s) => s.tareaId === tareaId && !!s.payload && !s.payload.documento_producido,
  )
}
