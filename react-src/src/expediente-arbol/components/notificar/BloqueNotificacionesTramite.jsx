// BloqueNotificacionesTramite.jsx — a quién falta notificar en un trámite (#929, A2; ADR-051 §D, §E).
//
// Vive en el inspector del trámite en modo edición, junto al Editor genérico (como
// `AccionesFaseConsultas` en la fase). Lee `GET …/tramite/<id>/notificaciones` y pinta
// lo que diga el servidor: las fuentes del trámite según el catálogo, y `textos` —los
// «falta notificar a X» y «sobra la notificación a Y» ya redactados— de forma genérica,
// que es la idea que #980 aplicará al resto de trámites («¿qué falta?» estructural).
// El botón «añadir las notificaciones que faltan» es el mismo en todos los trámites:
// idempotente, refresca las que no han salido, rellena las vacías y crea las que faltan.
// Lo que no puede resolver (a quién hay que elegir) lo devuelve en `pendientes`.
//
// Un trámite sin fuentes en el catálogo (`fuentes` vacío) no notifica a nadie: no se pinta.
import React from 'react'
import { useArbolStore } from '../../store.js'
import { getNotificacionesTramite, postAnadirFaltan } from '../../api.js'
import { showToast } from '../../../shared/ui/toast.js'

function resumen(res) {
  const partes = []
  if (res.creadas.length) partes.push(`${res.creadas.length} creada(s)`)
  if (res.rellenadas.length) partes.push(`${res.rellenadas.length} con destinatario`)
  if (res.refrescadas.length) partes.push(`${res.refrescadas.length} con la dirección actualizada`)
  return partes.length ? partes.join(', ') : 'No había nada que añadir ni refrescar'
}

export default function BloqueNotificacionesTramite({ expedienteId, tramiteId }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const [estado, setEstado] = React.useState(null)
  const [pendientes, setPendientes] = React.useState([])
  const [enviando, setEnviando] = React.useState(false)
  const [error, setError] = React.useState(null)

  React.useEffect(() => {
    let cancelado = false
    setEstado(null)
    setPendientes([])
    setError(null)
    getNotificacionesTramite(expedienteId, tramiteId)
      .then((data) => { if (!cancelado) setEstado(data) })
      .catch((e) => { if (!cancelado) setError((e && e.message) || 'No se pudo cargar las notificaciones') })
    return () => { cancelado = true }
  }, [expedienteId, tramiteId])

  if (error && !estado) return <div className="text-danger small mb-3">{error}</div>
  if (!estado || estado.fuentes.length === 0) return null

  const anadir = async () => {
    setEnviando(true)
    setError(null)
    try {
      const res = await postAnadirFaltan(expedienteId, tramiteId)
      setEstado(res.estado)
      setPendientes(res.pendientes || [])
      showToast(resumen(res), 'success')
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      setError((e.payload && (e.payload.error || e.payload.motivo)) || e.message
        || 'No se pudieron añadir las notificaciones')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Notificaciones del trámite</div>
      <div className="card-body card-body-tinted">
        <div className="small mb-2">
          <span className="text-muted">Se notifica a: </span>
          {estado.fuentes.map((f) => estado.fuentes_etiquetas[f] || f).join(' · ')}
        </div>

        {estado.completo ? (
          <div className="alert alert-success py-2 px-3 small">Nadie falta ni sobra.</div>
        ) : (
          <ul className="alert alert-warning py-2 ps-4 pe-3 small mb-2">
            {estado.textos.map((t) => <li key={t}>{t}</li>)}
          </ul>
        )}

        {pendientes.length > 0 && (
          <div className="small text-muted mb-2">
            El botón no puede resolver:
            <ul className="mb-0">{pendientes.map((t) => <li key={t}>{t}</li>)}</ul>
          </div>
        )}

        <button type="button" className="btn btn-sm btn-primary" disabled={enviando} onClick={anadir}>
          {enviando ? 'Añadiendo…' : 'Añadir las notificaciones que faltan'}
        </button>
        <div className="small text-muted mt-1">
          Crea las que faltan y actualiza la dirección de las que aún no han salido. Las que
          sobran no se tocan: se corrige su origen y se borran a mano.
        </div>
        {error && <div className="alert alert-danger py-2 px-3 small mt-2 mb-0">{error}</div>}
      </div>
    </div>
  )
}
