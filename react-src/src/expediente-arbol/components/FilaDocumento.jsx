// FilaDocumento.jsx — renderizador React de la fila común de documento (ADR-053 §E y su anexo, #1044).
//
// Su gemelo en Jinja es el macro `macros/documento_fila.html`: los dos pintan lo mismo, con las mismas
// clases (`.fila-doc*`, en v2-components.css), a partir del mismo dato: la fila que entrega
// `detalle_nodo.documento_fila`. Si cambia uno, cambia el otro.
//
// Dos líneas apiladas, nunca columnas y sin scroll propio. Línea 1: el nombre y, a la derecha, las
// acciones. Línea 2: rol o subrol, fecha dd/mm/aaaa, marcas (iconos con tooltip) y tipo. Lo que no
// cabe se trunca con puntos suspensivos y el valor completo va en el `title`; el asunto no se pinta,
// va en el `title` de la fila. El orden de supervivencia lo fija el CSS: el nombre se trunca el
// primero, después el tipo; el rótulo, la fecha y las marcas conservan su ancho.
//
// Tres modos de interacción (D14):
//   · `vinculados` (por defecto): el nombre es el enlace que abre el documento. Con `onQuitar`
//     (el borrador de una tarea) lleva la ✕ de «Quitar vínculo».
//   · `selector`: la fila entera elige el documento (`onSeleccionar`); el nombre es texto y la
//     acción es abrir. Es el pool de la Despensa.
//   · edición del documento: sin hacer, llega con #881 (el botón «Editar» de las filas).
//
// También exporta la pieza «enlace» (`EnlaceDocumento`): el nombre como lo que abre el documento, para
// los sitios de un solo documento (el anuncio del edicto, el del requisito del checklist).
import React from 'react'
import { fechaLarga } from '../plazoActo.js'

const ROTULO_ROL = { CONSUMIDO: 'Consumido', PRODUCIDO: 'Producido' }
const ROTULO_SUBROL = { A_NOTIFICAR: 'A notificar', JUSTIFICANTE_PREVIO: 'Previo' }
const ICONO_MARCA = {
  PROYECTO: 'bi-flag-fill text-primary',
  REFORMADO: 'bi-layers-fill text-warning',
  PRIORITARIO: 'bi-star-fill text-warning',
}

// El modal grande se abre llamando a `AppModalLarge`, no con el atributo declarativo: en el selector
// la fila corta la propagación del clic y el atributo no llegaría al listener global del shell.
const abrirEnModal = (doc) => window.AppModalLarge && window.AppModalLarge.open(doc.enlace, { title: doc.nombre })

export function EnlaceDocumento({ doc }) {
  if (!doc) return null
  if (doc.puede_abrir && doc.abrir_en === 'modal') {
    return (
      <button type="button" className="fila-doc__nombre fila-doc__enlace" title={doc.nombre}
              onClick={() => abrirEnModal(doc)}>
        {doc.nombre}
      </button>
    )
  }
  if (doc.puede_abrir) {
    return (
      <a href={doc.enlace} target="_blank" rel="noreferrer" className="fila-doc__nombre" title={doc.nombre}>
        {doc.nombre}
      </a>
    )
  }
  return <span className="fila-doc__nombre text-muted" title={doc.nombre}>{doc.nombre}</span>
}

// La acción «abrir» del modo selector: un icono, porque el nombre de la fila ya no es el enlace.
function AbrirDocumento({ doc }) {
  if (!doc.puede_abrir || !doc.enlace) return null
  if (doc.abrir_en === 'modal') {
    return (
      <button type="button" className="btn btn-sm btn-link p-0 text-secondary lh-1" title="Ver documento"
              onClick={(e) => { e.stopPropagation(); abrirEnModal(doc) }}>
        <i className="bi bi-box-arrow-up-right" />
      </button>
    )
  }
  return (
    <a href={doc.enlace} target="_blank" rel="noreferrer" className="btn btn-sm btn-link p-0 text-secondary lh-1"
       title="Abrir documento" onClick={(e) => e.stopPropagation()}>
      <i className="bi bi-box-arrow-up-right" />
    </a>
  )
}

function LineaDos({ doc, rol }) {
  // En el selector el rol lo pone quien llama (el que dice el borrador); en una lista, el de la fila.
  const rolFila = rol ?? doc.rol
  const subrol = rol ? undefined : doc.subrol
  const rotulo = ROTULO_SUBROL[subrol] || ROTULO_ROL[rolFila] || rolFila
  return (
    <div className="fila-doc__l2 small text-muted">
      {rolFila && (
        <span className={`badge ${rolFila === 'PRODUCIDO' ? 'text-bg-primary' : 'text-bg-success'}`}>{rotulo}</span>
      )}
      <span>{doc.fecha ? fechaLarga(doc.fecha) : 'sin fecha'}</span>
      {(doc.marcas || []).map((m) => (
        <i key={m.codigo} className={`bi ${ICONO_MARCA[m.codigo] || 'bi-tag-fill'}`} role="img"
           title={m.texto} aria-label={m.texto} />
      ))}
      {doc.tipo_doc && <span className="fila-doc__tipo" title={doc.tipo_doc}>· {doc.tipo_doc}</span>}
    </div>
  )
}

export default function FilaDocumento({
  doc, rol, modo = 'vinculados', seleccionada = false, onSeleccionar, onQuitar,
}) {
  if (!doc) return null

  if (modo === 'selector') {
    const elegir = () => onSeleccionar && onSeleccionar(doc)
    return (
      <div className={`fila-doc fila-doc--selector${seleccionada ? ' fila-doc--seleccionada' : ''}`}
           role="button" tabIndex={0} aria-pressed={seleccionada} title={doc.asunto || undefined}
           onClick={elegir}
           onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); elegir() } }}>
        <div className="fila-doc__l1">
          <i className="bi bi-file-earmark flex-shrink-0" />
          <span className="fila-doc__nombre fw-semibold" title={doc.nombre}>{doc.nombre}</span>
          <span className="fila-doc__acciones"><AbrirDocumento doc={doc} /></span>
        </div>
        <LineaDos doc={doc} rol={rol} />
      </div>
    )
  }

  return (
    <div className="fila-doc" title={doc.asunto || undefined}>
      <div className="fila-doc__l1">
        <i className="bi bi-file-earmark flex-shrink-0" />
        <EnlaceDocumento doc={doc} />
        {onQuitar && (
          <span className="fila-doc__acciones">
            <button type="button" className="btn btn-sm btn-link text-danger p-0 lh-1" title="Quitar vínculo"
                    aria-label={`Quitar vínculo con ${doc.nombre}`} onClick={onQuitar}>
              ✕
            </button>
          </span>
        )}
      </div>
      <LineaDos doc={doc} rol={rol} />
    </div>
  )
}
