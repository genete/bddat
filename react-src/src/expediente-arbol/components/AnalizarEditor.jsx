// AnalizarEditor.jsx — contenedor de la tarea ANALIZAR (#442, ADR-023 §6).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo ANALIZAR
// (ver Inspector.jsx). Se compone de:
//   - Secciones extendidas (check documental #495, check técnico #581,
//     requerimientos #440), solo si el backend las declara (secciones_extendidas)
//     — no todo trámite con ANALIZAR las necesita (p.ej. CONSULTA_SEPARATA).
//   - Núcleo común (resultado + producir documento), siempre presente.
// documentos_consumidos_ids se sigue eligiendo desde Despensa, pero Despensa
// solo apila el borrador (store.js::vincularDoc) — el PATCH real lo dispara
// `guardar()` del store, igual que en el Editor genérico. Por eso este
// componente incluye el mismo par Guardar/Cancelar, o el consumido elegido
// nunca llegaría a persistirse.
import React from 'react'
import { useArbolStore, selectHayCambios } from '../store.js'
import {
  getAnalizar, postAnalizar,
  vincularRequisitoDocumental, desvincularRequisitoDocumental,
} from '../api.js'
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

// Fila de un requisito documental (#495): estado + selector de documento del pool.
function FilaRequisitoDocumental({ item, expedienteId, tareaId, pool, onRecargar }) {
  const [seleccionando, setSeleccionando] = React.useState(false)
  const [documentoId, setDocumentoId] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)

  const vincular = async () => {
    if (!documentoId) return
    setEnviando(true)
    try {
      await vincularRequisitoDocumental(expedienteId, tareaId, item.requisito_id, Number(documentoId))
      setSeleccionando(false)
      setDocumentoId('')
      await onRecargar()
    } catch (e) {
      showToast((e && e.message) || 'No se pudo vincular el documento', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  const desvincular = async () => {
    setEnviando(true)
    try {
      await desvincularRequisitoDocumental(expedienteId, tareaId, item.requisito_id)
      await onRecargar()
    } catch (e) {
      showToast((e && e.message) || 'No se pudo desvincular el documento', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  const cita = [item.articulo, item.norma].filter(Boolean).join(', ')

  return (
    <div className="border-bottom pb-2 mb-2">
      <div className="d-flex justify-content-between align-items-start gap-2 mb-1">
        <div className="small">
          <div className="fw-semibold">{item.tipo_documento || 'Documento'}</div>
          {item.descripcion_legal && <div className="text-muted">{item.descripcion_legal}</div>}
          {cita && <div className="text-muted fst-italic">{cita}</div>}
        </div>
        <span className={`badge ${item.cubierto ? 'text-bg-success' : 'text-bg-warning'}`}>
          {item.cubierto ? 'Cubierto' : 'Pendiente'}
        </span>
      </div>

      {item.documento && (
        <div className="d-flex align-items-center gap-2 small mb-1">
          <span className="text-truncate">{item.documento.nombre}</span>
          <button
            type="button"
            className="btn btn-sm btn-link text-danger p-0 lh-1"
            disabled={enviando}
            onClick={desvincular}
          >
            Quitar
          </button>
        </div>
      )}

      {seleccionando ? (
        <div className="d-flex gap-1">
          <select
            className="form-select form-select-sm"
            value={documentoId}
            onChange={(e) => setDocumentoId(e.target.value)}
          >
            <option value="">Selecciona un documento…</option>
            {pool.map((d) => (
              <option key={d.id} value={d.id}>{d.nombre}</option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            disabled={!documentoId || enviando}
            onClick={vincular}
          >
            Vincular
          </button>
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary"
            disabled={enviando}
            onClick={() => { setSeleccionando(false); setDocumentoId('') }}
          >
            Cancelar
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setSeleccionando(true)}
        >
          {item.documento ? 'Cambiar documento' : 'Vincular documento'}
        </button>
      )}
    </div>
  )
}

function SeccionDocumental({ checklist, expedienteId, tareaId, onRecargar }) {
  const pool = useArbolStore((s) => s.pool)
  const cargarPool = useArbolStore((s) => s.cargarPool)

  React.useEffect(() => { cargarPool() }, [cargarPool])

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Check documental</div>
      <div className="card-body card-body-tinted">
        {checklist.length === 0 ? (
          <div className="text-muted small fst-italic">No hay requisitos documentales aplicables.</div>
        ) : (
          checklist.map((item) => (
            <FilaRequisitoDocumental
              key={item.requisito_id}
              item={item}
              expedienteId={expedienteId}
              tareaId={tareaId}
              pool={pool}
              onRecargar={onRecargar}
            />
          ))
        )}
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
  const guardar = useArbolStore((s) => s.guardar)
  const guardando = useArbolStore((s) => s.guardando)
  const hayCambios = useArbolStore(selectHayCambios)

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
          <SeccionDocumental
            checklist={payload.checklist_documental || []}
            expedienteId={expedienteId}
            tareaId={tareaId}
            onRecargar={cargar}
          />
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

      {/* Mismo par Guardar/Cancelar que el Editor genérico — persiste lo que
          Despensa apiló en el borrador (documentos_consumidos_ids; el
          producido lo fija crear_diagnostico, no este PATCH). El resultado y
          la producción del documento son un circuito aparte (arriba), no
          pasan por este borrador. */}
      <div className="d-flex gap-2 border-top pt-3 mt-3">
        <button
          type="button"
          className="btn btn-sm btn-primary"
          disabled={guardando || !hayCambios}
          onClick={guardar}
        >
          {guardando ? 'Guardando…' : 'Guardar'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={guardando} onClick={cancelar}>
          Cancelar
        </button>
      </div>
    </div>
  )
}
