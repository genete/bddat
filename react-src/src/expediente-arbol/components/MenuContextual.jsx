// MenuContextual.jsx — menú right-click del árbol (ADR-016 §8, S3b-4).
// Sin Borrar — vive en el inspector modo edición (ADR §7 enmendado 2026-06-03).
// Estado de posición/visibilidad en el store (menuCtx) para que NodoTareas pueda abrirlo.
import React, { useState, useEffect, useRef } from 'react'
import { useArbolStore } from '../store.js'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'
import { puedeEditarNodo, puedeCrearHijoDe } from '../../shared/auth.js'

async function copiarReferencia(ref) {
  try {
    await navigator.clipboard.writeText(ref)
    showToast('Referencia copiada al portapapeles', 'success')
  } catch {
    showToast('No se pudo copiar la referencia', 'danger')
  }
}

async function postAccion(url) {
  try { await api.post(url) }
  catch (e) { showToast((e && e.message) || 'No se pudo completar la acción', 'danger') }
}

const MENU_W = 220
const MENU_H = 220

export default function MenuContextual() {
  const menuCtx               = useArbolStore((s) => s.menuCtx)
  const cerrarMenu            = useArbolStore((s) => s.cerrarMenu)
  const tiposCreables         = useArbolStore((s) => s.tiposCreables)
  const tiposCreablesCargando = useArbolStore((s) => s.tiposCreablesCargando)
  const detalle               = useArbolStore((s) => s.detalle)
  const expedienteId          = useArbolStore((s) => s.expedienteId)
  const entrarEdicion         = useArbolStore((s) => s.entrarEdicion)
  const seleccionarTipoCrear  = useArbolStore((s) => s.seleccionarTipoCrear)
  const crearHijo             = useArbolStore((s) => s.crearHijo)

  const menuRef = useRef(null)
  const [submenuActivo, setSubmenuActivo] = useState(null) // 'crear-hijo' | 'consumidos' | null

  // Cerrar menú al cambiar sel (reset submenu)
  useEffect(() => { setSubmenuActivo(null) }, [menuCtx?.sel])

  // Click fuera → cerrar
  useEffect(() => {
    if (!menuCtx) return
    const onMouseDown = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) cerrarMenu()
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [menuCtx, cerrarMenu])

  // Esc y scroll → cerrar
  useEffect(() => {
    if (!menuCtx) return
    const onKey    = (e) => { if (e.key === 'Escape') cerrarMenu() }
    const onScroll = () => cerrarMenu()
    document.addEventListener('keydown', onKey)
    document.addEventListener('scroll', onScroll, true)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('scroll', onScroll, true)
    }
  }, [menuCtx, cerrarMenu])

  if (!menuCtx) return null

  const { x, y, sel } = menuCtx
  const px = Math.min(x, window.innerWidth  - MENU_W - 8)
  const py = Math.min(y, window.innerHeight - MENU_H - 8)

  const esTarea    = sel.tipo === 'tarea'
  const puedeEditar    = puedeEditarNodo(sel.tipo) && sel.tipo !== 'expediente'
  const puedeCrearHijo = puedeCrearHijoDe(sel.tipo)

  const tipos        = tiposCreables?.tipos || []
  const permitidos   = tipos.filter((t) => t.permitido)
  const noPermitidos = tipos.filter((t) => !t.permitido)

  const producido  = detalle?.documentos?.find((d) => d.rol === 'PRODUCIDO')
  const consumidos = detalle?.documentos?.filter((d) => d.rol === 'CONSUMIDO') || []
  // Consumidos con enlace de apertura (bddat:// sin representación, p.ej. diagnósticos, no lo tienen — #610)
  const consumidosAbribles = consumidos.filter((d) => d.puede_abrir)
  // Carpeta del documento: producido con carpeta > primer consumido con carpeta > expediente
  const docParaCarpeta = producido?.puede_abrir_carpeta
    ? producido
    : consumidos.find((d) => d.puede_abrir_carpeta) || null

  const handleEditar = () => { entrarEdicion(sel); cerrarMenu() }

  const handleCrearTipo = (tipo) => {
    seleccionarTipoCrear({ tipo_id: tipo.tipo_id, codigo: tipo.codigo, nombre: tipo.nombre })
    crearHijo()
    cerrarMenu()
  }

  const handleCarpetaDoc = (doc) => {
    postAccion(`/expedientes/${expedienteId}/documentos/${doc.id}/abrir-en-carpeta`)
    cerrarMenu()
  }

  const handleCarpetaExp = () => {
    postAccion(`/expedientes/${expedienteId}/abrir-carpeta`)
    cerrarMenu()
  }

  const handleCopiarRef = () => {
    if (detalle?.referencia) copiarReferencia(detalle.referencia)
    cerrarMenu()
  }

  // Documento sin representación física (diagnósticos, #629): en vez de href,
  // dispara AppModalLarge vía atributo declarativo (delegación global en
  // inspector-overlay.js) — no hace falta JS propio en este componente.
  const ItemDoc = ({ doc, children }) => (doc.abrir_en === 'modal' ? (
    <div className="arbol-menu__item"
         data-modal-large-url={doc.enlace}
         data-modal-large-title={doc.nombre}
         onClick={cerrarMenu}>
      {children}
    </div>
  ) : (
    <a href={doc.enlace} target="_blank" rel="noreferrer"
       className="arbol-menu__item" onClick={cerrarMenu}>
      {children}
    </a>
  ))

  return (
    <div ref={menuRef} className="arbol-menu"
         style={{ position: 'fixed', top: py, left: px, zIndex: 9999 }}>

      {/* ── Nodo no-tarea ── */}
      {!esTarea && (
        <>
          {puedeCrearHijo && (
          <div className="arbol-menu__submenu-wrap"
               onMouseEnter={() => setSubmenuActivo('crear-hijo')}
               onMouseLeave={() => setSubmenuActivo(null)}>
            <div className="arbol-menu__item">
              <span>➕ Crear hijo</span>
              <span style={{ marginLeft: 'auto', opacity: .5, fontSize: 10 }}>▶</span>
            </div>
            {submenuActivo === 'crear-hijo' && (
              <div className="arbol-menu__submenu">
                {tiposCreablesCargando && (
                  <div className="arbol-menu__item" style={{ opacity: .6 }}>Cargando…</div>
                )}
                {!tiposCreablesCargando && tipos.length === 0 && (
                  <div className="arbol-menu__item" style={{ opacity: .6 }}>Sin tipos disponibles</div>
                )}
                {permitidos.map((t) => (
                  <div key={t.tipo_id} className="arbol-menu__item"
                       onClick={() => handleCrearTipo(t)}>
                    {t.nombre || t.codigo}
                  </div>
                ))}
                {noPermitidos.length > 0 && permitidos.length > 0 && (
                  <div className="arbol-menu__sep" />
                )}
                {noPermitidos.map((t) => (
                  <div key={t.tipo_id}
                       className="arbol-menu__item arbol-menu__item--disabled"
                       title={[t.motivo, t.norma].filter(Boolean).join(' — ')}>
                    {t.nombre || t.codigo}
                  </div>
                ))}
              </div>
            )}
          </div>
          )}
          {puedeEditar && (
            <div className="arbol-menu__item" onClick={handleEditar}>✏️ Editar</div>
          )}
        </>
      )}

      {/* ── Nodo tarea ── */}
      {esTarea && (
        <>
          {producido?.puede_abrir && (
            <ItemDoc doc={producido}>📄 Abrir documento producido</ItemDoc>
          )}
          {consumidosAbribles.length === 1 && (
            <ItemDoc doc={consumidosAbribles[0]}>📄 Abrir consumido</ItemDoc>
          )}
          {consumidosAbribles.length > 1 && (
            <div className="arbol-menu__submenu-wrap"
                 onMouseEnter={() => setSubmenuActivo('consumidos')}
                 onMouseLeave={() => setSubmenuActivo(null)}>
              <div className="arbol-menu__item">
                <span>📄 Abrir consumido(s)</span>
                <span style={{ marginLeft: 'auto', opacity: .5, fontSize: 10 }}>▶</span>
              </div>
              {submenuActivo === 'consumidos' && (
                <div className="arbol-menu__submenu">
                  {consumidosAbribles.map((d) => (
                    <ItemDoc key={d.id} doc={d}>{d.nombre}</ItemDoc>
                  ))}
                </div>
              )}
            </div>
          )}
          {puedeEditar && (
            <div className="arbol-menu__item" onClick={handleEditar}>✏️ Editar</div>
          )}
        </>
      )}

      <div className="arbol-menu__sep" />

      {/* ── Carpeta ── */}
      {esTarea && docParaCarpeta ? (
        <div className="arbol-menu__item" onClick={() => handleCarpetaDoc(docParaCarpeta)}>
          📂 Abrir carpeta del documento
        </div>
      ) : (
        <div className="arbol-menu__item" onClick={handleCarpetaExp}>
          📂 Abrir carpeta del expediente
        </div>
      )}

      <div className="arbol-menu__item" onClick={handleCopiarRef}>
        📋 Copiar referencia
      </div>
    </div>
  )
}
