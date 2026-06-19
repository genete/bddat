// Command Palette (ADR-018 / #532) — isla React global del shell.
//
// Comportamiento:
//   - Ctrl/Cmd+K → abre/cierra (toggle).
//   - "/"        → abre, salvo que el foco esté en un input/textarea/contenteditable.
//   - Clic en el input del topbar [data-app-shell-search] → abre.
//   - Esc / clic fuera / seleccionar un resultado → cierra.
//
// Búsqueda: con ≥2 caracteres, fetch en paralelo a /api/search/{expedientes,entidades}
// con debounce de 150 ms. Con el input vacío: recientes (sessionStorage) + atajos "IR A".
//
// Los atajos "IR A" NO están hardcodeados: llegan en data-nav, derivados de
// palette_nav() en el backend (misma fuente que el sidebar). Ver react_islas.py.
import { useState, useEffect } from 'react'
import { Command } from 'cmdk'
import { api } from '../shared/api.js'

const RECENTS_KEY = 'bddat.palette.recientes'

// --- sessionStorage: recientes -------------------------------------------------
function leerRecientes() {
  try {
    return JSON.parse(sessionStorage.getItem(RECENTS_KEY)) || []
  } catch {
    return []
  }
}

function guardarReciente(item) {
  // Quita el duplicado previo (mismo tipo+id) y lo recoloca al principio. Tope 10.
  const lista = leerRecientes().filter(
    (r) => !(r.tipo === item.tipo && r.id === item.id),
  )
  lista.unshift({ ...item, timestamp: Date.now() })
  try {
    sessionStorage.setItem(RECENTS_KEY, JSON.stringify(lista.slice(0, 10)))
  } catch {
    /* sessionStorage lleno o no disponible: los recientes son best-effort */
  }
}

// --- data-nav (atajos "IR A", inyectado por palette_nav() en Jinja) -----------
function leerNav() {
  const el = document.querySelector('[data-react-island="command-palette"]')
  if (!el || !el.dataset.nav) return []
  try {
    return JSON.parse(el.dataset.nav)
  } catch {
    return []
  }
}

function iconoTipo(tipo) {
  if (tipo === 'entidad') return 'bi-building'
  if (tipo === 'usuario') return 'bi-person'
  return 'bi-folder2-open'
}

