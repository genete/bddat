// MenuContextual.jsx — menú right-click del árbol (ADR-016 §8, S3b-4).
// Sin Borrar — vive en el inspector modo edición (ADR §7 enmendado 2026-06-03).
// Estado de posición/visibilidad en el store (menuCtx) para que NodoTareas pueda abrirlo.
import React, { useState, useEffect, useRef } from 'react'
import { useArbolStore } from '../store.js'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'
import { puedeEditarNodo, puedeCrearHijoDe } from '../../shared/auth.js'
import { estaSellado } from '../sellado.js'
import { FilaTipoCreable, BloqueoForzar } from './TiposCreablesCompartido.jsx'

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
  const menuDetalle           = useArbolStore((s) => s.menuDetalle)
  const arbol                 = useArbolStore((s) => s.arbol)
  const expedienteId          = useArbolStore((s) => s.expedienteId)
  const entrarEdicion         = useArbolStore((s) => s.entrarEdicion)
  const tipoCreacionPendiente = useArbolStore((s) => s.tipoCreacionPendiente)
  const bloqueoActual         = useArbolStore((s) => s.bloqueoActual)
  const justificacionForzar   = useArbolStore((s) => s.justificacionForzar)
  const creando               = useArbolStore((s) => s.creando)
  const seleccionarTipoCrear  = useArbolStore((s) => s.seleccionarTipoCrear)
  const cancelarCrear         = useArbolStore((s) => s.cancelarCrear)
  const setJustificacionForzar = useArbolStore((s) => s.setJustificacionForzar)
  const crearHijo             = useArbolStore((s) => s.crearHijo)

  const menuRef = useRef(null)
  const [submenuActivo, setSubmenuActivo] = useState(null) // 'crear-hijo' | 'consumidos' | null
  const [mostrarResto, setMostrarResto] = useState(false)

  // Cerrar menú al cambiar sel (reset submenu)
  useEffect(() => { setSubmenuActivo(null); setMostrarResto(false) }, [menuCtx?.sel])

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
  // Sellado (#720, ADR-036): crear hijo nunca se ofrece bajo un nodo sellado (incluida
  // la propia fase cerrada). Editar SÍ se permite sobre una fase sellada — es el único
  // camino hasta el botón "Reabrir fase" del editor — pero no sobre un trámite/tarea
  // cuya fase está cerrada, donde el backend rechazaría cualquier guardado.
  const sellado         = estaSellado(arbol, sel)
  const puedeEditar     = puedeEditarNodo(sel.tipo) && sel.tipo !== 'expediente' &&
                          (sel.tipo === 'fase' || !sellado)
  const puedeCrearHijo  = puedeCrearHijoDe(sel.tipo) && !sellado

  // canonicos/resto (ADR-037 §D): vocabulario, no permiso — el motor no se ha
  // evaluado todavía para ninguno de los dos; el bloqueo (si lo hay) se revela
  // tras el intento real (bloqueoActual, más abajo), no en este listado.
  const canonicos = tiposCreables?.canonicos || []
  const resto     = tiposCreables?.resto || []

  const producido  = menuDetalle?.documentos?.find((d) => d.rol === 'PRODUCIDO')
  const consumidos = menuDetalle?.documentos?.filter((d) => d.rol === 'CONSUMIDO') || []
  // Consumidos con enlace de apertura (bddat:// sin representación, p.ej. diagnósticos, no lo tienen — #610)
  const consumidosAbribles = consumidos.filter((d) => d.puede_abrir)
  // Carpeta del documento: producido con carpeta > primer consumido con carpeta > expediente
  const docParaCarpeta = producido?.puede_abrir_carpeta
    ? producido
    : consumidos.find((d) => d.puede_abrir_carpeta) || null

  const handleEditar = () => { entrarEdicion(sel); cerrarMenu() }

  // Crea de inmediato (sin staging visible, a diferencia de la Despensa). Si el
  // intento queda bloqueado, bloqueoActual se rellena (store.js) y el menú
  // permanece abierto mostrando BloqueoForzar en vez de cerrarse a ciegas —
  // por eso se espera la respuesta antes de decidir si cierra (ADR-037 §D).
  const handleCrearTipo = async (tipo) => {
    seleccionarTipoCrear({ tipo_id: tipo.tipo_id, codigo: tipo.codigo, nombre: tipo.nombre }, sel)
    await crearHijo()
    if (!useArbolStore.getState().bloqueoActual) cerrarMenu()
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
    if (menuDetalle?.referencia) copiarReferencia(menuDetalle.referencia)
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
                {tipoCreacionPendiente && bloqueoActual ? (
                  <div style={{ width: 240 }}>
                    <BloqueoForzar
                      bloqueo={bloqueoActual}
                      tipoNombre={tipoCreacionPendiente.nombre}
                      justificacion={justificacionForzar}
                      setJustificacion={setJustificacionForzar}
                      creando={creando}
                      onForzar={crearHijo}
                      onCancelar={cancelarCrear}
                    />
                  </div>
                ) : (
                  <>
                    {tiposCreablesCargando && (
                      <div className="arbol-menu__item" style={{ opacity: .6 }}>Cargando…</div>
                    )}
                    {!tiposCreablesCargando && canonicos.length === 0 && resto.length === 0 && (
                      <div className="arbol-menu__item" style={{ opacity: .6 }}>Sin tipos disponibles</div>
                    )}
                    {canonicos.map((t) => (
                      <FilaTipoCreable key={t.tipo_id} tipo={t} variante="menu"
                                       onClick={() => handleCrearTipo(t)} />
                    ))}
                    {resto.length > 0 && (
                      <>
                        {canonicos.length > 0 && <div className="arbol-menu__sep" />}
                        {mostrarResto
                          ? resto.map((t) => (
                              <FilaTipoCreable key={t.tipo_id} tipo={t} variante="menu"
                                               onClick={() => handleCrearTipo(t)} />
                            ))
                          : (
                            <div className="arbol-menu__item" style={{ opacity: .7 }}
                                 onClick={() => setMostrarResto(true)}>
                              Mostrar todos…
                            </div>
                          )}
                      </>
                    )}
                  </>
                )}
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
