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

// El control de un dato que no se edita: el `readonly` de los fragmentos Jinja. `multilinea` para
// los textos largos: mismo alto (3 filas) que su control vivo, para que no salte al editar.
export function ValorSoloLectura({ rotulo, valor, multilinea = false }) {
  if (multilinea) {
    return (
      <textarea className="form-control form-control-sm" rows={3} value={valor} readOnly
                aria-label={rotulo} placeholder="—" style={{ resize: 'none' }} />
    )
  }
  return (
    <input type="text" className="form-control form-control-sm"
           value={valor} readOnly aria-label={rotulo} />
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

// El control vivo de un campo del esquema editable (`campo` = {campo, etiqueta, control,
// opciones?}, tal como lo da `esquema_de_nodo`). `onChange` recibe el valor ya del tipo del
// campo: texto, o el `valor` original de la opción elegida (no se fuerza a número: hay selectores
// de texto, como la vía del organismo) o `null` si se elige «—».
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
    return (
      <select ref={ref} className="form-select form-select-sm" value={valor ?? ''}
              aria-label={campo.etiqueta} disabled={disabled}
              onChange={(e) => {
                const o = opciones.find((x) => String(x.valor) === e.target.value)
                onChange(o ? o.valor : null)
              }}>
        <option value="">—</option>
        {opciones.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
      </select>
    )
  }
  return (
    <input ref={ref} type="text" className="form-control form-control-sm" value={valor}
           aria-label={campo.etiqueta} disabled={disabled}
           onChange={(e) => onChange(e.target.value)} />
  )
})
