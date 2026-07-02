// theme.js — Tematizado de Recharts a la paleta JdA (#579, ADR-028 §2).
//
// Recharts no trae hoja de estilos propia (pinta SVG inline), pero SÍ tiene un
// "sistema visual propio": los colores se pasan por prop (fill/stroke). El pase de
// tematizado documentado (REGLAS_DESARROLLO §React) consiste en NO inventar colores
// aquí, sino derivarlos de la MISMA fuente que el resto del sistema: las bandas de
// color del núcleo `estado_dominio.COLOR` (rojo/naranja/amarillo/azul/gris/verde).
//
// Las variables --jda-* las define el CDN de la Junta de Andalucía cargado en
// base_app.html; se leen en runtime para no hardcodear hex. Si una variable no
// existe (entorno sin CDN), se cae a un hex de respaldo coherente con la banda.

// Respaldo por banda (semáforo MODELO §2). Solo se usa si la variable CSS falta.
const FALLBACK_BANDA = {
  rojo:     '#c0392b',
  naranja:  '#e67e22',
  amarillo: '#f1c40f',
  azul:     '#2980b9',
  gris:     '#95a5a6',
  verde:    '#27ae60',
}

// Variable CSS JdA preferente por banda (paleta de la Junta de Andalucía).
// OJO: en la paleta JdA --bs-primary es VERDE (#087021), no azul; la banda 'azul'
// usa --bs-blue para no colisionar con el verde de 'verde'/--bs-success (#558).
const VAR_BANDA = {
  rojo:     '--bs-danger',
  naranja:  '--jda-naranja',
  amarillo: '--bs-warning',
  azul:     '--bs-blue',
  gris:     '--bs-secondary',
  verde:    '--bs-success',
}

function leerVarCss(nombre) {
  if (!nombre) return ''
  const v = getComputedStyle(document.documentElement).getPropertyValue(nombre)
  return v ? v.trim() : ''
}

// Color final de una banda: variable JdA si existe, si no el respaldo de la banda.
export function colorBanda(banda) {
  return leerVarCss(VAR_BANDA[banda]) || FALLBACK_BANDA[banda] || FALLBACK_BANDA.gris
}

// Colores fijos para las dos series de "carga por técnico".
export const COLOR_COMPLETADOS = () => colorBanda('verde')
export const COLOR_EN_TRAMITE  = () => colorBanda('azul')
