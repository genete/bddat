// Despensa.jsx — zona inferior del split del inspector en edición (ADR-016 §5/§10).
//
// Modo adaptativo según el tipo de nodo seleccionado:
//   · tipos-creables (S3b-2): solicitud, fase, trámite, tarea  → lista de tipos + zona de drop/staging
//   · docs del pool (S3b-3):  tarea  → fichas de doc del pool + staging consumido/producido
import React from 'react'
import { useArbolStore } from '../store.js'
import { api } from '../../shared/api.js'
import { getTiposDocumento } from '../api.js'
import { showToast } from '../../shared/ui/toast.js'
import { estaSellado } from '../sellado.js'
import { FilaTipoCreable, BloqueoForzar } from './TiposCreablesCompartido.jsx'

// ─── Modo tipos-creables (S3b-2) ────────────────────────────────────────────

const ETIQUETA_TIPO_HIJO = {
  solicitud: 'solicitud',
  fase:      'fase',
  tramite:   'trámite',
  tarea:     'tarea',
}

function DespensaTipos() {
  const seleccion              = useArbolStore((s) => s.seleccion)
  const tiposCreables          = useArbolStore((s) => s.tiposCreables)
  const tiposCreablesCargando  = useArbolStore((s) => s.tiposCreablesCargando)
  const tipoCreacionPendiente  = useArbolStore((s) => s.tipoCreacionPendiente)
  const bloqueoActual          = useArbolStore((s) => s.bloqueoActual)
  const justificacionForzar    = useArbolStore((s) => s.justificacionForzar)
  const creando                = useArbolStore((s) => s.creando)
  const cargarTiposCreables    = useArbolStore((s) => s.cargarTiposCreables)
  const seleccionarTipoCrear   = useArbolStore((s) => s.seleccionarTipoCrear)
  const cancelarCrear          = useArbolStore((s) => s.cancelarCrear)
  const setJustificacionForzar = useArbolStore((s) => s.setJustificacionForzar)
  const crearHijo              = useArbolStore((s) => s.crearHijo)
  const anclaSolicitudId       = useArbolStore((s) => s.anclaSolicitudId)

  // Lo que se crea bajo un expediente es siempre una solicitud, y esa necesita
  // ancla documental (#428).
  const creaSolicitud = tiposCreables?.tipo_hijo === 'solicitud'

  const [mostrarResto, setMostrarResto] = React.useState(false)
  const [draggingOver, setDraggingOver] = React.useState(false)

  React.useEffect(() => {
    cargarTiposCreables(seleccion)
  }, [seleccion?.tipo, seleccion?.id])  // eslint-disable-line

  if (tiposCreablesCargando) {
    return <div className="p-2 text-muted small fst-italic">Cargando tipos…</div>
  }
  if (!tiposCreables) return null

  // canonicos/resto (ADR-037 §D): vocabulario, no permiso — el motor no se ha
  // evaluado todavía para ninguno de los dos. "Mostrar todos" ahora revela el
  // resto (tipos válidos pero fuera del patrón habitual de esta fase/trámite).
  const canonicos  = tiposCreables.canonicos || []
  const resto      = tiposCreables.resto || []
  const mostrados  = mostrarResto ? [...canonicos, ...resto] : canonicos
  const hayResto   = resto.length > 0
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
        {(canonicos.length + resto.length) > 0 && (
          <div className="form-check form-switch d-flex align-items-center gap-1 m-0">
            <input
              className="form-check-input"
              type="checkbox"
              role="switch"
              id="despensa-mostrar-todos"
              checked={mostrarResto}
              disabled={!hayResto}
              onChange={() => setMostrarResto((v) => !v)}
              title={!hayResto ? 'No hay más tipos que mostrar' : undefined}
            />
            <label className="form-check-label small text-muted" htmlFor="despensa-mostrar-todos">
              Mostrar todos
            </label>
          </div>
        )}
      </div>

      {mostrados.length > 0 ? (
        <div className="d-flex flex-column gap-1">
          {mostrados.map((t) => (
            <FilaTipoCreable
              key={t.tipo_id}
              tipo={t}
              variante="panel"
              seleccionado={tipoCreacionPendiente?.tipo_id === t.tipo_id}
              onClick={() => seleccionarTipoCrear(t)}
              draggable
              onDragStart={onDragStart(t)}
            />
          ))}
        </div>
      ) : (
        <div className="text-muted small fst-italic">No hay tipos disponibles</div>
      )}

      {tipoCreacionPendiente && bloqueoActual ? (
        <BloqueoForzar
          bloqueo={bloqueoActual}
          tipoNombre={tipoCreacionPendiente.nombre}
          justificacion={justificacionForzar}
          setJustificacion={setJustificacionForzar}
          creando={creando}
          onForzar={crearHijo}
          onCancelar={cancelarCrear}
        />
      ) : tipoCreacionPendiente ? (
        <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-primary-subtle border-primary-subtle">
          {/* Bajo expediente lo que se crea es una solicitud, y ninguna nace sin su
              escrito (#428): el selector va aquí, antes del botón, para que no se
              pueda pulsar Crear sin haberlo elegido. */}
          {creaSolicitud && <AnclaSolicitud />}
          <div className="d-flex align-items-center gap-2">
            <span className="small flex-grow-1 text-truncate">
              <strong>{tipoCreacionPendiente.nombre}</strong>
            </span>
            <button
              type="button"
              className="btn btn-sm btn-primary"
              disabled={creando || (creaSolicitud && !anclaSolicitudId)}
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

// Regla de recepción de #764 (ADR-004 y ADR-010, notas 2026-08-07;
// `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §5): el vínculo PRODUCIDO de
// ESPERAR_PLAZO es de cardinalidad 1 y se reserva al documento que acredita el
// hecho y porta su fecha administrativa; los anexos que lleguen con él entran al
// pool y los consume el ANALIZAR siguiente. La regla no estaba en ninguna parte
// de la interfaz y quien tramita no sabía cuál de los documentos recién llegados
// elegir (#766).
//
// GEMELO EN PYTHON: `AYUDA_PRODUCIDO_ESPERAR_PLAZO` en
// `app/modules/tareas_y_subidas/routes.py` — misma redacción para los dos sitios
// donde aparece la decisión (allí, la cola; aquí, el árbol, que es donde se
// vincula de verdad). Si cambia una, cambiar la otra.
export const AYUDA_PRODUCIDO_ESPERAR_PLAZO =
  'Vincula el documento que acredita la recepción y su fecha: registro de entrada, '
  + 'solicitud, justificante de BandeJA o acuse de publicación. Los anexos que lo '
  + 'acompañen se consumen después, en la tarea de análisis.'

async function postAccion(url) {
  try {
    await api.post(url)
  } catch (e) {
    showToast((e && e.message) || 'No se pudo completar la acción', 'danger')
  }
}

// Acciones de apertura (enlace + carpeta) de un documento del pool — mismo
// mecanismo que Inspector.jsx en modo lectura, disponible aquí también antes
// de decidir enlazar el documento a la tarea (#609).
function AccionesApertura({ doc, expedienteId }) {
  return (
    <div className="d-flex align-items-center gap-1" onClick={(e) => e.stopPropagation()}>
      {doc.enlace && doc.abrir_en === 'modal' && (
        <button
          type="button"
          // El div padre corta la propagación (stopPropagation, más abajo) para
          // que estos botones no disparen el onClick de selección de FichaDoc —
          // eso impide que el atributo declarativo data-modal-large-url llegue
          // al listener global de document (inspector-overlay.js). Se llama
          // AppModalLarge directamente en vez de depender de esa delegación.
          onClick={() => window.AppModalLarge && window.AppModalLarge.open(doc.enlace, { title: doc.nombre })}
          className="btn btn-sm btn-link p-0 text-secondary lh-1"
          style={{ fontSize: '0.85rem' }}
          title="Ver documento"
        >
          <i className="bi bi-box-arrow-up-right" />
        </button>
      )}
      {doc.enlace && doc.abrir_en !== 'modal' && (
        <a
          href={doc.enlace}
          target="_blank"
          rel="noreferrer"
          className="btn btn-sm btn-link p-0 text-secondary lh-1"
          style={{ fontSize: '0.85rem' }}
          title="Abrir documento"
        >
          <i className="bi bi-box-arrow-up-right" />
        </a>
      )}
      {doc.puede_abrir_carpeta && (
        <button
          type="button"
          className="btn btn-sm btn-link p-0 text-secondary lh-1"
          style={{ fontSize: '0.85rem' }}
          title="Abrir carpeta del documento"
          onClick={() => postAccion(`/expedientes/${expedienteId}/documentos/${doc.id}/abrir-en-carpeta`)}
        >
          <i className="bi bi-folder2-open" />
        </button>
      )}
    </div>
  )
}

// Contenedor no-button (para poder anidar enlace/botón de apertura sin HTML
// inválido) con el mismo aspecto visual que el botón que sustituye.
function FichaDoc({ doc, vinculado, seleccionada, onClick, expedienteId }) {
  return (
    <div
      className={`btn btn-sm w-100 text-start border rounded px-2 py-1 d-flex align-items-center gap-2 ${
        seleccionada
          ? 'btn-primary'
          : vinculado
            ? 'btn-outline-success'
            : 'btn-outline-secondary'
      }`}
      style={{ fontSize: '0.78rem', cursor: 'pointer' }}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() } }}
      title={doc.nombre}
    >
      <div className="flex-grow-1 text-truncate">
        <div className="text-truncate fw-semibold">{doc.nombre}</div>
        <div className="text-truncate opacity-75">
          {[doc.tipo_doc, doc.fecha].filter(Boolean).join(' · ')}
        </div>
      </div>
      <AccionesApertura doc={doc} expedienteId={expedienteId} />
    </div>
  )
}

