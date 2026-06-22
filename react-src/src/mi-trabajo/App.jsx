// App.jsx — raíz de la isla "Mi trabajo" (#501, ADR-017).
//
// Dos modos en v1 (Cola / Subir documento) por tabs. Los tabs viven en la viewbar
// del shell: se portalan sobre el slot #mi-trabajo-viewbar-slot (mismo patrón que
// el árbol, #523). El inspector de la cola usa el overlay global del shell.
import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import Viewbar from './components/Viewbar.jsx'
import Cola from './components/Cola.jsx'
import SubirDocumento from './components/SubirDocumento.jsx'

const viewbarSlot = () => document.getElementById('mi-trabajo-viewbar-slot')

function leerJSON(attr, fallback) {
  const el = document.querySelector('[data-react-island="mi-trabajo"]')
  const raw = el && el.getAttribute(attr)
  if (!raw) return fallback
  try {
    return JSON.parse(raw)
  } catch {
    return fallback
  }
}

export default function App() {
  const [tab, setTab] = useState('cola')
  const [tiposExpediente] = useState(() => leerJSON('data-tipos-expediente', []))

  return (
    <div className="d-flex flex-column" style={{ flex: 1, minHeight: 0 }}>
      {viewbarSlot() && createPortal(
        <Viewbar tab={tab} onTab={setTab} />, viewbarSlot(),
      )}
      {tab === 'cola'
        ? <Cola tiposExpediente={tiposExpediente} />
        : <SubirDocumento />}
    </div>
  )
}
