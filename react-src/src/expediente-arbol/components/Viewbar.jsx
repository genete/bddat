// Viewbar.jsx — cabecera de la isla del árbol (#500, ADR-016 §11).
//
// Vive DENTRO de la isla (no en el slot viewbar de Jinja) para no cruzar estado
// React↔Jinja con el toggle. El slot viewbar de base_app conserva su default
// (código AT + bombilla de acceso).
// Botón "Editar" y resumen-mini de pistas → S3.
import React from 'react'
import { useArbolStore } from '../store.js'

export default function Viewbar() {
  const arbol = useArbolStore((s) => s.arbol)
  const colapsarFinalizados = useArbolStore((s) => s.colapsarFinalizados)
  const toggle = useArbolStore((s) => s.toggleColapsarFinalizados)
  const exp = arbol && arbol.expediente

  return (
    <div className="d-flex align-items-center justify-content-between border-bottom px-3 py-2 bg-body-tertiary">
      <div className="text-truncate">
        <strong>{exp && exp.codigo}</strong>
        {exp && exp.tipo_expediente && (
          <span className="text-muted ms-2">{exp.tipo_expediente}</span>
        )}
        {exp && exp.titular && <span className="text-muted ms-2">· {exp.titular}</span>}
      </div>
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
    </div>
  )
}
