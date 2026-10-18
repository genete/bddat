// notificarEstado.js — El payload de una tarea NOTIFICAR, compartido entre sus tarjetas (#657/#658,
// #929; #1043, ADR-053 §C).
//
// Las tarjetas de la NOTIFICAR (destinatario, registro, justificantes previos y el aviso al
// solicitante) pintan lo mismo, `GET …/tarea/<id>/notificar`, que solo exige poder ver el
// expediente. Cada escritura (PATCH del registro, PUT del destinatario) devuelve el payload nuevo
// con la misma forma: se mete aquí con `poner` y la pantalla queda como la dice el servidor, sin
// recargar.
//
// `tareaId` dice de qué tarea es `payload`: al cambiar de tarea se descarta, pero al recargar la
// misma se conserva y no parpadea.
import { create } from 'zustand'
import { getNotificar } from './api.js'

export const useNotificarTarea = create((set, get) => ({
  tareaId: null,
  payload: null,
  error: null,

  cargar: async (expedienteId, tareaId) => {
    if (get().tareaId !== tareaId) set({ tareaId, payload: null, error: null })
    try {
      const payload = await getNotificar(expedienteId, tareaId)
      if (get().tareaId === tareaId) set({ payload, error: null })
    } catch (e) {
      if (get().tareaId === tareaId) {
        set({ error: (e && e.message) || 'No se pudo cargar la notificación' })
      }
    }
  },

  poner: (tareaId, payload) => {
    if (get().tareaId === tareaId) set({ payload, error: null })
  },
}))
