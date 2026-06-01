// layout.js — construcción del grafo xyflow con tidy-tree (d3-flextree). #500, ADR-016 §1.
//
// MODELO (acordado con el usuario; enmienda ADR §1/§2):
//   - 5 niveles de NODOS: expediente → solicitud → fase → trámite → bloque-tareas.
//   - El TRÁMITE y sus TAREAS son DOS nodos independientes: el trámite tiene como
//     ÚNICO hijo un nodo "tareas" (las tareas juntas, como filas internas). Así el
//     trámite nunca tiene N hijos en vertical → flextree lo centra debajo sin hacks.
//     Las tareas NO se encadenan entre sí; son filas dentro del nodo-bloque.
//   - flextree reparte el ancho proporcionalmente al tamaño de cada subárbol
//     (los hijos expandidos ocupan más espacio) — requisito (d) del usuario.
//
// Colapso (ADR §11): con "Colapsar finalizados", un nodo no-hoja finalizado se
// muestra plegado (sin hijos, con badge de agregados); su subárbol se omite.
//
// NOTA: tamaños base PROVISIONALES (andamiaje). El color es una fase aparte.

import { flextree } from 'd3-flextree'

// --- dimensiones base por nivel (mínimos; el alto del bloque-tareas es variable) ---
// Ajustados al contenido real (cabecera icono+título+círculo; solicitud lleva docs).
const TAM = {
  expediente: [210, 60],
  solicitud:  [232, 76],
  fase:       [190, 60],
  tramite:    [182, 56],
}
const HGAP = 36                  // separación horizontal mínima entre hermanos
const VGAP = 58                  // separación vertical entre niveles
export const FILA_TAREA_H = 30   // alto de cada fila-tarea (la barra de plazo va superpuesta)
const TAREAS_PAD = 12            // padding vertical del bloque-tareas
const TAREAS_W = 212             // ancho del bloque-tareas

function claveDom(dom) {
  return `${dom.tipo}-${dom.id}`
}

// Estado "finalizado" por nivel (criterio de dominio).
function esFinalizado(dom) {
  switch (dom.tipo) {
    case 'solicitud': return dom.estado !== 'EN_TRAMITE'
    case 'fase':      return dom.estado === 'FINALIZADA'
    case 'tramite':   return dom.estado === 'FINALIZADO'
    default:          return false
  }
}

// Texto que se pinta en la caja (en MAYÚSCULAS vía CSS).
function derivarTitulo(dom) {
  switch (dom.tipo) {
    case 'expediente': return dom.codigo || ''
    case 'solicitud':  return (dom.siglas || '').replace(/_/g, ' ')   // AE_DEFINITIVA → AE DEFINITIVA
    case 'fase':
    case 'tramite':    return dom.abrev || dom.nombre || dom.tipo_codigo || ''
    default:           return ''
  }
}

function tamano(dom) {
  if (dom.tipo === 'tareas') {
    const n = Math.max(1, (dom.tareas || []).length)
    return [TAREAS_W, TAREAS_PAD + n * FILA_TAREA_H]
  }
  return TAM[dom.tipo] || [160, 48]
}

// Construye la jerarquía {ref, children, colapsado} aplicando el colapso.
function construirJerarquia(arbol, colapsarFinalizados) {
  const colapso = (dom, tieneHijos) =>
    colapsarFinalizados && esFinalizado(dom) && tieneHijos

  const exp = { ref: arbol.expediente, children: [], colapsado: false }

  for (const sol of arbol.solicitudes || []) {
    const cSol = colapso(sol, (sol.fases || []).length > 0)
    const nSol = { ref: sol, children: [], colapsado: cSol }
    if (!cSol) {
      for (const fase of sol.fases || []) {
        const cFase = colapso(fase, (fase.tramites || []).length > 0)
        const nFase = { ref: fase, children: [], colapsado: cFase }
        if (!cFase) {
          for (const tram of fase.tramites || []) {
            const cTram = colapso(tram, (tram.tareas || []).length > 0)
            const nTram = { ref: tram, children: [], colapsado: cTram }
            if (!cTram && (tram.tareas || []).length > 0) {
              // Bloque de tareas: hijo ÚNICO del trámite (nodo sintético).
              nTram.children.push({
                ref: { tipo: 'tareas', id: tram.id, tareas: tram.tareas },
                children: [],
                colapsado: false,
              })
            }
            nFase.children.push(nTram)
          }
        }
        nSol.children.push(nFase)
      }
    }
    exp.children.push(nSol)
  }
  return exp
}

export function construirGrafo(arbol, { colapsarFinalizados = false, seleccion = null } = {}) {
  if (!arbol || !arbol.expediente) return { nodes: [], edges: [] }

  const raiz = construirJerarquia(arbol, colapsarFinalizados)

  // tidy-tree con tamaños variables: el gap va dentro del nodeSize.
  const layout = flextree({
    nodeSize: (n) => {
      const [w, h] = tamano(n.data.ref)
      return [w + HGAP, h + VGAP]
    },
    spacing: 0,
  })
  const tree = layout.hierarchy(raiz)
  layout(tree)

  const selTarea = seleccion && seleccion.tipo === 'tarea' ? seleccion.id : null
  const seleccionado = (dom) =>
    !!seleccion && seleccion.tipo === dom.tipo && seleccion.id === dom.id

  const nodes = []
  const edges = []

  tree.each((n) => {
    const dom = n.data.ref
    const [w, h] = tamano(dom)
    // flextree centra el nodo en (x, y); ReactFlow posiciona por la esquina.
    let posY = n.y - h / 2
    if (dom.tipo === 'tareas' && n.parent) {
      // Top-alinear los bloques-tarea primos: flextree los centra en la línea del
      // nivel, así que con alturas distintas (nº de tareas) sus topes se desalinean.
      // Como todos los trámites comparten centro vertical, anclamos el TOPE del bloque
      // un VGAP por debajo del trámite padre → todos arrancan igual y crecen hacia abajo.
      const [, ph] = tamano(n.parent.data.ref)
      posY = n.parent.y + ph / 2 + VGAP
    }
    const node = {
      id: claveDom(dom),
      type: dom.tipo,
      position: { x: n.x - w / 2, y: posY },
      data: {},
    }
    if (dom.tipo === 'tareas') {
      node.data = {
        tipo: 'tareas',
        tramiteId: dom.id,
        tareas: dom.tareas,
        seleccionTarea: selTarea,
      }
    } else {
      node.data = {
        tipo: dom.tipo,
        id: dom.id,
        titulo: derivarTitulo(dom),
        tituloCompleto: dom.nombre || dom.descripcion || null,
        estado: dom.estado || null,
        semaforo: dom.semaforo || null,
        // Columna de documentos solo en solicitud (§8); el resto no la trae.
        docConsumido: dom.doc_consumido || null,
        docProducido: dom.doc_producido || null,
        agregados: dom.agregados || null,
        colapsado: n.data.colapsado,
        seleccionado: seleccionado(dom),
        raw: dom,
      }
    }
    nodes.push(node)

    if (n.parent) {
      const pdom = n.parent.data.ref
      edges.push({
        id: `e-${claveDom(pdom)}-${claveDom(dom)}`,
        source: claveDom(pdom),
        target: claveDom(dom),
      })
    }
  })

  return { nodes, edges }
}
