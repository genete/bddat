// BloqueRegistro.jsx — registro de la notificación (#929, A1; ADR-049 §B-§D, ADR-052).
//
// Escribe con `PATCH …/notificar`, que devuelve el payload nuevo, de modo que lo que
// ve la pantalla tras guardar es lo que dice el servidor. Persiste por su cuenta, fuera
// del ciclo Guardar/Cancelar de la cabecera (superficie de trabajo, ADR-023 §5 bis).
//
// Qué se registra y qué no (cada cosa por una razón de ADR-049):
//   - NO hay fechas que escribir: la de cumplimiento y la de efectos salen de la
//     `fecha_administrativa` de los justificantes (§G) y aquí se muestran, con el
//     documento que las origina. Tampoco número de intento: sale de cuántos
//     justificantes postales fallidos hay vinculados (ADR-052 §C) y es de solo lectura.
//   - El canal tampoco se elige: lo fija el primer justificante (`canal_de_vinculos`).
//     Por eso los resultados posibles (`resultados_validos`) solo se conocen cuando
//     hay canal o se ha elegido el justificante final.
//   - Solo se vincula aquí el justificante FINAL (el PATCH no admite otro); los previos
//     —postales fallidos, puesta a disposición, sede— se vinculan como consumidos desde
//     la Despensa (decisión 1 de #929, resuelta en «no»: sin atajo por tipo).
//   - El resultado lo decide el usuario; el parseo solo lo propone (`resultado_sugerido`).
//
// El cuerpo del PATCH lleva solo lo que ha cambiado (ausente conserva; `null` vacía,
// REGLAS_DESARROLLO «Rutas que editan un registro existente»).
import React from 'react'
import { useArbolStore } from '../../store.js'
import { patchNotificar, postNotificarParsearDocumento } from '../../api.js'
import { showToast } from '../../../shared/ui/toast.js'
import { BloqueoForzar } from '../TiposCreablesCompartido.jsx'
import EnlaceDocumento from './EnlaceDocumento.jsx'

const ETIQUETA_CANAL = {
  NOTIFICA: 'Notifica-PNT',
  BANDEJA: 'BandeJA',
  SIR: 'SIR / ARIES',
  POSTAL: 'Postal',
  EDICTO: 'Edicto (anuncio publicado)',
}

const ETIQUETA_RESULTADO = {
  CORRECTA: 'Correcta',
  RECHAZADA: 'Rechazada (se tiene por efectuada)',
  INCORRECTA: 'Incorrecta (no llegó a practicarse)',
}

const ESTADO_SEDE = {
  PUESTA: ['success', 'Puesta a disposición en sede: consta el justificante de sede.'],
  JUSTIFICADA: ['secondary', 'No se pone en sede, y está justificado.'],
  PENDIENTE: ['warning', 'Pendiente: falta el justificante de sede o justificar por qué no se '
                          + 'pone a disposición en sede (art. 42.1 LPACAP).'],
}

// Los tipos que admite el desplegable: los justificantes FINALES, los únicos que el PATCH
// acepta como producido. Espejo de `JUSTIFICANTES_FINALES` en `services/notificaciones.py`:
// si falta uno aquí no se puede elegir; si sobra, el servidor lo rechaza con un 422.
const TIPOS_FINALES = [
  'JUSTIFICANTE_NOTIFICA', 'JUSTIFICANTE_POSTAL', 'JUSTIFICANTE_BANDEJA', 'JUSTIFICANTE_SIR',
  'ANUNCIO_PUBLICADO', 'JUSTIFICANTE_EDICTO',
]

const MAX_IDENTIFICADOR = 30

const fechaIso = (iso) => (iso ? iso.split('-').reverse().join('/') : '')

function textoAdvertencia(a) {
  return typeof a === 'string' ? a : (a && (a.motivo || a.mensaje)) || 'Revisa la advertencia'
}

// Los valores del formulario a partir de lo que dice el servidor.
function valoresDe(payload) {
  const notif = payload.notificaciones[0] || {}
  const producido = payload.documento_producido
  return {
    resultado: notif.resultado || '',
    identificador: notif.identificador_envio || '',
    observaciones: notif.observaciones || '',
    sedeJustificacion: notif.sede_justificacion || '',
    documentoId: producido ? producido.id : '',
    opciones: payload.resultados_validos || [],
  }
}

