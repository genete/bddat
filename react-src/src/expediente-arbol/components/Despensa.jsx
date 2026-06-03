// Despensa.jsx — zona inferior del split del inspector en edición (ADR-016 §5/§10).
// S3b-2: tipos de hijo creables con dos vías de creación equivalentes:
//   · Drag del chip → soltar en la zona de drop del inspector
//   · Click en el chip → botón "Crear" aparece en la zona de confirmación
import React from 'react'
import { useArbolStore } from '../store.js'

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

export default function Despensa() {
  const seleccion              = useArbolStore((s) => s.seleccion)
  const modoEdicion            = useArbolStore((s) => s.modoEdicion)
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
    if (modoEdicion && seleccion && seleccion.tipo !== 'tarea') {
      cargarTiposCreables(seleccion)
    }
  }, [seleccion?.tipo, seleccion?.id, modoEdicion])  // eslint-disable-line

  if (!modoEdicion || !seleccion || seleccion.tipo === 'tarea') return null

  if (tiposCreablesCargando) {
    return (
      <div className="p-2 text-muted small fst-italic">Cargando tipos…</div>
    )
  }
  if (!tiposCreables) return null

  const tipos     = tiposCreables.tipos || []
  const permitidos = tipos.filter((t) => t.permitido)
  const hayNoPermitidos = permitidos.length < tipos.length
  const mostrados = mostrarTodos ? tipos : permitidos
  const tipoHijo  = ETIQUETA_TIPO_HIJO[tiposCreables.tipo_hijo] || tiposCreables.tipo_hijo || 'hijo'

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
      {/* Cabecera */}
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

      {/* Chips de tipos */}
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

      {/* Zona de drop / confirmación de creación */}
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
