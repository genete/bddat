// TarjetaDatos.jsx — Bloques de datos del inspector del árbol con el aspecto de los
// inspectores Jinja (#1043, ADR-053 §C).
//
// El mismo marcado que `_inspector_expediente.html` y los demás fragmentos: una tarjeta con
// cabecera de acento y cuerpo teñido, y dentro un dato por celda de la rejilla de 12 (rótulo
// + control). Así lectura y edición del árbol se ven como el resto de inspectores.
//
// El control de cada dato lo pone quien usa el bloque: `ValorSoloLectura` y
// `CasillaSoloLectura` para lo que no se edita, y `ControlCampo` (el control vivo) para lo
// que sí. El rótulo, el sitio y el orden no cambian entre un modo y otro; solo el control
// (ADR-053 §C: lo que se ve antes de editar es casi lo mismo que al editar).
import React from 'react'

// `icono` es una clase de Font Awesome sin el prefijo (`fa-file-alt`), como en los fragmentos Jinja.
export function TarjetaDatos({ titulo, icono, children }) {
  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold">
        {icono && <i className={`fas ${icono} me-1`} />}{titulo}
      </div>
      <div className="card-body card-body-tinted">
        <div className="row g-2">{children}</div>
      </div>
    </div>
  )
}

// Un dato: rótulo y control. `col` es el ancho sobre 12 columnas (8 + 4, 6 + 6, 12).
export function CampoDato({ rotulo, col = 12, children }) {
  return (
    <div className={`col-${col}`}>
      <label className="form-label fw-semibold small">{rotulo}</label>
      {children}
    </div>
  )
}

// El «!» junto a un dato cuyo valor guardado ya no vale (#1038): el motivo va en el tooltip. Es el mismo
// aviso en lectura y en edición. Va superpuesto en el borde derecho del propio control (`derecha` es su
// distancia al borde, para dejar libre la flecha de un select) y no en un `input-group`: el tema pinta
// cada combinación de `input-group` con un alto y una letra distintos (28 px y 12 px el campo suelto;
// 31 o 40 px y 14 o 15 px dentro del grupo) y el campo dejaría de alinear con sus vecinos. Así el
// control conserva su geometría con o sin «!», y no hay salto de diseño al aparecer o quitarse.
const SOLAPE_MARCA = { select: '2rem', input: '.5rem' }
function MarcaAviso({ aviso, derecha }) {
  return (
    <span className="position-absolute top-50 translate-middle-y text-warning lh-1" style={{ right: derecha, cursor: 'help' }}
          role="img" aria-label={aviso} title={aviso}>
      <i className="fas fa-exclamation-circle" />
    </span>
  )
}

// El control de un dato que no se edita: el `readonly` de los fragmentos Jinja. `multilinea` para
// los textos largos: mismo alto (3 filas) que su control vivo, para que no salte al editar. `aviso`
// (solo en una línea) marca un valor guardado que ya no vale, con su motivo (#1038).
export function ValorSoloLectura({ rotulo, valor, multilinea = false, aviso = null }) {
  if (multilinea) {
    return (
      <textarea className="form-control form-control-sm" rows={3} value={valor} readOnly
                aria-label={rotulo} placeholder="—" style={{ resize: 'none' }} />
    )
  }
  if (!aviso) {
    return (
      <input type="text" className="form-control form-control-sm"
             value={valor} readOnly aria-label={rotulo} />
    )
  }
  return (
    <div className="position-relative">
      <input type="text" className="form-control form-control-sm" style={{ paddingRight: '1.75rem' }}
             value={valor} readOnly aria-label={rotulo} />
      <MarcaAviso aviso={aviso} derecha={SOLAPE_MARCA.input} />
    </div>
  )
}

