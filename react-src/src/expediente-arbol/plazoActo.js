// plazoActo.js — cómo se pinta el plazo de resolver de un acto (#922, MODELO §9).
//
// Lógica pura: del dict que vuelca `arbol_expediente.plazos_solicitud` a lo que necesita
// una barra. La comparten la caja del árbol (BarraPlazo) y el bloque del inspector.

// Barra SEMÁNTICA (v1, igual que la de las tareas, NodoTareas.barraPlazo): el relleno
// refleja el estado del plazo, no el tiempo transcurrido. La proporcional sigue diferida.
const RELLENO = {
  EN_PLAZO:       { color: 'gris',    width: '35%' },
  PROXIMO_VENCER: { color: 'naranja', width: '72%' },
  VENCIDO:        { color: 'rojo',    width: '100%' },
  CUMPLIDO:       { color: 'verde',   width: '100%' },
}

// 'YYYY-MM-DD' → 'DD/MM/YYYY' / 'DD/MM'. A mano y no con `Date`: el huso horario
// correría la fecha un día.
export function fechaLarga(iso) {
  if (!iso) return ''
  const [a, m, d] = iso.split('-')
  return `${d}/${m}/${a}`
}

export function fechaCorta(iso) {
  return iso ? fechaLarga(iso).slice(0, 5) : ''
}

const menos = (n) => (n < 0 ? `−${Math.abs(n)}` : `${n}`)   // U+2212, no el guion

// `plazo`: un elemento de `plazos` de la solicitud o de la fase.
//
// Devuelve lo que pinta la barra:
//   color, width  relleno semántico
//   tarde         cumplido fuera de plazo: roja con la punta verde. Es la evolución natural
//                 de la barra vencida (roja al 100 %): al notificar solo cambia el final.
//   parado        reloj parado por una suspensión viva (art. 22): rayada
//   dato          texto a la derecha; días en HÁBILES (el plazo legal va en meses)
//   datoRojo      el dato va en rojo (vencido o cumplido tarde)
//   titulo        tooltip con el detalle
export function barraDeActo(plazo) {
  const relleno = RELLENO[plazo.estado] || RELLENO.EN_PLAZO
  const cumplido = plazo.estado === 'CUMPLIDO'
  const vencido = plazo.estado === 'VENCIDO'
  const tarde = cumplido && !!plazo.cumplido_fuera_de_plazo
  const corriendo = plazo.estado === 'EN_PLAZO' || plazo.estado === 'PROXIMO_VENCER'
  const parado = !!plazo.suspendido && corriendo
  const dias = plazo.dias_restantes

  let dato
  if (cumplido) dato = `✓ ${fechaCorta(plazo.fecha_cumplimiento)}`
  else if (parado) dato = 'parado'
  else dato = dias === null || dias === undefined ? '' : `${menos(dias)} d`

  const partes = [plazo.acto.replace(/_/g, ' ')]
  if (cumplido) {
    partes.push(`notificada el ${fechaLarga(plazo.fecha_cumplimiento)}`)
    partes.push(`${tarde ? 'venció' : 'vencía'} el ${fechaLarga(plazo.fecha_limite)}${tarde ? ' (fuera de plazo)' : ''}`)
  } else if (vencido) {
    partes.push(`venció el ${fechaLarga(plazo.fecha_limite)}`)
    partes.push(`${Math.abs(dias)} días hábiles de retraso`)
  } else {
    partes.push(`vence el ${fechaLarga(plazo.fecha_limite)}`)
    if (dias !== null && dias !== undefined) partes.push(`${dias} días hábiles`)
  }
  if (parado) partes.push('reloj parado por suspensión (art. 22)')

  return {
    acto: plazo.acto.replace(/_/g, ' '),
    color: relleno.color,
    width: relleno.width,
    tarde,
    parado,
    dato,
    datoRojo: vencido || tarde,
    titulo: partes.join(' · '),
  }
}

// Alto de las filas del pie de plazos de una caja (nº de barras → px). Debe casar con
// el CSS de `.arbol-nodo__plazos` (arbol.css): el layout reserva este alto al colocar
// los niveles, y si no casa las cajas se pisan.
export const PLAZOS_PIE_H = 9     // padding + borde del pie
export const PLAZOS_FILA_H = 16   // una barra + su separación

export function altoPlazos(plazos) {
  const n = (plazos || []).length
  return n ? PLAZOS_PIE_H + n * PLAZOS_FILA_H : 0
}
