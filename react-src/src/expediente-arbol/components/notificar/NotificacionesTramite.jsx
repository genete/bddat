// NotificacionesTramite.jsx — a quién falta notificar en un trámite (#929, A2; ADR-051 §D, §E;
// #1043, ADR-053 §C).
//
// Son dos piezas del mismo dato, en las dos zonas del cuerpo del inspector (decisión de Carlos,
// 13/10/2026: lo que sale en edición también se ve en lectura):
//   - `TarjetaNotificacionesTramite`, en la zona de datos, en lectura y en edición: las fuentes
//     del trámite según el catálogo y lo que falte o sobre («falta notificar a X», «sobra la
//     notificación a Y», ya redactado por el servidor en `textos`).
//   - `AccionNotificacionesTramite`, en la zona de acciones, solo en edición: el botón «añadir las
//     notificaciones que faltan», el mismo en todos los trámites (idempotente: refresca las que no
//     han salido, rellena las vacías y crea las que faltan), y lo que no puede resolver
//     (`pendientes`: a quién hay que elegir).
//
// Comparten el estado en `useNotificacionesTramite`: la tarjeta lo carga al montarse y el botón lo
// actualiza con la respuesta, sin depender de que el inspector se vuelva a montar. Lee
// `GET …/tramite/<id>/notificaciones`, que solo exige poder ver el expediente.
//
// Un trámite sin fuentes en el catálogo (`fuentes` vacío) no notifica a nadie: no se pinta nada.
import React from 'react'
import { create } from 'zustand'
import { useArbolStore } from '../../store.js'
import { getNotificacionesTramite, postAnadirFaltan } from '../../api.js'
import { showToast } from '../../../shared/ui/toast.js'
import { TarjetaDatos, CampoDato, ValorSoloLectura } from '../TarjetaDatos.jsx'

// `tramiteId` dice de qué trámite es `estado`: al cambiar de trámite se descarta, pero al
// recargar el mismo (tras pulsar el botón y refrescar el árbol) se conserva y no parpadea.
export const useNotificacionesTramite = create((set, get) => ({
  tramiteId: null,
  estado: null,
  pendientes: [],
  error: null,
  enviando: false,

  cargar: async (expedienteId, tramiteId) => {
    if (get().tramiteId !== tramiteId) {
      set({ tramiteId, estado: null, pendientes: [], error: null, enviando: false })
    }
    try {
      const estado = await getNotificacionesTramite(expedienteId, tramiteId)
      if (get().tramiteId === tramiteId) set({ estado, error: null })
    } catch (e) {
      if (get().tramiteId === tramiteId) {
        set({ error: (e && e.message) || 'No se pudo cargar las notificaciones' })
      }
    }
  },

  anadir: async (expedienteId, tramiteId, refrescarArbol) => {
    set({ enviando: true, error: null })
    try {
      const res = await postAnadirFaltan(expedienteId, tramiteId)
      if (get().tramiteId === tramiteId) set({ estado: res.estado, pendientes: res.pendientes || [] })
      showToast(resumen(res), 'success')
      await refrescarArbol()
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      set({
        error: (e.payload && (e.payload.error || e.payload.motivo)) || e.message
          || 'No se pudieron añadir las notificaciones',
      })
    } finally {
      set({ enviando: false })
    }
  },
}))

function resumen(res) {
  const partes = []
  if (res.creadas.length) partes.push(`${res.creadas.length} creada(s)`)
  if (res.rellenadas.length) partes.push(`${res.rellenadas.length} con destinatario`)
  if (res.refrescadas.length) partes.push(`${res.refrescadas.length} con la dirección actualizada`)
  return partes.length ? partes.join(', ') : 'No había nada que añadir ni refrescar'
}

// ¿Tiene el trámite notificaciones que mostrar? Lo usa el inspector para saber si pinta la zona
// de acciones propias.
export function useHayNotificacionesTramite(tramiteId) {
  return useNotificacionesTramite(
    (s) => s.tramiteId === tramiteId && !!s.estado && s.estado.fuentes.length > 0,
  )
}

export function TarjetaNotificacionesTramite({ expedienteId, tramiteId }) {
  const cargar = useNotificacionesTramite((s) => s.cargar)
  const visible = useNotificacionesTramite((s) => s.tramiteId === tramiteId)
  const estado = useNotificacionesTramite((s) => (s.tramiteId === tramiteId ? s.estado : null))
  const error = useNotificacionesTramite((s) => (s.tramiteId === tramiteId ? s.error : null))

  React.useEffect(() => { cargar(expedienteId, tramiteId) }, [cargar, expedienteId, tramiteId])

  if (visible && error && !estado) return <div className="text-danger small mb-3">{error}</div>
  if (!estado || estado.fuentes.length === 0) return null

  return (
    <TarjetaDatos titulo="Notificaciones del trámite" icono="fa-envelope">
      <CampoDato rotulo="Se notifica a">
        <ValorSoloLectura
          rotulo="Se notifica a"
          valor={estado.fuentes.map((f) => estado.fuentes_etiquetas[f] || f).join(' · ')} />
      </CampoDato>
      <div className="col-12">
        {estado.completo ? (
          <div className="alert alert-success py-2 px-3 small mb-0">Nadie falta ni sobra.</div>
        ) : (
          <ul className="alert alert-warning py-2 ps-4 pe-3 small mb-0">
            {estado.textos.map((t) => <li key={t}>{t}</li>)}
          </ul>
        )}
      </div>
    </TarjetaDatos>
  )
}

export function AccionNotificacionesTramite({ expedienteId, tramiteId }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const anadir = useNotificacionesTramite((s) => s.anadir)
  const enviando = useNotificacionesTramite((s) => s.enviando)
  const pendientes = useNotificacionesTramite((s) => (s.tramiteId === tramiteId ? s.pendientes : []))
  const error = useNotificacionesTramite((s) => (s.tramiteId === tramiteId ? s.error : null))
  const hay = useHayNotificacionesTramite(tramiteId)

  if (!hay) return null

  return (
    <div className="mb-3">
      {pendientes.length > 0 && (
        <div className="small text-muted mb-2">
          El botón no puede resolver:
          <ul className="mb-0">{pendientes.map((t) => <li key={t}>{t}</li>)}</ul>
        </div>
      )}
      <button type="button" className="btn btn-sm btn-primary" disabled={enviando}
              onClick={() => anadir(expedienteId, tramiteId, refrescarArbol)}>
        {enviando ? 'Añadiendo…' : 'Añadir las notificaciones que faltan'}
      </button>
      <div className="small text-muted mt-1">
        Crea las que faltan y actualiza la dirección de las que aún no han salido. Las que
        sobran no se tocan: se corrige su origen y se borran a mano.
      </div>
      {error && <div className="alert alert-danger py-2 px-3 small mt-2 mb-0">{error}</div>}
    </div>
  )
}
