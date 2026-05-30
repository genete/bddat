// NodoTarea.jsx — hoja tarea (#500), la más rica en decoradores (ADR §2).
//
// Andamiaje neutro: doc-dots / plazo / resultado en texto plano. La maquetación
// real (2 puntos de documento posicionados, semáforo de plazo, ✓/✗ de notificación)
// se define en la conversación de "formas y colores".
import React from 'react'
import NodoBase from './NodoBase.jsx'

export default function NodoTarea({ data }) {
  const raw = data.raw || {}
  const cons = raw.doc_consumido || { count: 0 }
  const prod = raw.doc_producido || { count: 0 }

  return (
    <NodoBase data={data}>
      <div style={{ fontSize: 10, color: '#555', marginTop: 2 }}>
        doc consumido:{cons.count} · producido:{prod.count}
        {raw.plazo && ` · plazo:${raw.plazo.estado}`}
        {raw.resultado && ` · ${raw.resultado}`}
      </div>
    </NodoBase>
  )
}
