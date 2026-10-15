// BloqueNotas.jsx — campo directo `notas` de la tarea dentro de un contenedor
// bespoke (#688).
//
// Los contenedores de superficie-de-trabajo (ANALIZAR/ELABORAR/NOTIFICAR)
// sustituyen al diseño de tarea genérica, que es quien pinta las Notas (superficiesTarea.js).
// Sin este bloque, `notas` —único campo directo de una tarea— quedaría
// sin superficie donde escribirse: es lo que ocurría en ELABORAR y NOTIFICAR,
// donde el campo era simplemente inaccesible desde el árbol.
//
// No lleva Guardar propio a propósito: escribe en `borrador.notas` del store y
// lo persiste el par Guardar/Cancelar de la barra del marco (shell), igual
// que en cualquier otro nodo. Lo que cada contenedor persiste por su cuenta y de
// inmediato (checks, shuttle, registrar envío…) es otro asunto y no pasa por
// aquí.
import React from 'react'
import { useArbolStore } from '../store.js'

export default function BloqueNotas() {
  const borrador = useArbolStore((s) => s.borrador)
  const setCampo = useArbolStore((s) => s.setCampo)

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Notas</div>
      <div className="card-body card-body-tinted">
        <textarea
          className="form-control form-control-sm"
          rows={3}
          value={borrador.notas ?? ''}
          onChange={(e) => setCampo('notas', e.target.value)}
        />
      </div>
    </div>
  )
}
