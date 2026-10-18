// Inspector.jsx — panel read-only adaptativo al nodo seleccionado (#500, ADR-016 §5).
//
// S3a (lectura): datos finos y documentos del detalle lazy (§16) + plazo + agregados del
// subárbol + acciones rápidas no destructivas (abrir doc, copiar referencia).
// Edición / despensa → S3b.
//
// La cabecera (tipo, título, estado, semáforo, candado) y los gestos de ver / editar /
// guardar / cancelar los pinta el shell, no este fichero (marco único, ADR-053 §A, #1042):
// los alimenta `puenteInspector.js` con el estado del store.
import React from 'react'
import { useArbolStore } from '../store.js'
import { showToast } from '../../shared/ui/toast.js'
import { puedeEditarNodo } from '../../shared/auth.js'
import { estaSellado } from '../sellado.js'
import BarraPlazo from './nodos/BarraPlazo.jsx'
import { barraDeActo, fechaLarga } from '../plazoActo.js'
import Despensa from './Despensa.jsx'
import { BloqueoForzar } from './TiposCreablesCompartido.jsx'
import { AccionGenerarEscrito } from './ElaborarEditor.jsx'
import TarjetaDestinatarioTramite from './notificar/DestinatarioTramite.jsx'
import { TarjetasNotificar } from './NotificarEditor.jsx'
import DatosNodo from './DatosNodo.jsx'
import { disenoDeNodo } from '../disenosDatos.js'
import { superficieDeNodoTarea, tieneDisenoTarea, idTramiteDeTarea } from '../superficiesTarea.js'
import { entradaDe, useHechosDelNodo } from '../registroEditores.jsx'

