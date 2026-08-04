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

// Slots del shell declarados en arbol.html. Portales: un único árbol React / store.
const inspectorSlot = () => document.getElementById('arbol-inspector-slot')
const viewbarSlot   = () => document.getElementById('arbol-viewbar-slot')

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

// Radar de huérfanos (#630, ADR-038 §5): ?doc_pendiente=<id> junto a ?nodo=tarea-<id>
// — el documento se pre-carga en la Despensa (ver cargarPool en store.js) una vez
// entrada la edición. Se lee una sola vez al montar, como leerSeleccionURL().
function leerDocPendienteURL() {
  const p = new URLSearchParams(window.location.search).get('doc_pendiente')
  if (!p) return null
  const id = Number(p)
  return Number.isNaN(id) ? null : id
}

export default function App() {
  const cargar = useArbolStore((s) => s.cargar)
  const seleccionar = useArbolStore((s) => s.seleccionar)
  const entrarEdicion = useArbolStore((s) => s.entrarEdicion)
  const setDocPendienteIdDesdeUrl = useArbolStore((s) => s.setDocPendienteIdDesdeUrl)
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
    if (!sel) return
    const docPendienteId = leerDocPendienteURL()
    if (docPendienteId && sel.tipo === 'tarea') {
      // Radar de huérfanos (#630): entra directo en edición — la Despensa (única
      // superficie donde se puede vincular) solo vive en modoEdicion. cargarPool()
      // recoge docPendienteIdDesdeUrl y pre-carga el documento (ver store.js).
      setDocPendienteIdDesdeUrl(docPendienteId)
      entrarEdicion(sel)
    } else {
      seleccionar(sel)
    }
  }, [cargar, seleccionar, entrarEdicion, setDocPendienteIdDesdeUrl])

  // Reflejar la selección en la URL sin recargar.
  useEffect(() => {
    escribirSeleccionURL(seleccion)
  }, [seleccion])

  // Sincronizar selección con el inspector overlay (ADR-023 / #534).
  // mountReact abre/mantiene el panel; close lo recoge al deseleccionar.
  useEffect(() => {
    if (!window.AppInspector) return
    if (seleccion) {
      const tipo = seleccion.tipo.charAt(0).toUpperCase() + seleccion.tipo.slice(1)
      AppInspector.mountReact({
        selId: `${seleccion.tipo}-${seleccion.id}`,
        title: `${tipo} #${seleccion.id}`,
      })
    } else {
      AppInspector.close()
    }
  }, [seleccion])

  // Coherencia bidireccional: si el shell cierra el panel (botón ×, Escape, light-dismiss),
  // deseleccionamos en el store para que el árbol refleje el estado.
  useEffect(() => {
    function onInspectorClosed() { seleccionar(null) }
    document.addEventListener('inspector:closed', onInspectorClosed)
    return () => document.removeEventListener('inspector:closed', onInspectorClosed)
  }, [seleccionar])

  // Lock de la UI: al ENTRAR en edición se atenúa el chrome Jinja vía body.arbol-lock
  // y se bloquea el inspector overlay (setLocked). Idempotente → resiste StrictMode.
  useEffect(() => {
    document.body.classList.toggle('arbol-lock', enEdicion)
    if (window.AppInspector) AppInspector.setLocked(enEdicion)
    return () => {
      document.body.classList.remove('arbol-lock')
      if (window.AppInspector) AppInspector.setLocked(false)
    }
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

  return (
    <div style={{ height: '100%' }}>
      <Arbol />
      {inspectorSlot() && createPortal(<Inspector />, inspectorSlot())}
      {viewbarSlot()   && createPortal(<Viewbar />,   viewbarSlot())}
    </div>
  )
}
