// Store Zustand de la isla del árbol (#500, ADR-016).
//
// S2 (lectura): estado servidor (árbol de /arbol) + estado UI mínimo
// (selección única, toggle "Colapsar finalizados").
// S3a (inspector lectura): detalle lazy del nodo seleccionado (§5/§16) con caché
// por nodo + AbortController (cancela la petición anterior al cambiar de selección).
// S3b añadirá: modoEdicion, lock, despensa, colapsos manuales por nivel.
import { create } from 'zustand'
import { getArbol, getNodo } from './api.js'

// AbortController de la petición de detalle en curso (fuera del estado: no re-render).
let _detalleAbort = null

export const useArbolStore = create((set, get) => ({
  // --- estado servidor ---
  arbol: null,
  cargando: false,
  error: null,
  expedienteId: null,        // se fija al cargar; lo usa el detalle lazy

  // --- estado UI ---
  seleccion: null,            // { tipo, id } | null  (ADR §3, selección única)
  colapsarFinalizados: false, // toggle de viewbar (ADR §11)

  // --- detalle del inspector (S3a) ---
  detalle: null,              // payload del endpoint lazy del nodo seleccionado
  detalleCargando: false,
  detalleError: null,
  _detalleCache: {},          // { 'tipo-id': payload } — evita refetch al revisitar

  cargar: async (expedienteId) => {
    set({ cargando: true, error: null, expedienteId })
    try {
      const arbol = await getArbol(expedienteId)
      set({ arbol, cargando: false })
    } catch (e) {
      set({ error: e, cargando: false })
    }
  },

  // Selección única: además dispara la carga del detalle del nodo (o lo limpia).
  seleccionar: (sel) => {
    set({ seleccion: sel })
    get().cargarDetalle(sel)
  },

  cargarDetalle: async (sel) => {
    // Cancela la petición anterior siempre que cambie la selección.
    if (_detalleAbort) { _detalleAbort.abort(); _detalleAbort = null }

    if (!sel) {
      set({ detalle: null, detalleCargando: false, detalleError: null })
      return
    }

    const key = `${sel.tipo}-${sel.id}`
    const cacheado = get()._detalleCache[key]
    if (cacheado) {
      set({ detalle: cacheado, detalleCargando: false, detalleError: null })
      return
    }

    const expedienteId = get().expedienteId
    if (!expedienteId) {
      // Mock standalone (dev): no hay backend, no hay detalle que pedir.
      set({ detalle: null, detalleCargando: false, detalleError: null })
      return
    }

    const ctrl = new AbortController()
    _detalleAbort = ctrl
    set({ detalleCargando: true, detalleError: null, detalle: null })
    try {
      const data = await getNodo(expedienteId, sel.tipo, sel.id, { signal: ctrl.signal })
      if (ctrl.signal.aborted) return
      set((s) => ({
        detalle: data,
        detalleCargando: false,
        _detalleCache: { ...s._detalleCache, [key]: data },
      }))
    } catch (e) {
      if (e.name === 'AbortError' || ctrl.signal.aborted) return
      set({ detalleError: e, detalleCargando: false })
    } finally {
      if (_detalleAbort === ctrl) _detalleAbort = null
    }
  },

  toggleColapsarFinalizados: () =>
    set((s) => ({ colapsarFinalizados: !s.colapsarFinalizados })),
}))
