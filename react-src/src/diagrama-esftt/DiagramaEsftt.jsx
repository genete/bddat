import '@xyflow/react/dist/style.css'
import './styles/diagrama.css'
import React, { useMemo, useCallback } from 'react'
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState } from '@xyflow/react'
import { COLORES, MOCK } from './mockData.js'

// Posición X fija por nivel (columnas)
const X = { solicitud: 0, fase: 320, tramite: 640 }
// Separación vertical entre nodos del mismo nivel
const DY = 110

// width/height en style controla el render visual; en el nodo raíz lo necesita el MiniMap
const NODE_WIDTH = 260

function nodeStyle(nivel) {
  return {
    background:   COLORES[nivel],
    color:        '#fff',
    border:       'none',
    borderRadius: 8,
    padding:      '8px 14px',
    width:        NODE_WIDTH,
    fontSize:     13,
    fontWeight:   600,
    whiteSpace:   'normal',
    textAlign:    'center',
  }
}

// Convierte el árbol MOCK en arrays nodes/edges de ReactFlow.
// Las Y de cada nivel se calculan en orden de aparición para evitar solapamientos.
// La Y de cada solicitud se centra respecto a su bloque de fases.
function buildGraph(data) {
  const nodes = []
  const edges = []
  let yFase = 0
  let yTram = 0

  data.solicitudes.forEach((sol) => {
    const yFaseInicio = yFase

    sol.fases.forEach(fase => {
      const yTramInicio = yTram

      fase.tramites.forEach(tram => {
        nodes.push({
          id:       tram.id,
          data:     { label: tram.nombre },
          position: { x: X.tramite, y: yTram++ * DY },
          style:    nodeStyle('tramite'),
          width:    NODE_WIDTH,
        })
        edges.push({ id: `e-${fase.id}-${tram.id}`, source: fase.id, target: tram.id })
      })

      // Centrar la fase respecto a sus trámites
      const yFaseCentrada = (yTramInicio + yTram - 1) / 2 * DY
      nodes.push({
        id:       fase.id,
        data:     { label: fase.nombre },
        position: { x: X.fase, y: yFaseCentrada },
        style:    nodeStyle('fase'),
        width:    NODE_WIDTH,
      })
      edges.push({ id: `e-${sol.id}-${fase.id}`, source: sol.id, target: fase.id })
      yFase++
    })

    // Centrar la solicitud respecto a sus fases
    const yFaseFin = yTram - 1
    const ySolCentrada = (yFaseInicio * DY + yFaseFin * DY) / 2
    nodes.push({
      id:       sol.id,
      data:     { label: sol.nombre },
      position: { x: X.solicitud, y: ySolCentrada },
      style:    nodeStyle('solicitud'),
      width:    NODE_WIDTH,
    })
  })

  return { nodes, edges }
}

// Deduce el nivel del nodo a partir del prefijo de su id
function nivelNodo(id) {
  if (id.startsWith('sol')) return { label: 'Solicitud', icon: 'fa-file-alt' }
  if (id.startsWith('f-'))  return { label: 'Fase',      icon: 'fa-layer-group' }
  return                           { label: 'Trámite',   icon: 'fa-tasks' }
}

// Muestra un toast Bootstrap usando el .toast-container del layout Flask
function mostrarToast(nombre, nivel) {
  const container = document.querySelector('.toast-container')
  if (!container || !window.bootstrap) return

  const el = document.createElement('div')
  el.className = 'toast toast-info'
  el.setAttribute('role', 'alert')
  el.setAttribute('data-bs-autohide', 'true')
  el.setAttribute('data-bs-delay', '4000')
  el.innerHTML = `
    <div class="d-flex align-items-center p-3">
      <div class="flex-grow-1">
        <i class="fas ${nivel.icon} me-2"></i>
        <strong>${nivel.label}:</strong> ${nombre}
      </div>
      <button type="button" class="btn-close ms-3" data-bs-dismiss="toast" aria-label="Cerrar"></button>
    </div>`
  container.appendChild(el)
  const toast = new window.bootstrap.Toast(el)
  toast.show()
  el.addEventListener('hidden.bs.toast', () => el.remove())
}

export default function DiagramaEsftt() {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => buildGraph(MOCK), [])
  // useNodesState/useEdgesState habilitan el drag: onNodesChange actualiza posiciones en el store
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const handleNodeClick = useCallback((_, node) => {
    mostrarToast(node.data.label, nivelNodo(node.id))
  }, [])

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap nodeColor={(n) => n.style?.background ?? '#ccc'} nodeStrokeWidth={3} />
      </ReactFlow>
    </div>
  )
}
