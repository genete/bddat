// NodoTareas.jsx — bloque de tareas, hijo ÚNICO del trámite (#500, modelo acordado).
//
// Cada tarea es una FILA compacta (no una caja): versión horizontal de la anatomía
// (MODELO §6) → [icono-tipo] ABREV ··· ▼(n) ▲(n) ○círculo, con una barra fina de plazo
// en el borde inferior SOLO en ESPERAR_PLAZO (§9, v1 semántica). El círculo es el único
// canal de color (en NOTIFICAR codifica el resultado → sin ✓/✗ aparte).
import React from 'react'
import { Handle, Position } from '@xyflow/react'
import { useArbolStore } from '../../store.js'
import Semaforo from './Semaforo.jsx'
import Docs from './Docs.jsx'

// Icono de tipo de tarea (MODELO §6).
const ICONO = {
  ANALIZAR:      'bi-person-gear',
  ELABORAR:      'bi-pen',
  NOTIFICAR:     'bi-send',
  ESPERAR_PLAZO: 'bi-hourglass-split',
}

// Barra de plazo SEMÁNTICA (v1, §9): el relleno refleja el estado del plazo, no el
// progreso real. Verde congelado cuando la tarea está ejecutada (FIN).
function barraPlazo(tarea) {
  const ejecutada = tarea.semaforo && tarea.semaforo.estado === 'FIN'
  if (ejecutada) return { color: 'verde', width: '100%' }
  const estado = tarea.plazo && tarea.plazo.estado
  switch (estado) {
    case 'VENCIDO':        return { color: 'rojo',    width: '100%' }
    case 'PROXIMO_VENCER': return { color: 'naranja', width: '72%' }
    case 'EN_PLAZO':
    case 'INDEFINIDO':     return { color: 'gris',    width: '35%' }
    default:               return null   // SIN_PLAZO / sin configurar → sin barra
  }
}

function FilaTarea({ tarea, seleccionada, onSelect }) {
  const titulo = tarea.abrev || tarea.nombre || tarea.tipo_codigo || ''
  const sem = tarea.semaforo || { color: 'gris' }
  const esPlazo = tarea.tipo_codigo === 'ESPERAR_PLAZO'
  const barra = esPlazo ? barraPlazo(tarea) : null

  return (
    <div
      className={`arbol-tarea${seleccionada ? ' is-selected' : ''}`}
      title={tarea.nombre || ''}
      onClick={(e) => { e.stopPropagation(); onSelect(tarea.id) }}
    >
      <div className="arbol-tarea__fila">
        <i className={`bi ${ICONO[tarea.tipo_codigo] || 'bi-dot'} arbol-tarea__icono`} />
        <span className="arbol-tarea__titulo">{titulo}</span>
        <Docs consumido={tarea.doc_consumido} producido={tarea.doc_producido} className="arbol-docs--row" />
        <Semaforo color={sem.color} relleno />
      </div>
      {barra && (
        <div className="arbol-tarea__track">
          <div className="arbol-tarea__fill" data-color={barra.color} style={{ width: barra.width }} />
        </div>
      )}
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
