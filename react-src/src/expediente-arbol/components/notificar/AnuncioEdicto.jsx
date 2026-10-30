// AnuncioEdicto.jsx — el anuncio de un edicto y su aplicación a las notificaciones que recogió
// (#1037; ADR-052 §G; #568).
//
// Son dos piezas del mismo dato, como en `NotificacionesTramite.jsx`:
//   - `TarjetaAnuncioEdicto`, en la zona de datos, en lectura y en edición: el anuncio publicado
//     (si ya está vinculado) y las notificaciones que este edicto recogió al crearse, con su estado.
//   - `AccionAplicarAnuncio`, en la zona de acciones, solo en edición: «Aplicar el anuncio», que
//     cierra con una copia del anuncio las recogidas que sigan abiertas. Sin lista de ids: el
//     conjunto lo decidió el usuario al marcarlas en el trámite de notificación.
//
// Comparten el estado en `useEdicto`: la tarjeta lo carga al montarse y el botón lo recarga tras
// aplicar. Lee `GET …/tramite/<id>/edicto`, que solo exige poder ver el expediente, y aplica con
// el POST del mismo sitio. El servidor dice por qué hoy no se puede aplicar (`motivo_no_aplicar`);
// aquí solo se enseña.
import React from 'react'
import { create } from 'zustand'
import { useArbolStore } from '../../store.js'
import { getEdicto, postEdicto } from '../../api.js'
import { showToast, showAvisos } from '../../../shared/ui/toast.js'
import { TarjetaDatos } from '../TarjetaDatos.jsx'
import EnlaceDocumento from './EnlaceDocumento.jsx'

const mensajeDe = (e, porDefecto) => (
  (e && e.payload && (e.payload.error || e.payload.motivo)) || (e && e.message) || porDefecto
)

// `tramiteId` dice de qué trámite es `datos`: al cambiar de trámite se descarta, pero al recargar
// el mismo (tras aplicar) se conserva y no parpadea. `sedePendiente`: ids de tarea de las
// recogidas postales que el último «Aplicar» dejó con la sede pendiente (art. 42.1); el servidor
// solo lo dice en esa respuesta, así que dura lo que el usuario siga en este trámite.
export const useEdicto = create((set, get) => ({
  tramiteId: null,
  datos: null,
  sedePendiente: [],
  error: null,
  aplicando: false,

  cargar: async (expedienteId, tramiteId) => {
    if (get().tramiteId !== tramiteId) {
      set({ tramiteId, datos: null, sedePendiente: [], error: null, aplicando: false })
    }
    try {
      const datos = await getEdicto(expedienteId, tramiteId)
      if (get().tramiteId === tramiteId) set({ datos, error: null })
    } catch (e) {
      if (get().tramiteId === tramiteId) set({ error: mensajeDe(e, 'No se pudo cargar el edicto') })
    }
  },

  aplicar: async (expedienteId, tramiteId, refrescarArbol) => {
    set({ aplicando: true, error: null })
    let fallo = null
    try {
      const res = await postEdicto(expedienteId, tramiteId)
      const n = res.ids.length
      showToast(n === 1 ? 'Cerrada 1 notificación con el anuncio' : `Cerradas ${n} notificaciones con el anuncio`, 'success')
      const adv = res.advertencia
      if (adv && Array.isArray(adv.avisos) && adv.avisos.length > 0) showAvisos(adv.avisos)
      if (get().tramiteId === tramiteId) set({ sedePendiente: (adv && adv.sede_pendiente) || [] })
    } catch (e) {
      if (e.status === 401 || e.status === 403) return
      fallo = mensajeDe(e, 'No se pudo aplicar el anuncio')
    } finally {
      set({ aplicando: false })
    }
    // También tras un fallo a mitad: las ya cerradas están guardadas y el árbol tiene que verlas.
    // Recargar borra el error, así que el del fallo se vuelve a poner después.
    await Promise.all([get().cargar(expedienteId, tramiteId), refrescarArbol()])
    if (fallo && get().tramiteId === tramiteId) set({ error: fallo })
  },
}))

// ¿Hay un edicto con recogidas que mostrar? Lo usa el inspector para saber si pinta la zona de
// acciones propias (la regla de los hooks impide llamarlo desde una entrada del registro).
export function useHayEdicto(tramiteId) {
  return useEdicto((s) => s.tramiteId === tramiteId && !!s.datos && s.datos.recogidas.length > 0)
}

const fechaLarga = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('es-ES')

