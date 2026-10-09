// BarraPlazo.jsx — barra del plazo de resolver de UN acto (#922, MODELO §9).
//
// Una fila: [ACTO] ▬▬▬▬▬ dato. La usan el pie de las cajas solicitud/fase (NodoBase) y el
// bloque de plazos del inspector (sin la etiqueta del acto, que ya lleva su cabecera).
// Cómo se decide color, longitud y texto: ../../plazoActo.js.
import React from 'react'
import { barraDeActo } from '../../plazoActo.js'

export default function BarraPlazo({ plazo, conActo = true }) {
  const b = barraDeActo(plazo)
  const relleno = ['arbol-plazo__fill', b.tarde && 'is-tarde', b.parado && 'is-parado']
    .filter(Boolean).join(' ')
  const dato = ['arbol-plazo__dato', b.datoRojo && 'is-rojo', b.parado && 'is-parado']
    .filter(Boolean).join(' ')
  return (
    <div className="arbol-plazo" title={b.titulo}>
      {conActo && <span className="arbol-plazo__acto">{b.acto}</span>}
      <span className="arbol-plazo__track">
        <span className={relleno} data-color={b.color} style={{ width: b.width }} />
      </span>
      <span className={dato}>{b.dato}</span>
    </div>
  )
}
