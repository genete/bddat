// MarcasEdicto.jsx — qué notificaciones del trámite van por edicto (#1037; ADR-052 §A y §G).
//
// Es la tarjeta «Notificaciones por edicto» del trámite NOTIFICACION de una fase finalizadora.
// La marca la pone el usuario (no se deduce de los intentos): en edición, una casilla por cada
// `NOTIFICAR` cuyo destinatario admite edicto (interesados reconocidos, propietarios DUP); en
// lectura, las mismas filas con la casilla fija. Las marcas viajan en el borrador del inspector
// (`notificaciones_edicto`, la lista de ids de tarea) y se guardan con el Guardar de siempre, así
// que no hay botón propio.
//
// Los datos de cada fila los pone el servidor (`app/services/marcas_edicto.py`); aquí solo se
// agrupan. Arriba van las marcadas y las que ya han fallado alguna vez —lo que hay que decidir—;
// plegadas, las que siguen su curso y las ya cerradas, que no hace falta mirar. Una fila con
// `bloqueo` no se puede cambiar hoy (cerrada, o su edicto ya está remitido al BOE) y dice por qué.
//
// El servidor ofrece las candidatas y acepta las mismas (contrato de selector de #1038): si hay
// marcas sobre notificaciones que ya no lo son, llegan en `aviso` y se conservan al guardar.
import React from 'react'
import { useArbolStore } from '../../store.js'
import { TarjetaDatos } from '../TarjetaDatos.jsx'

const CAMPO = 'notificaciones_edicto'

// Lo que se ve en una fila además del nombre: el estado en llano, los intentos fallidos y, si es
// el caso, que está recogida por un edicto.
function Detalle({ fila }) {
  const partes = []
  if (fila.cerrada) partes.push('Cerrada')
  else if (fila.motivo) partes.push(fila.motivo)
  if (fila.intentos_fallidos > 0) {
    partes.push(fila.intentos_fallidos === 1 ? '1 intento fallido' : `${fila.intentos_fallidos} intentos fallidos`)
  }
  return (
    <span className="d-block small text-muted">
      {partes.join(' · ')}
      {fila.recogida && <span className="badge text-bg-info ms-1">En un edicto</span>}
      {fila.sin_destinatario && <span className="badge text-bg-warning ms-1">Sin destinatario</span>}
    </span>
  )
}

function Fila({ fila, marcada, editable, onToggle }) {
  // En lectura, el mismo recuadro que `CasillaSoloLectura`: una casilla deshabilitada se ve
  // desvaída y lo marcado es justo lo que hay que leer.
  if (!editable) {
    return (
      <div className="d-flex mb-2">
        <i className={`fas ${marcada ? 'fa-check-square text-warning' : 'fa-square text-secondary'} me-2 mt-1`}
           role="img" aria-label={marcada ? 'Va por edicto' : 'No va por edicto'} />
        <div>
          <span className="fw-semibold">{fila.texto}</span>
          <Detalle fila={fila} />
        </div>
      </div>
    )
  }
  const id = `edicto-marca-${fila.valor}`
  return (
    <div className="form-check mb-2">
      <input type="checkbox" className="form-check-input" id={id} checked={marcada}
             disabled={!!fila.bloqueo} onChange={() => onToggle(fila.valor)} />
      <label className="form-check-label" htmlFor={id}>
        <span className="fw-semibold">{fila.texto}</span>
        <Detalle fila={fila} />
      </label>
      {fila.bloqueo && <span className="d-block small text-warning-emphasis">{fila.bloqueo}</span>}
    </div>
  )
}

// ¿Va arriba? Lo marcado y lo que ya ha fallado sin cerrarse: lo que hay que decidir.
const aDecidir = (fila, marcada) => marcada || (!fila.cerrada && fila.intentos_fallidos > 0)

export default function TarjetaMarcasEdicto({ detalle }) {
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const editables = useArbolStore((s) => s.editableCampos)
  const borrador = useArbolStore((s) => s.borrador)
  const setCampo = useArbolStore((s) => s.setCampo)

  const marcas = detalle && detalle.marcas_edicto
  if (!marcas) return null

  // En edición manda el borrador (lo que el usuario va marcando); en lectura, lo guardado.
  const vivo = modoEdicion ? (editables || []).find((c) => c.campo === CAMPO) : null
  const filas = vivo ? vivo.opciones : marcas.filas
  const ids = vivo ? (borrador[CAMPO] || []) : marcas.marcadas
  const marcadas = new Set(ids)
  const aviso = (vivo && vivo.aviso) || marcas.aviso

  // Solo se añade o se quita el id pulsado: las marcas que no son opción siguen donde estaban.
  const alternar = (valor) => {
    const siguiente = marcadas.has(valor) ? ids.filter((i) => i !== valor) : [...ids, valor]
    setCampo(CAMPO, siguiente.sort((a, b) => a - b))
  }

  const arriba = filas.filter((f) => aDecidir(f, marcadas.has(f.valor)))
  const plegadas = filas.filter((f) => !aDecidir(f, marcadas.has(f.valor)))
  const pinta = (f) => (
    <Fila key={f.valor} fila={f} marcada={marcadas.has(f.valor)} editable={!!vivo} onToggle={alternar} />
  )

  return (
    <TarjetaDatos titulo="Notificaciones por edicto" icono="fa-bullhorn">
      <div className="col-12">
        <p className="small text-muted mb-2">
          Las marcadas se publicarán por anuncio. Se recogen al crear en esta fase el trámite
          «Notificación edictal»; hasta que se remita al BOE se pueden quitar.
        </p>
        {aviso && <div className="alert alert-warning py-2 px-3 small">{aviso}</div>}
        {arriba.length === 0 && (
          <p className="small text-muted mb-2">Ninguna notificación marcada ni fallida por ahora.</p>
        )}
        {arriba.map(pinta)}
        {plegadas.length > 0 && (
          <details className="mt-2">
            <summary className="small text-muted">
              {plegadas.length === 1 ? '1 notificación más' : `${plegadas.length} notificaciones más`}
              {' '}(en curso o ya cerradas)
            </summary>
            <div className="mt-2">{plegadas.map(pinta)}</div>
          </details>
        )}
      </div>
    </TarjetaDatos>
  )
}
