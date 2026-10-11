// SelectorEntidad.jsx — elegir una entidad entre las que da el servidor (#929, A2).
//
// La lista viene hecha del servidor (`entidades_elegibles`: las del rol de la fuente,
// ADR-051 §C) y aquí solo se elige. Con pocas, un desplegable; a partir de
// UMBRAL_BUSCADOR se pone encima un filtro de texto. El umbral es una estimación: no
// se ha comprobado cuántos organismos con rol de consultado habrá en producción.
// Lo comparten el bloque del destinatario de la NOTIFICAR y el del ELABORAR.
import React from 'react'

export const UMBRAL_BUSCADOR = 12

const normalizar = (s) => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export default function SelectorEntidad({
  entidades, valor, onChange, disabled, etiqueta = 'Entidad', textoVacio = '— Selecciona —',
}) {
  const [filtro, setFiltro] = React.useState('')
  const hayBuscador = entidades.length > UMBRAL_BUSCADOR
  const f = normalizar(filtro.trim())
  // La elegida se mantiene aunque el filtro la excluya, para no vaciar el desplegable.
  const visibles = hayBuscador && f
    ? entidades.filter((e) => e.id === valor || normalizar(`${e.nombre} ${e.nif || ''}`).includes(f))
    : entidades

  return (
    <div className="mb-2">
      <label className="form-label small text-muted mb-1">{etiqueta}</label>
      {hayBuscador && (
        <input type="search" className="form-control form-control-sm mb-1" value={filtro}
               placeholder="Filtrar por nombre o NIF…" disabled={disabled}
               onChange={(e) => setFiltro(e.target.value)} />
      )}
      <select className="form-select form-select-sm" value={valor} disabled={disabled}
              onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}>
        <option value="">{textoVacio}</option>
        {visibles.map((e) => (
          <option key={e.id} value={e.id}>{e.nombre}{e.nif ? ` (${e.nif})` : ''}</option>
        ))}
      </select>
      {hayBuscador && f && visibles.length === 0 && (
        <div className="small text-muted fst-italic mt-1">Ninguna entidad coincide.</div>
      )}
    </div>
  )
}
