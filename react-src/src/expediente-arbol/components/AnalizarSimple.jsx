// AnalizarSimple.jsx — la tarea ANALIZAR de un trámite sin secciones extendidas (#1043, ADR-053 §C,
// ADR-033): CONSULTA_SEPARATA, CONSULTA_TRASLADO_TITULAR…
//
// Su superficie es corta: decidir el resultado y producir el documento de diagnóstico. Por eso usa
// el diseño de datos de la tarea (Notas, plazo y documentos, en `DatosNodo`/`ZonaDatos`) y aporta
// dos piezas del mismo dato, en las dos zonas del cuerpo del inspector (criterio de Carlos,
// 13/10/2026: lo que sale en edición también se ve en lectura):
//   - `TarjetaResultadoDiagnostico`, en la zona de datos, en lectura y en edición: el resultado y
//     los defectos del diagnóstico ya producido, o «Pendiente de producir».
//   - `AccionProducirDiagnostico`, en la zona de acciones, solo en edición y solo mientras no se ha
//     producido: el radio de resultado y el botón irreversible (`NucleoResultado`, el mismo del
//     editor completo, que sigue atendiendo a las tareas de trámites con secciones extendidas).
//
// Comparten el estado en `useDiagnosticoTarea`: la tarjeta lo carga al montarse y la acción lo
// recarga tras producir, sin depender de que el inspector se vuelva a montar. Leen
// `GET …/tarea/<id>/analizar`, el mismo endpoint del editor completo, que solo exige poder ver el
// expediente. Qué trámites son «simples» lo dice el backend en el nodo del árbol
// (`analisis_extendido`, ver `superficiesTarea.js`); este fichero no lo decide.
import React from 'react'
import { create } from 'zustand'
import { useArbolStore } from '../store.js'
import { getAnalizar } from '../api.js'
import { TarjetaDatos, CampoDato, ValorSoloLectura } from './TarjetaDatos.jsx'
import { NucleoResultado, ETIQUETA_RESULTADO } from './AnalizarEditor.jsx'

// `tareaId` dice de qué tarea es `payload`: al cambiar de tarea se descarta, pero al recargar la
// misma (tras producir) se conserva y no parpadea.
export const useDiagnosticoTarea = create((set, get) => ({
  tareaId: null,
  payload: null,
  error: null,

  cargar: async (expedienteId, tareaId) => {
    if (get().tareaId !== tareaId) set({ tareaId, payload: null, error: null })
    try {
      const payload = await getAnalizar(expedienteId, tareaId)
      if (get().tareaId === tareaId) set({ payload, error: null })
    } catch (e) {
      if (get().tareaId === tareaId) {
        set({ error: (e && e.message) || 'No se pudo cargar el diagnóstico' })
      }
    }
  },
}))

// ¿Falta producir el diagnóstico de esta tarea? Lo usa el inspector para saber si pinta la zona de
// acciones propias.
export function useDiagnosticoPendiente(tareaId) {
  return useDiagnosticoTarea(
    (s) => s.tareaId === tareaId && !!s.payload && !s.payload.documento_producido,
  )
}

export function TarjetaResultadoDiagnostico({ expedienteId, tareaId }) {
  const cargar = useDiagnosticoTarea((s) => s.cargar)
  const payload = useDiagnosticoTarea((s) => (s.tareaId === tareaId ? s.payload : null))
  const error = useDiagnosticoTarea((s) => (s.tareaId === tareaId ? s.error : null))

  React.useEffect(() => { cargar(expedienteId, tareaId) }, [cargar, expedienteId, tareaId])

  if (error && !payload) return <div className="text-danger small mb-3">{error}</div>
  if (!payload) return null

  const producido = payload.documento_producido
  const defectos = producido ? (producido.defectos || []) : []
  return (
    <TarjetaDatos titulo="Resultado diagnóstico" icono="fa-clipboard-check">
      <CampoDato rotulo="Resultado">
        <ValorSoloLectura
          rotulo="Resultado"
          valor={producido
            ? (ETIQUETA_RESULTADO[producido.resultado] || producido.resultado)
            : 'Pendiente de producir'} />
      </CampoDato>
      {producido && (
        <>
          <CampoDato rotulo="Defectos">
            <ValorSoloLectura
              rotulo="Defectos" multilinea
              valor={defectos.length ? defectos.map((d) => d.texto).join('\n') : 'Sin defectos.'} />
          </CampoDato>
          <div className="col-12 text-muted small">
            Documento producido — el resultado queda bloqueado.
          </div>
        </>
      )}
    </TarjetaDatos>
  )
}

export function AccionProducirDiagnostico({ expedienteId, tareaId }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const sincronizarProducido = useArbolStore((s) => s.sincronizarProducidoNotificar)
  const cargar = useDiagnosticoTarea((s) => s.cargar)
  const payload = useDiagnosticoTarea((s) => (s.tareaId === tareaId ? s.payload : null))

  // Producido (o aún sin cargar): no hay nada que accionar.
  if (!payload || payload.documento_producido) return null

  // Producir cambia el estado de la tarea, sus documentos y el semáforo: se recarga el
  // diagnóstico (la tarjeta pasa a «producido»), se mete el documento producido en el borrador
  // (la Despensa lo enseña y un Guardar completo posterior no lo desvincula) y se refresca el
  // árbol, que invalida la caché del detalle.
  const alProducir = async () => {
    await cargar(expedienteId, tareaId)
    const producido = useDiagnosticoTarea.getState().payload?.documento_producido
    if (producido) sincronizarProducido(producido.id)
    await refrescarArbol()
  }

  return (
    <NucleoResultado
      expedienteId={expedienteId}
      tareaId={tareaId}
      titulo="Producir diagnóstico"
      completo={payload.completo}
      derivado={false}
      resultadoPrevisto={payload.resultado_previsto}
      onProducido={alProducir}
    />
  )
}
