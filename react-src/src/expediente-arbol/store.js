// Store Zustand de la isla del árbol (#500, ADR-016).
//
// S2 (lectura): estado servidor (árbol de /arbol) + estado UI mínimo
// (selección única, toggle "Colapsar finalizados").
// S3a (inspector lectura): detalle lazy del nodo seleccionado (§5/§16) con caché
// por nodo + AbortController (cancela la petición anterior al cambiar de selección).
// S3b-1: modoEdicion + lock + editor genérico (entrar/guardar/cancelar + refresco).
// S3b añadirá: despensa, colapsos manuales por nivel.
import { create } from 'zustand'
import { getArbol, getNodo, getEditable, patchNodo, getTiposCreables, postHijo, getPool, deleteNodo } from './api.js'
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

  // --- creación de hijo (S3b-2) ---
  _tiposCreablesCache: {},    // { 'tipo-id': payload } — compartida con menú contextual S3b-4
  tiposCreables: null,        // payload de GET tipos-creables del nodo seleccionado
  tiposCreablesCargando: false,
  tipoCreacionPendiente: null, // { tipo_id, codigo, nombre } staged para crear
  creando: false,

  // --- pool de documentos (S3b-3) ---
  pool: [],                       // [{id, nombre, tipo_doc, fecha}] del expediente
  poolCargado: false,             // carga perezosa una vez por isla (el pool no cambia en esta vista)
  poolCargando: false,
  docVinculandoPendiente: null,   // {id, nombre, tipo_doc, fecha} staged para vincular
  vinculando: false,

  // --- borrar (S3b-4) ---
  borrarPendienteConfirm: false, // true = inspector muestra bloque de consecuencias + "Borrar definitivamente"
  borrando: false,

  // --- menú contextual (S3b-4) ---
  menuCtx: null,           // { x, y, sel } | null

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
    set({ seleccion: sel, borrarPendienteConfirm: false, menuCtx: null })
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
          editableCampos: [], borrador: {}, borradorInicial: {},
          tiposCreables: null, tipoCreacionPendiente: null,
          docVinculandoPendiente: null,
          menuCtx: null, borrarPendienteConfirm: false })
    const expedienteId = get().expedienteId
    if (!expedienteId) { set({ edicionCargando: false }); return }  // mock standalone: editor vacío
    try {
      const data = await getEditable(expedienteId, sel.tipo, sel.id)
      const campos = data.campos || []
      const borrador = Object.fromEntries(campos.map((c) => [c.campo, c.valor ?? null]))
      // Para tarea: incluir vínculos documentales actuales en el borrador para que
      // el ciclo dirty → Guardar/Cancelar cubra también la despensa de documentos.
      if (sel.tipo === 'tarea') {
        const docs = (get().detalle && get().detalle.documentos) || []
        borrador.documentos_consumidos_ids = docs.filter((d) => d.rol === 'CONSUMIDO').map((d) => d.id)
        borrador.documento_producido_id    = (docs.find((d) => d.rol === 'PRODUCIDO') || {}).id ?? null
      }
      set({ editableCampos: campos, borrador, borradorInicial: { ...borrador }, edicionCargando: false })
    } catch (e) {
      set({ edicionCargando: false })
      if (e.status !== 401 && e.status !== 403) showToast(e.message || 'No se pudo cargar el editor', 'danger')
    }
  },

  setCampo: (campo, valor) => set((s) => ({ borrador: { ...s.borrador, [campo]: valor } })),

  cancelar: () => {
    const { seleccion } = get()
    set({ modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {}, edicionCargando: false,
          tiposCreables: null, tipoCreacionPendiente: null,
          docVinculandoPendiente: null,
          borrarPendienteConfirm: false,
          detalle: null, detalleCargando: false, detalleError: null })
    get().cargarDetalle(seleccion)
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
        showToast(typeof a === 'string' ? a : (a.motivo || 'Revisa la advertencia'), 'warning')
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

  // --- acciones de borrado (S3b-4) ---

  // Paso 1: muestra el bloque de consecuencias en el inspector (sin llamada API).
  solicitarBorrado: () => set({ borrarPendienteConfirm: true }),

  cancelarBorrado: () => set({ borrarPendienteConfirm: false }),

  // Paso 2: ejecuta el DELETE real. Motor 422 → toast + vuelve al editor; éxito → limpia.
  borrarNodo: async () => {
    const { expedienteId, seleccion } = get()
    if (!seleccion || !expedienteId) return
    set({ borrando: true })
    try {
      await deleteNodo(expedienteId, seleccion.tipo, seleccion.id)
      showToast('Elemento borrado', 'success')
      set({
        borrando: false, borrarPendienteConfirm: false,
        seleccion: null,
        modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {},
        edicionCargando: false, tiposCreables: null, tipoCreacionPendiente: null,
        docVinculandoPendiente: null,
        detalle: null, detalleCargando: false, detalleError: null, _detalleCache: {},
      })
      await get().refrescarArbol()
    } catch (e) {
      set({ borrando: false, borrarPendienteConfirm: false })
      if (e.status === 401 || e.status === 403) return
      if (e.status === 422 && e.payload && e.payload.motivo) {
        showToast(e.payload.motivo, 'danger')
      } else {
        showToast(e.message || 'No se pudo borrar el elemento', 'danger')
      }
    }
  },

  // --- menú contextual (S3b-4) ---

  // Selecciona el nodo, carga su detalle y tipos-creables, abre el menú.
  abrirMenu: (x, y, sel) => {
    get().seleccionar(sel)
    if (sel.tipo !== 'tarea') get().cargarTiposCreables(sel)
    set({ menuCtx: { x, y, sel } })
  },

  cerrarMenu: () => set({ menuCtx: null }),

  // --- acciones de creación (S3b-2) ---

  // Carga tipos-creables del nodo `sel` (con caché compartida con el menú S3b-4).
  cargarTiposCreables: async (sel) => {
    if (!sel || sel.tipo === 'tarea') {
      set({ tiposCreables: null, tiposCreablesCargando: false })
      return
    }
    const key = `${sel.tipo}-${sel.id}`
    const cacheado = get()._tiposCreablesCache[key]
    if (cacheado) {
      set({ tiposCreables: cacheado, tiposCreablesCargando: false })
      return
    }
    const expedienteId = get().expedienteId
    if (!expedienteId) { set({ tiposCreables: null, tiposCreablesCargando: false }); return }
    set({ tiposCreablesCargando: true })
    try {
      const data = await getTiposCreables(expedienteId, sel.tipo, sel.id)
      set((s) => ({
        tiposCreables: data,
        tiposCreablesCargando: false,
        _tiposCreablesCache: { ...s._tiposCreablesCache, [key]: data },
      }))
    } catch {
      set({ tiposCreables: null, tiposCreablesCargando: false })
    }
  },

  seleccionarTipoCrear: (tipo) => set({ tipoCreacionPendiente: tipo }),

  cancelarCrear: () => set({ tipoCreacionPendiente: null }),

  crearHijo: async () => {
    const { expedienteId, seleccion, tipoCreacionPendiente, tiposCreables } = get()
    if (!seleccion || !tipoCreacionPendiente || !expedienteId) return
    set({ creando: true })
    try {
      const esMulti = seleccion.tipo === 'expediente'
      const body = esMulti
        ? { tipo_ids: [tipoCreacionPendiente.tipo_id] }
        : { tipo_id: tipoCreacionPendiente.tipo_id }
      const data = await postHijo(expedienteId, seleccion.tipo, seleccion.id, body)
      const nuevoTipo = tiposCreables?.tipo_hijo   // 'solicitud', 'fase', 'tramite', 'tarea'
      const nuevoId = (data.ids || [])[0]

      set({ creando: false, tipoCreacionPendiente: null })
      showToast('Elemento creado', 'success')
      if (data.advertencia) {
        const a = data.advertencia
        showToast(typeof a === 'string' ? a : (a.motivo || 'Revisa la advertencia'), 'warning')
      }
      // Invalidar caché de tipos del padre (el nuevo hijo puede cambiar lo creable).
      set((s) => {
        const cache = { ...s._tiposCreablesCache }
        delete cache[`${seleccion.tipo}-${seleccion.id}`]
        return { _tiposCreablesCache: cache }
      })
      await get().refrescarArbol()
      if (nuevoId && nuevoTipo) {
        await get().entrarEdicion({ tipo: nuevoTipo, id: nuevoId })
      }
    } catch (e) {
      set({ creando: false })
      if (e.status === 401 || e.status === 403) return
      if (e.status === 422 && e.payload) {
        showToast(e.payload.motivo || e.payload.error || 'Operación bloqueada', 'danger')
      } else {
        showToast(e.message || 'No se pudo crear el elemento', 'danger')
      }
    }
  },

  // --- acciones del pool (S3b-3) ---

  // Carga el pool una sola vez por vida de la isla (lazy). El pool no cambia mientras
  // se usa la despensa de tareas (las subidas viven en otra vista).
  cargarPool: async () => {
    if (get().poolCargado || get().poolCargando) return
    const expedienteId = get().expedienteId
    if (!expedienteId) return
    set({ poolCargando: true })
    try {
      const data = await getPool(expedienteId)
      set({ pool: data.documentos || [], poolCargado: true, poolCargando: false })
    } catch {
      set({ poolCargando: false })
    }
  },

  seleccionarDocVincular: (doc) => set({ docVinculandoPendiente: doc }),

  cancelarVincular: () => set({ docVinculandoPendiente: null }),

  // Añade `docVinculandoPendiente` al borrador con el rol dado.
  // No hace PATCH directamente: sigue el ciclo borrador → hayCambios → Guardar/Cancelar.
  // El PATCH lo ejecuta `guardar` con el borrador completo.
  vincularDoc: (rol) => {
    const { seleccion, docVinculandoPendiente, borrador } = get()
    if (!seleccion || seleccion.tipo !== 'tarea' || !docVinculandoPendiente) return

    const consumidosIds = borrador.documentos_consumidos_ids || []
    const producidoId   = borrador.documento_producido_id ?? null

    let nuevosConsumidosIds = [...consumidosIds]
    let nuevoProducidoId    = producidoId

    if (rol === 'CONSUMIDO') {
      if (!nuevosConsumidosIds.includes(docVinculandoPendiente.id)) {
        nuevosConsumidosIds = [...nuevosConsumidosIds, docVinculandoPendiente.id]
      }
    } else {
      nuevoProducidoId = docVinculandoPendiente.id
    }

    set((s) => ({
      borrador: {
        ...s.borrador,
        documentos_consumidos_ids: nuevosConsumidosIds,
        documento_producido_id:    nuevoProducidoId,
      },
      docVinculandoPendiente: null,
    }))
  },

  // Quita un documento del borrador según su rol (#517).
  // No hace PATCH directamente: sigue el ciclo borrador → hayCambios → Guardar/Cancelar.
  quitarDoc: (rol, docId) => {
    if (rol === 'CONSUMIDO') {
      set((s) => ({
        borrador: {
          ...s.borrador,
          documentos_consumidos_ids: (s.borrador.documentos_consumidos_ids || []).filter((id) => id !== docId),
        },
      }))
    } else {
      set((s) => ({ borrador: { ...s.borrador, documento_producido_id: null } }))
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
