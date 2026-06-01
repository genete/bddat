// Inspector.jsx — panel read-only adaptativo al nodo seleccionado (#500, ADR-016 §5).
//
// S3a (lectura): cabecera (tipo+nombre+estado+semáforo, tomada del árbol del store)
// + datos finos y documentos del detalle lazy (§16) + plazo + agregados del subárbol
// + acciones rápidas no destructivas (abrir doc, abrir carpeta, copiar referencia).
// Edición / despensa → S3b.
import React from 'react'
import { useArbolStore } from '../store.js'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'
import Semaforo from './nodos/Semaforo.jsx'

const ETIQUETA_TIPO = {
  expediente: 'Expediente',
  solicitud:  'Solicitud',
  fase:       'Fase',
  tramite:    'Trámite',
  tarea:      'Tarea',
}

const ETIQUETA_PLAZO = {
  EN_PLAZO:       'En plazo',
  PROXIMO_VENCER: 'Próximo a vencer',
  VENCIDO:        'Vencido',
  INDEFINIDO:     'Indefinido',
  SIN_PLAZO:      'Sin plazo',
}

const ROL_DOC = { CONSUMIDO: 'Consumido', PRODUCIDO: 'Producido' }

// --- Búsqueda del nodo en el árbol del store (cabecera + agregados, §5) ---------

function buscarNodo(arbol, sel) {
  if (!arbol || !sel) return null
  if (sel.tipo === 'expediente') return arbol.expediente
  for (const sol of arbol.solicitudes || []) {
    if (sel.tipo === 'solicitud' && sol.id === sel.id) return sol
    for (const fase of sol.fases || []) {
      if (sel.tipo === 'fase' && fase.id === sel.id) return fase
      for (const tr of fase.tramites || []) {
        if (sel.tipo === 'tramite' && tr.id === sel.id) return tr
        for (const ta of tr.tareas || []) {
          if (sel.tipo === 'tarea' && ta.id === sel.id) return ta
        }
      }
    }
  }
  return null
}

function tituloNodo(tipo, nodo) {
  if (!nodo) return ''
  if (tipo === 'expediente') return nodo.codigo || ''
  if (tipo === 'solicitud') return [nodo.siglas, nodo.descripcion].filter(Boolean).join(' — ')
  return nodo.nombre || nodo.abrev || nodo.tipo_codigo || ''
}

// --- Acciones rápidas (no destructivas) ----------------------------------------

async function copiarReferencia(ref) {
  try {
    await navigator.clipboard.writeText(ref)
    showToast('Referencia copiada al portapapeles', 'success')
  } catch {
    showToast('No se pudo copiar la referencia', 'danger')
  }
}

async function postAccion(url, okMsg) {
  try {
    await api.post(url)
    if (okMsg) showToast(okMsg, 'success')
  } catch (e) {
    showToast((e && e.message) || 'No se pudo completar la acción', 'danger')
  }
}

// --- Subcomponentes -------------------------------------------------------------

function Cabecera({ tipo, nodo }) {
  const sem = nodo && nodo.semaforo
  return (
    <div className="d-flex align-items-start gap-2 mb-3">
      {sem && <span className="mt-1"><Semaforo color={sem.color} relleno /></span>}
      <div className="flex-grow-1 min-w-0">
        <div className="text-uppercase text-muted small fw-semibold">{ETIQUETA_TIPO[tipo] || tipo}</div>
        <div className="fw-bold">{tituloNodo(tipo, nodo) || '—'}</div>
        {nodo && nodo.estado && <span className="badge text-bg-light mt-1">{nodo.estado}</span>}
      </div>
    </div>
  )
}

function Campos({ campos }) {
  if (!campos || campos.length === 0) return null
  return (
    <dl className="row row-cols-1 g-1 small mb-3">
      {campos.map((c, i) => (
        <div key={i} className="d-flex flex-column">
          <dt className="text-muted fw-normal">{c.etiqueta}</dt>
          <dd className="mb-1">{c.valor}</dd>
        </div>
      ))}
    </dl>
  )
}

function Plazo({ plazo }) {
  if (!plazo) return null
  const dias = plazo.dias_restantes
  return (
    <div className="alert alert-light border py-2 px-3 small mb-3">
      <div className="fw-semibold mb-1">Plazo</div>
      <div>{ETIQUETA_PLAZO[plazo.estado] || plazo.estado}</div>
      {plazo.fecha_limite && <div className="text-muted">Fecha límite: {plazo.fecha_limite}</div>}
      {dias !== null && dias !== undefined && (
        <div className="text-muted">Días restantes: {dias}</div>
      )}
    </div>
  )
}

