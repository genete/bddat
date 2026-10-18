// BloqueJustificantesPrevios.jsx — los justificantes previos de la NOTIFICAR (#929, A1; #1043,
// ADR-053 §C).
//
// Puesta a disposición en Notifica, intentos postales fallidos y justificante de sede
// (`TIPOS_JUSTIFICANTE_PREVIO`): se vinculan como CONSUMIDO y son presupuesto del
// justificante final, nunca el documento que se notifica (ADR-049 §B/§C). Solo se
// listan, por separado del registro: se vinculan desde la Despensa de abajo, que es el
// único sitio (decisión 1 de #929, resuelta en «no»: sin atajo de subida por tipo).
//
// Tarjeta de datos igual en lectura y en edición: es una lista, no tiene control vivo.
import React from 'react'
import { TarjetaDatos } from '../TarjetaDatos.jsx'
import EnlaceDocumento from './EnlaceDocumento.jsx'

const fechaIso = (iso) => (iso ? iso.split('-').reverse().join('/') : null)

export default function BloqueJustificantesPrevios({ previos, soloLectura }) {
  return (
    <TarjetaDatos titulo="Justificantes previos" icono="fa-paperclip">
      <div className="col-12">
        {previos.length === 0 ? (
          <div className="small text-muted fst-italic">
            {soloLectura
              ? 'Ninguno vinculado.'
              : 'Ninguno vinculado. Si los hay (puesta a disposición, intentos postales fallidos, '
                + 'sede), se vinculan como consumidos desde la Despensa.'}
          </div>
        ) : (
          <ul className="list-unstyled small mb-0">
            {previos.map((d) => (
              <li key={d.id} className="mb-1">
                <div className="d-flex align-items-center gap-2">
                  <i className="bi bi-file-earmark" />
                  <EnlaceDocumento doc={d} />
                </div>
                <div className="text-muted ms-4">
                  {d.tipo_doc || d.tipo_doc_codigo}
                  {d.fecha_administrativa ? ` · ${fechaIso(d.fecha_administrativa)}` : ' · sin fecha'}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </TarjetaDatos>
  )
}