// Ancla documental de la solicitud que se está creando (#428).
//
// Toda solicitud nace con el escrito que la abre, porque de su fecha de registro
// cuelga el inicio del plazo para resolver. En esta vía el expediente ya existe, así
// que el escrito se elige de su pool; si todavía no está, se sube aquí mismo con el
// tipo ya fijado, sin salir del árbol.
//
// Solo se ofrecen documentos CON fecha administrativa: uno sin fecha no ancla nada
// —el backend lo rechaza por lo mismo— y ofrecerlo sería invitar a un error que se
// descubre tarde, cuando el plazo consta SIN_PLAZO.
function AnclaSolicitud() {
  const pool               = useArbolStore((s) => s.pool)
  const poolCargando       = useArbolStore((s) => s.poolCargando)
  const cargarPool         = useArbolStore((s) => s.cargarPool)
  const anclaSolicitudId   = useArbolStore((s) => s.anclaSolicitudId)
  const setAnclaSolicitudId = useArbolStore((s) => s.setAnclaSolicitudId)

  const [subiendo, setSubiendo] = React.useState(false)

  React.useEffect(() => { cargarPool() }, [])  // eslint-disable-line

  // Los del tipo canónico primero: es lo que se busca el 99% de las veces, pero no
  // se filtra el resto porque un escrito puede haber entrado clasificado de otra
  // manera y obligar a salir del árbol para arreglarlo sería peor.
  const candidatos = React.useMemo(() => {
    const conFecha = (pool || []).filter((d) => d.fecha)
    const canonicos = conFecha.filter((d) => d.tipo_doc_codigo === 'MODELO_SOLICITUD')
    const resto = conFecha.filter((d) => d.tipo_doc_codigo !== 'MODELO_SOLICITUD')
    return [...canonicos, ...resto]
  }, [pool])

  return (
    <div className="d-flex flex-column gap-1">
      <label className="small fw-semibold mb-0">
        Escrito de solicitud <span className="text-danger">*</span>
      </label>

      {poolCargando ? (
        <div className="small text-muted fst-italic">Cargando el pool…</div>
      ) : (
        <select
          className="form-select form-select-sm"
          value={anclaSolicitudId}
          onChange={(e) => setAnclaSolicitudId(e.target.value)}
        >
          <option value="">— Elija el documento —</option>
          {candidatos.map((d) => (
            <option key={d.id} value={d.id}>
              {d.fecha} · {d.nombre}
            </option>
          ))}
        </select>
      )}

      {!poolCargando && candidatos.length === 0 && (
        <div className="small text-muted">
          No hay documentos con fecha de registro en el pool. Suba el escrito aquí.
        </div>
      )}

      {subiendo ? (
        <SubidaAncla onHecho={() => setSubiendo(false)} />
      ) : (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setSubiendo(true)}
        >
          <i className="bi bi-upload me-1" /> Subir el escrito
        </button>
      )}

      <div className="small text-muted">
        De su fecha de registro arranca el plazo para resolver.
      </div>
    </div>
  )
}


