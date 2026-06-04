// Viewbar.jsx — cabecera de la isla del árbol (#500, ADR-016 §11 / #523 / #525).
//
// Montada vía createPortal en #arbol-viewbar-slot (declarado en arbol.html
// {% block viewbar %}), igual que el Inspector. Usa clases app-viewbar__* del
// shell; el <header class="app-viewbar"> del shell aporta flex + padding + borde
// y renderiza la bombilla de asignación como chrome propio (#525).
import React from 'react'
import { useArbolStore } from '../store.js'

export default function Viewbar() {
  const arbol = useArbolStore((s) => s.arbol)
  const colapsarFinalizados = useArbolStore((s) => s.colapsarFinalizados)
  const toggle = useArbolStore((s) => s.toggleColapsarFinalizados)
  const exp = arbol && arbol.expediente

  return (
    <>
      <div className="app-viewbar__title" style={{ minWidth: 0, overflow: 'hidden' }}>
        <strong className="text-truncate">{exp && exp.codigo}</strong>
        {exp && exp.tipo_expediente && (
          <span className="text-muted ms-2 text-truncate">{exp.tipo_expediente}</span>
        )}
        {exp && exp.titular && (
          <span className="text-muted ms-2 text-truncate">· {exp.titular}</span>
        )}
      </div>
      <div className="app-viewbar__spacer" />
      <div className="form-check form-switch m-0 flex-shrink-0">
        <input
          className="form-check-input"
          type="checkbox"
          role="switch"
          id="arbol-toggle-colapsar"
          checked={colapsarFinalizados}
          onChange={toggle}
        />
        <label className="form-check-label" htmlFor="arbol-toggle-colapsar">
          Colapsar finalizados
        </label>
      </div>
    </>
  )
}
