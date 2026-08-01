// sellado.js — Sellado de fase cerrada (#720, ADR-036 §6 capa 4).
//
// Determina si la selección actual del árbol cuelga de una fase FINALIZADA.
// Mismo criterio que el backend (invariantes_esftt._fase_de): la fase misma
// para sujeto FASE, la fase contenedora para TRAMITE/TAREA. SOLICITUD y
// EXPEDIENTE no cuelgan de ninguna fase — nunca sellados por este criterio.
//
// Solo condiciona la UI (oculta/deshabilita controles que el backend rechazaría
// de todos modos, capas 1-3 del ADR): la garantía de integridad vive en el
// backend, no aquí.

export function faseDeSeleccion(arbol, seleccion) {
  if (!arbol || !seleccion) return null
  for (const sol of arbol.solicitudes || []) {
    for (const fase of sol.fases || []) {
      if (seleccion.tipo === 'fase' && fase.id === seleccion.id) return fase
      for (const tr of fase.tramites || []) {
        if (seleccion.tipo === 'tramite' && tr.id === seleccion.id) return fase
        for (const ta of tr.tareas || []) {
          if (seleccion.tipo === 'tarea' && ta.id === seleccion.id) return fase
        }
      }
    }
  }
  return null
}

export function estaSellado(arbol, seleccion) {
  const fase = faseDeSeleccion(arbol, seleccion)
  return !!fase && fase.estado === 'FINALIZADA'
}
