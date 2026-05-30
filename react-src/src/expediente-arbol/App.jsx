// App.jsx — raíz de la isla del árbol (#500, ADR-016).
//
// Lee data-expediente-id del contenedor, carga el árbol y compone Viewbar + Arbol.
// Sincroniza la selección con la URL (?nodo=tipo-id, ADR §12) vía history.replaceState.
// El Inspector real es S3 (aquí solo Viewbar + Arbol).
import React, { useEffect } from 'react'
import { useArbolStore } from './store.js'
import Viewbar from './components/Viewbar.jsx'
import Arbol from './components/Arbol.jsx'

function expedienteIdDesdeDOM() {
  const el = document.querySelector('[data-react-island="expediente-arbol"]')
  const raw = el && el.getAttribute('data-expediente-id')
  return raw ? Number(raw) : null
}

// --- Sincronización selección ↔ URL (ADR §12) ---------------------------------

function leerSeleccionURL() {
  const p = new URLSearchParams(window.location.search).get('nodo')
  if (!p) return null
  const i = p.lastIndexOf('-')            // tipo puede no tener guiones; el id es numérico al final
  if (i < 0) return null
  const id = Number(p.slice(i + 1))
  if (Number.isNaN(id)) return null
  return { tipo: p.slice(0, i), id }
}

function escribirSeleccionURL(sel) {
  const url = new URL(window.location.href)
  if (sel) url.searchParams.set('nodo', `${sel.tipo}-${sel.id}`)
  else url.searchParams.delete('nodo')
  window.history.replaceState(null, '', url)
}

export default function App() {
  const cargar = useArbolStore((s) => s.cargar)
  const seleccionar = useArbolStore((s) => s.seleccionar)
  const seleccion = useArbolStore((s) => s.seleccion)
  const cargando = useArbolStore((s) => s.cargando)
  const error = useArbolStore((s) => s.error)
  const arbol = useArbolStore((s) => s.arbol)

  // Carga inicial + restaurar selección desde la URL. (En dev standalone no hay
  // data-expediente-id: el mock se preinyecta en el store desde main.jsx.)
  useEffect(() => {
    const id = expedienteIdDesdeDOM()
    if (id) cargar(id)
    const sel = leerSeleccionURL()
    if (sel) seleccionar(sel)
  }, [cargar, seleccionar])

  // Reflejar la selección en la URL sin recargar.
  useEffect(() => {
    escribirSeleccionURL(seleccion)
  }, [seleccion])

  if (cargando) return <div className="p-4 text-muted">Cargando árbol…</div>
  if (error) {
    return (
      <div className="p-4 text-danger">
        Error al cargar el árbol: {String((error && error.message) || error)}
      </div>
    )
  }
  if (!arbol) return null

  return (
    <div className="d-flex flex-column" style={{ height: '100%' }}>
      <Viewbar />
      <div style={{ flex: 1, minHeight: 0 }}>
        <Arbol />
      </div>
    </div>
  )
}
