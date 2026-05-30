// Store Zustand de la isla del árbol (#500, ADR-016).
//
// S2 (lectura): estado servidor (árbol de /arbol) + estado UI mínimo
// (selección única, toggle "Colapsar finalizados").
// S3 añadirá: modoEdicion, lock, despensa, colapsos manuales por nivel.
import { create } from 'zustand'
import { getArbol } from './api.js'

export const useArbolStore = create((set) => ({
  // --- estado servidor ---
  arbol: null,
  cargando: false,
  error: null,

  // --- estado UI ---
  seleccion: null,           // { tipo, id } | null  (ADR §3, selección única)
  colapsarFinalizados: false, // toggle de viewbar (ADR §11)

  cargar: async (expedienteId) => {
    set({ cargando: true, error: null })
    try {
      const arbol = await getArbol(expedienteId)
      set({ arbol, cargando: false })
    } catch (e) {
      set({ error: e, cargando: false })
    }
  },

  seleccionar: (sel) => set({ seleccion: sel }),

  toggleColapsarFinalizados: () =>
    set((s) => ({ colapsarFinalizados: !s.colapsarFinalizados })),
}))
