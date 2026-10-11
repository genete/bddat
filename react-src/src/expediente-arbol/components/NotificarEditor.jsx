// NotificarEditor.jsx — contenedor de la tarea NOTIFICAR (#657/#658/#712, ADR-034;
// rehecho en #929, zona A: tramitarla en el navegador).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo NOTIFICAR
// (ver Inspector.jsx). Solo carga el payload de `GET …/notificar` y reparte; cada cosa
// vive en su componente de `notificar/`:
//   - BloqueDestinatario            a quién se notifica y cómo se elige (A2)
//   - BloqueRegistro                justificante final, resultado, sede, fechas (A1)
//   - BloqueJustificantesPrevios    lo vinculado como consumido, por separado
//
// Los bloques persisten por su cuenta y de inmediato, fuera del par Guardar/Cancelar de
// la cabecera (superficie de trabajo, ADR-023 §5 bis); ese par guarda lo que apila la
// Despensa y el bloque de notas del pie. La Despensa NO se deshabilita aquí (a diferencia
// de ANALIZAR): sigue siendo donde se vinculan los justificantes previos y la vía manual
// del final.
//
// El payload que devuelve cada escritura (PATCH, PUT destinatario) es el mismo de GET:
// los bloques lo pasan a `onPayload` y la pantalla queda como la dice el servidor, sin
// recargar.
import React from 'react'
import { useArbolStore } from '../store.js'
import { getNotificar } from '../api.js'
import BloqueNotas from './BloqueNotas.jsx'
import BloqueDestinatario from './notificar/BloqueDestinatario.jsx'
import BloqueRegistro from './notificar/BloqueRegistro.jsx'
import BloqueJustificantesPrevios from './notificar/BloqueJustificantesPrevios.jsx'

export default function NotificarEditor({ tareaId }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)

  const [payload, setPayload] = React.useState(null)
  const [cargando, setCargando] = React.useState(true)
  const [error, setError] = React.useState(null)

  const cargar = React.useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setPayload(await getNotificar(expedienteId, tareaId))
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

  return (
    <div>
      {payload.es_notificacion_del_solicitante && (
        <div className="alert alert-info py-2 px-3 small">
          <strong>Notificación al solicitante.</strong> Su fecha de cumplimiento es la que cuenta
          para el plazo de resolver del acto.
        </div>
      )}

      <BloqueDestinatario expedienteId={expedienteId} tareaId={tareaId}
                          payload={payload} onPayload={setPayload} />
      <BloqueRegistro key={tareaId} expedienteId={expedienteId} tareaId={tareaId}
                      payload={payload} onPayload={setPayload} />
      <BloqueJustificantesPrevios previos={payload.justificantes_previos} />

      <BloqueNotas />
    </div>
  )
}