function focoEsEditable() {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [expedientes, setExpedientes] = useState([])
  const [entidades, setEntidades] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [recientes, setRecientes] = useState([])
  const [nav] = useState(leerNav)

  // Atajos globales de teclado + apertura desde el input del topbar.
  useEffect(() => {
    const topbar = document.querySelector('[data-app-shell-search]')

    function onKeydown(e) {
      const ctrl = e.ctrlKey || e.metaKey
      if (ctrl && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault()
        setOpen((o) => !o)
      } else if (e.key === '/' && !open && !focoEsEditable()) {
        e.preventDefault()
        setOpen(true)
      }
    }

    // mousedown + preventDefault: abre sin que el input del topbar robe el foco
    // (el foco va al input del propio palette). Evita además el bucle
    // "devolver foco al cerrar → reabrir" que daría un listener de focus.
    function onTopbarMousedown(e) {
      e.preventDefault()
      setOpen(true)
    }

    document.addEventListener('keydown', onKeydown)
    if (topbar) topbar.addEventListener('mousedown', onTopbarMousedown)
    return () => {
      document.removeEventListener('keydown', onKeydown)
      if (topbar) topbar.removeEventListener('mousedown', onTopbarMousedown)
    }
  }, [open])

  // Al abrir: cargar recientes y soltar cualquier foco del topbar. Al cerrar:
  // limpiar la query. No devolvemos el foco al input del topbar a propósito: es
  // un disparador (readonly), no un campo de escritura, y dejar el cursor ahí
  // resultaba engañoso (parecía editable sin serlo).
  useEffect(() => {
    const topbar = document.querySelector('[data-app-shell-search]')
    if (open) {
      setRecientes(leerRecientes())
      if (topbar) topbar.blur()
    } else {
      setQuery('')
      setExpedientes([])
      setEntidades([])
      setUsuarios([])
    }
  }, [open])

  // Búsqueda con debounce 150 ms. Guarda de "cancelled" para descartar respuestas
  // obsoletas (no usamos AbortController para no propagar AbortError por api.js).
  useEffect(() => {
    const q = query.trim()
    if (q.length < 2) {
      setExpedientes([])
      setEntidades([])
      setUsuarios([])
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    const t = setTimeout(async () => {
      try {
        const [exp, ent, usr] = await Promise.all([
          api.get(`/api/search/expedientes?q=${encodeURIComponent(q)}`),
          api.get(`/api/search/entidades?q=${encodeURIComponent(q)}`),
          api.get(`/api/search/usuarios?q=${encodeURIComponent(q)}`),
        ])
        if (cancelled) return
        setExpedientes(exp.results || [])
        setEntidades(ent.results || [])
        setUsuarios(usr.results || [])
      } catch {
        if (!cancelled) {
          setExpedientes([])
          setEntidades([])
          setUsuarios([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 150)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [query])

  function navegar(item) {
    // Los registros (expediente/entidad/usuario) alimentan recientes; los
    // atajos "IR A" (sin tipo) no.
    if (['expediente', 'entidad', 'usuario'].includes(item.tipo)) {
      guardarReciente({ tipo: item.tipo, id: item.id, label: item.label, url: item.url })
    }
    window.location.href = item.url
  }

  function onCommandKeyDown(e) {
    if (e.key === 'Escape') {
      e.preventDefault()
      setOpen(false)
    }
  }

  if (!open) return null

  const hayQuery = query.trim().length >= 2
  const navFiltrado = hayQuery
    ? nav.filter((n) => n.label.toLowerCase().includes(query.trim().toLowerCase()))
    : nav

  return (
    <div className="cmdp-backdrop" onMouseDown={() => setOpen(false)}>
      <div
        className="cmdp-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Buscador global"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <Command label="Buscador global" shouldFilter={false} onKeyDown={onCommandKeyDown}>
          <div className="cmdp-input-row">
            <i className="bi bi-search cmdp-input-icon" aria-hidden="true"></i>
            <Command.Input
              autoFocus
              value={query}
              onValueChange={setQuery}
              placeholder="Buscar expedientes, entidades…"
            />
            <kbd className="cmdp-kbd">Esc</kbd>
          </div>

          <Command.List className="cmdp-list">
            {loading && <div className="cmdp-status">Buscando…</div>}

            {!hayQuery ? (
              <>
                {recientes.length > 0 && (
                  <Command.Group heading="RECIENTES">
                    {recientes.map((r) => (
                      <Command.Item
                        key={`rec-${r.tipo}-${r.id}`}
                        value={`rec-${r.tipo}-${r.id}`}
                        onSelect={() => navegar(r)}
                      >
                        <i
                          className={`bi ${iconoTipo(r.tipo)} cmdp-item-icon`}
                          aria-hidden="true"
                        ></i>
                        <span className="cmdp-item-label">{r.label}</span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}
                <Command.Group heading="IR A">
                  {nav.map((n) => (
                    <Command.Item
                      key={`nav-${n.url}`}
                      value={`nav-${n.url}`}
                      onSelect={() => navegar(n)}
                    >
                      <i className={`fas ${n.icon} cmdp-item-icon`} aria-hidden="true"></i>
                      <span className="cmdp-item-label">{n.label}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
              </>
            ) : (
              <>
                <Command.Empty className="cmdp-status">
                  Sin resultados para «{query.trim()}»
                </Command.Empty>

                {expedientes.length > 0 && (
                  <Command.Group heading="EXPEDIENTES">
                    {expedientes.map((exp) => (
                      <Command.Item
                        key={`exp-${exp.id}`}
                        value={`exp-${exp.id}`}
                        onSelect={() => navegar(exp)}
                      >
                        <i className="bi bi-folder2-open cmdp-item-icon" aria-hidden="true"></i>
                        <span className="cmdp-item-label">{exp.label}</span>
                        {exp.breadcrumb && (
                          <span className="cmdp-item-breadcrumb">{exp.breadcrumb}</span>
                        )}
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}

                {entidades.length > 0 && (
                  <Command.Group heading="ENTIDADES">
                    {entidades.map((ent) => (
                      <Command.Item
                        key={`ent-${ent.id}`}
                        value={`ent-${ent.id}`}
                        onSelect={() => navegar(ent)}
                      >
                        <i className="bi bi-building cmdp-item-icon" aria-hidden="true"></i>
                        <span className="cmdp-item-label">{ent.label}</span>
                        {ent.breadcrumb && (
                          <span className="cmdp-item-breadcrumb">{ent.breadcrumb}</span>
                        )}
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}

                {usuarios.length > 0 && (
                  <Command.Group heading="USUARIOS">
                    {usuarios.map((u) => (
                      <Command.Item
                        key={`usr-${u.id}`}
                        value={`usr-${u.id}`}
                        onSelect={() => navegar(u)}
                      >
                        <i className="bi bi-person cmdp-item-icon" aria-hidden="true"></i>
                        <span className="cmdp-item-label">{u.label}</span>
                        {u.breadcrumb && (
                          <span className="cmdp-item-breadcrumb">{u.breadcrumb}</span>
                        )}
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}

                {navFiltrado.length > 0 && (
                  <Command.Group heading="IR A">
                    {navFiltrado.map((n) => (
                      <Command.Item
                        key={`nav-${n.url}`}
                        value={`nav-${n.url}`}
                        onSelect={() => navegar(n)}
                      >
                        <i className={`fas ${n.icon} cmdp-item-icon`} aria-hidden="true"></i>
                        <span className="cmdp-item-label">{n.label}</span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                )}
              </>
            )}
          </Command.List>

          <div className="cmdp-footer">
            <span><kbd className="cmdp-kbd">↑</kbd><kbd className="cmdp-kbd">↓</kbd> navegar</span>
            <span><kbd className="cmdp-kbd">⏎</kbd> abrir</span>
            <span><kbd className="cmdp-kbd">Esc</kbd> cerrar</span>
          </div>
        </Command>
      </div>
    </div>
  )
}
