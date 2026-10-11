// BloqueDestinatario.jsx — a quién se notifica en una NOTIFICAR (#929, A2; ADR-051 §B, §D, §H).
//
// Componente aparte del registro (`BloqueRegistro`) porque son dos asuntos con dos
// ritmos: el destinatario se fija antes del primer justificante y desde entonces
// queda fijo; el registro se va completando. Lee todo del payload de
// `GET …/notificar` (`notificaciones[0].destinatario` es la copia congelada;
// `destinatario` dice si se puede cambiar y si bloquea; `eleccion_destinatario`,
// cómo se elige) y escribe con `PUT …/notificar/destinatario`, que devuelve el
// payload nuevo.
//
// Quién lo elige depende de la fuente (`se_elige_en`):
//   - 'NOTIFICAR'  boletín, ayuntamiento, ministerio, órgano superior u órgano
//                  ambiental en un trámite sin ELABORAR: el selector está aquí.
//   - 'ELABORAR'   los mismos con ELABORAR delante: se elige al elaborar el escrito
//                  (el documento y la notificación tienen que decir lo mismo, §H);
//                  aquí solo se avisa.
//   - null         sale de los datos del expediente (solicitante, organismos…): no
//                  se elige; si falta algo, el motivo dice dónde ponerlo.
import React from 'react'
import { useArbolStore } from '../../store.js'
import { putNotificarDestinatario } from '../../api.js'
import { showToast } from '../../../shared/ui/toast.js'
import SelectorEntidad from './SelectorEntidad.jsx'

const fechaCorta = (iso) => (iso ? new Date(iso).toLocaleDateString('es-ES') : null)

function lineaDireccion(d) {
  const poblacion = [d.codigo_postal, d.municipio].filter(Boolean).join(' ')
  const provincia = d.provincia ? `(${d.provincia})` : ''
  return [d.direccion, [poblacion, provincia].filter(Boolean).join(' ')].filter(Boolean).join(', ')
}

// La copia congelada en la fila (ADR-051 §B): lo que se enviará, no lo que diga hoy la ficha.
function CopiaDestinatario({ copia }) {
  const direccion = lineaDireccion(copia)
  return (
    <div className="small mb-2">
      <div className="fw-semibold">
        {copia.nombre || '—'}{copia.nif ? <span className="text-muted fw-normal"> · {copia.nif}</span> : null}
      </div>
      {copia.en_nombre_de && (
        <div>
          en nombre de <span className="fw-semibold">{copia.en_nombre_de}</span>
          {copia.en_nombre_de_nif ? <span className="text-muted"> · {copia.en_nombre_de_nif}</span> : null}
        </div>
      )}
      <div className={direccion ? '' : 'text-muted fst-italic'}>{direccion || 'Sin dirección postal'}</div>
      {copia.email && <div>{copia.email}</div>}
      {(copia.dir3 || copia.sir) && (
        <div className="text-muted">
          {copia.dir3 ? `DIR3 ${copia.dir3}` : ''}{copia.dir3 && copia.sir ? ' · ' : ''}{copia.sir ? `SIR ${copia.sir}` : ''}
        </div>
      )}
      {copia.fijado_en && (
        <div className="text-muted">Copiado el {fechaCorta(copia.fijado_en)}</div>
      )}
    </div>
  )
}