// Subida del escrito de solicitud, con el tipo documental ya resuelto (#428).
//
// El tipo se busca por código y nunca por id: MODELO_SOLICITUD es 146 en desarrollo
// y 56 en una instalación limpia, así que un id escrito aquí funcionaría hasta el
// día del despliegue. La fecha es obligatoria porque es el dato que se está
// aportando — el fichero solo lo acredita.
function SubidaAncla({ onHecho }) {
  const subiendoDocumento   = useArbolStore((s) => s.subiendoDocumento)
  const subirAnclaSolicitud = useArbolStore((s) => s.subirAnclaSolicitud)

  const [fichero, setFichero]   = React.useState(null)
  const [fecha, setFecha]       = React.useState('')
  const [tipoDocId, setTipoDocId] = React.useState(null)

  React.useEffect(() => {
    getTiposDocumento()
      .then((d) => {
        const t = (d.data || []).find((x) => x.codigo === 'MODELO_SOLICITUD')
        setTipoDocId(t ? t.id : null)
      })
      .catch(() => setTipoDocId(null))
  }, [])

  const enviar = async () => {
    if (!fichero || !fecha) return
    const ok = await subirAnclaSolicitud(fichero, {
      tipo_doc_id: tipoDocId,
      asunto: 'Escrito de solicitud',
      fecha_administrativa: fecha,
      prioridad: false,
    })
    if (ok) onHecho()
  }

  return (
    <div className="d-flex flex-column gap-1 p-2 rounded border bg-body">
      <div className="d-flex align-items-center gap-2">
        <label htmlFor="ancla-solicitud-file"
               className="btn btn-sm btn-outline-secondary mb-0 flex-shrink-0">
          Seleccionar archivo
        </label>
        <input
          type="file"
          id="ancla-solicitud-file"
          className="visually-hidden"
          onChange={(e) => setFichero(e.target.files?.[0] || null)}
        />
        <span className="small text-truncate text-muted">
          {fichero ? fichero.name : 'Ningún archivo seleccionado'}
        </span>
      </div>
      <input
        type="date"
        className="form-control form-control-sm"
        value={fecha}
        onChange={(e) => setFecha(e.target.value)}
        title="Fecha de registro de entrada"
      />
      <div className="d-flex gap-1">
        <button
          type="button"
          className="btn btn-sm btn-primary flex-grow-1"
          disabled={!fichero || !fecha || subiendoDocumento}
          onClick={enviar}
        >
          {subiendoDocumento ? '…' : 'Subir'}
        </button>
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          disabled={subiendoDocumento}
          onClick={onHecho}
        >
          ✕
        </button>
      </div>
    </div>
  )
}


