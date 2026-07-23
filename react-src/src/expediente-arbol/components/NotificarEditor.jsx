// NotificarEditor.jsx — contenedor de la tarea NOTIFICAR (#657/#658, ADR-034).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo NOTIFICAR
// (ver Inspector.jsx). Dos acciones independientes, de persistencia inline propia
// (no pasan por el ciclo borrador/Guardar general):
//   - "Registrar envío" (camino A, opcional): canal + identificador_envio +
//     fecha_puesta_disposicion. Para NOTIFICA admite adjuntar el justificante de
//     puesta a disposición solo para parseo transitorio (nunca se guarda como
//     Documento, ver ADR-034 §1) — autorrellena el formulario, el usuario
//     verifica/corrige antes de confirmar.
//   - "Completar resultado" (camino B manual): resultado + fecha_resultado +
//     numero_intento + observaciones. Requiere que exista fila (creada por
//     "Registrar envío" o por el hook automático al vincular un justificante
//     parseable) — bloqueado con aviso si no hay ninguna todavía.
// La vinculación del documento producido sigue el mecanismo genérico ya
// existente (Despensa/editar_tarea, ver Inspector.jsx) — desacoplada de estos
// dos formularios, igual que ELABORAR: por eso la Despensa NO se deshabilita
// aquí (a diferencia de ANALIZAR) y el par Guardar/Cancelar del pie persiste
// lo que la Despensa apile.
import React from 'react'
import { useArbolStore, selectHayCambios } from '../store.js'
import { getNotificar, postNotificar, patchNotificar, postNotificarParsear } from '../api.js'
import { showToast } from '../../shared/ui/toast.js'

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

function BloqueRegistrarEnvio({ expedienteId, tareaId, notificacion, onGuardado }) {
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
      showToast('Envío registrado', 'success')
      await onGuardado(data.notificacion)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo registrar el envío', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Registrar envío</div>
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
          {enviando ? 'Registrando…' : notificacion ? 'Actualizar envío' : 'Registrar envío'}
        </button>
      </div>
    </div>
  )
}

function BloqueCompletarResultado({ expedienteId, tareaId, notificacion, onGuardado }) {
  const [resultado, setResultado] = React.useState(notificacion?.resultado || '')
  const [fechaResultado, setFechaResultado] = React.useState(notificacion?.fecha_resultado || '')
  const [numeroIntento, setNumeroIntento] = React.useState(notificacion?.numero_intento || 1)
  const [observaciones, setObservaciones] = React.useState(notificacion?.observaciones || '')
  const [enviando, setEnviando] = React.useState(false)

  const guardar = async () => {
    if (!resultado || !fechaResultado) return
    setEnviando(true)
    try {
      const data = await patchNotificar(expedienteId, tareaId, {
        resultado, fecha_resultado: fechaResultado,
        numero_intento: Number(numeroIntento), observaciones: observaciones.trim() || null,
      })
      showToast('Resultado guardado', 'success')
      await onGuardado(data.notificacion)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo guardar el resultado', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Completar resultado</div>
      <div className="card-body card-body-tinted">
        {!notificacion ? (
          <div className="text-muted small fst-italic">
            Registra el envío antes de completar el resultado.
          </div>
        ) : (
          <>
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
                    disabled={!resultado || !fechaResultado || enviando} onClick={guardar}>
              {enviando ? 'Guardando…' : 'Guardar resultado'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default function NotificarEditor({ tareaId }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)
  const cancelar = useArbolStore((s) => s.cancelar)
  const guardar = useArbolStore((s) => s.guardar)
  const guardando = useArbolStore((s) => s.guardando)
  const hayCambios = useArbolStore(selectHayCambios)

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

  return (
    <div>
      <BloqueRegistrarEnvio
        expedienteId={expedienteId} tareaId={tareaId}
        notificacion={payload.notificacion} onGuardado={onGuardado}
      />
      <BloqueCompletarResultado
        expedienteId={expedienteId} tareaId={tareaId}
        notificacion={payload.notificacion} onGuardado={onGuardado}
      />

      {/* Par Guardar/Cancelar del pie (patrón ElaborarEditor): persiste lo que la
          Despensa apile — es el mecanismo genérico que vincula el documento
          producido, desacoplado de los dos bloques de arriba. */}
      <div className="d-flex gap-2 border-top pt-3 mt-3">
        <button type="button" className="btn btn-sm btn-primary"
                disabled={guardando || !hayCambios} onClick={guardar}>
          {guardando ? 'Guardando…' : 'Guardar'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={guardando} onClick={cancelar}>
          Cancelar
        </button>
      </div>
    </div>
  )
}
