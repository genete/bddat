// App.jsx — raíz de la isla "estadisticas" del supervisor (#579, ADR-028 §2).
//
// Carga SÍNCRONA con skeleton (ADR-028 §2: nada de streaming/contador en vivo en
// v1). Pide {kpis, por_estado, por_tecnico} a /gestion_y_control/api/estadisticas
// y pinta tres bloques: fila de KPIs, tarta por estado y barras de carga por técnico.
import React, { useEffect, useState } from 'react'
import { api, ApiError } from '../shared/api.js'
import Kpis from './components/Kpis.jsx'
import TartaPorEstado from './components/TartaPorEstado.jsx'
import BarrasPorTecnico from './components/BarrasPorTecnico.jsx'

const ENDPOINT = '/gestion_y_control/api/estadisticas'

export default function App() {
  const [estado, setEstado] = useState('cargando') // cargando | listo | error
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let vivo = true
    api.get(ENDPOINT)
      .then((d) => { if (vivo) { setDatos(d); setEstado('listo') } })
      .catch((e) => {
        if (!vivo) return
        // 401/403 ya muestran toast y (401) redirigen desde api.js.
        setError(e instanceof ApiError ? e.message : 'Error al cargar las estadísticas')
        setEstado('error')
      })
    return () => { vivo = false }
  }, [])

  if (estado === 'cargando') return <Skeleton />
  if (estado === 'error') {
    return (
      <div className="content-constrained py-4">
        <div className="alert alert-danger" role="alert">
          <i className="fas fa-triangle-exclamation me-2"></i>
          No se pudieron cargar las estadísticas. {error}
        </div>
      </div>
    )
  }

  return (
    <div className="content-constrained py-4">
      <Kpis kpis={datos.kpis} />
      <div className="row g-4 mt-1">
        <div className="col-12 col-xl-5">
          <TartaPorEstado datos={datos.por_estado} />
        </div>
        <div className="col-12 col-xl-7">
          <BarrasPorTecnico datos={datos.por_tecnico} />
        </div>
      </div>
    </div>
  )
}

// Skeleton de carga: placeholders Bootstrap mientras llega el agregado síncrono.
function Skeleton() {
  return (
    <div className="content-constrained py-4" aria-busy="true">
      <div className="row g-3">
        {[0, 1, 2, 3].map((i) => (
          <div className="col-6 col-lg-3" key={i}>
            <div className="card h-100">
              <div className="card-body">
                <p className="placeholder-glow mb-2">
                  <span className="placeholder col-7"></span>
                </p>
                <p className="placeholder-glow mb-0">
                  <span className="placeholder col-4" style={{ height: '2rem' }}></span>
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="row g-4 mt-1">
        <div className="col-12 col-xl-5">
          <div className="card"><div className="card-body" style={{ height: 320 }}>
            <span className="placeholder col-12" style={{ height: '100%' }}></span>
          </div></div>
        </div>
        <div className="col-12 col-xl-7">
          <div className="card"><div className="card-body" style={{ height: 320 }}>
            <span className="placeholder col-12" style={{ height: '100%' }}></span>
          </div></div>
        </div>
      </div>
    </div>
  )
}
