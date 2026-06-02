// Store Zustand de la isla del árbol (#500, ADR-016).
//
// S2 (lectura): estado servidor (árbol de /arbol) + estado UI mínimo
// (selección única, toggle "Colapsar finalizados").
// S3a (inspector lectura): detalle lazy del nodo seleccionado (§5/§16) con caché
// por nodo + AbortController (cancela la petición anterior al cambiar de selección).
// S3b-1: modoEdicion + lock + editor genérico (entrar/guardar/cancelar + refresco).
// S3b añadirá: despensa, colapsos manuales por nivel.
import { create } from 'zustand'
import { getArbol, getNodo, getEditable, patchNodo } from './api.js'
import { showToast } from '../shared/ui/toast.js'

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

  // --- edición (S3b-1, ADR §4/§5/§6) ---
  modoEdicion: false,
  editableCampos: [],         // [{campo, etiqueta, control, valor, opciones?}] del esquema editable
  borrador: {},               // { campo: valor } en edición
  borradorInicial: {},        // snapshot al entrar (detección de cambios → lock)
  edicionCargando: false,
  guardando: false,

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

  // --- acciones de edición (S3b-1) ---

  // Entra en edición del nodo `sel`: fija selección, pide el esquema editable y
  // siembra borrador/borradorInicial con el mismo objeto (hayCambios=false al entrar).
  entrarEdicion: async (sel) => {
    if (!sel) return
    set({ seleccion: sel, modoEdicion: true, edicionCargando: true,
          editableCampos: [], borrador: {}, borradorInicial: {} })
    const expedienteId = get().expedienteId
    if (!expedienteId) { set({ edicionCargando: false }); return }  // mock standalone: editor vacío
    try {
      const data = await getEditable(expedienteId, sel.tipo, sel.id)
      const campos = data.campos || []
      const borrador = Object.fromEntries(campos.map((c) => [c.campo, c.valor ?? null]))
      set({ editableCampos: campos, borrador, borradorInicial: borrador, edicionCargando: false })
    } catch (e) {
      set({ edicionCargando: false })
      if (e.status !== 401 && e.status !== 403) showToast(e.message || 'No se pudo cargar el editor', 'danger')
    }
  },

  setCampo: (campo, valor) => set((s) => ({ borrador: { ...s.borrador, [campo]: valor } })),

  cancelar: () => {
    set({ modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {}, edicionCargando: false })
    showToast('Cambios descartados', 'info')
  },

  guardar: async () => {
    const { expedienteId, seleccion, borrador } = get()
    if (!seleccion) return
    set({ guardando: true })
    try {
      const data = await patchNodo(expedienteId, seleccion.tipo, seleccion.id, borrador)
      showToast('Cambios guardados', 'success')
      if (data && data.advertencia) {                 // defensivo (PATCH editar no lo emite hoy)
        const a = data.advertencia
        showToast(typeof a === 'string' ? a : (a.mensaje || a.texto || 'Revisa la advertencia'), 'warning')
      }
      set({ guardando: false, modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {} })
      await get().refrescarArbol()
    } catch (e) {
      set({ guardando: false })
      if (e.status === 401 || e.status === 403) return // shared/api.js ya mostró su toast
      if (e.status === 422 && e.payload && e.payload.motivo) {
        showToast(e.payload.motivo, 'danger')          // bloqueo motor: PERMANECE en edición
      } else {
        showToast(e.message || 'No se pudo guardar', 'danger')
      }
    }
  },

  // Re-pide /arbol e invalida TODA la caché de detalle (una mutación puede recomputar
  // agregados/plazos de los ancestros → decisión F). Tras refrescar, re-dispara el
  // detalle de lectura del nodo seleccionado.
  refrescarArbol: async () => {
    const { expedienteId, seleccion } = get()
    if (!expedienteId) return
    try {
      const arbol = await getArbol(expedienteId)
      set({ arbol, _detalleCache: {} })
    } catch (e) {
      showToast('No se pudo refrescar el árbol', 'danger')
    }
    get().cargarDetalle(seleccion)
  },
}))

// --- selectores derivados de edición (S3b-1) ----------------------------------
// hayCambios = el borrador difiere del snapshot inicial.
//   · habilita/inhabilita Guardar
//   · arma el aviso beforeunload (solo si hay datos reales que perder)
// El LOCK de la UI (atenuar el chrome + overlay + inspector elevado) NO depende de
// hayCambios: se activa al ENTRAR en edición (lock-on-enter), porque editar es "editar
// este nodo" y debe ser inequívoco desde el primer momento. Lo gobierna `modoEdicion`.
export const selectHayCambios = (s) =>
  JSON.stringify(s.borrador) !== JSON.stringify(s.borradorInicial)
