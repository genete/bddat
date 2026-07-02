// Kpis.jsx — fila de 4 indicadores del panel (#579, ADR-028 §2):
// total · en trámite · plazos vencidos · finalizados.
import React from 'react'

// Cada KPI con su icono FA y la banda de color del borde superior (acento JdA).
const TARJETAS = [
  { clave: 'total',           etiqueta: 'Total expedientes', icono: 'fa-folder-open',        acento: 'border-secondary' },
  { clave: 'en_tramite',      etiqueta: 'En trámite',        icono: 'fa-spinner',            acento: 'border-primary' },
  { clave: 'plazos_vencidos', etiqueta: 'Plazos vencidos',   icono: 'fa-triangle-exclamation', acento: 'border-danger' },
  { clave: 'finalizados',     etiqueta: 'Finalizados',       icono: 'fa-circle-check',       acento: 'border-success' },
]

export default function Kpis({ kpis }) {
  return (
    <div className="row g-3">
      {TARJETAS.map(({ clave, etiqueta, icono, acento }) => (
        <div className="col-6 col-lg-3" key={clave}>
          <div className={`card h-100 border-top border-3 ${acento}`}>
            <div className="card-body">
              <div className="text-muted small text-uppercase mb-1">
                <i className={`fas ${icono} me-1`}></i> {etiqueta}
              </div>
              <div className="fs-2 fw-semibold">{kpis[clave] ?? 0}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
