// NotificarEditor.jsx — contenedor de la tarea NOTIFICAR (#657/#658/#712, ADR-034).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo NOTIFICAR
// (ver Inspector.jsx). Dos bloques independientes, de persistencia inline propia
// (no pasan por el ciclo borrador/Guardar general):
//   - "Registrar puesta a disposición" (camino A, opcional): canal + identificador_envio
//     + fecha_puesta_disposicion. Para NOTIFICA admite adjuntar el justificante de
//     puesta a disposición solo para parseo transitorio (nunca se guarda como
//     Documento, ver ADR-034 §1) — autorrellena el formulario, el usuario
//     verifica/corrige antes de confirmar.
//   - "Registrar notificación" (camino B): resultado + fecha_resultado +
//     numero_intento + observaciones, MÁS (#712) un desplegable con los
//     documentos JUSTIFICANTE_* del pool para vincular el definitivo como
//     Producido en el mismo acto. Flujo de dos actos deliberado (ver ADR del
//     issue #712): seleccionar del desplegable solo dispara un preview
//     (parseo sin persistir) que autorrellena resultado/fecha_resultado —
//     el usuario revisa/corrige y Guardar persiste esos valores ya revisados,
//     nunca un re-parseo automático en el instante de guardar. Requiere que
//     exista fila de Notificacion (creada por "Registrar puesta a disposición"
//     o, si el documento elegido es un NOTIFICA parseable, por el hook
//     automático al vincularlo) — 422 con aviso si no hay ninguna todavía.
// La vinculación del documento producido por el desplegable reutiliza el mismo
// mecanismo de movimiento físico que la Despensa (editar_tarea/mover_a_esftt,
// backend) — la Despensa sigue siendo la vía manual de respaldo y NO se
// deshabilita aquí (a diferencia de ANALIZAR), en paralelo al desplegable
// nuevo (issue #712). Lo que la Despensa apila por su cuenta lo persiste el
// par Guardar/Cancelar de la cabecera fija (BarraEdicion, #688), que es
// también el que guarda el bloque Notas del pie.
import React from 'react'
import { useArbolStore } from '../store.js'
import {
  getNotificar, postNotificar, patchNotificar, postNotificarParsear, postNotificarParsearDocumento,
} from '../api.js'
import { showToast } from '../../shared/ui/toast.js'
import BloqueNotas from './BloqueNotas.jsx'

const CANALES = [
  ['NOTIFICA', 'Notifica-PNT'],
  ['BANDEJA', 'BandeJA'],
  ['SIR', 'SIR / ARIES'],
  ['POSTAL', 'Postal'],
]

const RESULTADOS = [
  ['CORRECTA', 'Correcta'],
  ['INCORRECTA', 'Incorrecta'],
]

// Tipos de documento admitidos en el desplegable de "Registrar notificación"
// (#712) — mismo mapeo canal↔tipo que el backend (MAPA_CANAL_POR_TIPO_DOC).
const TIPOS_JUSTIFICANTE = ['JUSTIFICANTE_NOTIFICA', 'JUSTIFICANTE_BANDEJA', 'JUSTIFICANTE_SIR', 'JUSTIFICANTE_POSTAL']

