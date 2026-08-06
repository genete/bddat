// ElaborarEditor.jsx — contenedor de la tarea ELABORAR (#608).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo ELABORAR
// (ver Inspector.jsx). Engancha el backend de generación de escritos (#167,
// app/routes/api_escritos.py) ya existente y completo, huérfano de UI desde que
// el sistema Jinja "BC" que lo alojaba se eliminó en #500.
//
// Alcance acordado (#608): el .docx generado es un auxiliar de trabajo, no un
// documento de expediente — se genera, se registra en el pool (asignar_doc_
// producido:false, ver api.js) y se vincula como CONSUMIDO de inmediato
// (onGenerado, más abajo) para que la tarea deje rastro de que ya existe un
// borrador en curso — sin esto, volver a editar la tarea mostraba otra vez el
// formulario vacío, como si no se hubiera hecho nada. Vincularlo como
// CONSUMIDO (nunca PRODUCIDO) es inocuo para el semáforo: MODELO_ESTADOS_
// SEMAFORO.md §3 ELABORAR solo mira si hay un consumido de tipo BORRADOR_FIRMA
// (un PDF), no la mera presencia de otros consumidos — sigue en PENDIENTE_
// REDACTAR. El resto del ciclo (PDF corregido con tipo BORRADOR_FIRMA como
// consumido → PENDIENTE_FIRMA; PDF firmado como producido → FIN) ya funciona
// con el mecanismo genérico de la Despensa (+Consumido/+Producido) y con el
// alta de documentos vía explorador de servidor — no se toca aquí. Por eso la
// Despensa NO se deshabilita para ELABORAR (a diferencia de ANALIZAR): sigue
// siendo el único punto donde se vinculan el borrador de firma y el documento
// firmado.
//
// El par Guardar/Cancelar que persiste lo que la Despensa apila vive en la
// cabecera fija (BarraEdicion, #688), no en el pie de este contenedor.
import React from 'react'
import { useArbolStore } from '../store.js'
import { getEscritosPlantillas, getEscritosPreview, postEscritosGenerar, postEscritosGenerarConfirmar } from '../api.js'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'
import BloqueNotas from './BloqueNotas.jsx'

// Casos de la matriz de regeneración (#730) que dejan un documento realmente
// nuevo o sustituido — se muestran en el panel persistente. 3 (no-op) y 4
// (renombrado puro) solo merecen un toast, no hay nada sustancial que revisar.
const CASOS_CON_PANEL = new Set([1, 6, 7, 8])

function _mensajeCaso(data) {
  if (data.caso === 3) return 'Sin cambios respecto al documento actual: no se ha generado nada nuevo.'
  if (data.caso === 4 || data.caso === 5) return `Sin cambios en el contenido — renombrado a "${data.nombre_fichero}".`
  return `Escrito generado: ${data.nombre_fichero}`
}

// Aviso de sustitución (casos 6/7/8, #730): el borrador anterior se desconecta
// de bddat, no pasa por pool/ (nunca perteneció al expediente, #608) — queda
// recuperable por su código de seguimiento embebido en el pie de página.
const AVISO_SUSTITUCION = 'Ya existe un borrador generado antes para esta tarea. Si continúas, el ' +
  'fichero anterior se desconectará de bddat: quedará en la misma carpeta con la fecha del propio ' +
  'fichero añadida al nombre — recuperable por su código de seguimiento si hace falta revisarlo.'

// Card de decisión revelada cuando /generar devuelve requiere_confirmacion
// (#730) — mismo patrón visual que BloqueoForzar (TiposCreablesCompartido.jsx):
// aviso en línea dentro del panel, no un modal aparte.
function ConfirmarRegeneracion({ caso, colisionNombre, confirmando, onDecidir }) {
  const conColision = colisionNombre != null
  const conSustitucion = caso === 6 || caso === 7 || caso === 8
  return (
    <div className="d-flex flex-column gap-1 px-2 py-2 rounded border bg-warning-subtle border-warning-subtle mb-2">
      {/* text-warning-emphasis, no text-muted (#730): mismo motivo que el panel de
          éxito — el gris genérico no da contraste suficiente sobre el fondo coloreado. */}
      {conSustitucion && <span className="small text-warning-emphasis">{AVISO_SUSTITUCION}</span>}
      {conColision && (
        <span className="small text-warning-emphasis">
          Ya existe un fichero llamado <strong>{colisionNombre}</strong> en la carpeta destino que no
          pertenece a bddat.
        </span>
      )}
      <div className="d-flex gap-2 flex-wrap">
        {conColision ? (
          <>
            <button type="button" className="btn btn-sm btn-warning" disabled={confirmando}
                    onClick={() => onDecidir('renombrar_nuevo')}>
              Renombrar el nuevo
            </button>
            <button type="button" className="btn btn-sm btn-warning" disabled={confirmando}
                    onClick={() => onDecidir('renombrar_existente')}>
              Renombrar el existente
            </button>
          </>
        ) : (
          <button type="button" className="btn btn-sm btn-warning" disabled={confirmando}
                  onClick={() => onDecidir('continuar')}>
            {confirmando ? '…' : 'Continuar'}
          </button>
        )}
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={confirmando}
                onClick={() => onDecidir('cancelar')}>
          Cancelar
        </button>
      </div>
    </div>
  )
}