function Agregados({ agregados }) {
  if (!agregados) return null
  const { plazos_vencidos = 0, plazos_proximos = 0, plazos_en_plazo = 0, pendientes_notificar = 0 } = agregados
  const total = plazos_vencidos + plazos_proximos + plazos_en_plazo + pendientes_notificar
  if (total === 0) return null
  return (
    <div className="mb-3 small">
      <div className="text-muted fw-semibold mb-1">Plazos del subárbol</div>
      <ul className="list-unstyled mb-0">
        {plazos_vencidos > 0 && <li>· {plazos_vencidos} vencido(s)</li>}
        {plazos_proximos > 0 && <li>· {plazos_proximos} próximo(s) a vencer</li>}
        {plazos_en_plazo > 0 && <li>· {plazos_en_plazo} en plazo</li>}
        {pendientes_notificar > 0 && <li>· {pendientes_notificar} pendiente(s) de notificar</li>}
      </ul>
    </div>
  )
}

function Documentos({ documentos, expedienteId }) {
  if (!documentos || documentos.length === 0) return null
  return (
    <div className="mb-3">
      <div className="text-muted fw-semibold small mb-1">Documentos</div>
      <ul className="list-group list-group-flush">
        {documentos.map((d) => (
          <li key={`${d.rol}-${d.id}`} className="list-group-item px-0 py-2">
            <div className="d-flex align-items-center gap-2">
              <i className="bi bi-file-earmark" />
              <a href={d.enlace} target="_blank" rel="noreferrer" className="flex-grow-1 text-truncate" title={d.nombre}>
                {d.nombre}
              </a>
              {d.puede_abrir_carpeta && (
                <button
                  type="button"
                  className="btn btn-sm btn-link p-0 text-secondary"
                  title="Abrir carpeta del documento"
                  onClick={() => postAccion(
                    `/expedientes/${expedienteId}/documentos/${d.id}/abrir-en-carpeta`)}
                >
                  <i className="bi bi-folder2-open" />
                </button>
              )}
            </div>
            <div className="small text-muted ms-4">
              {ROL_DOC[d.rol] || d.rol}
              {d.tipo_doc ? ` · ${d.tipo_doc}` : ''}
              {d.fecha ? ` · ${d.fecha}` : ''}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Acciones({ referencia, expedienteId }) {
  return (
    <div className="d-flex flex-wrap gap-2 border-top pt-3 mt-auto">
      <button
        type="button"
        className="btn btn-sm btn-outline-secondary"
        onClick={() => postAccion(`/expedientes/${expedienteId}/abrir-carpeta`)}
      >
        <i className="bi bi-folder2 me-1" />Abrir carpeta
      </button>
      {referencia && (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={() => copiarReferencia(referencia)}
        >
          <i className="bi bi-clipboard me-1" />Copiar referencia
        </button>
      )}
    </div>
  )
}

// --- Componente principal -------------------------------------------------------

export default function Inspector() {
  const seleccion = useArbolStore((s) => s.seleccion)
  const arbol = useArbolStore((s) => s.arbol)
  const detalle = useArbolStore((s) => s.detalle)
  const cargando = useArbolStore((s) => s.detalleCargando)
  const error = useArbolStore((s) => s.detalleError)
  const expedienteId = useArbolStore((s) => s.expedienteId)

  if (!seleccion) {
    return (
      <div className="p-3 text-muted small d-flex align-items-center justify-content-center h-100 text-center">
        Selecciona un elemento del árbol
      </div>
    )
  }

  const nodo = buscarNodo(arbol, seleccion)
  const esHoja = seleccion.tipo === 'tarea'

  return (
    <div className="p-3 d-flex flex-column h-100">
      <Cabecera tipo={seleccion.tipo} nodo={nodo} />

      {cargando && <div className="text-muted small">Cargando detalle…</div>}
      {error && (
        <div className="text-danger small">
          No se pudo cargar el detalle: {String((error && error.message) || error)}
        </div>
      )}

      {detalle && !cargando && (
        <>
          <Campos campos={detalle.campos} />
          {!esHoja && nodo && <Agregados agregados={nodo.agregados} />}
          <Plazo plazo={detalle.plazo} />
          <Documentos documentos={detalle.documentos} expedienteId={expedienteId} />
        </>
      )}

      {detalle && !cargando && (
        <Acciones referencia={detalle.referencia} expedienteId={expedienteId} />
      )}
    </div>
  )
}
