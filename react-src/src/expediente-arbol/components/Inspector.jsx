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
import { estaSellado } from '../sellado.js'
import Semaforo from './nodos/Semaforo.jsx'
import Despensa from './Despensa.jsx'
import { BloqueoForzar } from './TiposCreablesCompartido.jsx'
import AnalizarEditor from './AnalizarEditor.jsx'
import ElaborarEditor from './ElaborarEditor.jsx'
import NotificarEditor from './NotificarEditor.jsx'

const ETIQUETA_TIPO = {
  expediente: 'Expediente',
  solicitud:  'Solicitud',
  fase:       'Fase',
  tramite:    'Trámite',
  organismo:  'Organismo',
  tarea:      'Tarea',
}

// INDEFINIDO (#789): reservado sin productor actual, no borrar — ver comentario
// gemelo en NodoTareas.jsx::barraPlazo. `catalogo_plazos` no admite
// `plazo_valor=0`; un ESPERAR_PLAZO sin plazo legal queda sin fila, y
// SIN_PLAZO (rojo permanente hasta el documento) es el estado correcto.
const ETIQUETA_PLAZO = {
  EN_PLAZO:       'En plazo',
  PROXIMO_VENCER: 'Próximo a vencer',
  VENCIDO:        'Vencido',
  CUMPLIDO:       'Cumplido',       // #778 — llegó el documento que lo acredita
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
      for (const org of fase.organismos || []) {
        if (sel.tipo === 'organismo' && org.id === sel.id) return org
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
  if (sel.tipo === 'organismo') {
    return { tramites: (nodo.tramite_ids || []).length }
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

function Cabecera({ tipo, nodo, compacta }) {
  const sem = nodo && nodo.semaforo
  // Candado (#720, ADR-036): solo la propia fase lleva el indicador — es el único
  // nivel con un acto de cierre formal (documento_resultado_id); trámite/tarea
  // quedan cubiertos transitivamente, sin badge propio.
  const cerrada = tipo === 'fase' && nodo && nodo.estado === 'FINALIZADA'
  return (
    <div className={`d-flex align-items-start gap-2 min-w-0 ${compacta ? '' : 'mb-3'}`}>
      {sem && <span className="mt-1"><Semaforo color={sem.color} relleno /></span>}
      <div className="flex-grow-1 min-w-0">
        <div className="text-uppercase text-muted small fw-semibold">{ETIQUETA_TIPO[tipo] || tipo}</div>
        <div className="fw-bold text-truncate">{tituloNodo(tipo, nodo) || '—'}</div>
        {nodo && nodo.estado && (
          <span className="badge text-bg-light mt-1">
            {cerrada && <i className="bi bi-lock-fill me-1" title="Fase cerrada" />}
            {nodo.estado}
          </span>
        )}
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

// Bloque Organismos (ADR-042 §B): read-only, solo presente en fase CONSULTAS.
// Pulsar una fila navega al nodo organismo en el árbol — ninguna mutación desde
// aquí, la regla del árbol como único sitio de edición se mantiene sin excepción.
function Organismos({ organismos, seleccionar }) {
  if (!organismos || organismos.length === 0) return null
  return (
    <div className="mb-3">
      <div className="text-muted fw-semibold small mb-1">Organismos</div>
      <ul className="list-group list-group-flush">
        {organismos.map((o) => (
          <li key={o.id} className="list-group-item px-0 py-2" style={{ cursor: 'pointer' }}
              role="button"
              onClick={() => seleccionar({ tipo: 'organismo', id: o.id })}>
            <div className="d-flex align-items-center gap-2">
              <span className="flex-grow-1 text-truncate fw-semibold">{o.nombre_completo || '—'}</span>
              {o.traslado_titular_vencido && (
                <span className="badge text-bg-danger" title="Traslado al titular vencido">
                  <i className="bi bi-exclamation-triangle-fill" />
                </span>
              )}
            </div>
            <div className="small text-muted">
              {o.via}
              {o.resultado ? ` · ${o.resultado}` : ''}
              {/* "Plazo legal del oficio", nunca "Plazo" a secas (#558): el estado
                  real del plazo lo da la tarea ESPERAR_PLAZO, este es el valor
                  congelado del oficio en el momento de enviarlo. */}
              {o.plazo_legal_dias != null ? ` · Plazo legal del oficio: ${o.plazo_legal_dias} días` : ''}
            </div>
          </li>
        ))}
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
              {d.puede_abrir && d.abrir_en === 'modal' ? (
                // .btn global (v2-components.css) es inline-flex + justify-content:center
                // (pensado para botones icono+texto de ancho ajustado); este botón además
                // crece con flex-grow-1 dentro de la fila, así que sin justify-content-start
                // el nombre queda centrado en el hueco sobrante — text-start no basta, ese
                // solo afecta text-align, no la alineación del flex item (#696).
                <button type="button"
                        className="btn btn-link p-0 text-start justify-content-start flex-grow-1 text-truncate"
                        data-modal-large-url={d.enlace}
                        data-modal-large-title={d.nombre}
                        title={d.nombre}>
                  {d.nombre}
                </button>
              ) : d.puede_abrir ? (
                <a href={d.enlace} target="_blank" rel="noreferrer" className="flex-grow-1 text-truncate" title={d.nombre}>
                  {d.nombre}
                </a>
              ) : (
                <span className="flex-grow-1 text-truncate text-muted" title={d.nombre}>
                  {d.nombre}
                </span>
              )}
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

// Bloque de reapertura (#720, ADR-036 §6 capa 4): única vía para tocar el interior
// de una fase cerrada. Justificación siempre obligatoria (validada también
// server-side) — mismo patrón visual que el forzado de creación (Despensa.jsx).
function ReabrirFase() {
  const [justificacion, setJustificacion] = React.useState('')
  const reabriendo  = useArbolStore((s) => s.reabriendoFase)
  const reabrirFase = useArbolStore((s) => s.reabrirFase)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-warning-subtle border-warning-subtle mb-3">
      <span className="small">
        <i className="bi bi-lock-fill me-1" /><strong>Fase cerrada.</strong> Su interior está congelado.
      </span>
      <span className="small text-muted">
        Para modificarla, reábrala primero. La reapertura queda registrada en bitácora.
      </span>
      <textarea
        className="form-control form-control-sm"
        rows={2}
        placeholder="Justificación obligatoria para reabrir la fase"
        value={justificacion}
        onChange={(e) => setJustificacion(e.target.value)}
        disabled={reabriendo}
      />
      <button
        type="button"
        className="btn btn-sm btn-warning"
        disabled={reabriendo || !justificacion.trim()}
        onClick={() => reabrirFase(justificacion.trim())}
      >
        {reabriendo ? 'Reabriendo…' : '🔓 Reabrir fase'}
      </button>
    </div>
  )
}

// Organismos vía consulta de la fase sin ninguna CONSULTA_SEPARATA vinculada
// (ADR-042 §C, #396 bloque 5) — mismo criterio estructural que el backend
// (consultas_organismos.organismos_pendientes_separata), derivado aquí del
// payload del árbol ya cargado (fase.organismos[].tramite_ids + fase.tramites)
// en vez de pedir un recuento aparte al backend.
function organismosPendientesSeparata(fase) {
  const tramitesPorId = new Map((fase.tramites || []).map((t) => [t.id, t]))
  return (fase.organismos || []).filter((org) => {
    if (org.via !== 'consulta') return false
    return !(org.tramite_ids || []).some((tid) => {
      const t = tramitesPorId.get(tid)
      return t && t.tipo_codigo === 'CONSULTA_SEPARATA'
    })
  })
}

// Acción de fase CONSULTAS en modo edición (ADR-042 §C, #396 bloque 5): vive
// junto al Editor genérico, no lo sustituye — resultado_fase_id/documento_
// resultado_id de esta fase siguen editándose igual que en cualquier otra.
// Oculto sin organismos pendientes: el botón no tiene nada útil que decir.
function AccionesFaseConsultas({ nodo }) {
  const enviarConsultas = useArbolStore((s) => s.enviarConsultas)
  const enviando = useArbolStore((s) => s.enviandoConsultas)
  const pendientes = organismosPendientesSeparata(nodo)
  if (pendientes.length === 0) return null
  return (
    <div className="mb-3">
      <button type="button" className="btn btn-sm btn-primary"
              disabled={enviando} onClick={enviarConsultas}>
        {enviando ? 'Enviando…' : `📤 Enviar consultas pendientes (${pendientes.length})`}
      </button>
    </div>
  )
}

// Editor genérico: pinta un control por campo del esquema editable, autofocus en
// el primero. Guardar/Cancelar viven en la barra fija (BarraEdicion, ADR-023 §5 bis);
// aquí solo queda Borrar, que no es parte del control de salida del marco.
//
// Fase cerrada (#720): los campos se deshabilitan (el backend rechazaría el guardado
// de todos modos, capas 1-3 del ADR) y se antepone ReabrirFase — único camino para
// volver a poder editarlos. Borrar tampoco se ofrece: nunca tiene sentido borrar el
// nodo de una fase cerrada sin reabrirla antes.
function Editor({ nodo }) {
  const seleccion  = useArbolStore((s) => s.seleccion)
  const campos     = useArbolStore((s) => s.editableCampos)
  const cargando   = useArbolStore((s) => s.edicionCargando)
  const borrador   = useArbolStore((s) => s.borrador)
  const setCampo   = useArbolStore((s) => s.setCampo)
  const guardando  = useArbolStore((s) => s.guardando)
  const guardar    = useArbolStore((s) => s.guardar)
  const hayCambios = useArbolStore(selectHayCambios)
  const solicitarBorrado = useArbolStore((s) => s.solicitarBorrado)
  const firstRef = React.useRef(null)
  React.useEffect(() => { if (firstRef.current) firstRef.current.focus() }, [campos])

  const faseCerrada = seleccion && seleccion.tipo === 'fase' && nodo && nodo.estado === 'FINALIZADA'
  const puedeBorrar = seleccion && seleccion.tipo !== 'expediente' &&
                      puedeEditarNodo(seleccion.tipo) && !faseCerrada

  if (cargando) return <div className="text-muted small">Cargando editor…</div>
  if (!campos.length)
    return (
      <div className="text-muted small mb-3">
        Sin campos editables. Usa la despensa inferior para añadir elementos al árbol.
      </div>
    )

  const ctrl = (c, ref) => {
    const val = borrador[c.campo] ?? ''
    if (c.control === 'textarea')
      return <textarea ref={ref} className="form-control form-control-sm" rows={3}
               value={val} onChange={(e) => setCampo(c.campo, e.target.value)} disabled={faseCerrada} />
    if (c.control === 'select')
      return (
        <select ref={ref} className="form-select form-select-sm" value={val} disabled={faseCerrada}
          onChange={(e) => setCampo(c.campo, e.target.value === '' ? null : Number(e.target.value))}>
          <option value="">—</option>
          {(c.opciones || []).map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
        </select>
      )
    return <input ref={ref} type="text" className="form-control form-control-sm"
             value={val} onChange={(e) => setCampo(c.campo, e.target.value)} disabled={faseCerrada} />
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (hayCambios && !guardando && !faseCerrada) guardar() }}>
      {faseCerrada && <ReabrirFase />}
      {campos.map((c, i) => (
        <div className="mb-2" key={c.campo}>
          <label className="form-label small text-muted mb-1">{c.etiqueta}</label>
          {ctrl(c, i === 0 ? firstRef : null)}
        </div>
      ))}
      {puedeBorrar && (
        <div className="d-flex mt-3">
          <button type="button" className="btn btn-sm btn-outline-danger"
                  onClick={solicitarBorrado}>🗑️ Borrar</button>
        </div>
      )}
    </form>
  )
}

// Vía de escape del Guardar cuando el backend devuelve un bloqueo FORZABLE
// (#765). Hasta ahora `puede_escapar:true` solo se ofrecía al CREAR: los tres
// bloqueos forzables del cierre de fase —completitud (#723), diagnóstico
// desfavorable sin consumir (#419/#711) y resultado desfavorable sin respaldo
// (#765)— llegaban aquí y morían en un toast, dejando al técnico sin más salida
// que guardar el resultado sin documento (la ventana que esquiva el check).
//
// Se pinta arriba del editor, dentro del scroll: el borrador sigue vivo debajo,
// así que "Cancelar" devuelve al formulario para corregir el resultado en vez de
// forzarlo. Reutiliza BloqueoForzar (mismo patrón intento→422→justificación→
// reintento) en vez de un aviso propio.
function BloqueoGuardarForzable() {
  const bloqueoGuardar = useArbolStore((s) => s.bloqueoGuardar)
  const guardando      = useArbolStore((s) => s.guardando)
  const guardar        = useArbolStore((s) => s.guardar)
  const cancelar       = useArbolStore((s) => s.cancelarBloqueoGuardar)
  const [justificacion, setJustificacion] = React.useState('')

  if (!bloqueoGuardar) return null

  return (
    <div className="mb-3">
      <BloqueoForzar
        bloqueo={{ ...bloqueoGuardar, puede_escapar: true }}
        titulo="Este guardado necesita justificación"
        textoAccion="Guardar igualmente"
        placeholder="Motivo por el que se guarda igualmente (queda en bitácora)"
        justificacion={justificacion}
        setJustificacion={setJustificacion}
        creando={guardando}
        onForzar={() => guardar(justificacion.trim())}
        onCancelar={cancelar}
      />
    </div>
  )
}

// Control de borrado compartido por los tres editores bespoke de tarea (ANALIZAR/
// ELABORAR/NOTIFICAR, #742): el Editor genérico lo integra en su propio form (arriba),
// pero ninguno de los tres bespoke lo trae de fábrica — se hoistea aquí, al nivel de
// InspectorEdicion, en vez de triplicarlo en cada uno (mismo criterio ya aplicado a
// Despensa: es el contenedor común quien pone el "chrome" alrededor del editor bespoke).
function BotonBorrarTarea() {
  const solicitarBorrado = useArbolStore((s) => s.solicitarBorrado)
  return (
    <div className="d-flex mt-3">
      <button type="button" className="btn btn-sm btn-outline-danger"
              onClick={solicitarBorrado}>🗑️ Borrar</button>
    </div>
  )
}

// Barra superior fija del marco de edición (ADR-023 §5 bis, #676): cabecera +
// control de salida, inmutable al scroll del contenido de abajo.
//
// El par Guardar/Cancelar de los CAMPOS DIRECTOS del nodo (el esquema editable
// genérico — hoy `notas` en tarea, `observaciones` en el resto) vive siempre
// aquí, para cualquier tipo de nodo incluida la superficie-de-trabajo (#688,
// enmienda de ADR-023 §5 bis): el emplazamiento del control no depende de qué
// pinte el contenedor de abajo. Lo que cada contenedor bespoke persiste por su
// cuenta y de inmediato (check documental, check técnico, shuttle, registrar
// envío…) es ortogonal y no pasa por este ciclo.
//
//   onClick del botón de salida siempre `cancelar` — misma acción del store para
//   ambos rótulos; solo cambia el texto según haya borrador vivo. La confirmación
//   en sucio ya la impone el bloqueo de light-dismiss del shell (ADR-023 §5 bis),
//   no un diálogo aparte aquí.
function BarraEdicion({ tipo, nodo }) {
  const guardando  = useArbolStore((s) => s.guardando)
  const guardar    = useArbolStore((s) => s.guardar)
  const cancelar   = useArbolStore((s) => s.cancelar)
  const hayCambios = useArbolStore(selectHayCambios)

  return (
    <div className="flex-shrink-0 border-bottom p-3 d-flex align-items-start justify-content-between gap-2">
      <Cabecera tipo={tipo} nodo={nodo} compacta />
      <div className="d-flex gap-2 flex-shrink-0">
        {/* `() => guardar()` y no `onClick={guardar}`: desde #765 el primer argumento
            de `guardar` es la justificación del escape, y pasarle el evento del click
            lo convertiría en un bypass involuntario. */}
        <button type="button" className="btn btn-sm btn-primary"
                disabled={guardando || !hayCambios} onClick={() => guardar()}>
          {guardando ? 'Guardando…' : 'Guardar'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={cancelar}>
          {hayCambios ? 'Cancelar' : 'Cerrar'}
        </button>
      </div>
    </div>
  )
}

// En edición: cabecera+control de salida fijos (BarraEdicion) + un ÚNICO contenedor
// con scroll para editor y despensa juntos (#725 tarea 6). Antes la despensa vivía en
// un split fijo aparte (120px al fondo del panel) que competía por la misma franja del
// viewport con el toast-container (bottom-0, custom.css) — dos elementos fijos al fondo
// siempre se pisan. Al meterla en el flujo normal del scroll deja de ser un elemento
// fijo propio. En lectura NO hay split (igual que S3a). El inspector lleva siempre el
// borde+sombra de edición (arbol-inspector--lock, CSS) porque editar bloquea el resto
// de la UI desde que se entra; el inspector NUNCA se atenúa (es la zona interactiva).
function InspectorEdicion({ nodo }) {
  const seleccion             = useArbolStore((s) => s.seleccion)
  const borrarPendienteConfirm = useArbolStore((s) => s.borrarPendienteConfirm)
  const seccionesExtendidas   = useArbolStore((s) => s.analizarSeccionesExtendidas)
  // ANALIZAR (#442): contenedor bespoke en vez del Editor genérico — secciones de
  // checklist + resultado + producir diagnóstico no encajan en el esquema
  // campo-a-campo. InspectorEdicion (cabecera, lock, split con Despensa) se
  // reutiliza igual para el resto de tareas.
  const esAnalizar = seleccion.tipo === 'tarea' && nodo && nodo.tipo_codigo === 'ANALIZAR'
  // ELABORAR (#608): idem, para enganchar "Generar escrito" (backend #167, huérfano
  // de UI desde la eliminación del sistema BC en #500).
  const esElaborar = seleccion.tipo === 'tarea' && nodo && nodo.tipo_codigo === 'ELABORAR'
  // NOTIFICAR (#657/#658, ADR-034): idem, "Registrar envío"/"Completar resultado".
  // Igual que ELABORAR, la Despensa NO se deshabilita — sigue siendo el mecanismo
  // genérico que vincula el documento producido (desacoplado de estos formularios).
  const esNotificar = seleccion.tipo === 'tarea' && nodo && nodo.tipo_codigo === 'NOTIFICAR'
  // ESPERAR_PLAZO (#766): sin editor bespoke — solo la ayuda de la Despensa sobre
  // qué documento es el producido cuando en la recepción llegan varios (regla de
  // #764). Es la única tarea cuyo producido es un documento recibido de fuera.
  const esEsperarPlazo = seleccion.tipo === 'tarea' && nodo && nodo.tipo_codigo === 'ESPERAR_PLAZO'
  // ADR-033 §1: en ANALIZAR extendido (ANÁLISIS_DOCUMENTAL/REQUERIMIENTO_SUBSANACIÓN)
  // casar un requisito documental deriva el consumido — la Despensa queda sin uso
  // legítimo y se oculta. En ANALIZAR simple (p.ej. CONSULTA_SEPARATA) sigue viva,
  // sin cambios. `seccionesExtendidas` es null hasta que AnalizarEditor confirma el
  // valor real (primer getAnalizar) — se muestra por defecto hasta saberlo con certeza.
  const ocultarDespensa = esAnalizar && seccionesExtendidas === true
  // Los tres editores bespoke no traen su propio control de borrado (a diferencia
  // del Editor genérico, que lo integra en su form) — #742. Fase cerrada no aplica
  // aquí: seleccion.tipo es siempre 'tarea', nunca 'fase' (mismo supuesto que ya
  // asume el Editor genérico para tareas).
  const esBespoke = esAnalizar || esElaborar || esNotificar
  const puedeBorrarTarea = esBespoke && puedeEditarNodo('tarea')
  // Fase CONSULTAS (ADR-042 §C, #396 bloque 5): a diferencia de los bespoke de
  // tarea, esto NO sustituye al Editor genérico — vive junto a él, como un
  // bloque de acciones más (mismo criterio que ReabrirFase).
  const esFaseConsultas = seleccion.tipo === 'fase' && nodo && nodo.tipo_codigo === 'CONSULTAS'
  return (
    <div className="d-flex flex-column h-100 arbol-inspector--lock">
      <BarraEdicion tipo={seleccion.tipo} nodo={nodo} />
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }} className="p-3">
        {!borrarPendienteConfirm && <BloqueoGuardarForzable />}
        {!borrarPendienteConfirm && esFaseConsultas && <AccionesFaseConsultas nodo={nodo} />}
        {borrarPendienteConfirm
          ? <ConfirmacionBorrado nodo={nodo} />
          : esAnalizar
            ? <AnalizarEditor tareaId={seleccion.id} />
            : esElaborar
              ? <ElaborarEditor tareaId={seleccion.id} nodo={nodo} />
              : esNotificar
                ? <NotificarEditor tareaId={seleccion.id} />
                : <Editor nodo={nodo} />
        }
        {!borrarPendienteConfirm && puedeBorrarTarea && <BotonBorrarTarea />}
        {!borrarPendienteConfirm && !ocultarDespensa && (
          <div className="border-top mt-3 pt-3">
            <Despensa deshabilitarProducido={esAnalizar} esEsperarPlazo={esEsperarPlazo} />
          </div>
        )}
      </div>
    </div>
  )
}

// --- Componente principal -------------------------------------------------------

export default function Inspector() {
  const seleccion = useArbolStore((s) => s.seleccion)
  const seleccionar = useArbolStore((s) => s.seleccionar)
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
  // Sellado (#720, ADR-036): Editar sigue disponible sobre la propia fase cerrada —
  // es el único camino hasta el botón "Reabrir fase" del editor — pero no sobre un
  // trámite/tarea cuya fase está cerrada, donde el backend rechazaría el guardado.
  const sellado = estaSellado(arbol, seleccion)
  const puedeEditar = puedeEditarNodo(seleccion.tipo) && (seleccion.tipo === 'fase' || !sellado)

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

      {sellado && seleccion.tipo !== 'fase' && (
        <div className="alert alert-secondary py-2 px-3 small mb-3">
          <i className="bi bi-lock-fill me-1" />
          Su fase está cerrada. Ábrala desde el inspector de la fase para reabrirla y
          poder modificar este elemento.
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
          <Organismos organismos={detalle.organismos} seleccionar={seleccionar} />
          <Documentos documentos={detalle.documentos} expedienteId={expedienteId} />
        </>
      )}

      {detalle && !cargando && (
        <Acciones referencia={detalle.referencia} expedienteId={expedienteId} />
      )}
    </div>
  )
}
