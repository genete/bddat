// DatosNodo.jsx — La zona de datos de un nodo con diseño (#1043, ADR-053 §C).
//
// Pinta las tarjetas que declara `disenosDatos.js` y es la MISMA zona en lectura y en edición:
// criterio de Carlos (13/10/2026), lo que se ve en lectura no se oculta en edición, y lo que sale
// en edición también se ve en lectura. Lo único que cambia entre modos es el control de los
// datos editables: de solo lectura en lectura, vivo en edición, en el mismo sitio y con el
// mismo rótulo.
//
// El dato sale del payload de `detalle_de_nodo` (`detalle.campos`, {etiqueta, valor}), que no
// cambia; lo editable, de `editableCampos` y `borrador` del store (el ciclo de siempre:
// Guardar / Cancelar del marco). Dos garantías para que no se pierda información en silencio:
// una etiqueta que el payload traiga y el diseño no conozca cae en «Otros datos», y un dato que
// el payload no traiga (el backend omite los vacíos) sale con «—», como en el listado.
//
// `bloqueado` deshabilita los controles vivos (fase cerrada, ADR-036: el backend rechazaría el
// guardado de todos modos).
import React from 'react'
import { useArbolStore } from '../store.js'
import {
  TarjetaDatos, CampoDato, ValorSoloLectura, CasillaSoloLectura, ControlCampo,
} from './TarjetaDatos.jsx'

export default function DatosNodo({ diseno, detalle, nodo, bloqueado = false }) {
  const modoEdicion = useArbolStore((s) => s.modoEdicion)
  const editables   = useArbolStore((s) => s.editableCampos)
  const borrador    = useArbolStore((s) => s.borrador)
  const setCampo    = useArbolStore((s) => s.setCampo)
  const primerVivo  = React.useRef(null)

  // Al entrar en edición el foco va al primer control vivo, como hacía el `Editor`, pero sin
  // mover el scroll: la pantalla no debe saltar al pulsar Editar.
  React.useEffect(() => {
    if (primerVivo.current) primerVivo.current.focus({ preventScroll: true })
  }, [editables])

  const ctx       = { detalle, nodo }
  const lista     = detalle.campos || []
  const valores   = new Map(lista.map((c) => [c.etiqueta, c.valor]))
  const conocidas = new Set(diseno.tarjetas.flatMap((t) => t.campos.map((c) => c.etiqueta)))
  const ocultas   = new Set(diseno.ocultas || [])
  const otros     = lista.filter((c) => !conocidas.has(c.etiqueta) && !ocultas.has(c.etiqueta))
  const vivos     = new Map(modoEdicion ? (editables || []).map((e) => [e.campo, e]) : [])
  let refAsignada = false

  const control = (c, rotulo, valor) => {
    const vivo = c.campo ? vivos.get(c.campo) : null
    if (vivo) {
      const ref = refAsignada ? null : primerVivo
      refAsignada = true
      return (
        <ControlCampo ref={ref} campo={vivo} valor={borrador[vivo.campo] ?? ''} disabled={bloqueado}
                      onChange={(v) => setCampo(vivo.campo, v)} />
      )
    }
    if (c.casilla) {
      // El payload manda «Sí» / «No» (`detalle_nodo._detalle_expediente`).
      return <CasillaSoloLectura rotulo={rotulo} marcada={valor === 'Sí'} />
    }
    const multilinea = c.control === 'textarea'
    return <ValorSoloLectura rotulo={rotulo} multilinea={multilinea}
                             valor={valor || (multilinea ? '' : '—')} />
  }

  return (
    <>
      {diseno.tarjetas.map((t) => (
        <TarjetaDatos key={t.titulo} titulo={t.titulo} icono={t.icono}>
          {t.campos.map((c) => {
            if (c.visibleSi && !c.visibleSi(ctx)) return null
            const valor = c.valorDe ? c.valorDe(ctx) : valores.get(c.etiqueta)
            if (c.opcional && valor === undefined) return null
            const rotulo = c.rotulo || c.etiqueta
            return (
              <CampoDato key={c.etiqueta} rotulo={rotulo} col={c.col}>
                {control(c, rotulo, valor)}
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