// Abre el Explorador de Windows enfocando el fichero, ejecutado en el SERVIDOR
// (subprocess.Popen, requiere Flask en el mismo PC — despliegue local). Mismo
// endpoint que el icono "abrir carpeta" del bloque Documentos en modo lectura
// (Inspector.jsx). uri_explorador (file://) NO sirve: el navegador bloquea
// window.open a file:// desde una página http.
function abrirEnCarpeta(expedienteId, docId) {
  api.post(`/expedientes/${expedienteId}/documentos/${docId}/abrir-en-carpeta`)
    .catch((e) => showToast((e && e.message) || 'No se pudo abrir la carpeta', 'danger'))
}

// Campos de contexto a mostrar en el preview (mismo subconjunto que el modal legacy).
const CAMPOS_PREVIEW = [
  ['numero_at', 'N.º AT'],
  ['titular_nombre', 'Titular'],
  ['titular_nif', 'NIF titular'],
  ['proyecto_titulo', 'Proyecto'],
  ['responsable_nombre', 'Responsable'],
  ['fecha_hoy', 'Fecha'],
]

function PreviewCampos({ campos }) {
  return (
    <div className="row g-1 small mb-3">
      {CAMPOS_PREVIEW.map(([clave, etiqueta]) => (
        <div className="col-6" key={clave}>
          <span className="fw-semibold">{etiqueta}:</span> {campos[clave] || '—'}
        </div>
      ))}
    </div>
  )
}

