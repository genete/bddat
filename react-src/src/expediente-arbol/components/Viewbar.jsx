// Viewbar.jsx — cabecera de la isla del árbol (#500, ADR-016 §11 / #523).
//
// Montada vía createPortal en #arbol-viewbar-slot (declarado en arbol.html
// {% block viewbar %}), igual que el Inspector. Usa clases app-viewbar__* del
// shell; el <header class="app-viewbar"> del shell ya aporta flex + padding + borde.
//
// indicador_asignacion se pasa como data-indicador='ajeno'|'propio' en el slot
// desde Jinja (context processor inject_indicador_asignacion).
import React from 'react'
import { useArbolStore } from '../store.js'

function leerIndicador() {
  const slot = document.getElementById('arbol-viewbar-slot')
  return slot ? slot.dataset.indicador : undefined  // 'ajeno' | 'propio' | undefined
}

export default function Viewbar() {
  const arbol = useArbolStore((s) => s.arbol)
  const colapsarFinalizados = useArbolStore((s) => s.colapsarFinalizados)
  const toggle = useArbolStore((s) => s.toggleColapsarFinalizados)
  const exp = arbol && arbol.expediente
  const indicador = leerIndicador()

  return (
    <>
      {indicador !== undefined && (
        <i className={`bi bi-lightbulb-fill app-viewbar__indicador ${indicador === 'ajeno' ? 'text-danger' : 'text-success'}`}
           title={indicador === 'ajeno'
             ? 'Expediente no asignado a ti — actuación registrada en bitácora'
             : 'Tu expediente'} />
      )}
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