function FilaFecha({ rotulo, ayuda, fecha }) {
  return (
    <div className="mb-1">
      <span className="text-muted">{rotulo}: </span>
      {fecha ? (
        <>
          <span className="fw-semibold">{fechaIso(fecha.fecha)}</span>
          <span className="text-muted"> · </span>
          <EnlaceDocumento doc={fecha.documento} />
        </>
      ) : (
        <span className="text-muted fst-italic">{ayuda}</span>
      )}
    </div>
  )
}

export default function BloqueRegistro({ expedienteId, tareaId, payload, onPayload }) {
  const pool = useArbolStore((s) => s.pool)
  const poolCargando = useArbolStore((s) => s.poolCargando)
  const cargarPool = useArbolStore((s) => s.cargarPool)
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const sincronizarProducidoNotificar = useArbolStore((s) => s.sincronizarProducidoNotificar)

  const notif = payload.notificaciones[0] || null
  const producido = payload.documento_producido
  const sede = payload.sede

  const [form, setForm] = React.useState(() => valoresDe(payload))
  const [previsualizando, setPrevisualizando] = React.useState(false)
  const [notaPreview, setNotaPreview] = React.useState(null)
  const [confirmandoSustitucion, setConfirmandoSustitucion] = React.useState(false)
  const [enviando, setEnviando] = React.useState(false)
  const [error, setError] = React.useState(null)
  const [advertencia, setAdvertencia] = React.useState(null)
  const [bloqueo, setBloqueo] = React.useState(null)
  const [justificacion, setJustificacion] = React.useState('')

  React.useEffect(() => { cargarPool() }, [cargarPool])

  const poner = (campo) => (valor) => setForm((f) => ({ ...f, [campo]: valor }))

  const documentosFinales = React.useMemo(
    () => pool.filter((d) => TIPOS_FINALES.includes(d.tipo_doc_codigo)),
    [pool],
  )

  if (!notif) {
    return (
      <div className="alert alert-danger small">La tarea no tiene ficha de notificación.</div>
    )
  }

  const documentoNuevo = form.documentoId !== '' && form.documentoId !== (producido ? producido.id : '')
  const hayJustificante = !!notif.canal || documentoNuevo
  const sustituye = documentoNuevo && !!producido

  // Solo lo que ha cambiado: lo ausente se conserva, y vaciar un campo es mandar null.
  const cuerpo = {}
  if (form.resultado !== (notif.resultado || '')) cuerpo.resultado = form.resultado || null
  if (form.identificador.trim() !== (notif.identificador_envio || '')) {
    cuerpo.identificador_envio = form.identificador.trim() || null
  }
  if (form.observaciones.trim() !== (notif.observaciones || '')) {
    cuerpo.observaciones = form.observaciones.trim() || null
  }
  if (sede.aplica && form.sedeJustificacion.trim() !== (notif.sede_justificacion || '')) {
    cuerpo.sede_justificacion = form.sedeJustificacion.trim() || null
  }
  if (documentoNuevo) cuerpo.documento_id = form.documentoId
  const hayCambios = Object.keys(cuerpo).length > 0

  // Acto 1 del flujo de dos actos (#712): elegir el documento solo previsualiza —no se
  // vincula ni se guarda nada— y propone el resultado; el usuario lo revisa y Guardar
  // persiste lo ya revisado, nunca un re-parseo automático.
  const seleccionarDocumento = async (e) => {
    const valor = e.target.value
    const nuevoId = valor ? Number(valor) : ''
    setForm((f) => ({ ...f, documentoId: nuevoId }))
    setNotaPreview(null)
    setError(null)
    if (!nuevoId || nuevoId === (producido ? producido.id : '')) {
      setForm((f) => ({ ...f, opciones: payload.resultados_validos || [] }))
      return
    }
    setPrevisualizando(true)
    try {
      const data = await postNotificarParsearDocumento(expedienteId, tareaId, nuevoId)
      const opciones = data.resultados_validos || []
      setForm((f) => ({
        ...f,
        opciones,
        resultado: data.resultado_sugerido && opciones.includes(data.resultado_sugerido)
          ? data.resultado_sugerido
          : (opciones.includes(f.resultado) ? f.resultado : ''),
      }))
      setNotaPreview(data.resultado_sugerido
        ? { tipo: 'success',
            texto: `Resultado propuesto: ${ETIQUETA_RESULTADO[data.resultado_sugerido] || data.resultado_sugerido}. `
                   + 'Compruébalo antes de guardar.' }
        : { tipo: 'warning', texto: 'Sin propuesta de resultado: indícalo a mano.' })
    } catch (e2) {
      if (e2.status === 401 || e2.status === 403) return
      setError((e2.payload && e2.payload.error) || e2.message || 'No se pudo previsualizar el documento')
    } finally {
      setPrevisualizando(false)
    }
  }

  const guardarReal = async (extra) => {
    setEnviando(true)
    setConfirmandoSustitucion(false)
    setError(null)
    setAdvertencia(null)
    setBloqueo(null)
    try {
      const data = await patchNotificar(expedienteId, tareaId, { ...cuerpo, ...extra })
      showToast('Notificación registrada', 'success')
      if (data.advertencia) setAdvertencia(textoAdvertencia(data.advertencia))
      // El PATCH vincula el producido por una vía ajena al borrador de la Despensa:
      // se resincroniza para que no muestre el vínculo anterior (#712).
      if (cuerpo.documento_id) sincronizarProducidoNotificar(cuerpo.documento_id)
      setForm(valoresDe(data))
      setNotaPreview(null)
      setJustificacion('')
      onPayload(data)
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      const p = e.payload || {}
      if (e.status === 422 && p.puede_escapar === true) {
        // Bloqueo forzable (típicamente, vincular sin destinatario): se queda en
        // pantalla para ofrecer el escape con justificación, como el resto del árbol.
        setBloqueo({ motivo: p.motivo || p.error || 'Operación bloqueada', url_norma: p.url_norma || '',
                     puede_escapar: true })
      } else {
        const detalle = p.motivo && p.error && p.error !== 'Bloqueado por el motor'
          ? `${p.error}. ${p.motivo}` : (p.motivo || e.message)
        setError(detalle || 'No se pudo guardar la notificación')
      }
    } finally {
      setEnviando(false)
    }
  }

  const guardar = () => {
    // Sustituir un producido ya vinculado por otro devuelve el anterior al pool: se
    // confirma antes (#712).
    if (sustituye) { setConfirmandoSustitucion(true); return }
    guardarReal()
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Registro de la notificación</div>
      <div className="card-body card-body-tinted">
        <div className="small mb-2">
          <span className="text-muted">Canal: </span>
          {notif.canal
            ? <span className="fw-semibold">{ETIQUETA_CANAL[notif.canal] || notif.canal}</span>
            : <span className="text-muted fst-italic">sin fijar (lo fija el primer justificante)</span>}
          <span className="text-muted ms-3">Intentos postales fallidos: </span>
          <span className="fw-semibold">{notif.intentos_fallidos}</span>
          <span className="text-muted"> de 2</span>
        </div>

        {!hayJustificante && (
          <div className="alert alert-info py-2 px-3 small">
            Aún no hay ningún justificante vinculado. Vincula el que corresponda desde la Despensa
            (los previos, como consumidos) o elige abajo el justificante final.
          </div>
        )}

        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Justificante final</label>
          <select className="form-select form-select-sm" value={form.documentoId}
                  disabled={poolCargando || previsualizando || enviando} onChange={seleccionarDocumento}>
            {!producido && <option value="">— Selecciona documento —</option>}
            {documentosFinales.map((d) => (
              <option key={d.id} value={d.id}>
                {d.nombre}{d.tipo_doc ? ` — ${d.tipo_doc}` : ''}{d.fecha ? ` · ${d.fecha}` : ''}
              </option>
            ))}
          </select>
          {previsualizando && <div className="text-muted small mt-1">Previsualizando…</div>}
          {notaPreview && (
            <div className={`small mt-1 text-${notaPreview.tipo === 'success' ? 'success' : 'warning-emphasis'}`}>
              {notaPreview.texto}
            </div>
          )}
        </div>

        {confirmandoSustitucion && (
          <div className="alert alert-warning py-2 px-3 mb-2 small">
            <div className="mb-2">
              Vas a sustituir el documento producido actual («{producido && producido.nombre}») por el
              seleccionado. El anterior volverá al pool.
            </div>
            <div className="d-flex gap-1">
              <button type="button" className="btn btn-sm btn-warning" onClick={() => guardarReal()}>
                Sustituir y guardar
              </button>
              <button type="button" className="btn btn-sm btn-outline-secondary"
                      onClick={() => setConfirmandoSustitucion(false)}>
                Cancelar
              </button>
            </div>
          </div>
        )}

        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Resultado</label>
          <select className="form-select form-select-sm" value={form.resultado}
                  disabled={enviando || form.opciones.length === 0}
                  onChange={(e) => poner('resultado')(e.target.value)}>
            <option value="">— Sin resultado —</option>
            {form.opciones.map((cod) => (
              <option key={cod} value={cod}>{ETIQUETA_RESULTADO[cod] || cod}</option>
            ))}
          </select>
          {form.opciones.length === 0 && (
            <div className="small text-muted mt-1">
              Los resultados posibles dependen del canal: aparecerán al vincular un justificante.
            </div>
          )}
        </div>

        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Identificador de envío</label>
          <input type="text" className="form-control form-control-sm" value={form.identificador}
                 maxLength={MAX_IDENTIFICADOR} disabled={enviando}
                 onChange={(e) => poner('identificador')(e.target.value)} />
          <div className="small text-muted text-end">{form.identificador.length}/{MAX_IDENTIFICADOR}</div>
        </div>

        {sede.aplica && (
          <div className="mb-2">
            <div className="text-muted small fw-semibold mb-1">Sede electrónica (art. 42.1 LPACAP)</div>
            {sede.estado && ESTADO_SEDE[sede.estado] && (
              <div className={`alert alert-${ESTADO_SEDE[sede.estado][0]} py-1 px-2 small mb-1`}>
                {ESTADO_SEDE[sede.estado][1]}
              </div>
            )}
            {sede.estado !== 'PUESTA' && (
              <>
                <label className="form-label small text-muted mb-1">Justificación de no poner en sede</label>
                <textarea className="form-control form-control-sm" rows={2} value={form.sedeJustificacion}
                          disabled={enviando}
                          onChange={(e) => poner('sedeJustificacion')(e.target.value)} />
              </>
            )}
          </div>
        )}

        <div className="mb-3">
          <label className="form-label small text-muted mb-1">Observaciones</label>
          <textarea className="form-control form-control-sm" rows={2} value={form.observaciones}
                    disabled={enviando} onChange={(e) => poner('observaciones')(e.target.value)} />
        </div>

        <div className="small border-top pt-2 mb-3">
          <FilaFecha rotulo="Cumplimiento del deber de notificar" fecha={payload.fechas.cumplimiento}
                     ayuda="sin justificante con fecha" />
          <FilaFecha rotulo="Efectos frente al interesado" fecha={payload.fechas.efectos}
                     ayuda="aún no hay justificante final con resultado Correcta o Rechazada" />
          <div className="text-muted">
            Las fechas salen de los justificantes: para corregirlas, corrige la fecha del documento.
          </div>
        </div>

        {bloqueo && (
          <div className="mb-2">
            <BloqueoForzar
              bloqueo={bloqueo}
              titulo="Este registro necesita justificación"
              textoAccion="Registrar igualmente"
              placeholder="Motivo por el que se registra igualmente (queda en bitácora)"
              justificacion={justificacion}
              setJustificacion={setJustificacion}
              creando={enviando}
              onForzar={() => guardarReal({ bypass: true, justificacion: justificacion.trim() })}
              onCancelar={() => setBloqueo(null)}
            />
            {payload.destinatario.bloquea && (
              <div className="small text-muted mt-1">
                Registrarlo sin destinatario es irreversible: la tarea queda sin destinatario para siempre.
              </div>
            )}
          </div>
        )}

        {error && <div className="alert alert-danger py-2 px-3 small mb-2">{error}</div>}
        {advertencia && <div className="alert alert-warning py-2 px-3 small mb-2">{advertencia}</div>}

        <button type="button" className="btn btn-sm btn-primary"
                disabled={enviando || confirmandoSustitucion || !hayCambios || !hayJustificante}
                onClick={guardar}>
          {enviando ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </div>
  )
}
