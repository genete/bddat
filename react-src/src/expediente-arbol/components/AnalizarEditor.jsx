// AnalizarEditor.jsx — contenedor de la tarea ANALIZAR (#442, ADR-023 §6).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo ANALIZAR
// (ver Inspector.jsx). Se compone de:
//   - Secciones extendidas (check documental #495, check técnico #581,
//     requerimientos #440), solo si el backend las declara (secciones_extendidas)
//     — no todo trámite con ANALIZAR las necesita (p.ej. CONSULTA_SEPARATA).
//   - Núcleo común (resultado + producir documento), siempre presente.
// notas / documentos_consumidos_ids siguen gestionándose por Despensa; este
// componente no los reimplementa.
import React from 'react'
import { useArbolStore } from '../store.js'
import { getAnalizar, postAnalizar } from '../api.js'
import { showToast } from '../../shared/ui/toast.js'

const ETIQUETA_RESULTADO = {
  favorable: 'Favorable',
  condicionado: 'Condicionado',
  desfavorable: 'Desfavorable',
}

function SeccionPlaceholder({ titulo, texto }) {
  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">{titulo}</div>
      <div className="card-body card-body-tinted">
        <div className="text-muted small fst-italic">{texto}</div>
      </div>
    </div>
  )
}

function SeccionRequerimientos() {
  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small d-flex justify-content-between align-items-center">
        <span>Requerimientos</span>
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          disabled
          title="Disponible cuando se implemente #440"
        >
          Gestionar requerimientos…
        </button>
      </div>
      <div className="card-body card-body-tinted">
        <div className="text-muted small fst-italic">Sin requerimientos seleccionados todavía.</div>
      </div>
    </div>
  )
}

function DefectosConsolidados({ items }) {
  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Defectos consolidados</div>
      <div className="card-body card-body-tinted">
        {items.length === 0 ? (
          <div className="text-muted small fst-italic">Sin defectos detectados todavía.</div>
        ) : (
          <ul className="list-unstyled small mb-0">
            {items.map((it, i) => <li key={i} className="mb-1">{it.texto}</li>)}
          </ul>
        )}
      </div>
    </div>
  )
}

// Resumen de solo lectura una vez producido el documento — el resultado queda bloqueado.
function ResultadoProducido({ documentoProducido }) {
  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Resultado</div>
      <div className="card-body card-body-tinted">
        <div className="mb-2">
          <span className="badge text-bg-light border">
            {ETIQUETA_RESULTADO[documentoProducido.resultado] || documentoProducido.resultado}
          </span>
        </div>
        {documentoProducido.defectos.length > 0 ? (
          <ul className="list-unstyled small mb-2">
            {documentoProducido.defectos.map((d, i) => <li key={i}>{d.texto}</li>)}
          </ul>
        ) : (
          <div className="text-muted small fst-italic mb-2">Sin defectos.</div>
        )}
        <div className="text-muted small">Documento producido — el resultado queda bloqueado.</div>
      </div>
    </div>
  )
}

