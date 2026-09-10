// NodoVersion.jsx — nivel version, nodo sintético (ADR-044 §G, #895).
// Sin decoradores propios: reutiliza NodoBase igual que fase/trámite/organismo.
import React from 'react'
import NodoBase from './NodoBase.jsx'

export default function NodoVersion({ data }) {
  return <NodoBase data={data} />
}
