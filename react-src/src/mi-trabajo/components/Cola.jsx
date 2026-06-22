// Cola.jsx — listado transversal de tareas administrativas pendientes (#501, ADR-017 §2).
//
// Tabla densa con scroll infinito por cursor. Click en fila → inspector overlay de
// LECTURA del agregado (Opción A, ADR-023 §9): el fragmento es el detalle de la
// tarea en lenguaje del árbol, con "Ir a tramitar". La edición se delega al árbol.
import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../shared/api.js'

const PLAZOS = [
  { v: '',          t: 'Plazo: todos' },
  { v: 'vencido',   t: 'Vencido' },
  { v: 'hoy',       t: 'Hoy' },
  { v: 'semana',    t: 'Esta semana' },
  { v: 'sin_plazo', t: 'Sin plazo' },
]

export default function Cola({ tiposExpediente }) {
  const [filas, setFilas] = useState([])
  const [cursor, setCursor] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [cargando, setCargando] = useState(false)
  const [selId, setSelId] = useState(null)
  const [search, setSearch] = useState('')
  const [tipoExp, setTipoExp] = useState('')
  const [plazo, setPlazo] = useState('')
  const scrollRef = useRef(null)
  const cargandoRef = useRef(false)

  const params = useCallback((cur) => {
    const p = new URLSearchParams({ cursor: cur, limit: 50 })
    if (search) p.set('search', search)
    if (tipoExp) p.set('tipo_expediente_id', tipoExp)
    if (plazo) p.set('plazo', plazo)
    return p
  }, [search, tipoExp, plazo])

  // Carga una página. En reset arranca de cursor 0. El bucle salta ventanas que solo
  // traen tareas FIN (data vacía pero has_more): así el scroll nunca se "atasca".
  const cargar = useCallback(async (reset = false) => {
    if (cargandoRef.current) return
    if (!reset && !hasMore) return
    cargandoRef.current = true
    setCargando(true)
    try {
      let cur = reset ? 0 : cursor
      let primera = reset
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const data = await api.get(`/api/administrativo/cola?${params(cur)}`)
        cur = data.next_cursor
        if (primera) { setFilas(data.data); primera = false }
        else if (data.data.length) setFilas((prev) => [...prev, ...data.data])
        setCursor(data.next_cursor)
        setHasMore(data.has_more)
        if (data.data.length > 0 || !data.has_more) break
      }
    } finally {
      cargandoRef.current = false
      setCargando(false)
    }
  }, [cursor, hasMore, params])

  // Recargar al cambiar filtros (con debounce para el search).
  useEffect(() => {
    const t = setTimeout(() => cargar(true), 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, tipoExp, plazo])

  // Deseleccionar la fila cuando el shell cierra el inspector.
  useEffect(() => {
    const onClosed = () => setSelId(null)
    document.addEventListener('inspector:closed', onClosed)
    return () => document.removeEventListener('inspector:closed', onClosed)
  }, [])

  const onScroll = () => {
    const el = scrollRef.current
    if (!el || cargandoRef.current || !hasMore) return
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 120) cargar(false)
  }

  const abrirFila = (fila) => {
    setSelId(fila.tarea_id)
    if (window.AppInspector) {
      window.AppInspector.open({
        selId: `tarea-${fila.tarea_id}`,
        fragmentUrl: `/mi_trabajo/tarea/${fila.tarea_id}/fragmento`,
      })
    }
  }

  return (
    <div className="d-flex flex-column h-100">
      {/* Filtros */}
      <div className="d-flex flex-wrap align-items-center gap-2 p-2 border-bottom">
        <input
          type="search" className="form-control form-control-sm" style={{ maxWidth: 240 }}
          placeholder="Nº AT o titular…" value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="form-select form-select-sm" style={{ width: 'auto' }}
                value={tipoExp} onChange={(e) => setTipoExp(e.target.value)}>
          <option value="">Tipo: todos</option>
          {tiposExpediente.map((te) => <option key={te.id} value={te.id}>{te.tipo}</option>)}
        </select>
        <select className="form-select form-select-sm" style={{ width: 'auto' }}
                value={plazo} onChange={(e) => setPlazo(e.target.value)}>
          {PLAZOS.map((p) => <option key={p.v} value={p.v}>{p.t}</option>)}
        </select>
        <span className="text-secondary small ms-auto">{filas.length} tarea(s)</span>
      </div>

      {/* Tabla densa con scroll infinito */}
      <div ref={scrollRef} onScroll={onScroll} className="flex-grow-1" style={{ overflowY: 'auto' }}>
        <table className="table table-hover table-sm align-middle small mb-0">
          <thead className="table-light" style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr>
              <th>AT</th><th>Titular</th><th>Solicitud</th><th>Fase</th>
              <th>Trámite</th><th>Tarea</th><th>Pendiente</th><th>Tocado por</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.tarea_id}
                  className={selId === f.tarea_id ? 'table-active' : ''}
                  style={{ cursor: 'pointer' }}
                  onClick={() => abrirFila(f)}>
                <td className="fw-semibold text-nowrap">AT-{f.num_at}</td>
                <td className="text-truncate" style={{ maxWidth: 160 }} title={f.titular}>{f.titular}</td>
                <td className="text-nowrap">{f.solicitud}</td>
                <td className="text-truncate" style={{ maxWidth: 150 }} title={f.fase}>{f.fase}</td>
                <td className="text-truncate" style={{ maxWidth: 170 }} title={f.tramite}>{f.tramite}</td>
                <td className="text-nowrap">{f.tarea}</td>
                <td>
                  {f.pendiente}
                  {f.plazo && f.plazo.fecha_limite && (
                    <span className="badge bg-light text-dark border ms-1">
                      {f.plazo.dias_restantes != null ? `${f.plazo.dias_restantes} d` : f.plazo.estado}
                    </span>
                  )}
                </td>
                <td className="text-secondary">{f.tocado_por || '—'}</td>
              </tr>
            ))}
            {!cargando && filas.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center text-secondary py-4">
                  No hay tareas administrativas pendientes con estos filtros.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        {cargando && (
          <div className="text-center text-secondary small py-3">
            <i className="fas fa-spinner fa-spin me-1" /> Cargando…
          </div>
        )}
      </div>
    </div>
  )
}
