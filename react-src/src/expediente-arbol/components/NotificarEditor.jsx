// NotificarEditor.jsx — las tarjetas de la tarea NOTIFICAR (#657/#658/#712, ADR-034; rehecho en
// #929, zona A: tramitarla en el navegador; migrado a las tarjetas de datos en #1043, ADR-053 §C).
//
// La NOTIFICAR ya usa el diseño de datos de la tarea (`superficiesTarea.js`): lo suyo son tarjetas de
// la zona de datos, iguales en lectura y en edición (criterio de Carlos, 13/10/2026: lo que sale en
// edición también se ve en lectura), y no tiene acciones propias en la zona de acciones: los controles
// vivos son campos de sus tarjetas, en el mismo sitio y con el mismo rótulo que su valor en lectura.
// Solo carga el payload de `GET …/notificar` y reparte; cada cosa vive en su componente de `notificar/`:
//   - aviso «Notificación al solicitante»
//   - BloqueDestinatario            a quién se notifica y cómo se elige (A2)
//   - BloqueRegistro                justificante final, resultado, sede, fechas (A1)
//   - BloqueJustificantesPrevios    lo vinculado como consumido, por separado
//
// Los bloques persisten por su cuenta y de inmediato, fuera del par Guardar/Cancelar de la cabecera
// (superficie de trabajo, ADR-023 §5 bis; el aviso de lo que «Cerrar» descarta es de #1055). La
// Despensa NO se deshabilita aquí (a diferencia de ANALIZAR): sigue siendo donde se vinculan los
// justificantes previos y la vía manual del final.
//
// El payload que devuelve cada escritura (PATCH, PUT destinatario) es el mismo de GET: los bloques lo
// pasan a `onPayload` y la pantalla queda como la dice el servidor, sin recargar. Vive en
// `useNotificarTarea`, con el id de la tarea, para no parpadear al refrescar el árbol.
import React from 'react'
import { useNotificarTarea } from '../notificarEstado.js'
import BloqueDestinatario from './notificar/BloqueDestinatario.jsx'
import BloqueRegistro from './notificar/BloqueRegistro.jsx'
import BloqueJustificantesPrevios from './notificar/BloqueJustificantesPrevios.jsx'

export function TarjetasNotificar({ expedienteId, tareaId, soloLectura }) {
  const tareaCargada = useNotificarTarea((s) => s.tareaId)
  const payloadStore = useNotificarTarea((s) => s.payload)
  const error = useNotificarTarea((s) => s.error)
  const cargar = useNotificarTarea((s) => s.cargar)
  const poner = useNotificarTarea((s) => s.poner)
  // Los bloques parten del payload con su propio formulario (el registro lo copia al montarse):
  // por eso no se pintan hasta que llega el de esta visita, y no el que quedó en el store de otra.
  const [pedidaPara, setPedidaPara] = React.useState(null)

  React.useEffect(() => {
    let vigente = true
    setPedidaPara(null)
    cargar(expedienteId, tareaId).then(() => { if (vigente) setPedidaPara(tareaId) })
    return () => { vigente = false }
  }, [cargar, expedienteId, tareaId])

  const payload = pedidaPara === tareaId && tareaCargada === tareaId ? payloadStore : null
  const onPayload = React.useCallback((p) => poner(tareaId, p), [poner, tareaId])

  if (!payload) {
    if (error) {
      return <div className="text-danger small mb-3">No se pudo cargar la notificación: {error}</div>
    }
    return <div className="text-muted small mb-3">Cargando…</div>
  }

  return (
    <>
      {payload.es_notificacion_del_solicitante && (
        <div className="alert alert-info py-2 px-3 small">
          <strong>Notificación al solicitante.</strong> Su fecha de cumplimiento es la que cuenta
          para el plazo de resolver del acto.
        </div>
      )}
      <BloqueDestinatario expedienteId={expedienteId} tareaId={tareaId}
                          payload={payload} onPayload={onPayload} soloLectura={soloLectura} />
      <BloqueRegistro key={tareaId} expedienteId={expedienteId} tareaId={tareaId}
                      payload={payload} onPayload={onPayload} soloLectura={soloLectura} />
      <BloqueJustificantesPrevios previos={payload.justificantes_previos} soloLectura={soloLectura} />
    </>
  )
}