// Núcleo: generar un escrito desde plantilla. Vive siempre en el Inspector de
// edición de una tarea ELABORAR no ejecutada — no hay lista, es una acción
// única por tarea (una tarea produce a lo sumo un documento).
function GenerarEscrito({ tareaId, expedienteId, onGenerado }) {
  const [plantillas, setPlantillas] = React.useState([])
  const [cargandoPlantillas, setCargandoPlantillas] = React.useState(true)
  const [plantillaId, setPlantillaId] = React.useState('')
  const [preview, setPreview] = React.useState(null)
  const [cargandoPreview, setCargandoPreview] = React.useState(false)
  const [nombreFichero, setNombreFichero] = React.useState('')
  const [abrirCarpeta, setAbrirCarpeta] = React.useState(false)
  const [generando, setGenerando] = React.useState(false)
  const [resultado, setResultado] = React.useState(null)
  // Caso de la matriz #730 que requiere decisión del usuario antes de escribir
  // nada — null cuando no hay ninguna decisión pendiente.
  const [confirmacionPendiente, setConfirmacionPendiente] = React.useState(null)
  const [confirmando, setConfirmando] = React.useState(false)

  React.useEffect(() => {
    let cancelado = false
    setCargandoPlantillas(true)
    getEscritosPlantillas(tareaId)
      .then((data) => { if (!cancelado) setPlantillas(data.plantillas || []) })
      .catch((e) => showToast((e && e.message) || 'No se pudieron cargar las plantillas', 'danger'))
      .finally(() => { if (!cancelado) setCargandoPlantillas(false) })
    return () => { cancelado = true }
  }, [tareaId])

  const seleccionarPlantilla = (id) => {
    setPlantillaId(id)
    setPreview(null)
    setResultado(null)
    setConfirmacionPendiente(null)
    if (!id) return
    setCargandoPreview(true)
    getEscritosPreview(id, tareaId)
      .then((data) => {
        setPreview(data)
        setNombreFichero(data.nombre_propuesto || '')
      })
      .catch((e) => showToast((e && e.message) || 'No se pudo cargar el preview', 'danger'))
      .finally(() => setCargandoPreview(false))
  }

  // Común a la ejecución directa (casos 1/3/4, sin decisión que pedir) y a la
  // confirmación (tras resolver el popup, #730).
  const _aplicarResultado = async (data) => {
    if (CASOS_CON_PANEL.has(data.caso)) setResultado(data)
    showToast(_mensajeCaso(data), data.caso === 3 ? 'info' : 'success')
    await onGenerado(data.doc_id)
    // Abrir después de onGenerado (#729): mover_a_esftt ya ha reubicado el
    // fichero para cuando el Explorador resuelve la ruta — antes había una
    // carrera con el fichero todavía en AT-N/.
    if (abrirCarpeta && data.doc_id) abrirEnCarpeta(expedienteId, data.doc_id)
  }

  const generar = async () => {
    if (!plantillaId) return
    setGenerando(true)
    setConfirmacionPendiente(null)
    try {
      const data = await postEscritosGenerar(plantillaId, tareaId, nombreFichero.trim())
      if (data.requiere_confirmacion) {
        setConfirmacionPendiente({ caso: data.caso, colisionNombre: data.colision_nombre })
        return
      }
      await _aplicarResultado(data)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo generar el escrito', 'danger')
    } finally {
      setGenerando(false)
    }
  }

  const confirmar = async (decision) => {
    setConfirmando(true)
    try {
      const data = await postEscritosGenerarConfirmar(plantillaId, tareaId, nombreFichero.trim(), decision)
      setConfirmacionPendiente(null)
      if (data.cancelado) {
        showToast('Regeneración cancelada', 'info')
        return
      }
      await _aplicarResultado(data)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo confirmar la regeneración', 'danger')
    } finally {
      setConfirmando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Generar escrito</div>
      <div className="card-body card-body-tinted">
        {cargandoPlantillas ? (
          <div className="text-muted small fst-italic">Cargando plantillas…</div>
        ) : plantillas.length === 0 ? (
          <div className="text-muted small fst-italic">No hay plantillas aplicables a esta tarea.</div>
        ) : (
          <>
            <div className="mb-2">
              <label className="form-label small text-muted mb-1">Plantilla</label>
              <select
                className="form-select form-select-sm"
                value={plantillaId}
                disabled={generando}
                onChange={(e) => seleccionarPlantilla(e.target.value)}
              >
                <option value="">— Seleccione una plantilla —</option>
                {plantillas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}{p.variante ? ` — ${p.variante}` : ''} ({p.especificidad}/4)
                  </option>
                ))}
              </select>
            </div>

            {cargandoPreview && <div className="text-muted small fst-italic mb-2">Cargando preview…</div>}

            {preview && !cargandoPreview && (
              <>
                <PreviewCampos campos={preview.campos || {}} />
                <div className="mb-2">
                  <label className="form-label small text-muted mb-1">Nombre de fichero</label>
                  <input
                    type="text"
                    className="form-control form-control-sm"
                    value={nombreFichero}
                    disabled={generando}
                    onChange={(e) => setNombreFichero(e.target.value)}
                  />
                </div>
                <div className="form-check mb-3">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="ge-abrir-carpeta"
                    checked={abrirCarpeta}
                    disabled={generando}
                    onChange={(e) => setAbrirCarpeta(e.target.checked)}
                  />
                  <label className="form-check-label small" htmlFor="ge-abrir-carpeta">
                    Abrir carpeta al generar
                  </label>
                </div>
                {confirmacionPendiente ? (
                  <ConfirmarRegeneracion
                    caso={confirmacionPendiente.caso}
                    colisionNombre={confirmacionPendiente.colisionNombre}
                    confirmando={confirmando}
                    onDecidir={confirmar}
                  />
                ) : (
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    disabled={generando || !nombreFichero.trim()}
                    onClick={generar}
                  >
                    {generando ? 'Generando…' : 'Generar'}
                  </button>
                )}
              </>
            )}

            {resultado && (
              <div className="alert alert-success py-2 px-3 small mt-3 mb-0">
                <div className="fw-semibold">Generado y vinculado como consumido</div>
                <div className="text-truncate">{resultado.ruta}</div>
                {/* text-success-emphasis, no text-muted (#730): el gris genérico de
                    Bootstrap pisa el verde oscuro que ya trae alert-success y queda
                    ilegible sobre el fondo verde claro. */}
                <div className="text-success-emphasis mt-1">
                  No cambia el estado de la tarea (sigue pendiente de redactar).
                  Revísalo, corrígelo y, cuando esté listo para firma, sube el PDF con
                  tipo «Borrador para firma» y vincúlalo también desde la despensa.
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function ElaborarEditor({ tareaId, nodo }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)

  const ejecutada = !!(nodo && nodo.doc_producido && nodo.doc_producido.presente)

  // Vincula el .docx recién generado como CONSUMIDO y persiste de inmediato —
  // reutiliza el mismo circuito que la Despensa (borrador.documentos_consumidos_ids
  // + guardar → PATCH editar_tarea), sin tocar el backend de escritos. Seguro para
  // el semáforo: estado_dominio.ELABORAR solo mira si hay un consumido de tipo
  // BORRADOR_FIRMA, no la mera presencia de otros consumidos — sigue en
  // PENDIENTE_REDACTAR. getState() en vez del hook: se llama dentro de un async
  // tras el POST, y el valor cerrado por el hook podría haber quedado stale.
  const onGenerado = async (docId) => {
    const actuales = useArbolStore.getState().borrador.documentos_consumidos_ids || []
    if (actuales.includes(docId)) return
    useArbolStore.getState().setCampo('documentos_consumidos_ids', [...actuales, docId])
    await useArbolStore.getState().guardar()
  }

  return (
    <div>
      {ejecutada ? (
        <div className="card mb-3">
          <div className="card-header card-header-accent fw-semibold small">Generar escrito</div>
          <div className="card-body card-body-tinted">
            <div className="text-muted small">
              Tarea ejecutada — el documento producido (PDF firmado) está en el
              bloque «Documentos» del modo lectura.
            </div>
          </div>
        </div>
      ) : (
        <GenerarEscrito tareaId={tareaId} expedienteId={expedienteId} onGenerado={onGenerado} />
      )}

      <BloqueNotas />
    </div>
  )
}
