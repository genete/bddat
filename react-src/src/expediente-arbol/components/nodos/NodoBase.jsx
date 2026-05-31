// NodoBase.jsx — caja común de los nodos no-tarea (#500).
//
// Andamiaje en GRIS: el título va en MAYÚSCULAS (CSS), estado y badges en texto.
// El color (paleta JdA por nivel + modulación por estado) es la fase siguiente.
import React from 'react'
import { Handle, Position } from '@xyflow/react'

export default function NodoBase({ data }) {
  const { tipo, titulo, tituloCompleto, estado, seleccionado, colapsado, agregados } = data

  return (
    <div className={`arbol-nodo arbol-nodo--${tipo}${seleccionado ? ' is-selected' : ''}`}>
      <Handle type="target" position={Position.Top} className="arbol-handle" />

      <div className="arbol-nodo__titulo" title={tituloCompleto || titulo}>{titulo || '—'}</div>
      {estado && <div className="arbol-nodo__estado">{estado}</div>}

      {colapsado && agregados && (
        <div className="arbol-nodo__badges">
          ⊕ venc {agregados.plazos_vencidos} · próx {agregados.plazos_proximos} · notif{' '}
          {agregados.pendientes_notificar}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="arbol-handle" />
    </div>
  )
}
