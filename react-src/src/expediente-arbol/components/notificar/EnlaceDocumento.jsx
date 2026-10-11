// EnlaceDocumento.jsx — el nombre de un documento como enlace que lo abre (#929, A1).
//
// Mismo reparto que `Documentos` del inspector en lectura: si el documento se consulta en
// un modal (certificados de fase, diagnósticos) lo abre `AppModalLarge` por el atributo
// declarativo; si no, es un enlace en pestaña nueva; sin apertura, solo el nombre. Los
// campos (`enlace`, `puede_abrir`, `abrir_en`) los pone el servidor con
// `info_apertura_documento`, la única que sabe cómo se abre cada documento.
//
// Es una copia más de ese pintado (ADR-053 / PRE-ADR §6.12 ya lo cuenta repetido): la
// sustituirá la fila común del mini-listado de documentos (#1044, D13-D14).
import React from 'react'

export default function EnlaceDocumento({ doc }) {
  if (!doc) return null
  if (doc.puede_abrir && doc.abrir_en === 'modal') {
    return (
      <button type="button" className="btn btn-link p-0 text-start justify-content-start text-truncate"
              data-modal-large-url={doc.enlace} data-modal-large-title={doc.nombre} title={doc.nombre}>
        {doc.nombre}
      </button>
    )
  }
  if (doc.puede_abrir) {
    return <a href={doc.enlace} target="_blank" rel="noreferrer" className="text-truncate" title={doc.nombre}>{doc.nombre}</a>
  }
  return <span className="text-truncate text-muted" title={doc.nombre}>{doc.nombre}</span>
}
