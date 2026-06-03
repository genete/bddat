// Arbol.jsx — lienzo ReactFlow del árbol (#500, ADR-016 §1/§3).
//
// Modo LECTURA: nodos no arrastrables ni conectables; solo selección única + pan/zoom.
// Sin minimapa (§13 revertido, #500): zoom (+/−), fit-view y el pan del fondo bastan.
// El tematizado JdA (arbol.css) y los decoradores de cada nodo se afinan en la
// conversación de "formas y colores"; aquí va el wiring estructural.
import '@xyflow/react/dist/style.css'
import '../styles/arbol.css'
import React, { useMemo, useCallback } from 'react'
import { ReactFlow, Background, Controls } from '@xyflow/react'
import { useArbolStore } from '../store.js'
import { construirGrafo } from '../layout.js'
import NodoExpediente from './nodos/NodoExpediente.jsx'
import NodoSolicitud from './nodos/NodoSolicitud.jsx'
import NodoFase from './nodos/NodoFase.jsx'
import NodoTramite from './nodos/NodoTramite.jsx'
import NodoTareas from './nodos/NodoTareas.jsx'
import MenuContextual from './MenuContextual.jsx'

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
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const entrarEdicion = useArbolStore((s) => s.entrarEdicion)
  const abrirMenu = useArbolStore((s) => s.abrirMenu)

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
  // Doble-clic = atajo para editar ese nodo (en lectura). En edición el overlay
  // intercepta los clics del lienzo, así que no permite cambiar de nodo objetivo.
  const onNodeDoubleClick = useCallback(
    (_, node) => {
      if (node.data.tipo === 'tareas') return
      entrarEdicion({ tipo: node.data.tipo, id: node.data.id })
    },
    [entrarEdicion],
  )
  const onPaneClick = useCallback(() => seleccionar(null), [seleccionar])

  const onNodeContextMenu = useCallback(
    (e, node) => {
      if (node.data.tipo === 'tareas') return  // container-nodo; cada tarea lo gestiona internamente
      e.preventDefault()
      abrirMenu(e.clientX, e.clientY, { tipo: node.data.tipo, id: node.data.id })
    },
    [abrirMenu],
  )

  return (
    <>
    <ReactFlow
      className={modoEdicion ? 'arbol-lienzo--edicion' : undefined}
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      onNodeDoubleClick={onNodeDoubleClick}
      onNodeContextMenu={onNodeContextMenu}
      onPaneClick={onPaneClick}
      defaultEdgeOptions={defaultEdgeOptions}
      nodesDraggable={false}
      nodesConnectable={false}
      zoomOnDoubleClick={false}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.2}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
    >
      <Background />
      <Controls showInteractive={false} />
    </ReactFlow>
    <MenuContextual />
    </>
  )
}