// Casilla que no se edita («Heredado»): el recuadro con icono de `_inspector_expediente.html`.
export function CasillaSoloLectura({ rotulo, marcada }) {
  return (
    <div className="form-control form-control-sm d-flex align-items-center"
         style={{ background: '#fff', pointerEvents: 'none' }}
         role="img" aria-label={`${rotulo}: ${marcada ? 'Sí' : 'No'}`}>
      {marcada
        ? <><i className="fas fa-check-square text-warning me-1" /> Sí</>
        : <><i className="fas fa-square text-secondary me-1" /> No</>}
    </div>
  )
}

// Valor interno del `<select>` cuando el guardado no es ninguna de sus opciones (ver `ControlCampo`).
const VALOR_FUERA_DE_OPCIONES = '__fuera_de_opciones__'
const AVISO_FUERA_DE_OPCIONES =
  'El valor guardado ya no es una de las opciones posibles. Elija otra o deje el campo vacío.'

// El control vivo de un campo del esquema editable (`campo` = {campo, etiqueta, control,
// opciones?, texto_vacio?, aviso?}, tal como lo da `esquema_de_nodo`). `onChange` recibe el valor ya
// del tipo del campo: texto, o el `valor` original de la opción elegida (no se fuerza a número: hay
// selectores de texto, como la vía del organismo) o `null` si se elige la opción vacía.
//
// Contrato del select (GUIA_COMPONENTES_INTERACTIVOS «Contrato de un selector», #1038):
//  - La opción vacía dice qué implica no elegir (`texto_vacio`), y «—» si el esquema no lo dice.
//  - Si el valor guardado no está entre las opciones (autorización revocada, sede de baja, un
//    valor inyectado), el select se ve vacío y junto a él sale un «!» con el motivo (`aviso`, o uno
//    genérico): lo dice el esquema porque solo el servidor sabe por qué. El «!» desaparece en cuanto
//    el usuario cambia el select, a otra opción o a la vacía.
//  - Volver a elegir «nada» tiene que poder cambiar algo: un `<select>` nativo no dispara `change`
//    al elegir lo que ya se ve elegido. Mientras el guardado esté fuera de las opciones, el elegido
//    por dentro es una opción oculta con el mismo texto que la vacía.
export const ControlCampo = React.forwardRef(function ControlCampo(
  { campo, valor, onChange, disabled = false }, ref,
) {
  if (campo.control === 'textarea') {
    return (
      <textarea ref={ref} className="form-control form-control-sm" rows={3} value={valor}
                aria-label={campo.etiqueta} disabled={disabled}
                onChange={(e) => onChange(e.target.value)} />
    )
  }
  if (campo.control === 'select') {
    const opciones = campo.opciones || []
    const vacio = campo.texto_vacio || '—'
    const fuera = valor != null && valor !== '' && !opciones.some((o) => String(o.valor) === String(valor))
    // El envoltorio es siempre el mismo: si el select cambiara de padre al aparecer o quitarse
    // el «!», React lo remontaría y se perdería el foco justo al elegir.
    return (
      <div className="position-relative">
        <select ref={ref} className="form-select form-select-sm"
                style={fuera ? { paddingRight: '3.25rem' } : undefined}
                value={fuera ? VALOR_FUERA_DE_OPCIONES : (valor ?? '')}
                aria-label={campo.etiqueta} disabled={disabled}
                onChange={(e) => {
                  const o = opciones.find((x) => String(x.valor) === e.target.value)
                  onChange(o ? o.valor : null)
                }}>
          {fuera && <option value={VALOR_FUERA_DE_OPCIONES} hidden>{vacio}</option>}
          <option value="">{vacio}</option>
          {opciones.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
        </select>
        {fuera && <MarcaAviso aviso={campo.aviso || AVISO_FUERA_DE_OPCIONES} derecha={SOLAPE_MARCA.select} />}
      </div>
    )
  }
  return (
    <input ref={ref} type="text" className="form-control form-control-sm" value={valor}
           aria-label={campo.etiqueta} disabled={disabled}
           onChange={(e) => onChange(e.target.value)} />
  )
})