function FilaRecogida({ fila, sedePendiente }) {
  return (
    <li className="mb-2">
      <span className="fw-semibold">{fila.texto}</span>
      <span className="d-block small text-muted">
        {fila.cerrada ? <><i className="fas fa-check text-success me-1" />Cerrada</> : fila.motivo}
        {fila.sin_destinatario && <span className="badge text-bg-warning ms-1">Sin destinatario</span>}
        {sedePendiente && <span className="badge text-bg-warning ms-1">Sede electrónica pendiente</span>}
      </span>
    </li>
  )
}

export function TarjetaAnuncioEdicto({ expedienteId, tramiteId }) {
  const cargar = useEdicto((s) => s.cargar)
  const visible = useEdicto((s) => s.tramiteId === tramiteId)
  const datos = useEdicto((s) => (s.tramiteId === tramiteId ? s.datos : null))
  const error = useEdicto((s) => (s.tramiteId === tramiteId ? s.error : null))
  const sedePendiente = useEdicto((s) => (s.tramiteId === tramiteId ? s.sedePendiente : []))

  React.useEffect(() => { cargar(expedienteId, tramiteId) }, [cargar, expedienteId, tramiteId])

  if (visible && error && !datos) return <div className="text-danger small mb-3">{error}</div>
  if (!datos) return null

  const { anuncio, recogidas } = datos
  return (
    <TarjetaDatos titulo="Anuncio y notificaciones recogidas" icono="fa-bullhorn">
      <div className="col-12">
        <div className="form-label fw-semibold small">Anuncio publicado</div>
        {anuncio ? (
          <div className="d-flex flex-wrap align-items-baseline gap-2">
            <EnlaceDocumento doc={anuncio} />
            {anuncio.fecha_administrativa && (
              <span className="small text-muted">publicado el {fechaLarga(anuncio.fecha_administrativa)}</span>
            )}
          </div>
        ) : (
          <div className="small text-muted">
            Aún no hay anuncio publicado vinculado a este trámite.
          </div>
        )}
      </div>
      <div className="col-12">
        <div className="form-label fw-semibold small">
          Notificaciones que recoge este edicto ({recogidas.length})
        </div>
        {recogidas.length === 0 ? (
          <div className="small text-muted">
            Este edicto no recogió ninguna notificación: se marcan en el trámite de notificación de la fase.
          </div>
        ) : (
          <ul className="list-unstyled mb-0">
            {recogidas.map((f) => (
              <FilaRecogida key={f.valor} fila={f} sedePendiente={sedePendiente.includes(f.valor)} />
            ))}
          </ul>
        )}
      </div>
    </TarjetaDatos>
  )
}

export function AccionAplicarAnuncio({ expedienteId, tramiteId }) {
  const refrescarArbol = useArbolStore((s) => s.refrescarArbol)
  const aplicar = useEdicto((s) => s.aplicar)
  const aplicando = useEdicto((s) => s.aplicando)
  const datos = useEdicto((s) => (s.tramiteId === tramiteId ? s.datos : null))
  const error = useEdicto((s) => (s.tramiteId === tramiteId ? s.error : null))
  const hay = useHayEdicto(tramiteId)
  const [confirmando, setConfirmando] = React.useState(false)

  // Al cambiar de trámite no se arrastra una confirmación a medias.
  React.useEffect(() => { setConfirmando(false) }, [tramiteId])

  if (!hay) return null
  const motivo = datos.motivo_no_aplicar
  const abiertas = datos.recogidas.filter((f) => !f.cerrada).length

  const lanzar = async () => {
    setConfirmando(false)
    await aplicar(expedienteId, tramiteId, refrescarArbol)
  }

  return (
    <div className="mb-3">
      {!confirmando ? (
        <button type="button" className="btn btn-sm btn-primary" disabled={!!motivo || aplicando}
                onClick={() => setConfirmando(true)}>
          {aplicando ? 'Aplicando…' : 'Aplicar el anuncio'}
        </button>
      ) : (
        <div className="alert alert-warning py-2 px-3 small mb-0">
          <div className="mb-2">
            Se {abiertas === 1 ? 'cerrará 1 notificación' : `cerrarán ${abiertas} notificaciones`} con
            una copia del anuncio publicado, como notificadas por edicto.
          </div>
          <button type="button" className="btn btn-sm btn-primary me-2" onClick={lanzar}>Aplicar</button>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setConfirmando(false)}>
            Cancelar
          </button>
        </div>
      )}
      {motivo
        ? <div className="small text-muted mt-1">{motivo}</div>
        : !confirmando && (
          <div className="small text-muted mt-1">
            Cierra con una copia del anuncio las notificaciones recogidas que sigan abiertas.
          </div>
        )}
      {error && <div className="alert alert-danger py-2 px-3 small mt-2 mb-0">{error}</div>}
    </div>
  )
}
