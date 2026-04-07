import '@xyflow/react/dist/style.css'
import './styles/diagrama.css'
import React, { useMemo } from 'react'
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react'
import { COLORES, MOCK } from './mockData.js'

// Posición X fija por nivel (columnas)
const X = { solicitud: 0, fase: 320, tramite: 640 }
// Separación vertical entre nodos del mismo nivel
const DY = 110

function nodeStyle(nivel) {
  return {
    background:   COLORES[nivel],
    color:        '#fff',
    border:       'none',
    borderRadius: 8,
    padding:      '8px 14px',
    width:        260,
    fontSize:     13,
    fontWeight:   600,
    whiteSpace:   'normal',
    textAlign:    'center',
  }
}

// Convierte el árbol MOCK en arrays nodes/edges de ReactFlow.
// Usa contadores globales yFase/yTram para evitar solapamientos entre ramas.
function buildGraph(data) {
  const nodes = []
  const edges = []
  let yFase = 0
  let yTram = 0

  data.solicitudes.forEach((sol, i) => {
    nodes.push({
      id:       sol.id,
      data:     { label: sol.nombre },
      position: { x: X.solicitud, y: i * DY * 4 },
      style:    nodeStyle('solicitud'),
    })

    sol.fases.forEach(fase => {
      nodes.push({
        id:       fase.id,
        data:     { label: fase.nombre },
        position: { x: X.fase, y: yFase++ * DY },
        style:    nodeStyle('fase'),
      })
      edges.push({ id: `e-${sol.id}-${fase.id}`, source: sol.id, target: fase.id })

      fase.tramites.forEach(tram => {
        nodes.push({
          id:       tram.id,
          data:     { label: tram.nombre },
          position: { x: X.tramite, y: yTram++ * DY },
          style:    nodeStyle('tramite'),
        })
        edges.push({ id: `e-${fase.id}-${tram.id}`, source: fase.id, target: tram.id })
      })
    })
  })

  return { nodes, edges }
}

export default function DiagramaEsftt() {
  const { nodes, edges } = useMemo(() => buildGraph(MOCK), [])

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap nodeStrokeWidth={3} />
      </ReactFlow>
    </div>
  )
}
