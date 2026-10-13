// TarjetaDatos.jsx — Bloques de datos del inspector del árbol con el aspecto de los
// inspectores Jinja (#1043, ADR-053 §C).
//
// El mismo marcado que `_inspector_expediente.html` y los demás fragmentos: una tarjeta con
// cabecera de acento y cuerpo teñido, y dentro un dato por celda de la rejilla de 12 (rótulo
// + control). Así lectura y edición del árbol se ven como el resto de inspectores.
//
// El control de cada dato lo pone quien usa el bloque: `ValorSoloLectura` y
// `CasillaSoloLectura` para lo que no se edita, y el `input` / `select` / `textarea` vivo
// para lo que sí. El rótulo, el sitio y el orden no cambian entre un modo y otro; solo el
// control (ADR-053 §C: lo que se ve antes de editar es casi lo mismo que al editar).
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

// El control de un dato que no se edita: el `readonly` de los fragmentos Jinja.
export function ValorSoloLectura({ rotulo, valor }) {
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
