// Despensa.jsx — zona inferior del split del inspector en edición (ADR-016 §5/§10).
//
// Modo adaptativo según el tipo de nodo seleccionado:
//   · tipos-creables (S3b-2): solicitud, fase, trámite, tarea  → chips de tipo + zona de drop/staging
//   · docs del pool (S3b-3):  tarea  → fichas de doc del pool + staging consumido/producido
import React from 'react'
import { useArbolStore } from '../store.js'

// ─── Modo tipos-creables (S3b-2) ────────────────────────────────────────────

const ETIQUETA_TIPO_HIJO = {
  solicitud: 'solicitud',
  fase:      'fase',
  tramite:   'trámite',
  tarea:     'tarea',
}

function ChipTipo({ tipo, seleccionado, onClickChip, onDragStart }) {
  const tooltip = !tipo.permitido
    ? [tipo.motivo, tipo.norma].filter(Boolean).join(' — ')
    : tipo.advertencia ? `Advertencia: ${tipo.advertencia}` : ''

  return (
    <span
      className={`badge border small ${
        seleccionado
          ? 'text-bg-primary border-primary'
          : tipo.permitido
            ? 'text-bg-light border-secondary-subtle'
            : 'text-bg-secondary opacity-50 border-0'
      }`}
      style={{
        cursor: tipo.permitido ? 'grab' : 'not-allowed',
        userSelect: 'none',
      }}
      draggable={tipo.permitido}
      onDragStart={tipo.permitido ? onDragStart : undefined}
      onClick={tipo.permitido ? onClickChip : undefined}
      title={tooltip || undefined}
    >
      {tipo.advertencia && <span className="me-1">⚠</span>}
      {tipo.codigo}
    </span>
  )
}

function DespensaTipos() {
  const seleccion              = useArbolStore((s) => s.seleccion)
  const tiposCreables          = useArbolStore((s) => s.tiposCreables)
  const tiposCreablesCargando  = useArbolStore((s) => s.tiposCreablesCargando)
  const tipoCreacionPendiente  = useArbolStore((s) => s.tipoCreacionPendiente)
  const creando                = useArbolStore((s) => s.creando)
  const cargarTiposCreables    = useArbolStore((s) => s.cargarTiposCreables)
  const seleccionarTipoCrear   = useArbolStore((s) => s.seleccionarTipoCrear)
  const cancelarCrear          = useArbolStore((s) => s.cancelarCrear)
  const crearHijo              = useArbolStore((s) => s.crearHijo)

  const [mostrarTodos, setMostrarTodos] = React.useState(false)
  const [draggingOver, setDraggingOver] = React.useState(false)

  React.useEffect(() => {
    cargarTiposCreables(seleccion)
  }, [seleccion?.tipo, seleccion?.id])  // eslint-disable-line

  if (tiposCreablesCargando) {
    return <div className="p-2 text-muted small fst-italic">Cargando tipos…</div>
  }
  if (!tiposCreables) return null

  const tipos      = tiposCreables.tipos || []
  const permitidos = tipos.filter((t) => t.permitido)
  const hayNoPermitidos = permitidos.length < tipos.length
  const mostrados  = mostrarTodos ? tipos : permitidos
  const tipoHijo   = ETIQUETA_TIPO_HIJO[tiposCreables.tipo_hijo] || tiposCreables.tipo_hijo || 'hijo'

  const onDragStart = (tipo) => (e) => {
    e.dataTransfer.setData('application/despensa-tipo', JSON.stringify({
      tipo_id: tipo.tipo_id,
      codigo:  tipo.codigo,
      nombre:  tipo.nombre,
    }))
    e.dataTransfer.effectAllowed = 'copy'
  }

  const onDragOver = (e) => {
    if (e.dataTransfer.types.includes('application/despensa-tipo')) {
      e.preventDefault()
      setDraggingOver(true)
    }
  }
  const onDragLeave = () => setDraggingOver(false)
  const onDrop = (e) => {
    e.preventDefault()
    setDraggingOver(false)
    try {
      const tipo = JSON.parse(e.dataTransfer.getData('application/despensa-tipo'))
      seleccionarTipoCrear(tipo)
    } catch { /* ignorar datos malformados */ }
  }

  return (
    <div className="p-2 d-flex flex-column gap-2">
      <div className="d-flex justify-content-between align-items-center">
        <span className="text-muted small fw-semibold">Crear {tipoHijo}</span>
        {hayNoPermitidos && (
          <button
            type="button"
            className="btn btn-link btn-sm p-0 small"
            onClick={() => setMostrarTodos((v) => !v)}
          >
            {mostrarTodos ? 'Solo permitidos' : 'Mostrar todos'}
          </button>
        )}
      </div>

      {mostrados.length > 0 ? (
        <div className="d-flex flex-wrap gap-1">
          {mostrados.map((t) => (
            <ChipTipo
              key={t.tipo_id}
              tipo={t}
              seleccionado={tipoCreacionPendiente?.tipo_id === t.tipo_id}
              onClickChip={() => seleccionarTipoCrear({ tipo_id: t.tipo_id, codigo: t.codigo, nombre: t.nombre })}
              onDragStart={onDragStart(t)}
            />
          ))}
        </div>
      ) : (
        <div className="text-muted small fst-italic">No hay tipos disponibles</div>
      )}

      {tipoCreacionPendiente ? (
        <div className="d-flex align-items-center gap-2 px-2 py-1 rounded border bg-primary-subtle border-primary-subtle">
          <span className="small flex-grow-1 text-truncate">
            <strong>{tipoCreacionPendiente.nombre}</strong>
          </span>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            disabled={creando}
            onClick={crearHijo}
          >
            {creando ? '…' : 'Crear'}
          </button>
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary"
            disabled={creando}
            onClick={cancelarCrear}
          >
            ✕
          </button>
        </div>
      ) : (
        <div
          className={`d-flex align-items-center justify-content-center rounded border small text-muted p-2 ${
            draggingOver ? 'bg-primary-subtle border-primary text-primary' : 'border-secondary-subtle'
          }`}
          style={{ borderStyle: 'dashed', minHeight: 36 }}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
        >
          {draggingOver ? 'Suelta aquí' : 'Arrastra o selecciona un tipo'}
        </div>
      )}
    </div>
  )
}

