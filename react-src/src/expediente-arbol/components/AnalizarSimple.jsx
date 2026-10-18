// AnalizarSimple.jsx — la tarea ANALIZAR de un trámite sin secciones extendidas (#1043, ADR-053 §C,
// ADR-033): CONSULTA_SEPARATA, CONSULTA_TRASLADO_TITULAR…
//
// Su superficie es corta: decidir el resultado y producir el documento de diagnóstico. Por eso usa
// el diseño de datos de la tarea (Notas, plazo y documentos, en `DatosNodo`/`ZonaDatos`) y aporta
// una tarjeta de datos, en lectura y en edición (criterio de Carlos, 13/10/2026: lo que sale en
// edición también se ve en lectura): `TarjetaResultadoDiagnostico`, con el resultado y los defectos
// del diagnóstico ya producido, o «Pendiente de producir». Producirlo es una acción de la zona de
// acciones, solo en edición (`AccionProducirDiagnostico`, en `AnalizarEditor.jsx`, igual que para el
// ANALIZAR extendido, que tiene sus propias tarjetas en `AnalisisExtendido`).
//
// Lee `GET …/tarea/<id>/analizar` a través del estado compartido (`analizarEstado.js`): el mismo
// endpoint del editor extendido, que solo exige poder ver el expediente. Qué trámites son «simples»
// lo dice el backend en el nodo del árbol (`analisis_extendido`, ver `superficiesTarea.js`); este
// fichero no lo decide.
import React from 'react'
import { useAnalisisTarea } from '../analizarEstado.js'
import { TarjetaDatos, CampoDato, ValorSoloLectura } from './TarjetaDatos.jsx'
import { ETIQUETA_RESULTADO } from './AnalizarEditor.jsx'

export function TarjetaResultadoDiagnostico({ expedienteId, tareaId }) {
  const cargar = useAnalisisTarea((s) => s.cargar)
  const payload = useAnalisisTarea((s) => (s.tareaId === tareaId ? s.payload : null))
  const error = useAnalisisTarea((s) => (s.tareaId === tareaId ? s.error : null))

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
