// Inspector.jsx — panel read-only adaptativo al nodo seleccionado (#500, ADR-016 §5).
//
// S3a (lectura): cabecera (tipo+nombre+estado+semáforo, tomada del árbol del store)
// + datos finos y documentos del detalle lazy (§16) + plazo + agregados del subárbol
// + acciones rápidas no destructivas (abrir doc, abrir carpeta, copiar referencia).
// Edición / despensa → S3b.
import React from 'react'
import { useArbolStore, selectHayCambios } from '../store.js'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'
import { puedeEditarNodo } from '../../shared/auth.js'
import Semaforo from './nodos/Semaforo.jsx'
import Despensa from './Despensa.jsx'

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

// --- Búsqueda y conteo de subárbol (para confirmación de borrado, §7) -----------

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

function contarSubarbol(arbol, sel) {
  if (!sel || !arbol) return {}
  const nodo = buscarNodo(arbol, sel)
  if (!nodo) return {}
  if (sel.tipo === 'solicitud') {
    const fases = nodo.fases || []
    const tramites = fases.reduce((n, f) => n + (f.tramites || []).length, 0)
    const tareas = fases.reduce((n, f) =>
      n + (f.tramites || []).reduce((n2, tr) => n2 + (tr.tareas || []).length, 0), 0)
    return { fases: fases.length, tramites, tareas }
  }
  if (sel.tipo === 'fase') {
    const tramites = nodo.tramites || []
    const tareas = tramites.reduce((n, tr) => n + (tr.tareas || []).length, 0)
    return { tramites: tramites.length, tareas }
  }
  if (sel.tipo === 'tramite') {
    return { tareas: (nodo.tareas || []).length }
  }
  return {}
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

// --- Borrado (S3b-4): bloque inline de consecuencias + confirmación dos pasos ---

function ConfirmacionBorrado({ nodo }) {
  const seleccion      = useArbolStore((s) => s.seleccion)
  const arbol          = useArbolStore((s) => s.arbol)
  const borrando       = useArbolStore((s) => s.borrando)
  const borrarNodo     = useArbolStore((s) => s.borrarNodo)
  const cancelarBorrado = useArbolStore((s) => s.cancelarBorrado)

  const titulo = tituloNodo(seleccion.tipo, nodo)
  const conteo = contarSubarbol(arbol, seleccion)

  const partes = []
  if (conteo.fases)    partes.push(`${conteo.fases} fase${conteo.fases    !== 1 ? 's' : ''}`)
  if (conteo.tramites) partes.push(`${conteo.tramites} trámite${conteo.tramites !== 1 ? 's' : ''}`)
  if (conteo.tareas)   partes.push(`${conteo.tareas} tarea${conteo.tareas   !== 1 ? 's' : ''}`)

  return (
    <div>
      <div className="alert alert-warning py-2 px-3 mb-3 small">
        <div className="fw-semibold mb-1">
          ¿Borrar {ETIQUETA_TIPO[seleccion.tipo]?.toLowerCase()} «{titulo || '—'}»?
        </div>
        {partes.length > 0 && (
          <div>Contiene: {partes.join(', ')}.</div>
        )}
        <div className="text-danger fw-semibold mt-1">Esta acción es irreversible.</div>
      </div>
      <div className="d-flex gap-2">
        <button type="button" className="btn btn-sm btn-danger"
                disabled={borrando} onClick={borrarNodo}>
          {borrando ? 'Borrando…' : 'Borrar definitivamente'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary"
                disabled={borrando} onClick={cancelarBorrado}>
          Cancelar
        </button>
      </div>
    </div>
  )
}

// --- Edición (S3b-1): editor genérico + split editor/despensa ------------------

// Editor genérico: pinta un control por campo del esquema editable, autofocus en
// el primero, botonera Guardar/Cancelar. value/onChange contra borrador/setCampo.
function Editor() {
  const seleccion  = useArbolStore((s) => s.seleccion)
  const campos     = useArbolStore((s) => s.editableCampos)
  const cargando   = useArbolStore((s) => s.edicionCargando)
  const borrador   = useArbolStore((s) => s.borrador)
  const setCampo   = useArbolStore((s) => s.setCampo)
  const guardando  = useArbolStore((s) => s.guardando)
  const guardar    = useArbolStore((s) => s.guardar)
  const cancelar   = useArbolStore((s) => s.cancelar)
  const hayCambios = useArbolStore(selectHayCambios)
  const solicitarBorrado = useArbolStore((s) => s.solicitarBorrado)
  const firstRef = React.useRef(null)
  React.useEffect(() => { if (firstRef.current) firstRef.current.focus() }, [campos])

  const puedeBorrar = seleccion && seleccion.tipo !== 'expediente' &&
                      puedeEditarNodo(seleccion.tipo)

  if (cargando) return <div className="text-muted small">Cargando editor…</div>
  if (!campos.length)
    return (
      <div>
        <div className="text-muted small mb-3">
          Sin campos editables. Usa la despensa inferior para añadir elementos al árbol.
        </div>
        <button type="button" className="btn btn-sm btn-outline-secondary"
                onClick={cancelar}>Cancelar</button>
      </div>
    )

  const ctrl = (c, ref) => {
    const val = borrador[c.campo] ?? ''
    if (c.control === 'textarea')
      return <textarea ref={ref} className="form-control form-control-sm" rows={3}
               value={val} onChange={(e) => setCampo(c.campo, e.target.value)} />
    if (c.control === 'select')
      return (
        <select ref={ref} className="form-select form-select-sm" value={val}
          onChange={(e) => setCampo(c.campo, e.target.value === '' ? null : Number(e.target.value))}>
          <option value="">—</option>
          {(c.opciones || []).map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
        </select>
      )
    return <input ref={ref} type="text" className="form-control form-control-sm"
             value={val} onChange={(e) => setCampo(c.campo, e.target.value)} />
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (hayCambios && !guardando) guardar() }}>
      {campos.map((c, i) => (
        <div className="mb-2" key={c.campo}>
          <label className="form-label small text-muted mb-1">{c.etiqueta}</label>
          {ctrl(c, i === 0 ? firstRef : null)}
        </div>
      ))}
      <div className="d-flex gap-2 mt-3">
        <button type="button" className="btn btn-sm btn-primary"
                disabled={guardando || !hayCambios} onClick={guardar}>Guardar</button>
        <button type="button" className="btn btn-sm btn-outline-secondary"
                onClick={cancelar}>Cancelar</button>
        {puedeBorrar && (
          <button type="button" className="btn btn-sm btn-outline-danger ms-auto"
                  onClick={solicitarBorrado}>🗑️ Borrar</button>
        )}
      </div>
    </form>
  )
}

// Split vertical en edición: editor arriba (flex:1, scroll) + despensa abajo (120px
// fija). En lectura NO hay split (igual que S3a). El inspector lleva siempre el
// borde+sombra de edición (arbol-inspector--lock, CSS) porque editar bloquea el resto
// de la UI desde que se entra; el inspector NUNCA se atenúa (es la zona interactiva).
function InspectorEdicion({ nodo }) {
  const seleccion             = useArbolStore((s) => s.seleccion)
  const borrarPendienteConfirm = useArbolStore((s) => s.borrarPendienteConfirm)
  return (
    <div className="d-flex flex-column h-100 arbol-inspector--lock">
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }} className="p-3">
        <Cabecera tipo={seleccion.tipo} nodo={nodo} />
        {borrarPendienteConfirm
          ? <ConfirmacionBorrado nodo={nodo} />
          : <Editor />
        }
      </div>
      {!borrarPendienteConfirm && (
        <div style={{ flex: '0 0 auto' }} className="border-top">
          <Despensa />
        </div>
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
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const entrarEdicion = useArbolStore((s) => s.entrarEdicion)

  if (!seleccion) {
    return (
      <div className="p-3 text-muted small d-flex align-items-center justify-content-center h-100 text-center">
        Selecciona un elemento del árbol
      </div>
    )
  }

  const nodo = buscarNodo(arbol, seleccion)
  if (modoEdicion) return <InspectorEdicion nodo={nodo} />
  const esHoja = seleccion.tipo === 'tarea'
  const puedeEditar = puedeEditarNodo(seleccion.tipo)

  return (
    <div className="p-3 d-flex flex-column h-100">
      <Cabecera tipo={seleccion.tipo} nodo={nodo} />

      {puedeEditar && (
        <div className="mb-3">
          {/* Editar vive en el inspector: edita el nodo inspeccionado (no "toda la vista"). */}
          <button type="button" className="btn btn-sm btn-outline-primary"
                  onClick={() => entrarEdicion(seleccion)}>
            ✏️ Editar
          </button>
        </div>
      )}

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