// Núcleo (siempre presente): elegir resultado + confirmación de dos pasos + producir.
function NucleoResultado({ expedienteId, tareaId, completo, onProducido }) {
  const [resultado, setResultado] = React.useState('favorable')
  const [confirmando, setConfirmando] = React.useState(false)
  const [justificacion, setJustificacion] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)

  const producir = async () => {
    setEnviando(true)
    try {
      const body = { resultado }
      const just = justificacion.trim()
      if (just) body.justificacion = just
      await postAnalizar(expedienteId, tareaId, body)
      showToast('Documento de diagnóstico producido', 'success')
      await onProducido()
    } catch (e) {
      showToast((e && e.payload && e.payload.motivo) || (e && e.message) || 'No se pudo producir el documento', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Resultado</div>
      <div className="card-body card-body-tinted">
        <div className="mb-3">
          {['favorable', 'condicionado', 'desfavorable'].map((r) => (
            <div className="form-check" key={r}>
              <input
                type="radio"
                className="form-check-input"
                id={`analizar-resultado-${r}`}
                name="analizar-resultado"
                checked={resultado === r}
                disabled={confirmando}
                onChange={() => setResultado(r)}
              />
              <label className="form-check-label small" htmlFor={`analizar-resultado-${r}`}>
                {ETIQUETA_RESULTADO[r]}
              </label>
            </div>
          ))}
        </div>

        {!confirmando ? (
          <button type="button" className="btn btn-primary btn-sm w-100" onClick={() => setConfirmando(true)}>
            Producir documento de diagnóstico
          </button>
        ) : (
          <div className="border rounded p-2 bg-warning-subtle border-warning-subtle">
            <div className="small mb-2">
              Esta acción es <strong>irreversible</strong>: una vez producido, el resultado
              queda bloqueado. ¿Confirmas?
            </div>
            {!completo && (
              <div className="mb-2">
                <label className="form-label small text-muted mb-1">
                  Quedan ítems sin revisar — justifica para producir igualmente
                </label>
                <textarea
                  className="form-control form-control-sm"
                  rows={2}
                  value={justificacion}
                  onChange={(e) => setJustificacion(e.target.value)}
                />
              </div>
            )}
            <div className="d-flex gap-2">
              <button
                type="button"
                className="btn btn-sm btn-warning"
                disabled={enviando || (!completo && !justificacion.trim())}
                onClick={producir}
              >
                {enviando ? 'Produciendo…' : 'Confirmar producción'}
              </button>
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                disabled={enviando}
                onClick={() => { setConfirmando(false); setJustificacion('') }}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AnalizarEditor({ tareaId }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)
  const seleccion = useArbolStore((s) => s.seleccion)
  const cargarDetalle = useArbolStore((s) => s.cargarDetalle)
  const cancelar = useArbolStore((s) => s.cancelar)

  const [payload, setPayload] = React.useState(null)
  const [cargando, setCargando] = React.useState(true)
  const [error, setError] = React.useState(null)

  const cargar = React.useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const data = await getAnalizar(expedienteId, tareaId)
      setPayload(data)
    } catch (e) {
      setError(e)
    } finally {
      setCargando(false)
    }
  }, [expedienteId, tareaId])

  React.useEffect(() => { cargar() }, [cargar])

  if (cargando) return <div className="text-muted small">Cargando…</div>
  if (error) {
    return <div className="text-danger small">No se pudo cargar: {String((error && error.message) || error)}</div>
  }
  if (!payload) return null

  const onProducido = async () => {
    // Refresca el detalle de lectura del árbol (Documentos, rol Producido) y
    // el propio payload local (pasa a modo solo lectura). El pool de la
    // despensa no se invalida aquí (cacheado por vida de la isla, #517) — el
    // botón "+ Producido" ya está deshabilitado para ANALIZAR (ver Despensa.jsx).
    await cargarDetalle(seleccion)
    await cargar()
  }

  return (
    <div>
      {payload.secciones_extendidas && (
        <>
          <SeccionPlaceholder titulo="Check documental" texto="Disponible cuando se implemente #495." />
          <SeccionPlaceholder titulo="Check técnico" texto="Disponible cuando se implemente #581." />
          <SeccionRequerimientos />
          <DefectosConsolidados items={payload.defectos_consolidado} />
        </>
      )}

      {payload.documento_producido ? (
        <ResultadoProducido documentoProducido={payload.documento_producido} />
      ) : (
        <NucleoResultado
          expedienteId={expedienteId}
          tareaId={tareaId}
          completo={payload.completo}
          onProducido={onProducido}
        />
      )}

      {/* Sin ciclo borrador/hayCambios (a diferencia del Editor genérico): nada
          queda a medias fuera de la propia confirmación de producir, así que
          "Cerrar" siempre puede salir de edición sin aviso de cambios sin guardar. */}
      <div className="border-top pt-3 mt-3">
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={cancelar}>
          Cerrar
        </button>
      </div>
    </div>
  )
}
