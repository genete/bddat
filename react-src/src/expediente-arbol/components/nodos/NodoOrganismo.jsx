// NodoOrganismo.jsx — nivel organismo, nodo sintético (ADR-042 §A, #396).
// Sin decoradores propios: reutiliza NodoBase igual que fase/trámite.
import React from 'react'
import NodoBase from './NodoBase.jsx'

export default function NodoOrganismo({ data }) {
  return <NodoBase data={data} />
}