export const ETIQUETA_TIPO = {
  expediente: 'Expediente',
  solicitud:  'Solicitud',
  version:    'Versión',
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

export function buscarNodo(arbol, sel) {
  if (!arbol || !sel) return null
  if (sel.tipo === 'expediente') return arbol.expediente
  for (const sol of arbol.solicitudes || []) {
    if (sel.tipo === 'solicitud' && sol.id === sel.id) return sol
    for (const version of sol.versiones || []) {
      if (sel.tipo === 'version' && version.id === sel.id) return version
    }
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

export function tituloNodo(tipo, nodo) {
  if (!nodo) return ''
  if (tipo === 'expediente') return nodo.codigo || ''
  if (tipo === 'solicitud') return [nodo.siglas, nodo.descripcion].filter(Boolean).join(' — ')
  if (tipo === 'version') return nodo.etiqueta || ''
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

// --- Subcomponentes -------------------------------------------------------------

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

// --- Plazo de resolver por acto (#922, ADR-049 §E) ------------------------------
//
// El dato sale del propio nodo del árbol (`nodo.plazos`, lo vuelca
// `arbol_expediente.plazos_solicitud`), no del detalle lazy: el árbol ya lo trae, y así el
// bloque no puede discrepar de las barras ni cuesta una petición más. La solicitud
// enseña los de todos sus actos; la fase, solo los de los que ella resuelve.

const UNIDAD_PLAZO = {
  MESES:          ['mes', 'meses'],
  DIAS_HABILES:   ['día hábil', 'días hábiles'],
  DIAS_NATURALES: ['día natural', 'días naturales'],
  ANOS:           ['año', 'años'],
}

const diasHabiles = (n) => `${n} ${Math.abs(n) === 1 ? 'día hábil' : 'días hábiles'}`

// Las fases que resuelven un acto y que pueden aún no existir: se nombran por su código.
// Los actos con plazo solo caen en RESOLUCION, RESOLUCION_AAP/AAC y RESOLUCION_DUP.
function nombreFaseResolutora(codigo) {
  if (codigo === 'RESOLUCION') return 'Resolución'
  if (codigo && codigo.startsWith('RESOLUCION_')) return `Resolución ${codigo.slice('RESOLUCION_'.length)}`
  return codigo
}

function filasPlazoActo(p, { enFase, nombreFase }) {
  const filas = []
  const tarde = !!p.cumplido_fuera_de_plazo
  if (p.estado === 'CUMPLIDO') {
    filas.push(['Notificada', `${fechaLarga(p.fecha_cumplimiento)}, ${tarde ? 'fuera de plazo' : 'en plazo'}`])
    filas.push([tarde ? 'Venció' : 'Vencía', fechaLarga(p.fecha_limite)])
  } else if (p.estado === 'VENCIDO') {
    filas.push(['Venció', `${fechaLarga(p.fecha_limite)} (${diasHabiles(Math.abs(p.dias_restantes))} de retraso)`])
  } else {
    const resto = p.dias_restantes === null || p.dias_restantes === undefined
      ? '' : ` (${diasHabiles(p.dias_restantes)})`
    filas.push(['Vence', `${fechaLarga(p.fecha_limite)}${resto}`])
  }

  const [uno, varios] = UNIDAD_PLAZO[p.plazo_unidad] || [p.plazo_unidad, p.plazo_unidad]
  filas.push(['Plazo legal',
    `${p.plazo_valor} ${p.plazo_valor === 1 ? uno : varios} desde el ${fechaLarga(p.fecha_disparo)}`
    + (p.norma_origen ? ` · ${p.norma_origen}` : '')])

  // Suspensión (art. 22): el vencimiento de arriba ya viene desplazado.
  if (p.suspendido || p.dias_suspendidos > 0) {
    const sin = p.fecha_limite_sin_suspender
      ? `; sin la suspensión vencería el ${fechaLarga(p.fecha_limite_sin_suspender)}` : ''
    filas.push(['Suspensión', p.suspendido
      ? `Reloj parado desde el ${fechaLarga(p.suspendido_desde)}. Hasta hoy, ${diasHabiles(p.dias_suspendidos)} suspendidos${sin}`
      : `${diasHabiles(p.dias_suspendidos)} suspendidos${sin}`])
  }

  // El efecto del vencimiento: «Si vence» mientras corre; «Al vencer» si ya venció (aunque se
  // notificara después). Cumplido en plazo no lo muestra: ya no puede ocurrir. Una fila de
  // catálogo sin efecto llega sin `efecto_nombre` (el código es SIN_EFECTO_AUTOMATICO): sin
  // efecto que contar no se pinta la fila, y nunca se enseña el código en bruto.
  const cumplidoEnPlazo = p.estado === 'CUMPLIDO' && !tarde
  if (p.efecto_nombre && p.efecto !== 'NINGUNO' && !cumplidoEnPlazo) {
    const yaVencio = p.estado === 'VENCIDO' || tarde
    filas.push([yaVencio ? 'Al vencer' : 'Si vence', p.efecto_nombre])
  }
  if (!enFase) {
    filas.push(['Lo resuelve', nombreFase
      ? nombreFase : `${nombreFaseResolutora(p.fase_resolutora)} (aún sin crear)`])
  }
  return filas
}

function PlazosActos({ nodo, tipo }) {
  const plazos = nodo && nodo.plazos
  if (!plazos || plazos.length === 0) return null
  const enFase = tipo === 'fase'
  // La fase de cada acto, si ya existe, con el nombre que le da el árbol.
  const fases = (nodo.fases || [])
  return (
    <div className="mb-3">
      <div className="text-muted fw-semibold small mb-1">
        {enFase ? 'Plazo de resolver · actos que resuelve' : 'Plazo de resolver'}
      </div>
      {plazos.map((p) => {
        const b = barraDeActo(p)
        const etiqueta = b.tarde ? 'Cumplido fuera de plazo' : (ETIQUETA_PLAZO[p.estado] || p.estado)
        const fase = fases.find((f) => f.id === p.fase_resolutora_id)
        return (
          <div key={p.acto} className="arbol-plazo-acto">
            <div className="d-flex align-items-center justify-content-between gap-2 mb-1">
              <b className="small">{b.acto}</b>
              <span className="arbol-plazo-acto__estado" data-color={b.tarde ? 'rojo' : b.color}>
                {etiqueta}{b.parado ? ' · parado' : ''}
              </span>
            </div>
            <BarraPlazo plazo={p} conActo={false} />
            <dl className="arbol-plazo-acto__datos">
              {filasPlazoActo(p, { enFase, nombreFase: fase ? fase.nombre : null }).map(([k, v]) => (
                <React.Fragment key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </React.Fragment>
              ))}
            </dl>
          </div>
        )
      })}
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
// Sin `seleccionar` (en edición, #1043) las filas se ven pero no navegan: editar bloquea el
// árbol, y `seleccionar` no sale del modo edición ni limpia el borrador.
function Organismos({ organismos, seleccionar }) {
  if (!organismos || organismos.length === 0) return null
  return (
    <div className="mb-3">
      <div className="text-muted fw-semibold small mb-1">Organismos</div>
      <ul className="list-group list-group-flush">
        {organismos.map((o) => (
          <li key={o.id} className="list-group-item px-0 py-2"
              style={seleccionar ? { cursor: 'pointer' } : undefined}
              role={seleccionar ? 'button' : undefined}
              onClick={seleccionar ? () => seleccionar({ tipo: 'organismo', id: o.id }) : undefined}>
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

function Documentos({ documentos }) {
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

// Zona de datos del cuerpo: lo informativo del nodo, en el orden de siempre (#1043, ADR-053 §C).
//
// Es la misma en lectura y en edición: en edición lo informativo no desaparece, se pueda editar
// o no. La pintan en los dos modos los nodos que tienen un diseño en `disenosDatos.js`
// (expediente, solicitud, versión, fase, organismo, trámite y todas las tareas: la genérica,
// ANALIZAR, ELABORAR y NOTIFICAR). Solo sin nodo en el árbol (no debería pasar) cae en la lista de
// texto plano.
function ZonaDatos({ nodo, tipo, detalle, seleccionar }) {
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const expedienteId = useArbolStore((s) => s.expedienteId)
  const arbol = useArbolStore((s) => s.arbol)
  const esHoja = tipo === 'tarea'
  // Las tarjetas propias de los tipos ya migrados al registro de editores (#1047).
  const entrada = entradaDe(tipo, nodo, arbol)
  const ctx = { tipo, id: detalle.nodo.id, nodo, detalle, expedienteId, arbol, modoEdicion }
  // La tarea tiene diseño si es genérica o su superficie ya migró (todas hoy).
  const superficie = esHoja ? superficieDeNodoTarea(arbol, nodo) : null
  const tareaConDiseno = esHoja && !!nodo && tieneDisenoTarea(superficie)
  const diseno = disenoDeNodo(tipo, { tareaConDiseno })
  // Fase cerrada (#720, ADR-036): los controles vivos se deshabilitan.
  const faseCerrada = tipo === 'fase' && !!nodo && nodo.estado === 'FINALIZADA'
  return (
    <>
      {diseno
        ? <DatosNodo diseno={diseno} detalle={detalle} nodo={nodo} bloqueado={faseCerrada} />
        : <Campos campos={detalle.campos} />}
      {entrada && entrada.tarjetas.map((t) => <React.Fragment key={t.clave}>{t.render(ctx)}</React.Fragment>)}
      {superficie === 'ELABORAR' && idTramiteDeTarea(arbol, Number(detalle.nodo.id)) != null && (
        <TarjetaDestinatarioTramite expedienteId={expedienteId}
                                    tramiteId={idTramiteDeTarea(arbol, Number(detalle.nodo.id))} />
      )}
      {superficie === 'NOTIFICAR' && (
        <TarjetasNotificar expedienteId={expedienteId} tareaId={Number(detalle.nodo.id)}
                           soloLectura={!modoEdicion} />
      )}
      {!esHoja && nodo && <Agregados agregados={nodo.agregados} />}
      <Plazo plazo={detalle.plazo} />
      <PlazosActos nodo={nodo} tipo={tipo} />
      <Organismos organismos={detalle.organismos} seleccionar={modoEdicion ? null : seleccionar} />
      <Documentos documentos={detalle.documentos} />
    </>
  )
}

function Acciones({ referencia }) {
  if (!referencia) return null
  return (
    <div className="d-flex flex-wrap gap-2 border-top pt-2 mt-auto">
      <button
        type="button"
        className="btn btn-sm btn-outline-secondary"
        onClick={() => copiarReferencia(referencia)}
      >
        <i className="bi bi-clipboard me-1" />Copiar referencia
      </button>
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

// «Guardar» de la barra con texto sin guardar en un bloque interior (#1055): guardar sale a lectura y
// lo tiraría, igual que «Cancelar», así que antes se pregunta (`pedirGuardar`, en el store). Va como
// el aviso de arriba: en el flujo del panel, no en un diálogo.
function AvisoGuardarInterior() {
  const aviso     = useArbolStore((s) => s.avisoGuardarInterior)
  const interior  = useArbolStore((s) => s.interiorSucio)
  const guardando = useArbolStore((s) => s.guardando)
  const guardar   = useArbolStore((s) => s.guardar)
  const seguir    = useArbolStore((s) => s.seguirEditando)
  const ref       = React.useRef(null)

  // El «Guardar» está en la barra fija: con el panel desplazado, el aviso queda fuera de vista.
  React.useEffect(() => {
    if (aviso && ref.current) ref.current.scrollIntoView({ block: 'nearest' })
  }, [aviso])

  if (!aviso) return null
  const rotulos = [...new Set(Object.values(interior))]

  return (
    <div ref={ref} className="alert alert-warning py-2 px-3 small mb-3">
      <div className="fw-semibold">Hay texto sin guardar en {rotulos.length ? rotulos.join(', ') : 'un bloque'}.</div>
      <div>Cada bloque se guarda con su propio botón. Si guardas ahora, ese texto se perderá.</div>
      <div className="d-flex gap-2 mt-2">
        <button type="button" className="btn btn-sm btn-warning" disabled={guardando}
                onClick={() => { seguir(); guardar() }}>
          Guardar igualmente
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={guardando}
                onClick={seguir}>
          Seguir editando
        </button>
      </div>
    </div>
  )
}

// Control de borrado compartido por los tres editores bespoke de tarea (ANALIZAR/
// ELABORAR/NOTIFICAR, #742) y por los nodos con diseño de datos (#1043): ninguno de los tres
// bespoke lo trae de fábrica — se hoistea aquí, al nivel de InspectorEdicion, en vez de triplicarlo
// en cada uno (mismo criterio ya aplicado a Despensa: es el contenedor común quien pone el
// "chrome" alrededor del editor).
function BotonBorrar() {
  const solicitarBorrado = useArbolStore((s) => s.solicitarBorrado)
  return (
    <div className="d-flex mt-3">
      <button type="button" className="btn btn-sm btn-outline-danger"
              onClick={solicitarBorrado}>🗑️ Borrar</button>
    </div>
  )
}

// En edición: editor y despensa juntos, en el flujo normal del cuerpo del shell, que es el
// único que hace scroll (#725 tarea 6, #1042). La cabecera y el control de salida
// (Guardar / Cancelar / Cerrar) los pinta el marco del shell, fuera de ese scroll
// (ADR-023 §5 bis, ADR-053 §A). Antes la despensa vivía en un split fijo aparte (120px al
// fondo del panel) que competía por la misma franja del viewport con el toast-container
// (bottom-0, custom.css) — dos elementos fijos al fondo siempre se pisan. En lectura NO hay
// split (igual que S3a). El borde+sombra de edición va en el panel entero
// (`body.arbol-lock .app-inspector`, arbol.css) porque editar bloquea el resto de la UI desde
// que se entra; el inspector NUNCA se atenúa (es la zona interactiva).
function InspectorEdicion({ nodo }) {
  const expedienteId          = useArbolStore((s) => s.expedienteId)
  const seleccion             = useArbolStore((s) => s.seleccion)
  const borrarPendienteConfirm = useArbolStore((s) => s.borrarPendienteConfirm)
  const arbol                 = useArbolStore((s) => s.arbol)
  // Qué lleva este nodo, según el registro de editores (#1047). Los tipos que aún no tienen entrada
  // (`null`) siguen por las banderas de abajo, que se retiran a medida que se migran.
  const entrada = entradaDe(seleccion.tipo, nodo, arbol)
  // La superficie de trabajo propia de la tarea sale de una única tabla por tipo de tarea y trámite
  // (`superficiesTarea.js`); una tarea que no figura en ella es genérica (más abajo).
  const superficie = seleccion.tipo === 'tarea' ? superficieDeNodoTarea(arbol, nodo) : null
  // ELABORAR (#608, #1043): ya usa el diseño de datos de la tarea. El destinatario del escrito es
  // una tarjeta de datos —en lectura y en edición— y "Generar escrito" (backend #167, huérfano de UI
  // desde la eliminación del sistema BC en #500), una acción de la zona de acciones
  // (`AccionGenerarEscrito`). La Despensa NO se deshabilita — sigue siendo el mecanismo genérico que
  // vincula el borrador de firma y el documento firmado.
  const esElaborar = superficie === 'ELABORAR'
  // NOTIFICAR (#657/#658, ADR-034; #1043): ya usa el diseño de datos de la tarea. Aviso, destinatario,
  // registro y justificantes previos son tarjetas de datos —en lectura y en edición— con sus controles
  // vivos dentro (`TarjetasNotificar`); no tiene acciones propias. Igual que ELABORAR, la Despensa NO se
  // deshabilita.
  // Todos los nodos tienen diseño de datos (#1043, lectura ≈ edición): la edición pinta la misma zona
  // de datos que la lectura y debajo las acciones y el pie.
  const detalle      = useArbolStore((s) => s.detalle)
  const cargandoDet  = useArbolStore((s) => s.detalleCargando)
  const seleccionar  = useArbolStore((s) => s.seleccionar)
  const hayDetalle   = !!detalle && !cargandoDet
  // Los hechos que salen de un store (hooks que van siempre): los leen las entradas del registro.
  const hechos = useHechosDelNodo(Number(seleccion.id))
  // Nodos migrados (#1043): la misma columna que la lectura (alto completo, pie pegado abajo) y
  // tres zonas en este orden: datos (la misma zona que en lectura), acciones y creación (solo
  // en edición, debajo de los datos) y pie. En las acciones va primero la Despensa —lo
  // frecuente, con su panel a la vista—, después las propias del nodo (la bisagra de la
  // solicitud; las consultas, el cumplimiento, el cierre y la reapertura de la fase) y, al
  // fondo, «Borrar», por destructivo.
  const ctx = { tipo: seleccion.tipo, id: seleccion.id, nodo, detalle, hayDetalle, expedienteId, arbol, modoEdicion: true, ...hechos }
  // «Borrar» y la Despensa del nodo: de su entrada, o de las banderas mientras el tipo no esté migrado.
  const borrable = !entrada ? seleccion.tipo !== 'expediente'
    : (typeof entrada.borrable === 'function' ? entrada.borrable(ctx) : entrada.borrable)
  const puedeBorrar = borrable && puedeEditarNodo(seleccion.tipo)
  const despensa = entrada ? entrada.despensa : {}
  // Las acciones propias solo se pintan si hay alguna, para no dejar un separador vacío: con que una de las de
  // la entrada tenga algo que enseñar (`hay`) se pinta la zona y entonces van todas, cada una decide si dice algo.
  const hayPropias = (!!entrada && entrada.acciones.some((a) => a.hay(ctx)))
    || esElaborar
  return (
    <div className="p-3 d-flex flex-column h-100">
      {!borrarPendienteConfirm && <BloqueoGuardarForzable />}
      {!borrarPendienteConfirm && <AvisoGuardarInterior />}
      {hayDetalle && (
        <ZonaDatos nodo={nodo} tipo={seleccion.tipo} detalle={detalle} seleccionar={seleccionar} />
      )}
      {borrarPendienteConfirm
        ? <ConfirmacionBorrado nodo={nodo} />
        : (
          <>
            {!despensa.oculta && (
              <div className="border-top mt-3 pt-3">
                <Despensa deshabilitarProducido={!!despensa.deshabilitarProducido}
                          esEsperarPlazo={!!despensa.ayudaRecepcion} />
              </div>
            )}
            {hayPropias && (
              <div className="border-top mt-3 pt-3">
                {entrada && entrada.acciones.map((a) => <React.Fragment key={a.clave}>{a.render(ctx)}</React.Fragment>)}
                {esElaborar && <AccionGenerarEscrito tareaId={seleccion.id} nodo={nodo} />}
              </div>
            )}
            {puedeBorrar && <div className="mb-3"><BotonBorrar /></div>}
          </>
        )}
      {entrada && entrada.modales.map((m) => <React.Fragment key={m.clave}>{m.render(ctx)}</React.Fragment>)}
      {hayDetalle && <Acciones referencia={detalle.referencia} />}
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
  const modoEdicion = useArbolStore((s) => s.modoEdicion)

  if (!seleccion) {
    return (
      <div className="p-3 text-muted small d-flex align-items-center justify-content-center h-100 text-center">
        Selecciona un elemento del árbol
      </div>
    )
  }

  const nodo = buscarNodo(arbol, seleccion)
  if (modoEdicion) return <InspectorEdicion nodo={nodo} />
  // Sellado (#720, ADR-036): el botón Editar del marco sigue disponible sobre la propia fase
  // cerrada —es el único camino hasta el botón "Reabrir fase" del editor— pero no sobre un
  // trámite/tarea cuya fase está cerrada, donde el backend rechazaría el guardado (la
  // condición vive en puenteInspector.js: `puedeEditar`).
  const sellado = estaSellado(arbol, seleccion)

  return (
    <div className="p-3 d-flex flex-column h-100">
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
        <ZonaDatos nodo={nodo} tipo={seleccion.tipo} detalle={detalle} seleccionar={seleccionar} />
      )}

      {detalle && !cargando && (
        <Acciones referencia={detalle.referencia} />
      )}
    </div>
  )
}
