// Cola.jsx — listado transversal de tareas administrativas pendientes (#501, ADR-017 §2).
//
// Usa el chrome de listados de la app (lista-cabecera / lista-scroll-container /
// card.tabla-bloque / lista-table, ADR-022) para que se vea como el resto. Scroll
// infinito por cursor. Click en fila → inspector overlay de LECTURA (Opción A,
// ADR-023 §9): detalle de la tarea en lenguaje del árbol + "Ir a tramitar".
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

  // Carga una página. El bucle salta ventanas que solo traen tareas FIN (data vacía
  // pero has_more): así el scroll nunca se "atasca".
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

  // Recargar al cambiar filtros (debounce para el search).
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
        fragmentUrl: `/tareas_y_subidas/tarea/${fila.tarea_id}/fragmento`,
      })
    }
  }

  return (
    <div className="d-flex flex-column" style={{ flex: 1, minHeight: 0 }}>
      {/* C.1 — filtros + contador (chrome de listados) */}
      <div className="lista-cabecera">
        <div className="filters-row">
          <div className="filters">
            <input type="search" placeholder="Nº AT o titular…" aria-label="Buscar"
                   value={search} onChange={(e) => setSearch(e.target.value)} />
            <select value={tipoExp} onChange={(e) => setTipoExp(e.target.value)} aria-label="Tipo de expediente">
              <option value="">Tipo: todos</option>
              {tiposExpediente.map((te) => <option key={te.id} value={te.id}>{te.tipo}</option>)}
            </select>
            <select value={plazo} onChange={(e) => setPlazo(e.target.value)} aria-label="Plazo">
              {PLAZOS.map((p) => <option key={p.v} value={p.v}>{p.t}</option>)}
            </select>
          </div>
          <div className="pagination-info"><span>{filas.length}</span> tarea(s)</div>
        </div>
      </div>

      {/* C.2 — contenedor scrollable con la tabla unificada */}
      <div className="lista-scroll-container" ref={scrollRef} onScroll={onScroll}>
        <div className="py-3">
          <div className="card tabla-bloque">
            <table className="lista-table cola-table">
              <thead>
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
                    <td title={f.titular}>{f.titular}</td>
                    <td className="text-nowrap">{f.solicitud}</td>
                    <td title={f.fase}>{f.fase}</td>
                    <td title={f.tramite}>{f.tramite}</td>
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
          </div>
        </div>
        {cargando && (
          <div className="text-center text-secondary small py-3">
            <i className="fas fa-spinner fa-spin me-1" /> Cargando…
          </div>
        )}
      </div>
    </div>
  )
}
