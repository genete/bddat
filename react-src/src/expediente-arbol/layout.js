// layout.js — construcción del grafo xyflow desde el árbol de dominio (ADR-016 §1).
//
// Layout TOP-DOWN HÍBRIDO:
//   - 4 bandas horizontales fijas por nivel: expediente / solicitud / fase / tramite.
//     Cada padre se centra horizontalmente sobre sus hijos.
//   - El empaquetado horizontal se calcula sobre la fila de TRÁMITES; las tareas no
//     reparten ancho: cuelgan en columna vertical bajo su trámite (hojas en columna).
//
// Es el buildGraph del POC (#291) transpuesto (X↔Y) para los 4 niveles superiores,
// más el caso especial de las tareas verticales → de ahí "híbrido".
//
// Colapso (ADR §11): con "Colapsar finalizados" activo, un nodo no-hoja finalizado
// se muestra plegado (sin hijos, con badge de agregados); su subárbol se omite.
//
// NOTA: las dimensiones/separaciones son PROVISIONALES (andamiaje). Los valores
// finales se fijan en la conversación de "formas y colores".

const ANCHO_SLOT = 210                                          // ancho reservado por trámite
const BANDA_Y = { expediente: 0, solicitud: 130, fase: 260, tramite: 390 }
const TAREA_Y0 = 480                                            // Y de la primera tarea
const TAREA_DY = 64                                             // separación vertical entre tareas

function clave(tipo, id) {
  return `${tipo}-${id}`
}

// Estado "finalizado" por nivel (criterio de dominio, no estético).
function esFinalizado(nodo) {
  switch (nodo.tipo) {
    case 'solicitud': return nodo.estado !== 'EN_TRAMITE'
    case 'fase':      return nodo.estado === 'FINALIZADA'
    case 'tramite':   return nodo.estado === 'FINALIZADO'
    case 'tarea':     return nodo.estado === 'EJECUTADA'
    default:          return false
  }
}

export function construirGrafo(arbol, { colapsarFinalizados = false, seleccion = null } = {}) {
  const nodes = []
  const edges = []
  let cursorX = 0

  const seleccionado = (tipo, id) =>
    !!seleccion && seleccion.tipo === tipo && seleccion.id === id

  // Reserva un hueco horizontal y devuelve su X (hojas/colapsados sin hijos).
  const slotVacio = () => {
    const x = cursorX
    cursorX += ANCHO_SLOT
    return x
  }
  // Centro entre el primer y último hijo (centrado del padre sobre sus hijos).
  const centro = (xs) => (xs[0] + xs[xs.length - 1]) / 2

  function emitir(nodo, x, y, extra = {}) {
    nodes.push({
      id: clave(nodo.tipo, nodo.id),
      type: nodo.tipo,
      position: { x, y },
      data: {
        tipo: nodo.tipo,
        id: nodo.id,
        nombre: nodo.nombre ?? nodo.descripcion ?? nodo.codigo ?? null,
        estado: nodo.estado ?? null,
        agregados: nodo.agregados ?? null,
        seleccionado: seleccionado(nodo.tipo, nodo.id),
        raw: nodo,
        ...extra,
      },
    })
  }

  function arista(padre, hijo) {
    edges.push({
      id: `e-${clave(padre.tipo, padre.id)}-${clave(hijo.tipo, hijo.id)}`,
      source: clave(padre.tipo, padre.id),
      target: clave(hijo.tipo, hijo.id),
    })
  }

  // --- nivel trámite: asigna X (un slot por trámite) y apila sus tareas ---
  function colocarTramite(tramite) {
    const x = slotVacio()
    const colapsado = colapsarFinalizados && esFinalizado(tramite) && tramite.tareas.length > 0
    emitir(tramite, x, BANDA_Y.tramite, { colapsado })
    if (!colapsado) {
      tramite.tareas.forEach((tarea, i) => {
        emitir(tarea, x, TAREA_Y0 + i * TAREA_DY)
        arista(tramite, tarea)
      })
    }
    return x
  }

  // --- nivel fase: centra sobre sus trámites ---
  function colocarFase(fase) {
    const colapsado = colapsarFinalizados && esFinalizado(fase) && fase.tramites.length > 0
    if (colapsado || fase.tramites.length === 0) {
      const x = slotVacio()
      emitir(fase, x, BANDA_Y.fase, { colapsado })
      return x
    }
    const xs = fase.tramites.map(colocarTramite)
    const x = centro(xs)
    emitir(fase, x, BANDA_Y.fase, { colapsado: false })
    fase.tramites.forEach((t) => arista(fase, t))
    return x
  }

  // --- nivel solicitud: centra sobre sus fases ---
  function colocarSolicitud(sol) {
    const colapsado = colapsarFinalizados && esFinalizado(sol) && sol.fases.length > 0
    if (colapsado || sol.fases.length === 0) {
      const x = slotVacio()
      emitir(sol, x, BANDA_Y.solicitud, { colapsado })
      return x
    }
    const xs = sol.fases.map(colocarFase)
    const x = centro(xs)
    emitir(sol, x, BANDA_Y.solicitud, { colapsado: false })
    sol.fases.forEach((f) => arista(sol, f))
    return x
  }

  // --- raíz expediente: centra sobre las solicitudes ---
  const solicitudes = arbol.solicitudes || []
  const xs = solicitudes.map(colocarSolicitud)
  const xExp = xs.length ? centro(xs) : 0
  emitir(arbol.expediente, xExp, BANDA_Y.expediente)
  solicitudes.forEach((s) => arista(arbol.expediente, s))

  return { nodes, edges }
}