// ─── Modo docs del pool (S3b-3) ─────────────────────────────────────────────

function FichaDoc({ doc, vinculado, seleccionada, onClick }) {
  return (
    <button
      type="button"
      className={`btn btn-sm w-100 text-start border rounded px-2 py-1 ${
        seleccionada
          ? 'btn-primary'
          : vinculado
            ? 'btn-outline-success'
            : 'btn-outline-secondary'
      }`}
      style={{ fontSize: '0.78rem' }}
      onClick={onClick}
      title={doc.nombre}
    >
      <div className="text-truncate fw-semibold">{doc.nombre}</div>
      <div className="text-truncate opacity-75">
        {[doc.tipo_doc, doc.fecha].filter(Boolean).join(' · ')}
      </div>
    </button>
  )
}

function DespensaDocs() {
  const seleccion               = useArbolStore((s) => s.seleccion)
  const detalle                 = useArbolStore((s) => s.detalle)
  const pool                    = useArbolStore((s) => s.pool)
  const poolCargando            = useArbolStore((s) => s.poolCargando)
  const docVinculandoPendiente  = useArbolStore((s) => s.docVinculandoPendiente)
  const vinculando              = useArbolStore((s) => s.vinculando)
  const cargarPool              = useArbolStore((s) => s.cargarPool)
  const seleccionarDocVincular  = useArbolStore((s) => s.seleccionarDocVincular)
  const cancelarVincular        = useArbolStore((s) => s.cancelarVincular)
  const vincularDoc             = useArbolStore((s) => s.vincularDoc)

  React.useEffect(() => {
    cargarPool()
  }, [seleccion?.id])  // eslint-disable-line

  // Ids de docs ya vinculados a esta tarea (para marcarlos visualmente)
  const vinculadosIds = React.useMemo(() => {
    const docs = (detalle && detalle.documentos) || []
    return new Set(docs.map((d) => d.id))
  }, [detalle])

  if (poolCargando) {
    return <div className="p-2 text-muted small fst-italic">Cargando documentos…</div>
  }

  return (
    <div className="p-2 d-flex flex-column gap-2">
      <span className="text-muted small fw-semibold">Pool de documentos</span>

      {pool.length === 0 ? (
        <div className="text-muted small fst-italic">No hay documentos en el expediente</div>
      ) : (
        <div className="d-flex flex-column gap-1" style={{ maxHeight: 120, overflowY: 'auto' }}>
          {pool.map((doc) => (
            <FichaDoc
              key={doc.id}
              doc={doc}
              vinculado={vinculadosIds.has(doc.id)}
              seleccionada={docVinculandoPendiente?.id === doc.id}
              onClick={() =>
                docVinculandoPendiente?.id === doc.id
                  ? cancelarVincular()
                  : seleccionarDocVincular(doc)
              }
            />
          ))}
        </div>
      )}

      {/* Zona de confirmación / staging */}
      {docVinculandoPendiente ? (
        <div className="d-flex flex-column gap-1 px-2 py-1 rounded border bg-primary-subtle border-primary-subtle">
          <span className="small text-truncate fw-semibold">{docVinculandoPendiente.nombre}</span>
          <div className="d-flex gap-1">
            <button
              type="button"
              className="btn btn-sm btn-success flex-grow-1"
              disabled={vinculando}
              onClick={() => vincularDoc('CONSUMIDO')}
            >
              {vinculando ? '…' : '+ Consumido'}
            </button>
            <button
              type="button"
              className="btn btn-sm btn-primary flex-grow-1"
              disabled={vinculando}
              onClick={() => vincularDoc('PRODUCIDO')}
            >
              {vinculando ? '…' : '+ Producido'}
            </button>
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary"
              disabled={vinculando}
              onClick={cancelarVincular}
            >
              ✕
            </button>
          </div>
        </div>
      ) : (
        <div
          className="d-flex align-items-center justify-content-center rounded border small text-muted p-2 border-secondary-subtle"
          style={{ borderStyle: 'dashed', minHeight: 36 }}
        >
          Selecciona un documento
        </div>
      )}
    </div>
  )
}

// ─── Componente principal (adaptativo) ──────────────────────────────────────

export default function Despensa() {
  const seleccion   = useArbolStore((s) => s.seleccion)
  const modoEdicion = useArbolStore((s) => s.modoEdicion)

  if (!modoEdicion || !seleccion) return null

  if (seleccion.tipo === 'tarea') return <DespensaDocs />
  return <DespensaTipos />
}
