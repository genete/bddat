// Arbol.jsx — lienzo ReactFlow del árbol (#500, ADR-016 §1/§3/§13).
//
// Modo LECTURA: nodos no arrastrables ni conectables; solo selección única + pan/zoom.
// El tematizado JdA (arbol.css) y los decoradores de cada nodo se afinan en la
// conversación de "formas y colores"; aquí va el wiring estructural.
import '@xyflow/react/dist/style.css'
import '../styles/arbol.css'
import React, { useMemo, useCallback } from 'react'
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react'
import { useArbolStore } from '../store.js'
import { construirGrafo } from '../layout.js'
import NodoExpediente from './nodos/NodoExpediente.jsx'
import NodoSolicitud from './nodos/NodoSolicitud.jsx'
import NodoFase from './nodos/NodoFase.jsx'
import NodoTramite from './nodos/NodoTramite.jsx'
import NodoTareas from './nodos/NodoTareas.jsx'

const nodeTypes = {
  expediente: NodoExpediente,
  solicitud:  NodoSolicitud,
  fase:       NodoFase,
  tramite:    NodoTramite,
  tareas:     NodoTareas,
}

// Edges estructurales: ortogonales con esquinas redondeadas (ADR §1).
const defaultEdgeOptions = { type: 'smoothstep' }

export default function Arbol() {
  const arbol = useArbolStore((s) => s.arbol)
  const colapsarFinalizados = useArbolStore((s) => s.colapsarFinalizados)
  const seleccion = useArbolStore((s) => s.seleccion)
  const seleccionar = useArbolStore((s) => s.seleccionar)

  const { nodes, edges } = useMemo(
    () => construirGrafo(arbol, { colapsarFinalizados, seleccion }),
    [arbol, colapsarFinalizados, seleccion],
  )

  const onNodeClick = useCallback(
    (_, node) => {
      // El bloque-tareas no se selecciona como tal: cada fila-tarea maneja su click.
      if (node.data.tipo === 'tareas') return
      seleccionar({ tipo: node.data.tipo, id: node.data.id })
    },
    [seleccionar],
  )
  const onPaneClick = useCallback(() => seleccionar(null), [seleccionar])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      defaultEdgeOptions={defaultEdgeOptions}
      nodesDraggable={false}
      nodesConnectable={false}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.2}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
    >
      <Background />
      <Controls showInteractive={false} />
      <MiniMap pannable zoomable />
    </ReactFlow>
  )
}
