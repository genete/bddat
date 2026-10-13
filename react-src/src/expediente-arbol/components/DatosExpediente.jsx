// DatosExpediente.jsx — La zona de datos del nodo expediente (#1043, fase 1: nodo de ejemplo).
//
// Las mismas tarjetas que el inspector del expediente del listado
// (`_inspector_expediente.html`) y la MISMA zona en lectura y en edición (ADR-053 §C; criterio
// de Carlos, 13/10/2026: en modo edición, con más motivo, la parte informativa se sigue viendo,
// se pueda editar o no). El expediente no tiene ningún campo editable en el árbol —sus datos se
// editan desde el listado—, así que en edición no cambia nada de lo que se ve y lo único que se
// añade es la Despensa de tipos de solicitud (en `InspectorEdicion`).
//
// El dato sale del payload de `detalle_de_nodo` (`detalle.campos`, {etiqueta, valor}), sin
// cambios: aquí solo se reparte en tarjetas. Dos garantías para que no se pierda información
// en silencio: un campo que el payload traiga y este reparto no conozca cae en una tarjeta
// «Otros datos», y uno que el payload no traiga (el backend omite los vacíos) sale con «—»,
// como en el listado.
import React from 'react'
import {
  TarjetaDatos, CampoDato, ValorSoloLectura, CasillaSoloLectura,
} from './TarjetaDatos.jsx'

// Reparto en tarjetas, con los rótulos y el orden del listado. `etiqueta` es la clave del
// payload; `rotulo` solo si se pinta con otro nombre. `col` sobre 12 (por defecto 12).
const TARJETAS = [
  {
    titulo: 'Datos administrativos', icono: 'fa-file-alt',
    campos: [
      { etiqueta: 'Tipo de expediente', col: 8 },
      { etiqueta: 'Heredado', col: 4, casilla: true },
      { etiqueta: 'Responsable' },
      { etiqueta: 'Titular' },
      { etiqueta: 'NIF', col: 6 },
      { etiqueta: 'Nº de solicitudes', col: 6 },
    ],
  },
  {
    titulo: 'Datos del proyecto', icono: 'fa-bolt',
    campos: [
      // El payload lo llama «Proyecto»; dentro de «Datos del proyecto» es el título, como en el listado.
      { etiqueta: 'Proyecto', rotulo: 'Título' },
      { etiqueta: 'Finalidad' },
      { etiqueta: 'Emplazamiento' },
    ],
  },
]

const CONOCIDAS = new Set(TARJETAS.flatMap((t) => t.campos.map((c) => c.etiqueta)))

export default function DatosExpediente({ campos }) {
  const lista = campos || []
  const valores = new Map(lista.map((c) => [c.etiqueta, c.valor]))
  const otros = lista.filter((c) => !CONOCIDAS.has(c.etiqueta))

  return (
    <>
      {TARJETAS.map((t) => (
        <TarjetaDatos key={t.titulo} titulo={t.titulo} icono={t.icono}>
          {t.campos.map((c) => {
            const rotulo = c.rotulo || c.etiqueta
            const valor = valores.get(c.etiqueta)
            return (
              <CampoDato key={c.etiqueta} rotulo={rotulo} col={c.col}>
                {c.casilla
                  // El payload manda «Sí» / «No» (`detalle_nodo._detalle_expediente`).
                  ? <CasillaSoloLectura rotulo={rotulo} marcada={valor === 'Sí'} />
                  : <ValorSoloLectura rotulo={rotulo} valor={valor || '—'} />}
              </CampoDato>
            )
          })}
        </TarjetaDatos>
      ))}
      {otros.length > 0 && (
        <TarjetaDatos titulo="Otros datos" icono="fa-info-circle">
          {otros.map((c) => (
            <CampoDato key={c.etiqueta} rotulo={c.etiqueta}>
              <ValorSoloLectura rotulo={c.etiqueta} valor={c.valor} />
            </CampoDato>
          ))}
        </TarjetaDatos>
      )}
    </>
  )
}
