// BarrasPorTecnico.jsx — carga por técnico (#579, ADR-028 §2).
//
// Barras apiladas: completados (verde) vs. en trámite (azul) por responsable_id.
// Colores derivados del pase de tematizado JdA (theme.js), coherentes con la tarta.
import React from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer,
} from 'recharts'
import { COLOR_COMPLETADOS, COLOR_EN_TRAMITE } from '../theme.js'

export default function BarrasPorTecnico({ datos }) {
  const filas = (datos || []).map((d) => ({
    tecnico: d.tecnico,
    completados: d.completados,
    en_tramite: d.en_tramite,
  }))

  return (
    <div className="card h-100">
      <div className="card-header bg-transparent fw-semibold">
        <i className="fas fa-chart-column me-2"></i> Carga por técnico
      </div>
      <div className="card-body" style={{ height: 320 }}>
        {filas.length === 0 ? (
          <p className="text-muted text-center pt-5">Sin datos.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={filas} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="tecnico" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="completados" name="Completados" stackId="carga" fill={COLOR_COMPLETADOS()} isAnimationActive={false} />
              <Bar dataKey="en_tramite"  name="En trámite"  stackId="carga" fill={COLOR_EN_TRAMITE()} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
