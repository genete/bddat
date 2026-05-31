// NodoTareas.jsx — bloque de tareas, hijo ÚNICO del trámite (#500, modelo acordado).
//
// NO es "el trámite con cabecera": es un contenedor independiente con las tareas
// como filas. Cada fila es seleccionable individualmente (?nodo=tarea-id) con su
// propio onClick + stopPropagation (no pasa por onNodeClick de ReactFlow).
// Iconos monocromos (Bootstrap Icons, ya cargado); el color es fase aparte.
import React from 'react'
import { Handle, Position } from '@xyflow/react'
import { useArbolStore } from '../../store.js'

const ICONO = {
  ANALIZAR:      'bi-search',
  ELABORAR:      'bi-pencil',
  NOTIFICAR:     'bi-envelope',
  ESPERAR_PLAZO: 'bi-hourglass-split',
}

function FilaTarea({ tarea, seleccionada, onSelect }) {
  const cons = tarea.doc_consumido || { presente: false, count: 0 }
  const prod = tarea.doc_producido || { presente: false, count: 0 }
  const titulo = tarea.abrev || tarea.nombre || tarea.tipo_codigo || ''
  const resultadoIcono =
    tarea.resultado === 'CORRECTA' ? '✓' : tarea.resultado === 'INCORRECTA' ? '✗' : tarea.resultado ? '–' : null

  return (
    <div
      className={`arbol-tarea${seleccionada ? ' is-selected' : ''}`}
      title={tarea.nombre || ''}
      onClick={(e) => { e.stopPropagation(); onSelect(tarea.id) }}
    >
      <i className={`bi ${ICONO[tarea.tipo_codigo] || 'bi-dot'} arbol-tarea__icono`} />
      <span className="arbol-tarea__titulo">{titulo}</span>
      <span className="arbol-tarea__deco">
        <span className="arbol-dot" data-on={cons.presente ? '1' : '0'} title={`consumido: ${cons.count}`} />
        <span className="arbol-dot" data-on={prod.presente ? '1' : '0'} title={`producido: ${prod.count}`} />
        {tarea.plazo && <span className="arbol-plazo">{tarea.plazo.estado}</span>}
        {resultadoIcono && <span className="arbol-result">{resultadoIcono}</span>}
      </span>
    </div>
  )
}

export default function NodoTareas({ data }) {
  const seleccionar = useArbolStore((s) => s.seleccionar)
  const onSelect = (id) => seleccionar({ tipo: 'tarea', id })

  return (
    <div className="arbol-tareas">
      <Handle type="target" position={Position.Top} className="arbol-handle" />
      {data.tareas.map((t) => (
        <FilaTarea
          key={t.id}
          tarea={t}
          seleccionada={data.seleccionTarea === t.id}
          onSelect={onSelect}
        />
      ))}
      <Handle type="source" position={Position.Bottom} className="arbol-handle" />
    </div>
  )
}
