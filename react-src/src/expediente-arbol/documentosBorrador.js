// documentosBorrador.js — los documentos vinculados de una tarea, tal y como van a quedar al guardar
// (#1044, ADR-053 §E decisión 7).
//
// En edición la zona de datos y la Despensa enseñaban los mismos vinculados. Queda una sola lista, la
// de la zona de datos, y en edición sale del borrador: lo que se quita desaparece de ella al
// momento y lo que se vincula desde el pool aparece; Cancelar lo devuelve todo a como estaba.
//
// Las filas de lo ya guardado vienen del detalle del nodo (con su `subrol` en una NOTIFICAR); las de
// lo que se acaba de vincular, del pool, que es la misma fila (`documento_fila`) pero sin vínculo
// con la tarea: su rol es el que dice el borrador y no tienen subrol (se fija al guardar).

/**
 * @param {Array}  documentosDetalle  `detalle.documentos`: lo guardado, con `rol` y, a veces, `subrol`.
 * @param {Object} borrador           `{documentos_consumidos_ids, documento_producido_id}` del store.
 * @param {Array}  pool               el pool del expediente (`/api/expedientes/<id>/pool`).
 * @returns {Array} filas con su `rol`; los consumidos primero y el producido al final.
 */
export function documentosDelBorrador(documentosDetalle, borrador, pool) {
  const guardados = documentosDetalle || []
  // Sin sembrar (entrando en edición, mientras llega el esquema): se enseña lo guardado.
  if (!borrador || borrador.documentos_consumidos_ids === undefined) return guardados

  const guardadoPorId = new Map(guardados.map((d) => [d.id, d]))
  const poolPorId = new Map((pool || []).map((d) => [d.id, d]))

  const fila = (id, rol) => {
    const guardado = guardadoPorId.get(id)
    const base = guardado || poolPorId.get(id)
    if (!base) return null
    // El subrol es del vínculo guardado: si el documento cambia de rol, deja de valer.
    const subrol = guardado && guardado.rol === rol ? guardado.subrol : undefined
    const { subrol: _viejo, ...resto } = base
    return subrol ? { ...resto, rol, subrol } : { ...resto, rol }
  }

  const filas = (borrador.documentos_consumidos_ids || []).map((id) => fila(id, 'CONSUMIDO'))
  if (borrador.documento_producido_id != null) filas.push(fila(borrador.documento_producido_id, 'PRODUCIDO'))
  return filas.filter(Boolean)
}
