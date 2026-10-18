// DestinatarioTramite.jsx — a quién va el escrito de un ELABORAR (#929, A2; ADR-051 §H, §L;
// #1043, ADR-053 §C).
//
// El destinatario se decide al elaborar —el documento y la notificación tienen que decir lo
// mismo— y sin él no se genera el escrito. Es una tarjeta de la zona de datos, en lectura y en
// edición (criterio de Carlos, 13/10/2026: lo que sale en edición también se ve en lectura): en
// lectura es un dato; en edición, el mismo dato con el selector y el botón dentro de la misma
// tarjeta, como un control vivo en el mismo sitio y con el mismo rótulo.
//
// Tres situaciones, según el trámite (`GET …/tramite/<id>/destinatario`):
//   - `aplica` falso: el trámite no tiene un destinatario único (la ELABORACION de la
//     resolución no imprime destinatario): no se pinta nada.
//   - Resuelto sin elegir: sale de los datos del expediente (solicitante, organismo del
//     trámite); se muestra, no se elige.
//   - Se elige (boletín, ayuntamiento, ministerio, órgano superior u órgano ambiental en
//     su fase): selector entre las entidades del rol, solo en edición. Cambiable hasta el primer
//     justificante de la NOTIFICAR (§D).
//
// El cambio se guarda al pulsar el botón (`PUT …/tramite/<id>/destinatario`), de inmediato y fuera
// del borrador del marco: no es nuevo de #1043 (viene de #929) y está anotado en #1055. El estado
// lo comparten la tarjeta y el generador de escritos (`destinatarioEstado.js`).
import React from 'react'
import { useArbolStore } from '../../store.js'
import { useDestinatarioTramite } from '../../destinatarioEstado.js'
import { TarjetaDatos, CampoDato, ValorSoloLectura } from '../TarjetaDatos.jsx'
import SelectorEntidad from './SelectorEntidad.jsx'

export default function TarjetaDestinatarioTramite({ expedienteId, tramiteId }) {
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const cargar = useDestinatarioTramite((s) => s.cargar)
  const elegir = useDestinatarioTramite((s) => s.elegir)
  const enviando = useDestinatarioTramite((s) => s.enviando)
  const d = useDestinatarioTramite((s) => (s.tramiteId === tramiteId ? s.d : null))
  const error = useDestinatarioTramite((s) => (s.tramiteId === tramiteId ? s.error : null))
  const [entidadId, setEntidadId] = React.useState('')

  const elegidaAhora = d && d.destinatario ? d.destinatario.entidad_id : ''

  React.useEffect(() => { cargar(expedienteId, tramiteId) }, [cargar, expedienteId, tramiteId])
  React.useEffect(() => { setEntidadId(elegidaAhora) }, [elegidaAhora])

  if (error && !d) return <div className="text-danger small mb-3">{error}</div>
  if (!d || !d.aplica) return null

  const dest = d.destinatario
  const puedeElegir = modoEdicion && d.se_elige && d.cambiable
  const cambia = entidadId !== '' && entidadId !== elegidaAhora
  const textoBoton = dest ? 'Cambiar destinatario' : 'Elegir destinatario'

  return (
    <TarjetaDatos titulo="Destinatario del escrito" icono="fa-address-card">
      <CampoDato rotulo="Destinatario">
        {puedeElegir ? (
          <>
            <SelectorEntidad entidades={d.entidades} valor={entidadId} onChange={setEntidadId}
                             disabled={enviando} etiqueta={null} ariaLabel="Destinatario" />
            <button type="button" className="btn btn-sm btn-primary" disabled={enviando || !cambia}
                    onClick={() => elegir(expedienteId, tramiteId, entidadId, refrescarArbol)}>
              {enviando ? 'Guardando…' : textoBoton}
            </button>
          </>
        ) : (
          <ValorSoloLectura
            rotulo="Destinatario"
            valor={dest ? `${dest.nombre}${dest.nif ? ` · ${dest.nif}` : ''}` : 'Sin destinatario'} />
        )}
      </CampoDato>
      {dest && dest.en_nombre_de && (
        <CampoDato rotulo="En nombre de">
          <ValorSoloLectura rotulo="En nombre de" valor={dest.en_nombre_de} />
        </CampoDato>
      )}
      <CampoDato rotulo="Fuente">
        <ValorSoloLectura rotulo="Fuente" valor={d.fuente_etiqueta || '—'} />
      </CampoDato>

      {!dest && (
        <div className="col-12">
          <div className="alert alert-warning py-2 px-3 small mb-0">
            <div className="fw-semibold">No se genera el escrito sin destinatario.</div>
            {d.motivo && <div>{d.motivo}.</div>}
          </div>
        </div>
      )}
      {!d.se_elige && dest && (
        <div className="col-12 small text-muted">Sale de los datos del expediente; no se elige aquí.</div>
      )}
      {d.se_elige && !d.cambiable && (
        <div className="col-12 small text-muted">
          Fijo desde el primer justificante: ya se envió algo a este destinatario.
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
