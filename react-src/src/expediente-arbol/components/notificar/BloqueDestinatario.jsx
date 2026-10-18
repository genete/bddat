// BloqueDestinatario.jsx — a quién se notifica en una NOTIFICAR (#929, A2; ADR-051 §B, §D, §H;
// #1043, ADR-053 §C).
//
// Tarjeta de la zona de datos, en lectura y en edición (criterio de Carlos, 13/10/2026: lo que sale
// en edición también se ve en lectura). En lectura es la copia congelada del destinatario; en
// edición, esa misma copia y, dentro de la misma tarjeta, los controles vivos: el selector, «Refrescar
// datos» y «Fijar / Tomar destinatario». La copia no se sustituye por el selector (*interpretación*):
// es lo que se enviará, y el selector es lo que se elegiría de nuevo.
//
// Componente aparte del registro (`BloqueRegistro`) porque son dos asuntos con dos
// ritmos: el destinatario se fija antes del primer justificante y desde entonces
// queda fijo; el registro se va completando. Lee todo del payload de
// `GET …/notificar` (`notificaciones[0].destinatario` es la copia congelada;
// `destinatario` dice si se puede cambiar y si bloquea; `eleccion_destinatario`,
// cómo se elige) y escribe con `PUT …/notificar/destinatario`, que devuelve el
// payload nuevo. Esos PUT guardan de inmediato, fuera del borrador del marco: viene de #929 y está
// anotado en #1055.
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
import { TarjetaDatos, CampoDato, ValorSoloLectura } from '../TarjetaDatos.jsx'
import SelectorEntidad from './SelectorEntidad.jsx'

const fechaCorta = (iso) => (iso ? new Date(iso).toLocaleDateString('es-ES') : null)

function lineaDireccion(d) {
  const poblacion = [d.codigo_postal, d.municipio].filter(Boolean).join(' ')
  const provincia = d.provincia ? `(${d.provincia})` : ''
  return [d.direccion, [poblacion, provincia].filter(Boolean).join(' ')].filter(Boolean).join(', ')
}

// La copia congelada en la fila (ADR-051 §B): lo que se enviará, no lo que diga hoy la ficha.
function CamposCopia({ copia }) {
  const direccion = lineaDireccion(copia)
  const nombre = `${copia.nombre || '—'}${copia.nif ? ` · ${copia.nif}` : ''}`
  const enNombreDe = copia.en_nombre_de
    ? `${copia.en_nombre_de}${copia.en_nombre_de_nif ? ` · ${copia.en_nombre_de_nif}` : ''}` : null
  const dir3sir = [copia.dir3 ? `DIR3 ${copia.dir3}` : '', copia.sir ? `SIR ${copia.sir}` : '']
    .filter(Boolean).join(' · ')
  return (
    <>
      <CampoDato rotulo="Destinatario">
        <ValorSoloLectura rotulo="Destinatario" valor={nombre} />
      </CampoDato>
      {enNombreDe && (
        <CampoDato rotulo="En nombre de">
          <ValorSoloLectura rotulo="En nombre de" valor={enNombreDe} />
        </CampoDato>
      )}
      <CampoDato rotulo="Dirección">
        <ValorSoloLectura rotulo="Dirección" valor={direccion || 'Sin dirección postal'} />
      </CampoDato>
      {copia.email && (
        <CampoDato rotulo="Correo electrónico">
          <ValorSoloLectura rotulo="Correo electrónico" valor={copia.email} />
        </CampoDato>
      )}
      {dir3sir && (
        <CampoDato rotulo="DIR3 / SIR">
          <ValorSoloLectura rotulo="DIR3 / SIR" valor={dir3sir} />
        </CampoDato>
      )}
      {copia.fijado_en && (
        <CampoDato rotulo="Copiado el">
          <ValorSoloLectura rotulo="Copiado el" valor={fechaCorta(copia.fijado_en)} />
        </CampoDato>
      )}
    </>
  )
}

export default function BloqueDestinatario({ expedienteId, tareaId, payload, onPayload, soloLectura }) {
  const refrescarArbolSilencioso = useArbolStore((s) => s.refrescarArbolSilencioso)
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
      await refrescarArbolSilencioso()
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
    <TarjetaDatos titulo="Destinatario" icono="fa-address-card">
      {copia && !estado.escape_sin_destinatario && <CamposCopia copia={copia} />}
      <CampoDato rotulo="Fuente">
        <ValorSoloLectura rotulo="Fuente" valor={eleccion.fuente_etiqueta || '—'} />
      </CampoDato>

      {estado.escape_sin_destinatario ? (
        <div className="col-12">
          <div className="alert alert-secondary py-2 px-3 small mb-0">
            Esta notificación avanzó sin destinatario por un escape justificado (queda en la
            bitácora) y ya no admite fijarlo.
          </div>
        </div>
      ) : copia ? (
        estado.editable ? (
          !soloLectura && (
            <div className="col-12">
              {puedeElegir && <div className="mb-2">{selector('Cambiar destinatario', 'Destinatario cambiado')}</div>}
              <div>
                <button type="button" className="btn btn-sm btn-outline-secondary" disabled={enviando}
                        title="Vuelve a copiar la dirección que tiene hoy la entidad"
                        onClick={() => enviar({}, 'Destinatario refrescado')}>
                  {enviando ? '…' : 'Refrescar datos'}
                </button>
                <span className="small text-muted ms-2">Posible hasta el primer justificante.</span>
              </div>
            </div>
          )
        ) : (
          <div className="col-12 small text-muted">
            Fijo desde el primer justificante: ya se envió algo a este destinatario.
          </div>
        )
      ) : (
        <div className="col-12">
          <div className="alert alert-warning py-2 px-3 small mb-2">
            <div className="fw-semibold">Sin destinatario no se puede vincular ningún documento.</div>
            {eleccion.motivo && <div>{eleccion.motivo}.</div>}
          </div>
          {!soloLectura && puedeElegir && selector('Fijar destinatario', 'Destinatario fijado')}
          {eleccion.se_elige_en === 'ELABORAR' && (
            <div className="small">
              Se elige al elaborar el escrito del trámite: hazlo desde su tarea Elaborar y
              vuelve aquí.
            </div>
          )}
          {!soloLectura && !eleccion.se_elige_en && !eleccion.motivo && (
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
        </div>
      )}
      {error && (
        <div className="col-12">
          <div className="alert alert-danger py-2 px-3 small mb-0">{error}</div>
        </div>
      )}
    </TarjetaDatos>
  )
}
