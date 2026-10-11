// BloqueDestinatarioTramite.jsx — a quién va el escrito de un ELABORAR (#929, A2; ADR-051 §H, §L).
//
// El destinatario se decide al elaborar —el documento y la notificación tienen que
// decir lo mismo— y sin él no se genera el escrito. Antes solo se podía elegir al
// generarlo: sin plantilla, o con el escrito subido a mano, la única salida era el
// escape irreversible de la NOTIFICAR, y una vez elegido no había cómo cambiarlo. Este
// bloque lo elige o lo cambia sin generar nada, con `PUT …/tramite/<id>/destinatario`.
//
// Tres situaciones, según el trámite (`GET …/tramite/<id>/destinatario`):
//   - `aplica` falso: el trámite no tiene un destinatario único (la ELABORACION de la
//     resolución no imprime destinatario): no se pinta nada.
//   - Resuelto sin elegir: sale de los datos del expediente (solicitante, organismo del
//     trámite); se muestra, no se elige.
//   - Se elige (boletín, ayuntamiento, ministerio, órgano superior u órgano ambiental en
//     su fase): selector entre las entidades del rol. Cambiable hasta el primer
//     justificante de la NOTIFICAR (§D).
import React from 'react'
import { useArbolStore } from '../../store.js'
import { getDestinatarioTramite, putDestinatarioTramite } from '../../api.js'
import { showToast } from '../../../shared/ui/toast.js'
import SelectorEntidad from './SelectorEntidad.jsx'

export default function BloqueDestinatarioTramite({ expedienteId, tramiteId, version, onCambio }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const [d, setD] = React.useState(null)
  const [entidadId, setEntidadId] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)
  const [error, setError] = React.useState(null)

  const elegidaAhora = d && d.destinatario ? d.destinatario.entidad_id : ''

  React.useEffect(() => {
    let cancelado = false
    setD(null)
    getDestinatarioTramite(expedienteId, tramiteId)
      .then((data) => { if (!cancelado) setD(data) })
      .catch((e) => { if (!cancelado) setError((e && e.message) || 'No se pudo cargar el destinatario') })
    return () => { cancelado = true }
  }, [expedienteId, tramiteId, version])

  React.useEffect(() => { setEntidadId(elegidaAhora) }, [elegidaAhora])

  if (error && !d) return <div className="text-danger small mb-3">{error}</div>
  if (!d || !d.aplica) return null

  const cambia = entidadId !== '' && entidadId !== elegidaAhora

  const elegir = async () => {
    setEnviando(true)
    setError(null)
    try {
      const data = await putDestinatarioTramite(expedienteId, tramiteId, { entidad_id: entidadId })
      setD(data)
      showToast('Destinatario del trámite guardado', 'success')
      if (onCambio) onCambio()
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      setError((e.payload && (e.payload.motivo || e.payload.error)) || e.message
        || 'No se pudo guardar el destinatario')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small d-flex justify-content-between">
        <span>Destinatario del escrito</span>
        <span className="fw-normal text-muted">{d.fuente_etiqueta}</span>
      </div>
      <div className="card-body card-body-tinted">
        {d.destinatario ? (
          <div className="small mb-2">
            <span className="fw-semibold">{d.destinatario.nombre}</span>
            {d.destinatario.nif && <span className="text-muted"> · {d.destinatario.nif}</span>}
            {d.destinatario.en_nombre_de && (
              <div>en nombre de <span className="fw-semibold">{d.destinatario.en_nombre_de}</span></div>
            )}
          </div>
        ) : (
          <div className="alert alert-warning py-2 px-3 small mb-2">
            <div className="fw-semibold">No se genera el escrito sin destinatario.</div>
            {d.motivo && <div>{d.motivo}.</div>}
          </div>
        )}

        {!d.se_elige && d.destinatario && (
          <div className="small text-muted">Sale de los datos del expediente; no se elige aquí.</div>
        )}

        {d.se_elige && d.cambiable && (
          <>
            <SelectorEntidad entidades={d.entidades} valor={entidadId} onChange={setEntidadId}
                             disabled={enviando}
                             etiqueta={d.destinatario ? 'Cambiar destinatario' : 'Elegir destinatario'} />
            <button type="button" className="btn btn-sm btn-primary" disabled={enviando || !cambia}
                    onClick={elegir}>
              {enviando ? 'Guardando…' : d.destinatario ? 'Cambiar destinatario' : 'Elegir destinatario'}
            </button>
          </>
        )}
        {d.se_elige && !d.cambiable && (
          <div className="small text-muted">
            Fijo desde el primer justificante: ya se envió algo a este destinatario.
          </div>
        )}
        {error && <div className="alert alert-danger py-2 px-3 small mt-2 mb-0">{error}</div>}
      </div>
    </div>
  )
}
