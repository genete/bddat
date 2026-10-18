// destinatarioEstado.js — A quién va el escrito de un ELABORAR, compartido entre las piezas del
// inspector (#929, A2; ADR-051 §H, §L; #1043, ADR-053 §C).
//
// El destinatario se pinta en la zona de datos (tarjeta, en lectura y en edición) y condiciona la
// acción de generar el escrito (zona de acciones, solo edición): el generador reinicia su vista previa
// cuando cambia el destinatario, porque lleva `destinatario_*`, y recarga el estado cuando el servidor
// se niega a generar por no tenerlo. Las dos leen `GET …/tramite/<id>/destinatario`, que solo exige
// poder ver el expediente, y el store las mantiene de acuerdo sin depender de que el inspector se vuelva
// a montar.
//
// `tramiteId` dice de qué trámite es `d`: al cambiar de trámite se descarta, pero al recargar el mismo
// (tras elegir otro destinatario y refrescar el árbol) se conserva y no parpadea.
import { create } from 'zustand'
import { getDestinatarioTramite, putDestinatarioTramite } from './api.js'
import { showToast } from '../shared/ui/toast.js'

export const useDestinatarioTramite = create((set, get) => ({
  tramiteId: null,
  d: null,
  error: null,
  enviando: false,
  // Sube cuando cambia el destinatario (o falla un generar por no tenerlo): el generador se remonta.
  version: 0,

  cargar: async (expedienteId, tramiteId) => {
    if (get().tramiteId !== tramiteId) set({ tramiteId, d: null, error: null, enviando: false })
    try {
      const d = await getDestinatarioTramite(expedienteId, tramiteId)
      if (get().tramiteId === tramiteId) set({ d, error: null })
    } catch (e) {
      if (get().tramiteId === tramiteId) {
        set({ error: (e && e.message) || 'No se pudo cargar el destinatario' })
      }
    }
  },

  // 422 `elegir_destinatario` al generar: el destinatario pudo cambiar desde que se pintó.
  recargarTrasFalta: async (expedienteId, tramiteId) => {
    await get().cargar(expedienteId, tramiteId)
    set((s) => ({ version: s.version + 1 }))
  },

  // Guarda de inmediato (PUT), fuera del borrador del marco: viene de #929 zona A y #1055 lo deja
  // así (el generador de escritos lo necesita guardado dentro de la misma edición).
  elegir: async (expedienteId, tramiteId, entidadId, refrescarArbol) => {
    set({ enviando: true, error: null })
    try {
      const data = await putDestinatarioTramite(expedienteId, tramiteId, { entidad_id: entidadId })
      if (get().tramiteId === tramiteId) set({ d: data })
      showToast('Destinatario del trámite guardado', 'success')
      set((s) => ({ version: s.version + 1 }))
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      set({
        error: (e.payload && (e.payload.motivo || e.payload.error)) || e.message
          || 'No se pudo guardar el destinatario',
      })
    } finally {
      set({ enviando: false })
    }
  },
}))
