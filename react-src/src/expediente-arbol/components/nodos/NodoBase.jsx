// NodoBase.jsx — caja común de los nodos no-tarea (#500, MODELO §6).
//
// Anatomía: cabecera [icono-tipo · TÍTULO MAYÚS centrado · círculo-semáforo] con raya
// inferior; cuerpo (badge de estado + columna de documentos solo en solicitud, §8). Sin
// rayas verticales. El nivel se distingue por el ICONO de tipo, no por forma ni color.
import React from 'react'
import { Handle, Position } from '@xyflow/react'
import Semaforo from './Semaforo.jsx'
import Docs from './Docs.jsx'

// Icono de tipo por nivel (MODELO §6). El estado lo da el semáforo, no el icono.
const ICONO_TIPO = {
  expediente: 'bi-folder2',
  solicitud:  'bi-file-earmark',
  fase:       'bi-diagram-3',
  tramite:    'bi-clipboard',
}

export default function NodoBase({ data }) {
  const {
    tipo, titulo, tituloCompleto, estado, seleccionado, colapsado,
    agregados, semaforo, docConsumido, docProducido,
  } = data

  // Relleno del círculo (MODELO §7): colapsado → color agregado del subárbol;
  // expandido → solo si el nodo "tiene algo que decir" por sí mismo (propio).
  const relleno = colapsado ? true : !!(semaforo && semaforo.propio)
  const color = semaforo ? semaforo.color : 'gris'
  const tieneDocs = !!docConsumido   // solo la solicitud trae columna de documentos

  return (
    <div className={`arbol-nodo arbol-nodo--${tipo}${seleccionado ? ' is-selected' : ''}`}>
      <Handle type="target" position={Position.Top} className="arbol-handle" />

      <div className="arbol-nodo__cab">
        <i className={`bi ${ICONO_TIPO[tipo] || 'bi-square'} arbol-nodo__icono`} />
        <div className="arbol-nodo__titulo" title={tituloCompleto || titulo}>{titulo || '—'}</div>
        <Semaforo color={color} relleno={relleno} />
      </div>

      <div className="arbol-nodo__cuerpo">
        <div className="arbol-nodo__cuerpo-c">
          {estado && <span className="arbol-nodo__estado">{estado}</span>}
          {colapsado && agregados && (
            <span className="arbol-nodo__badges">
              ⊕ venc {agregados.plazos_vencidos} · próx {agregados.plazos_proximos} · notif{' '}
              {agregados.pendientes_notificar}
            </span>
          )}
        </div>
        {tieneDocs && (
          <Docs consumido={docConsumido} producido={docProducido} className="arbol-docs--col" />
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="arbol-handle" />
    </div>
  )
}
