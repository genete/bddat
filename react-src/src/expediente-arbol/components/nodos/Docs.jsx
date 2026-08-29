// Docs.jsx — decorador de documentos: icono-flecha + contador (#500, MODELO §8).
//
// consumido ▼ (entra) · producido ▲ (sale). Gris si ausente; con color si presente;
// (-) si el nodo no produce/consume ese rol (na). El contenedor decide la dirección
// (columna en cajas, fila en tareas) vía CSS.
import React from 'react'

function DocItem({ rol, info }) {
  const na = !!(info && info.na)
  const count = info ? info.count : 0
  const presente = !!(info && info.presente)
  const estado = na ? 'na' : presente ? 'has' : ''
  const icono = rol === 'consumido' ? 'bi-box-arrow-in-down' : 'bi-box-arrow-up'
  const texto = na ? '(-)' : `(${count})`
  const titulo = na
    ? `${rol}: no aplica`
    : presente
      ? `${rol}: ${count}`
      : `${rol}: ninguno`
  return (
    <span className={`arbol-doc ${estado}`.trim()} title={titulo}>
      <i className={`bi ${icono}`} />
      <b>{texto}</b>
    </span>
  )
}

export default function Docs({ consumido, producido, className = '' }) {
  return (
    <span className={`arbol-docs ${className}`.trim()}>
      <DocItem rol="consumido" info={consumido} />
      <DocItem rol="producido" info={producido} />
    </span>
  )
}
