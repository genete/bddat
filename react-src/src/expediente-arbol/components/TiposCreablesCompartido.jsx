// TiposCreablesCompartido.jsx — pieza común a Despensa.jsx (panel) y
// MenuContextual.jsx (submenú "Crear hijo"), ADR-016 §8/§10, #725 tarea 6.
//
// Misma base de código en las dos superficies; el envoltorio visual se adapta
// al contenedor vía `variante` ('panel' | 'menu'). Motivo del reparto: desde
// ADR-037 §D el listado de tipos-creables (canonicos/resto) es puramente
// didáctico y ya no evalúa el motor por candidato — el veredicto de permiso
// solo se conoce al intentar crear de verdad (mutaciones_arbol.py). Por eso
// ya no hay "chip bloqueado" al listar: cualquier tipo listado es clicable, y
// el bloqueo (si lo hay) se revela aquí tras el intento, no antes.
import React from 'react'

// Fila de un tipo creable: código visible (compacto, escaneable), nombre
// completo en tooltip nativo (title=) — mismo patrón en panel y menú.
export function FilaTipoCreable({ tipo, variante, seleccionado, onClick, draggable, onDragStart }) {
  if (variante === 'menu') {
    return (
      <div
        className={`arbol-menu__item${seleccionado ? ' arbol-menu__item--activo' : ''}`}
        title={tipo.nombre}
        onClick={onClick}
      >
        {tipo.codigo}
      </div>
    )
  }
  return (
    <div
      className={`btn btn-sm w-100 text-start border rounded px-2 py-1 ${
        seleccionado ? 'btn-primary' : 'btn-outline-secondary'
      }`}
      style={{ fontSize: '0.78rem', cursor: draggable ? 'grab' : 'pointer' }}
      title={tipo.nombre}
      draggable={draggable}
      onDragStart={onDragStart}
      onClick={onClick}
    >
      {tipo.codigo}
    </div>
  )
}

// Bloque de bloqueo revelado tras un intento real de creación (ADR-037 §D).
// Con puede_escapar ofrece forzar con justificación (#616/#723, misma bitácora
// que un escape de motor); sin él, solo informa — no hay vía de escape.
export function BloqueoForzar({ bloqueo, tipoNombre, justificacion, setJustificacion, creando, onForzar, onCancelar }) {
  return (
    <div className="d-flex flex-column gap-1 px-2 py-2 rounded border bg-warning-subtle border-warning-subtle">
      <span className="small">
        <strong>{tipoNombre}</strong> — bloqueado
      </span>
      <span className="small text-muted">
        {bloqueo.motivo}
        {bloqueo.url_norma && (
          <>
            {' '}
            <a href={bloqueo.url_norma} target="_blank" rel="noreferrer">Ver norma</a>
          </>
        )}
      </span>
      {bloqueo.puede_escapar ? (
        <>
          <textarea
            className="form-control form-control-sm"
            rows={2}
            placeholder="Justificación obligatoria para forzar la creación (queda en bitácora)"
            value={justificacion}
            onChange={(e) => setJustificacion(e.target.value)}
            disabled={creando}
          />
          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-sm btn-warning flex-grow-1"
              disabled={creando || !justificacion.trim()}
              onClick={onForzar}
            >
              {creando ? '…' : 'Forzar creación'}
            </button>
            <button type="button" className="btn btn-sm btn-outline-secondary" disabled={creando} onClick={onCancelar}>
              ✕
            </button>
          </div>
        </>
      ) : (
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={creando} onClick={onCancelar}>
          Cancelar
        </button>
      )}
    </div>
  )
}
