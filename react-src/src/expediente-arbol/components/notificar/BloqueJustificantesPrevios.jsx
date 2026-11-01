// BloqueJustificantesPrevios.jsx — los justificantes previos de la NOTIFICAR (#929, A1; #1043,
// ADR-053 §C).
//
// Puesta a disposición en Notifica, intentos postales fallidos y justificante de sede
// (`TIPOS_JUSTIFICANTE_PREVIO`): se vinculan como CONSUMIDO y son presupuesto del
// justificante final, nunca el documento que se notifica (ADR-049 §B/§C). Solo se
// listan, por separado del registro: se vinculan desde la Despensa de abajo, que es el
// único sitio (decisión 1 de #929, resuelta en «no»: sin atajo de subida por tipo).
//
// Tarjeta de datos igual en lectura y en edición: es una lista, no tiene control vivo. Cada documento
// es la fila común (#1044, ADR-053 §E); sin rótulo de rol, porque el título de la tarjeta ya lo dice.
import React from 'react'
import { TarjetaDatos } from '../TarjetaDatos.jsx'
import FilaDocumento from '../FilaDocumento.jsx'

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
          <ul className="list-group list-group-flush">
            {previos.map((d) => (
              <li key={d.id} className="list-group-item px-0 py-2 bg-transparent">
                <FilaDocumento doc={d} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </TarjetaDatos>
  )
}
