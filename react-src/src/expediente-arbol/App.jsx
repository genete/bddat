// App.jsx — raíz de la isla del árbol (#500, ADR-016).
//
// Lee data-expediente-id del contenedor, carga el árbol y compone Viewbar + Arbol.
// Sincroniza la selección con la URL (?nodo=tipo-id, ADR §12) vía history.replaceState.
// El Inspector real es S3 (aquí solo Viewbar + Arbol).
import React, { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useArbolStore, selectHayCambios } from './store.js'
import { showToast } from '../shared/ui/toast.js'
import Viewbar from './components/Viewbar.jsx'
import Arbol from './components/Arbol.jsx'
import Inspector from './components/Inspector.jsx'

// Slot del inspector en el shell base_app (lo define arbol.html como block inspector).
// El Inspector se renderiza ahí vía portal: un único árbol React / un único store.
const inspectorSlot = () => document.getElementById('arbol-inspector-slot')

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
  const enEdicion = useArbolStore((s) => s.modoEdicion)
  const hayCambios = useArbolStore(selectHayCambios)

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

  // Lock de la UI: al ENTRAR en edición se atenúa el chrome Jinja vía body.arbol-lock
  // (CSS) y se monta el overlay (más abajo). Idempotente (add/remove simétricos) →
  // resiste el doble-invoke de StrictMode en dev.
  useEffect(() => {
    if (!enEdicion) return
    document.body.classList.add('arbol-lock')
    return () => document.body.classList.remove('arbol-lock')
  }, [enEdicion])

  // beforeunload (diálogo nativo "cambios sin guardar"): solo si hay cambios reales que
  // perder. El overlay ya impide navegar dentro de la app durante la edición.
  useEffect(() => {
    if (!(enEdicion && hayCambios)) return
    const handler = (e) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [enEdicion, hayCambios])

  if (cargando) return <div className="p-4 text-muted">Cargando árbol…</div>
  if (error) {
    return (
      <div className="p-4 text-danger">
        Error al cargar el árbol: {String((error && error.message) || error)}
      </div>
    )
  }
  if (!arbol) return null

  const slot = inspectorSlot()

  return (
    <div className="d-flex flex-column" style={{ height: '100%' }}>
      <Viewbar />
      <div style={{ flex: 1, minHeight: 0 }}>
        <Arbol />
      </div>
      {slot && createPortal(<Inspector />, slot)}
      {enEdicion && createPortal(
        <div aria-hidden="true"
             onClick={() => showToast('Estás editando este elemento — Guarda o cancela primero.', 'warning')}
             style={{ position: 'fixed', inset: 0, zIndex: 1040, background: 'transparent', cursor: 'not-allowed' }} />,
        document.body)}
    </div>
  )
}
