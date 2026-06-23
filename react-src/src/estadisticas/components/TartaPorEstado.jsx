// TartaPorEstado.jsx — tarta de expedientes por estado (#579, ADR-028 §2).
//
// Los 10 estados canónicos del núcleo, cada porción coloreada por su banda de color
// (estado_dominio.COLOR) vía el pase de tematizado JdA (theme.js). El backend ya
// envía estado+color+n en orden de prioridad.
import React from 'react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { colorBanda } from '../theme.js'

// Etiquetas legibles de los códigos de estado canónicos (MODELO §2).
const ETIQUETA_ESTADO = {
  PENDIENTE_TRAMITAR:   'Pendiente tramitar',
  PENDIENTE_ESTUDIO:    'Pendiente estudio',
  PENDIENTE_REDACTAR:   'Pendiente redactar',
  NOTIFICACION_AGOTADA: 'Notificación agotada',
  PENDIENTE_CERRAR:     'Pendiente cerrar',
  NOTIFICACION_FALLIDA: 'Notificación fallida',
  PENDIENTE_FIRMA:      'Pendiente firma',
  PENDIENTE_NOTIFICAR:  'Pendiente notificar',
  PENDIENTE_PLAZOS:     'En plazo',
  FIN:                  'Finalizado',
}

export default function TartaPorEstado({ datos }) {
  const filas = (datos || []).map((d) => ({
    nombre: ETIQUETA_ESTADO[d.estado] || d.estado,
    valor: d.n,
    fill: colorBanda(d.color),
  }))

  return (
    <div className="card h-100">
      <div className="card-header bg-transparent fw-semibold">
        <i className="fas fa-chart-pie me-2"></i> Expedientes por estado
      </div>
      <div className="card-body" style={{ height: 320 }}>
        {filas.length === 0 ? (
          <p className="text-muted text-center pt-5">Sin datos.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={filas}
                dataKey="valor"
                nameKey="nombre"
                cx="50%"
                cy="50%"
                outerRadius="80%"
                label={(e) => e.valor}
                isAnimationActive={false}
              >
                {filas.map((f, i) => <Cell key={i} fill={f.fill} />)}
              </Pie>
              <Tooltip formatter={(v, n) => [`${v} expedientes`, n]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
