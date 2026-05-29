import { useEffect } from 'react'
import { showToast } from './toast.js'

// Primer wrapper Bootstrap del patrón "isla" (#499, ADR-015 §6 — UI primitives).
//
// Demuestra cómo un componente React orquesta un componente Bootstrap existente
// (bootstrap.Toast) sin arrastrar CSS propio: usa exclusivamente las clases del
// CDN JdA. No renderiza nada en su posición del árbol; dispara el toast al montar
// o al cambiar las props.
export default function Toast({ mensaje, categoria = 'info' }) {
  useEffect(() => {
    if (mensaje) showToast(mensaje, categoria)
  }, [mensaje, categoria])
  return null
}
