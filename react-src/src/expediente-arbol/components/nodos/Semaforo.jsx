// Semaforo.jsx — círculo-semáforo, único canal cromático del nodo (#500, MODELO §7).
//
// `relleno`=false → hueco con borde gris (el nodo "no tiene nada que decir" estando
// expandido). `relleno`=true → relleno con el color (`color` = nombre §2). El
// significado del color aparece en el hover (title).
import React from 'react'

const SIGNIFICADO = {
  rojo:     'Acción pendiente del tramitador',
  amarillo: 'En espera de firma',
  azul:     'En espera de un externo (destinatario o boletín)',
  naranja:  'Listo para cerrar o reintento disponible',
  gris:     'Espera pasiva (plazo legal o respuesta)',
  verde:    'Finalizado',
}

export default function Semaforo({ color, relleno }) {
  return (
    <span
      className={`arbol-sem${relleno ? ' is-relleno' : ''}`}
      data-color={color || 'gris'}
      title={relleno ? (SIGNIFICADO[color] || '') : ''}
    />
  )
}
