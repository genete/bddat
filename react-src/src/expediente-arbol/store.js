// Store Zustand de la isla del árbol (#500, ADR-016).
//
// S2 (lectura): estado servidor (árbol de /arbol) + estado UI mínimo
// (selección única, toggle "Colapsar finalizados").
// S3a (inspector lectura): detalle lazy del nodo seleccionado (§5/§16) con caché
// por nodo + AbortController (cancela la petición anterior al cambiar de selección).
// S3b-1: modoEdicion + lock + editor genérico (entrar/guardar/cancelar + refresco).
// S3b añadirá: despensa, colapsos manuales por nivel.
import { create } from 'zustand'
import { getArbol, getNodo, getEditable, patchNodo, getTiposCreables, postHijo, getPool, deleteNodo, guardarNotas, postReabrirFase } from './api.js'
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

  // --- ANALIZAR (#442/#677): flag conocido tras el primer getAnalizar de la
  // sesión de edición actual. null mientras se desconoce (o nodo no-ANALIZAR)
  // — Inspector.jsx lo trata como "no ocultar Despensa" hasta confirmar true,
  // para no ocultarla de golpe en ANALIZAR simple (donde sigue viva).
  analizarSeccionesExtendidas: null,

  // --- creación de hijo (S3b-2) ---
  _tiposCreablesCache: {},    // { 'tipo-id': payload } — compartida con menú contextual S3b-4
  tiposCreables: null,        // payload de GET tipos-creables del nodo seleccionado
  tiposCreablesCargando: false,
  tipoCreacionPendiente: null, // tipo staged para crear ({tipo_id, codigo, nombre, es_siguiente?}
                                // — item de canonicos/resto, ADR-037 §D: sin permitido/motivo,
                                // el motor no se evalúa aquí)
  creacionPadre: null,         // {tipo, id} bajo el que se crea — fijado al stagear
                                // (seleccionarTipoCrear), NO se lee de `seleccion`: el menú
                                // contextual crea sin seleccionar el nodo (abrirMenu no toca
                                // `seleccion`, ver más abajo), así que necesita su propio padre
  bloqueoActual: null,         // {motivo, url_norma, puede_escapar} revelado tras un intento de
                                // creación bloqueado — el veredicto ya no se conoce al listar
                                // (ADR-037 §D), solo al intentar (ver crearHijo)
  justificacionForzar: '',    // texto del bypass cuando bloqueoActual.puede_escapar (#616)
  bloqueoGuardar: null,        // {motivo, url_norma} del 422 FORZABLE del Guardar del inspector
                                // (#765): el equivalente de bloqueoActual para el PATCH del nodo.
                                // Hasta ahora el escape solo existía al CREAR — los tres bloqueos
                                // forzables del cierre de fase (completitud #723, desfavorable sin
                                // consumir #419/#711, desfavorable sin respaldo #765) llegaban con
                                // puede_escapar:true y morían en un toast, sin vía de forzado.
  creando: false,

  // --- pool de documentos (S3b-3) ---
  pool: [],                       // [{id, nombre, tipo_doc, fecha}] del expediente
  poolCargado: false,             // carga perezosa una vez por isla (el pool no cambia en esta vista)
  poolCargando: false,
  docVinculandoPendiente: null,   // {id, nombre, tipo_doc, fecha} staged para vincular
  vinculando: false,
  docPendienteIdDesdeUrl: null,   // id leído de ?doc_pendiente=<id> (#630, ADR-038 §5) — se
                                   // consume una sola vez en cargarPool() y se limpia ahí

  // --- borrar (S3b-4) ---
  borrarPendienteConfirm: false, // true = inspector muestra bloque de consecuencias + "Borrar definitivamente"
  borrando: false,

  // --- reabrir fase (#720, ADR-036 §6 capa 4) ---
  reabriendoFase: false,

  // --- menú contextual (S3b-4) ---
  menuCtx: null,           // { x, y, sel } | null
  menuDetalle: null,       // detalle del nodo del menú (documentos/referencia) — independiente
                           // de `detalle`/`seleccion`: abrir el menú NO selecciona el nodo ni
                           // monta el inspector, son dos acciones distintas (clic izq. vs. clic dcho.)

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
          tiposCreables: null, tipoCreacionPendiente: null, creacionPadre: null, bloqueoActual: null, justificacionForzar: '',
          bloqueoGuardar: null,
          docVinculandoPendiente: null, analizarSeccionesExtendidas: null,
          menuCtx: null, menuDetalle: null, borrarPendienteConfirm: false })
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

  setAnalizarSeccionesExtendidas: (v) => set({ analizarSeccionesExtendidas: v }),

  cancelar: () => {
    const { seleccion } = get()
    const habiaCambios = selectHayCambios(get())
    set({ modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {}, edicionCargando: false,
          tiposCreables: null, tipoCreacionPendiente: null, creacionPadre: null, bloqueoActual: null, justificacionForzar: '',
          bloqueoGuardar: null,
          docVinculandoPendiente: null,
          borrarPendienteConfirm: false,
          detalle: null, detalleCargando: false, detalleError: null })
    get().cargarDetalle(seleccion)
    // Solo avisa de descarte si de verdad había algo que perder (ADR-023 §5 bis:
    // en limpio "sale a lectura sin revertir nada" — sin toast que sugiera lo contrario).
    if (habiaCambios) showToast('Cambios descartados', 'info')
  },

  // Persiste el borrador completo y sale a lectura (ADR-023 §5 bis: Guardar es
  // control de salida, no un checkpoint intermedio).
  //
  // Enrutado del PATCH (#688): `editar_tarea` diffea los vínculos documentales
  // contra `documentos_consumidos_ids` y libera a pool/ lo que sobre. En una
  // tarea ANALIZAR extendida ese campo del borrador queda OBSOLETO durante la
  // sesión — el check documental deriva vínculos CONSUMIDO en el backend
  // (sincronizar_consumido_documental, #677) sin pasar por aquí. Por eso, si lo
  // único que difiere del snapshot inicial es `notas`, se guarda por la vía
  // estrecha (PATCH .../notas), que no toca vínculos: el Guardar de la cabecera
  // deja de poder deshacer lo que el propio contenedor acaba de derivar.
  // Si cambiaron los vínculos (Despensa viva: ANALIZAR simple, ELABORAR,
  // NOTIFICAR), el borrador SÍ es la verdad y va el PATCH completo de siempre.
  //
  // `justificacion` (#765): reintento del propio Guardar cuando el 422 anterior
  // traía `puede_escapar:true` (ver el catch). Viaja como `bypass`+`justificacion`
  // en el mismo PATCH — es lo que `api_expedientes.editar_nodo` lee con
  // `_leer_bypass` para la rama `fase`, y `editar_fase` deja en bitácora. No se
  // ofrece en la vía estrecha de notas: ningún invariante forzable cuelga de ella.
  guardar: async (justificacion) => {
    const { expedienteId, seleccion, borrador, borradorInicial } = get()
    if (!seleccion) return
    const camposSucios = Object.keys(borrador).filter(
      (k) => JSON.stringify(borrador[k]) !== JSON.stringify(borradorInicial[k]))
    const soloNotas = seleccion.tipo === 'tarea' &&
                      camposSucios.length > 0 && camposSucios.every((k) => k === 'notas')
    const cuerpo = justificacion ? { ...borrador, bypass: true, justificacion } : borrador
    set({ guardando: true })
    try {
      const data = soloNotas
        ? await guardarNotas(expedienteId, seleccion.id, borrador.notas)
        : await patchNodo(expedienteId, seleccion.tipo, seleccion.id, cuerpo)
      showToast(justificacion
        ? 'Cambios guardados con justificación — queda en la bitácora'
        : 'Cambios guardados', justificacion ? 'warning' : 'success')
      if (data && data.advertencia) {                 // fase: justificantes huérfanos en el pool (#738)
        const a = data.advertencia
        showToast(typeof a === 'string' ? a : (a.motivo || 'Revisa la advertencia'), 'warning')
      }
      set({ guardando: false, modoEdicion: false, editableCampos: [], borrador: {}, borradorInicial: {},
            bloqueoGuardar: null })
      await get().refrescarArbol()
    } catch (e) {
      set({ guardando: false })
      if (e.status === 401 || e.status === 403) return // shared/api.js ya mostró su toast
      if (e.status === 422 && e.payload && e.payload.puede_escapar === true) {
        // Bloqueo FORZABLE (#765): en vez de un toast que se va solo, se queda en
        // pantalla para poder ofrecer la vía de escape con justificación — mismo
        // criterio que `crearHijo` con `bloqueoActual`. PERMANECE en edición, con el
        // borrador intacto: confirmar reintenta este mismo Guardar.
        set({ bloqueoGuardar: {
          motivo: e.payload.motivo || e.payload.error || 'Operación bloqueada',
          url_norma: e.payload.url_norma || '',
        } })
      } else if (e.status === 422 && e.payload && e.payload.motivo) {
        showToast(e.payload.motivo, 'danger')          // puerta cerrada: PERMANECE en edición
      } else {
        showToast(e.message || 'No se pudo guardar', 'danger')
      }
    }
  },

  // Descarta el bloqueo forzable sin guardar (#765): vuelve al editor tal cual, con
  // el borrador vivo — el técnico corrige el resultado en vez de forzarlo.
  cancelarBloqueoGuardar: () => set({ bloqueoGuardar: null }),

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
        edicionCargando: false, tiposCreables: null, tipoCreacionPendiente: null, creacionPadre: null, bloqueoActual: null, justificacionForzar: '',
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

  // --- reabrir fase (#720, ADR-036 §6 capa 4) ---

  // Único camino para tocar el interior de una fase FINALIZADA. justificacion
  // siempre obligatoria (validado también server-side) — no hay reapertura
  // silenciosa. Bloqueo (422): la solicitud ya está resuelta y notificada,
  // puerta cerrada sin bypass (ADR-036 §4) — mismo canal de toast que el resto.
  reabrirFase: async (justificacion) => {
    const { expedienteId, seleccion } = get()
    if (!seleccion || seleccion.tipo !== 'fase' || !expedienteId) return
    set({ reabriendoFase: true })
    try {
      await postReabrirFase(expedienteId, seleccion.id, justificacion)
      showToast('Fase reabierta', 'success')
      set({
        reabriendoFase: false, modoEdicion: false,
        editableCampos: [], borrador: {}, borradorInicial: {},
        detalle: null, detalleCargando: false, detalleError: null, _detalleCache: {},
      })
      await get().refrescarArbol()
    } catch (e) {
      set({ reabriendoFase: false })
      if (e.status === 401 || e.status === 403) return
      if (e.status === 422 && e.payload && (e.payload.motivo || e.payload.error)) {
        showToast(e.payload.motivo || e.payload.error, 'danger')
      } else {
        showToast(e.message || 'No se pudo reabrir la fase', 'danger')
      }
    }
  },

  // --- menú contextual (S3b-4) ---

  // Abre el menú del nodo `sel` SIN seleccionarlo (eso es cosa del clic
  // izquierdo — seleccionar() — que monta el inspector vía App.jsx). Clic
  // derecho es una acción puntual sobre el nodo, no un cambio de foco: no debe
  // tocar `seleccion` ni el `detalle` del inspector abierto para otro nodo.
  // Carga tipos-creables (submenú) y, en menuDetalle, lo que necesitan
  // "Copiar referencia"/"Abrir documento"/"Abrir carpeta" del propio menú.
  abrirMenu: async (x, y, sel) => {
    set({ menuCtx: { x, y, sel }, menuDetalle: null })
    if (sel.tipo !== 'tarea') get().cargarTiposCreables(sel)

    const key = `${sel.tipo}-${sel.id}`
    const cacheado = get()._detalleCache[key]
    if (cacheado) { set({ menuDetalle: cacheado }); return }
    const expedienteId = get().expedienteId
    if (!expedienteId) return
    try {
      const data = await getNodo(expedienteId, sel.tipo, sel.id)
      // El menú pudo cerrarse o reabrirse en otro nodo mientras se esperaba.
      if (get().menuCtx?.sel !== sel) return
      set((s) => ({ menuDetalle: data, _detalleCache: { ...s._detalleCache, [key]: data } }))
    } catch { /* el menú sigue siendo útil sin documentos/referencia */ }
  },

  cerrarMenu: () => set({ menuCtx: null, menuDetalle: null }),

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

  // Selecciona un tipo (canónico o resto, sin distinción a priori — ADR-037 §D)
  // para stagearlo. Recibe el item de canonicos/resto: {tipo_id, codigo, nombre, es_siguiente?}.
  // `padre` es opcional: la Despensa lo omite (crea siempre bajo la selección actual, que
  // coincide con el nodo en edición); el menú contextual lo pasa explícito porque abrirMenu
  // ya no selecciona el nodo (clic derecho no debe montar el inspector, ver abrirMenu).
  seleccionarTipoCrear: (tipo, padre) => set({
    tipoCreacionPendiente: tipo,
    creacionPadre: padre ?? get().seleccion,
    bloqueoActual: null,
    justificacionForzar: '',
  }),

  cancelarCrear: () => set({
    tipoCreacionPendiente: null, creacionPadre: null, bloqueoActual: null, justificacionForzar: '',
  }),

  setJustificacionForzar: (texto) => set({ justificacionForzar: texto }),

  crearHijo: async () => {
    const { expedienteId, creacionPadre, tipoCreacionPendiente, tiposCreables, bloqueoActual, justificacionForzar } = get()
    if (!creacionPadre || !tipoCreacionPendiente || !expedienteId) return

    // Reintento tras bloqueo (ADR-037 §D): bloqueoActual solo existe si un intento
    // previo de este mismo tipo staged ya lo reveló — no se conoce de antemano.
    const forzando = !!bloqueoActual
    if (forzando && !justificacionForzar.trim()) {
      showToast('La justificación es obligatoria para forzar la creación', 'danger')
      return
    }

    set({ creando: true })
    try {
      const esMulti = creacionPadre.tipo === 'expediente'
      const body = esMulti
        ? { tipo_ids: [tipoCreacionPendiente.tipo_id] }
        : { tipo_id: tipoCreacionPendiente.tipo_id }
      if (forzando) {
        body.bypass = true
        body.justificacion = justificacionForzar.trim()
      }
      const data = await postHijo(expedienteId, creacionPadre.tipo, creacionPadre.id, body)
      const nuevoTipo = tiposCreables?.tipo_hijo   // 'solicitud', 'fase', 'tramite', 'tarea'
      const nuevoId = (data.ids || [])[0]

      set({ creando: false, tipoCreacionPendiente: null, creacionPadre: null, bloqueoActual: null, justificacionForzar: '' })
      showToast(forzando ? 'Elemento creado (forzado, registrado en bitácora)' : 'Elemento creado', 'success')
      if (data.advertencia) {
        const a = data.advertencia
        showToast(typeof a === 'string' ? a : (a.motivo || 'Revisa la advertencia'), 'warning')
      }
      // Invalidar caché de tipos del padre (el nuevo hijo puede cambiar lo creable).
      set((s) => {
        const cache = { ...s._tiposCreablesCache }
        delete cache[`${creacionPadre.tipo}-${creacionPadre.id}`]
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
        // Bloqueo del motor o de vocabulario (ADR-037 §C/§D): se revela aquí, no
        // antes — tipos-creables ya no lo sabe de antemano. Se queda en pantalla
        // (no toast) para poder ofrecer forzar si puede_escapar.
        set({
          bloqueoActual: {
            motivo: e.payload.motivo || e.payload.error || 'Operación bloqueada',
            url_norma: e.payload.url_norma || '',
            puede_escapar: !!e.payload.puede_escapar,
          },
        })
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
      const pool = data.documentos || []
      set({ pool, poolCargado: true, poolCargando: false })

      // Radar de huérfanos (#630, ADR-038 §5, vía A "Ir a la tarea"): si se llegó
      // con ?doc_pendiente=<id>, pre-carga ese documento en la zona de staging de
      // la Despensa — sin guardar nada, el técnico decide el rol y pulsa Guardar.
      // Consumo único: se limpia aquí para no re-stagear en cargas posteriores del
      // pool (p. ej. si el técnico navega a otra tarea sin recargar la página).
      const pendienteId = get().docPendienteIdDesdeUrl
      if (pendienteId) {
        set({ docPendienteIdDesdeUrl: null })
        const doc = pool.find((d) => d.id === pendienteId)
        if (doc) get().seleccionarDocVincular(doc)
      }
    } catch {
      set({ poolCargando: false })
    }
  },

  setDocPendienteIdDesdeUrl: (id) => set({ docPendienteIdDesdeUrl: id }),

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

  // Resincroniza el borrador tras vincular el Producido por una vía ajena al ciclo
  // Guardar/Cancelar general (#712: PATCH .../notificar con documento_id persiste
  // directamente, sin pasar por `guardar()`). Sin esto, la Despensa —que lee
  // `borrador.documento_producido_id`— se quedaría mostrando el vínculo anterior
  // hasta que el usuario reseleccione el nodo. `borradorInicial` se actualiza igual
  // que `borrador` (mismo patrón que entrarEdicion) para que hayCambios no marque
  // como "pendiente de guardar" un campo que ya se persistió por su cuenta.
  sincronizarProducidoNotificar: (documentoId) => set((s) => ({
    borrador: { ...s.borrador, documento_producido_id: documentoId },
    borradorInicial: { ...s.borradorInicial, documento_producido_id: documentoId },
  })),

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

// Invalida la caché de tipos-creables al cambiar el modo global del motor (#618).
// motor-estado.js (topbar, polling 60s) dispara este evento cuando detecta que
// el modo difiere del último conocido. Si hay un nodo con despensa/menú abiertos,
// se recarga directamente para que el usuario vea el estado vigente sin esperar
// a reabrir el menú.
window.addEventListener('bddat:motor-modo-cambio', () => {
  useArbolStore.setState({ _tiposCreablesCache: {} })
  const { seleccion, menuCtx, tiposCreables } = useArbolStore.getState()
  if (seleccion && (menuCtx || tiposCreables)) {
    useArbolStore.getState().cargarTiposCreables(seleccion)
  }
})

// --- selectores derivados de edición (S3b-1) ----------------------------------
// hayCambios = el borrador difiere del snapshot inicial.
//   · habilita/inhabilita Guardar
//   · arma el aviso beforeunload (solo si hay datos reales que perder)
// El LOCK de la UI (atenuar el chrome + overlay + inspector elevado) NO depende de
// hayCambios: se activa al ENTRAR en edición (lock-on-enter), porque editar es "editar
// este nodo" y debe ser inequívoco desde el primer momento. Lo gobierna `modoEdicion`.
export const selectHayCambios = (s) =>
  JSON.stringify(s.borrador) !== JSON.stringify(s.borradorInicial)