// Formulario de subida inline de la Despensa (#367): sube un fichero nuevo
// directamente desde la tarea, sin salir al pool del expediente. Nunca
// vincula directamente — deja el documento en la misma zona de staging que
// ya usa la vía A del radar de huérfanos (ADR-038 §5); el técnico confirma
// el rol y pulsa Guardar.
function SubidaInline({ tareaId }) {
  const subiendoDocumento      = useArbolStore((s) => s.subiendoDocumento)
  const sugerenciaSubida       = useArbolStore((s) => s.sugerenciaSubida)
  const subirDocumentoDespensa = useArbolStore((s) => s.subirDocumentoDespensa)

  const [abierto, setAbierto]     = React.useState(false)
  const [fichero, setFichero]     = React.useState(null)
  const [tipoDocId, setTipoDocId] = React.useState('')
  const [asunto, setAsunto]       = React.useState('')
  const [fecha, setFecha]         = React.useState('')
  const [prioridad, setPrioridad] = React.useState(false)
  const [tiposDoc, setTiposDoc]   = React.useState([])

  // Pre-rellena con la sugerencia ya cargada por cargarSugerenciaSubida() al
  // abrir el formulario — nunca bloqueante, siempre editable.
  React.useEffect(() => {
    if (!abierto) return
    if (sugerenciaSubida?.tipo_doc_id) setTipoDocId(String(sugerenciaSubida.tipo_doc_id))
    if (sugerenciaSubida?.asunto) setAsunto(sugerenciaSubida.asunto)
  }, [abierto])  // eslint-disable-line

  React.useEffect(() => {
    if (!abierto || tiposDoc.length > 0) return
    getTiposDocumento().then((d) => setTiposDoc(d.data || [])).catch(() => {})
  }, [abierto])  // eslint-disable-line

  if (!abierto) {
    return (
      <button
        type="button"
        className="btn btn-sm btn-outline-primary w-100"
        onClick={() => setAbierto(true)}
      >
        <i className="bi bi-upload me-1" /> Subir documento nuevo
      </button>
    )
  }

  const enviar = async () => {
    if (!fichero) return
    const ok = await subirDocumentoDespensa(fichero, {
      tipo_doc_id: tipoDocId || 1,
      asunto: asunto.trim() || null,
      fecha_administrativa: fecha || null,
      prioridad,
    })
    if (ok) {
      setAbierto(false); setFichero(null); setTipoDocId(''); setAsunto(''); setFecha(''); setPrioridad(false)
    }
  }

  return (
    <div className="d-flex flex-column gap-1 px-2 py-1 rounded border">
      {/* Input nativo oculto tras un <label>-botón (#367): el botón nativo
          "Seleccionar archivo" hereda en algunos entornos (Windows con acento
          oscuro) un estilo de hover que ni siquiera CSS !important sobrescribe
          — es un widget del SO, no un pseudo-elemento estilable. El <label>
          normal sí queda bajo control total de Bootstrap/nuestro CSS. */}
      <div className="d-flex align-items-center gap-2">
        <label
          htmlFor={`despensa-subida-file-${tareaId}`}
          className="btn btn-sm btn-outline-secondary mb-0 flex-shrink-0"
        >
          Seleccionar archivo
        </label>
        <input
          type="file"
          id={`despensa-subida-file-${tareaId}`}
          className="visually-hidden"
          onChange={(e) => setFichero(e.target.files?.[0] || null)}
        />
        <span className="small text-truncate text-muted">
          {fichero ? fichero.name : 'Ningún archivo seleccionado'}
        </span>
      </div>
      <select
        className="form-select form-select-sm"
        value={tipoDocId}
        onChange={(e) => setTipoDocId(e.target.value)}
      >
        <option value="">— Tipo —</option>
        {tiposDoc.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
      </select>
      <input
        type="text"
        className="form-control form-control-sm"
        placeholder="Asunto"
        value={asunto}
        onChange={(e) => setAsunto(e.target.value)}
        maxLength={500}
      />
      <input
        type="date"
        className="form-control form-control-sm"
        value={fecha}
        onChange={(e) => setFecha(e.target.value)}
      />
      <div className="form-check">
        <input
          type="checkbox"
          className="form-check-input"
          id="despensa-subida-inline-prioridad"
          checked={prioridad}
          onChange={(e) => setPrioridad(e.target.checked)}
        />
        <label className="form-check-label small" htmlFor="despensa-subida-inline-prioridad">
          Prioritario
        </label>
      </div>
      <div className="d-flex gap-1">
        <button
          type="button"
          className="btn btn-sm btn-primary flex-grow-1"
          disabled={!fichero || subiendoDocumento}
          onClick={enviar}
        >
          {subiendoDocumento ? 'Subiendo…' : 'Subir y vincular'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setAbierto(false)}>
          ✕
        </button>
      </div>
    </div>
  )
}

function DespensaDocs({ deshabilitarProducido, esEsperarPlazo }) {
  const seleccion               = useArbolStore((s) => s.seleccion)
  const expedienteId            = useArbolStore((s) => s.expedienteId)
  const borrador                = useArbolStore((s) => s.borrador)
  const pool                    = useArbolStore((s) => s.pool)
  const poolCargando            = useArbolStore((s) => s.poolCargando)
  const docVinculandoPendiente  = useArbolStore((s) => s.docVinculandoPendiente)
  const cargarPool              = useArbolStore((s) => s.cargarPool)
  const cargarSugerenciaSubida  = useArbolStore((s) => s.cargarSugerenciaSubida)
  const seleccionarDocVincular  = useArbolStore((s) => s.seleccionarDocVincular)
  const cancelarVincular        = useArbolStore((s) => s.cancelarVincular)
  const vincularDoc             = useArbolStore((s) => s.vincularDoc)
  const quitarDoc               = useArbolStore((s) => s.quitarDoc)

  React.useEffect(() => {
    cargarPool()
    cargarSugerenciaSubida(seleccion?.id)
  }, [seleccion?.id])  // eslint-disable-line

  // Separar roles para poder distinguirlos (#517: validaciones y lista activos)
  const consumidosIds = React.useMemo(
    () => new Set(borrador.documentos_consumidos_ids || []),
    [borrador.documentos_consumidos_ids],
  )
  const producidoId = borrador.documento_producido_id ?? null

  // Lookup rápido id→doc del pool para mostrar nombres en la lista de vínculos activos
  const poolById = React.useMemo(
    () => Object.fromEntries(pool.map((d) => [d.id, d])),
    [pool],
  )

  // Lista ordenada: consumidos primero, producido al final
  const vinculadosActivos = React.useMemo(() => {
    const items = []
    for (const id of consumidosIds) {
      const doc = poolById[id]
      if (doc) items.push({ doc, rol: 'CONSUMIDO' })
    }
    if (producidoId) {
      const doc = poolById[producidoId]
      if (doc) items.push({ doc, rol: 'PRODUCIDO' })
    }
    return items
  }, [consumidosIds, producidoId, poolById])

  if (poolCargando) {
    return <div className="p-2 text-muted small fst-italic">Cargando documentos…</div>
  }

  // Guards de staging: un doc no puede ser consumido y producido a la vez
  const docPendienteId = docVinculandoPendiente?.id
  const yaConsumido    = docPendienteId ? consumidosIds.has(docPendienteId) : false
  const yaProducido    = docPendienteId ? producidoId === docPendienteId : false

  return (
    <div className="p-2 d-flex flex-column gap-2">

      {/* ── Vínculos activos (solo si hay alguno) ── */}
      {vinculadosActivos.length > 0 && (
        <div className="d-flex flex-column gap-1">
          <span className="text-muted small fw-semibold">Documentos de esta tarea</span>
          {vinculadosActivos.map(({ doc, rol }) => (
            <div
              key={`${rol}-${doc.id}`}
              className="d-flex align-items-center gap-1 px-2 py-1 rounded border border-success-subtle bg-success-subtle"
              style={{ fontSize: '0.78rem' }}
            >
              <span className={`badge me-1 ${rol === 'CONSUMIDO' ? 'text-bg-success' : 'text-bg-primary'}`}>
                {rol === 'CONSUMIDO' ? 'Consumido' : 'Producido'}
              </span>
              <span className="text-truncate flex-grow-1 fw-semibold" title={doc.nombre}>{doc.nombre}</span>
              <AccionesApertura doc={doc} expedienteId={expedienteId} />
              <button
                type="button"
                className="btn btn-sm btn-link text-danger p-0 lh-1"
                style={{ fontSize: '0.9rem' }}
                title="Quitar vínculo"
                onClick={() => quitarDoc(rol, doc.id)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Pool ── */}
      <span className="text-muted small fw-semibold">Pool de documentos</span>

      {pool.length === 0 ? (
        <div className="text-muted small fst-italic">No hay documentos en el expediente</div>
      ) : (
        <div className="d-flex flex-column gap-1" style={{ maxHeight: 120, overflowY: 'auto' }}>
          {pool.map((doc) => (
            <FichaDoc
              key={doc.id}
              doc={doc}
              vinculado={consumidosIds.has(doc.id) || producidoId === doc.id}
              seleccionada={docVinculandoPendiente?.id === doc.id}
              expedienteId={expedienteId}
              onClick={() =>
                docVinculandoPendiente?.id === doc.id
                  ? cancelarVincular()
                  : seleccionarDocVincular(doc)
              }
            />
          ))}
        </div>
      )}

      {/* ── Ayuda de recepción (#766): qué documento es el producido cuando
             llegan varios. Va sobre la zona de staging, para que se lea tanto
             antes de elegir del pool como con el documento ya seleccionado. ── */}
      {esEsperarPlazo && (
        <div className="d-flex gap-2 rounded border border-info-subtle bg-info-subtle px-2 py-1"
             style={{ fontSize: '0.72rem' }}>
          <i className="bi bi-info-circle flex-shrink-0 mt-1" />
          <span>{AYUDA_PRODUCIDO_ESPERAR_PLAZO}</span>
        </div>
      )}

      {/* ── Subida inline (#367): sube un fichero nuevo sin salir de la tarea ── */}
      <SubidaInline tareaId={seleccion?.id} />

      {/* ── Zona de staging ── */}
      {docVinculandoPendiente ? (
        <div className="d-flex flex-column gap-1 px-2 py-1 rounded border bg-primary-subtle border-primary-subtle">
          <span className="small text-truncate fw-semibold">{docVinculandoPendiente.nombre}</span>
          <div className="d-flex gap-1">
            <button
              type="button"
              className="btn btn-sm btn-success flex-grow-1"
              disabled={yaConsumido || yaProducido}
              title={
                yaConsumido ? 'Ya está como consumido' :
                yaProducido ? 'No puede ser consumido y producido a la vez' :
                undefined
              }
              onClick={() => vincularDoc('CONSUMIDO')}
            >
              {yaConsumido ? 'Ya consumido' : '+ Consumido'}
            </button>
            <button
              type="button"
              className="btn btn-sm btn-primary flex-grow-1"
              disabled={yaProducido || yaConsumido || deshabilitarProducido}
              title={
                deshabilitarProducido ? 'Se genera automáticamente al fijar el resultado (#442)' :
                yaProducido ? 'Ya está como producido' :
                yaConsumido ? 'No puede ser consumido y producido a la vez' :
                undefined
              }
              onClick={() => vincularDoc('PRODUCIDO')}
            >
              {yaProducido ? 'Ya producido' : '+ Producido'}
            </button>
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary"
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

export default function Despensa({ deshabilitarProducido, esEsperarPlazo }) {
  const seleccion   = useArbolStore((s) => s.seleccion)
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const arbol       = useArbolStore((s) => s.arbol)

  if (!modoEdicion || !seleccion) return null

  // Sellado (#720, ADR-036): ni crear hijos ni vincular documentos tiene sentido con
  // la fase cerrada — el backend lo rechazaría de todos modos (capas 1-3). Incluye la
  // propia fase en edición (mientras esté cerrada no se crean trámites dentro); tras
  // reabrirla el modo edición se cierra y el árbol se refresca, así que al reeditar ya
  // no está sellada y la Despensa vuelve a su comportamiento normal.
  if (estaSellado(arbol, seleccion)) {
    return (
      <div className="p-2 text-muted small fst-italic">
        Fase cerrada: reábrala para poder crear elementos o vincular documentos.
      </div>
    )
  }

  if (seleccion.tipo === 'tarea') {
    return <DespensaDocs deshabilitarProducido={deshabilitarProducido} esEsperarPlazo={esEsperarPlazo} />
  }
  return <DespensaTipos />
}