export default function BloqueDestinatario({ expedienteId, tareaId, payload, onPayload }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const notif = payload.notificaciones[0] || null
  const copia = notif ? notif.destinatario : null
  const estado = payload.destinatario
  const eleccion = payload.eleccion_destinatario

  const [entidadId, setEntidadId] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)
  const [error, setError] = React.useState(null)

  // El selector parte de quien está elegido: el representado si se notifica a su
  // representante (`en_nombre_de_entidad_id`), o la entidad misma.
  const elegidaAhora = copia ? (copia.en_nombre_de_entidad_id || copia.entidad_id || '') : ''
  React.useEffect(() => { setEntidadId(elegidaAhora) }, [elegidaAhora])

  const puedeElegir = eleccion.se_elige_en === 'NOTIFICAR' && estado.editable
  const cambia = entidadId !== '' && entidadId !== elegidaAhora

  const enviar = async (body, mensaje) => {
    setEnviando(true)
    setError(null)
    try {
      const data = await putNotificarDestinatario(expedienteId, tareaId, body)
      onPayload(data)
      showToast(mensaje, 'success')
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      setError((e.payload && (e.payload.motivo || e.payload.error)) || e.message
        || 'No se pudo fijar el destinatario')
    } finally {
      setEnviando(false)
    }
  }

  const selector = (textoBoton, mensaje) => (
    <>
      <SelectorEntidad entidades={eleccion.entidades} valor={entidadId} onChange={setEntidadId}
                       disabled={enviando} etiqueta={`Destinatario (${eleccion.fuente_etiqueta})`} />
      <button type="button" className="btn btn-sm btn-primary" disabled={enviando || !cambia}
              onClick={() => enviar({ entidad_id: entidadId }, mensaje)}>
        {enviando ? 'Guardando…' : textoBoton}
      </button>
    </>
  )

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small d-flex justify-content-between">
        <span>Destinatario</span>
        <span className="fw-normal text-muted">{eleccion.fuente_etiqueta}</span>
      </div>
      <div className="card-body card-body-tinted">
        {estado.escape_sin_destinatario ? (
          <div className="alert alert-secondary py-2 px-3 small mb-0">
            Esta notificación avanzó sin destinatario por un escape justificado (queda en la
            bitácora) y ya no admite fijarlo.
          </div>
        ) : copia ? (
          <>
            <CopiaDestinatario copia={copia} />
            {estado.editable ? (
              <>
                {puedeElegir && <div className="mt-2">{selector('Cambiar destinatario', 'Destinatario cambiado')}</div>}
                <div className={puedeElegir ? 'mt-2' : ''}>
                  <button type="button" className="btn btn-sm btn-outline-secondary" disabled={enviando}
                          title="Vuelve a copiar la dirección que tiene hoy la entidad"
                          onClick={() => enviar({}, 'Destinatario refrescado')}>
                    {enviando ? '…' : 'Refrescar datos'}
                  </button>
                  <span className="small text-muted ms-2">Posible hasta el primer justificante.</span>
                </div>
              </>
            ) : (
              <div className="small text-muted">
                Fijo desde el primer justificante: ya se envió algo a este destinatario.
              </div>
            )}
          </>
        ) : (
          <>
            <div className="alert alert-warning py-2 px-3 small mb-2">
              <div className="fw-semibold">Sin destinatario no se puede vincular ningún documento.</div>
              {eleccion.motivo && <div>{eleccion.motivo}.</div>}
            </div>
            {puedeElegir && selector('Fijar destinatario', 'Destinatario fijado')}
            {eleccion.se_elige_en === 'ELABORAR' && (
              <div className="small">
                Se elige al elaborar el escrito del trámite: hazlo desde su tarea Elaborar y
                vuelve aquí.
              </div>
            )}
            {!eleccion.se_elige_en && !eleccion.motivo && (
              <button type="button" className="btn btn-sm btn-primary" disabled={enviando}
                      onClick={() => enviar({}, 'Destinatario fijado')}>
                {enviando ? 'Guardando…' : 'Tomar el destinatario que corresponde'}
              </button>
            )}
            <div className="small text-muted mt-2">
              Vincular un documento sin destinatario exige una justificación y es irreversible:
              la tarea queda sin destinatario para siempre y el certificado de cierre lo
              relata como salvado.
            </div>
          </>
        )}
        {error && <div className="alert alert-danger py-2 px-3 small mt-2 mb-0">{error}</div>}
      </div>
    </div>
  )
}
