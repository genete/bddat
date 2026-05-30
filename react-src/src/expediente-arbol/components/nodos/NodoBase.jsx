// NodoBase.jsx — caja común de los nodos del árbol (#500).
//
// ANDAMIAJE NEUTRO a propósito: caja sosa gris con tipo + nombre + estado en texto.
// La estética real (paleta JdA por nivel, tamaños, decoradores maquetados, posición
// de doc-dots/semáforo/badges) se define en la conversación de "formas y colores".
// No fijar paleta aquí.
import React from 'react'
import { Handle, Position } from '@xyflow/react'

export default function NodoBase({ data, children }) {
  const { tipo, nombre, estado, seleccionado, colapsado, agregados, atenuado } = data

  return (
    <div
      style={{
        border: seleccionado ? '2px solid #333' : '1px solid #aaa',
        borderRadius: 4,
        background: '#f4f4f4',
        padding: '6px 10px',
        fontSize: 12,
        minWidth: 150,
        boxShadow: seleccionado ? '0 0 0 3px rgba(0,0,0,.12)' : 'none',
        opacity: atenuado ? 0.55 : 1,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      <div style={{ textTransform: 'uppercase', fontSize: 9, letterSpacing: 0.5, color: '#888' }}>
        {tipo}
      </div>
      <div style={{ fontWeight: 600, lineHeight: 1.2 }}>{nombre || '—'}</div>
      {estado && <div style={{ color: '#666' }}>{estado}</div>}

      {children}

      {colapsado && agregados && (
        <div style={{ fontSize: 10, color: '#a30', marginTop: 2 }}>
          ⊕ venc {agregados.plazos_vencidos} · próx {agregados.plazos_proximos} · notif{' '}
          {agregados.pendientes_notificar}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  )
}