function BloqueRegistrarPuestaDisposicion({ expedienteId, tareaId, notificacion, onGuardado }) {
  const [canal, setCanal] = React.useState(notificacion?.canal || '')
  const [identificadorEnvio, setIdentificadorEnvio] = React.useState(notificacion?.identificador_envio || '')
  const [fechaPuesta, setFechaPuesta] = React.useState(notificacion?.fecha_puesta_disposicion || '')
  const [parseando, setParseando] = React.useState(false)
  const [notaParseo, setNotaParseo] = React.useState(null)
  const [enviando, setEnviando] = React.useState(false)

  const adjuntar = async (e) => {
    const fichero = e.target.files && e.target.files[0]
    e.target.value = ''
    if (!fichero) return
    setParseando(true)
    setNotaParseo(null)
    try {
      const data = await postNotificarParsear(expedienteId, tareaId, fichero)
      if (data.reconocido) {
        setCanal('NOTIFICA')
        if (data.id_remesa) setIdentificadorEnvio(data.id_remesa)
        if (data.fecha_puesta_disposicion) setFechaPuesta(data.fecha_puesta_disposicion.slice(0, 10))
        setNotaParseo({ tipo: 'success', texto: 'Justificante reconocido — verifica los datos antes de confirmar.' })
      } else {
        setNotaParseo({ tipo: 'warning', texto: 'No se reconoció como justificante Notifica-PNT — rellena a mano.' })
      }
    } catch (e2) {
      showToast((e2 && e2.message) || 'No se pudo parsear el fichero', 'danger')
    } finally {
      setParseando(false)
    }
  }

  const registrar = async () => {
    if (!canal || !fechaPuesta) return
    setEnviando(true)
    try {
      const data = await postNotificar(expedienteId, tareaId, {
        canal, identificador_envio: identificadorEnvio.trim() || null,
        fecha_puesta_disposicion: fechaPuesta,
      })
      showToast('Puesta a disposición registrada', 'success')
      await onGuardado(data.notificacion)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo registrar la puesta a disposición', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Registrar puesta a disposición</div>
      <div className="card-body card-body-tinted">
        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Canal</label>
          <select className="form-select form-select-sm" value={canal} disabled={enviando}
                  onChange={(e) => setCanal(e.target.value)}>
            <option value="">— Selecciona canal —</option>
            {CANALES.map(([cod, etiqueta]) => <option key={cod} value={cod}>{etiqueta}</option>)}
          </select>
        </div>

        {canal === 'NOTIFICA' && (
          <div className="mb-2">
            <label className="form-label small text-muted mb-1">
              Justificante de puesta a disposición (opcional — solo para autorrellenar, no se guarda)
            </label>
            <input type="file" accept=".pdf,.zip" className="form-control form-control-sm"
                   disabled={parseando || enviando} onChange={adjuntar} />
            {parseando && <div className="text-muted small mt-1">Parseando…</div>}
            {notaParseo && (
              <div className={`small mt-1 text-${notaParseo.tipo === 'success' ? 'success' : 'warning-emphasis'}`}>
                {notaParseo.texto}
              </div>
            )}
          </div>
        )}

        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Identificador de envío (remesa)</label>
          <input type="text" className="form-control form-control-sm" value={identificadorEnvio}
                 disabled={enviando} onChange={(e) => setIdentificadorEnvio(e.target.value)} />
        </div>

        <div className="mb-3">
          <label className="form-label small text-muted mb-1">Fecha de puesta a disposición</label>
          <input type="date" className="form-control form-control-sm" value={fechaPuesta}
                 disabled={enviando} onChange={(e) => setFechaPuesta(e.target.value)} />
        </div>

        <button type="button" className="btn btn-sm btn-primary" disabled={!canal || !fechaPuesta || enviando}
                onClick={registrar}>
          {enviando ? 'Registrando…' : notificacion ? 'Actualizar puesta a disposición' : 'Registrar puesta a disposición'}
        </button>
      </div>
    </div>
  )
}

function BloqueRegistrarNotificacion({
  expedienteId, tareaId, notificacion, documentoProducido, onGuardado, onDocumentoVinculado,
}) {
  const pool         = useArbolStore((s) => s.pool)
  const poolCargando = useArbolStore((s) => s.poolCargando)
  const cargarPool    = useArbolStore((s) => s.cargarPool)

  const [resultado, setResultado] = React.useState(notificacion?.resultado || '')
  const [fechaResultado, setFechaResultado] = React.useState(notificacion?.fecha_resultado || '')
  const [numeroIntento, setNumeroIntento] = React.useState(notificacion?.numero_intento || 1)
  const [observaciones, setObservaciones] = React.useState(notificacion?.observaciones || '')
  const [documentoId, setDocumentoId] = React.useState(notificacion?.documento_id || documentoProducido?.id || '')
  const [previsualizando, setPrevisualizando] = React.useState(false)
  const [notaPreview, setNotaPreview] = React.useState(null)
  const [confirmandoSustitucion, setConfirmandoSustitucion] = React.useState(false)
  const [enviando, setEnviando] = React.useState(false)

  React.useEffect(() => { cargarPool() }, [cargarPool])

  // #712: solo los 4 tipos JUSTIFICANTE_* — mismo criterio que el backend
  // (MAPA_CANAL_POR_TIPO_DOC).
  const documentosJustificante = React.useMemo(
    () => pool.filter((d) => TIPOS_JUSTIFICANTE.includes(d.tipo_doc_codigo)),
    [pool],
  )

  // Acto 1: seleccionar del desplegable dispara solo un preview (sin persistir
  // nada, sin vincular todavía) — autorrellena resultado/fecha_resultado si el
  // documento es un NOTIFICA reconocible; el resto de canales no tiene parser
  // (ADR-034), el usuario rellena a mano.
  const seleccionarDocumento = async (e) => {
    const valor = e.target.value
    const nuevoId = valor ? Number(valor) : ''
    setDocumentoId(nuevoId)
    setNotaPreview(null)
    if (!nuevoId) return
    setPrevisualizando(true)
    try {
      const data = await postNotificarParsearDocumento(expedienteId, tareaId, nuevoId)
      if (data.reconocido) {
        setResultado(data.resultado || '')
        if (data.fecha_lectura) setFechaResultado(data.fecha_lectura.slice(0, 10))
        setNotaPreview({ tipo: 'success', texto: 'Justificante reconocido — verifica los datos antes de guardar.' })
      } else {
        setNotaPreview({ tipo: 'warning', texto: 'No se pudo autorrellenar — revisa/completa los datos a mano.' })
      }
    } catch (e2) {
      showToast((e2 && e2.message) || 'No se pudo previsualizar el documento', 'danger')
    } finally {
      setPrevisualizando(false)
    }
  }

  // Acto 3: Guardar persiste resultado/fecha_resultado/numero_intento/observaciones
  // con los valores ya revisados (nunca un re-parseo automático) y, si hay
  // documento seleccionado, lo vincula como Producido en el mismo acto.
  const guardarReal = async () => {
    setEnviando(true)
    setConfirmandoSustitucion(false)
    try {
      const body = {
        resultado, fecha_resultado: fechaResultado,
        numero_intento: Number(numeroIntento), observaciones: observaciones.trim() || null,
      }
      if (documentoId) body.documento_id = documentoId
      const data = await patchNotificar(expedienteId, tareaId, body)
      showToast('Notificación registrada', 'success')
      if (data.advertencia) showToast(data.advertencia.motivo, 'warning')
      if (documentoId) {
        await onDocumentoVinculado(data.notificacion, documentoId)
      } else {
        await onGuardado(data.notificacion)
      }
    } catch (e) {
      showToast((e && e.message) || 'No se pudo guardar la notificación', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  const guardar = () => {
    if (!resultado || !fechaResultado) return
    // Confirmación inline de descarte (#712): solo si el guardado sustituye un
    // Producido YA vinculado por otro documento distinto del seleccionado.
    if (documentoId && documentoProducido && documentoProducido.id !== documentoId) {
      setConfirmandoSustitucion(true)
      return
    }
    guardarReal()
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Registrar notificación</div>
      <div className="card-body card-body-tinted">
        {!notificacion && (
          <div className="text-muted small fst-italic mb-2">
            Sin puesta a disposición registrada todavía — selecciona un justificante
            Notifica-PNT reconocible o completa antes "Registrar puesta a disposición".
          </div>
        )}

        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Documento justificante (opcional)</label>
          <select className="form-select form-select-sm" value={documentoId}
                  disabled={poolCargando || previsualizando || enviando} onChange={seleccionarDocumento}>
            <option value="">— Selecciona documento —</option>
            {documentosJustificante.map((d) => (
              <option key={d.id} value={d.id}>{d.nombre}</option>
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
              Vas a sustituir el documento producido actual («{documentoProducido?.nombre}»)
              por el seleccionado. El anterior volverá al pool.
            </div>
            <div className="d-flex gap-1">
              <button type="button" className="btn btn-sm btn-warning" onClick={guardarReal}>
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
          <select className="form-select form-select-sm" value={resultado} disabled={enviando}
                  onChange={(e) => setResultado(e.target.value)}>
            <option value="">— Selecciona resultado —</option>
            {RESULTADOS.map(([cod, etiqueta]) => <option key={cod} value={cod}>{etiqueta}</option>)}
          </select>
        </div>
        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Fecha del resultado</label>
          <input type="date" className="form-control form-control-sm" value={fechaResultado}
                 disabled={enviando} onChange={(e) => setFechaResultado(e.target.value)} />
        </div>
        <div className="mb-2">
          <label className="form-label small text-muted mb-1">Número de intento</label>
          <select className="form-select form-select-sm" value={numeroIntento} disabled={enviando}
                  onChange={(e) => setNumeroIntento(e.target.value)}>
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </div>
        <div className="mb-3">
          <label className="form-label small text-muted mb-1">Observaciones</label>
          <textarea className="form-control form-control-sm" rows={2} value={observaciones}
                    disabled={enviando} onChange={(e) => setObservaciones(e.target.value)} />
        </div>
        <button type="button" className="btn btn-sm btn-primary"
                disabled={!resultado || !fechaResultado || enviando || confirmandoSustitucion} onClick={guardar}>
          {enviando ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </div>
  )
}

export default function NotificarEditor({ tareaId }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)
  const sincronizarProducidoNotificar = useArbolStore((s) => s.sincronizarProducidoNotificar)

  const [payload, setPayload] = React.useState(null)
  const [cargando, setCargando] = React.useState(true)
  const [error, setError] = React.useState(null)

  const cargar = React.useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const data = await getNotificar(expedienteId, tareaId)
      setPayload(data)
    } catch (e) {
      setError(e)
    } finally {
      setCargando(false)
    }
  }, [expedienteId, tareaId])

  React.useEffect(() => {
    setPayload(null)
    cargar()
  }, [cargar])

  if (cargando && !payload) return <div className="text-muted small">Cargando…</div>
  if (error) {
    return <div className="text-danger small">No se pudo cargar: {String((error && error.message) || error)}</div>
  }
  if (!payload) return null

  const onGuardado = async (notificacion) => {
    setPayload((p) => ({ ...p, notificacion }))
  }

  // #712: el desplegable de "Registrar notificación" vincula el Producido por
  // su cuenta (PATCH .../notificar), fuera del ciclo Guardar/Cancelar general
  // — hay que resincronizar el borrador (Despensa) y refrescar el propio
  // payload (documento_producido, para la próxima comparación de sustitución).
  const onDocumentoVinculado = async (notificacion, documentoId) => {
    sincronizarProducidoNotificar(documentoId)
    await cargar()
  }

  return (
    <div>
      <BloqueRegistrarPuestaDisposicion
        expedienteId={expedienteId} tareaId={tareaId}
        notificacion={payload.notificacion} onGuardado={onGuardado}
      />
      <BloqueRegistrarNotificacion
        expedienteId={expedienteId} tareaId={tareaId}
        notificacion={payload.notificacion} documentoProducido={payload.documento_producido}
        onGuardado={onGuardado} onDocumentoVinculado={onDocumentoVinculado}
      />

      <BloqueNotas />
    </div>
  )
}
