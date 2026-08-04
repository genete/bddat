// AnalizarEditor.jsx — contenedor de la tarea ANALIZAR (#442, #677, ADR-033).
//
// Reemplaza al Editor genérico cuando la tarea seleccionada es de tipo ANALIZAR
// (ver Inspector.jsx). Se compone de:
//   - Secciones extendidas (check documental #495, check técnico #581,
//     requerimientos #440), solo si el backend las declara (secciones_extendidas)
//     — no todo trámite con ANALIZAR las necesita (p.ej. CONSULTA_SEPARATA).
//     Cada una es un acordeón con resumen en cabecera (ADR-033 §1) que se
//     colapsa (abrible) al producir el diagnóstico (§6).
//   - Bloque de defectos: un único bloque que muta de nombre y naturaleza al
//     producir — "Borrador defectos" en curso → "Resultado diagnóstico"
//     producido (§1). Solo en secciones extendidas.
//   - Núcleo de resultado (siempre presente): en secciones extendidas el
//     resultado es derivado del borrador, sin elección libre ni "Condicionado"
//     (§3); en ANALIZAR simple se mantiene el radio libre de siempre.
//   - Notas: campo directo de la tarea, enganchado a `borrador.notas` del store
//     (#688). No lleva botón propio — lo guarda el par Guardar/Cancelar de la
//     cabecera fija, igual que en cualquier otro nodo.
//
// Este contenedor NO monta Guardar/Cancelar: el de los campos directos vive en
// la cabecera (BarraEdicion, #688) y todo lo demás que se ve aquí (vincular
// documento, guardar ítem técnico, guardar shuttle) persiste por su cuenta y de
// inmediato, sin pasar por el borrador.
import React from 'react'
import { useArbolStore } from '../store.js'
import {
  getAnalizar, postAnalizar, revertirDiagnostico,
  vincularRequisitoDocumental, desvincularRequisitoDocumental,
  guardarCoberturaTecnica,
  getRequerimientos, postRequerimientos, crearRequerimientoCatalogo,
} from '../api.js'
import { showToast } from '../../shared/ui/toast.js'
import BloqueNotas from './BloqueNotas.jsx'

const ETIQUETA_RESULTADO = {
  favorable: 'Favorable',
  condicionado: 'Condicionado',
  desfavorable: 'Desfavorable',
}

// Acordeón genérico (ADR-033 §1/§6): cabecera clicable con resumen de estado +
// cuerpo colapsable. `abiertaInicial` solo se lee al montar: el padre fuerza
// un remount (key) cuando cambia el estado producido/no-producido para que la
// regla "colapsado al entrar en edición" se aplique en el momento correcto.
function Acordeon({ titulo, resumen, abiertaInicial, children }) {
  const [abierta, setAbierta] = React.useState(abiertaInicial)
  const toggle = () => setAbierta((a) => !a)

  return (
    <div className="card mb-3">
      <div
        className="card-header card-header-accent fw-semibold small d-flex justify-content-between align-items-center"
        style={{ cursor: 'pointer' }}
        role="button"
        tabIndex={0}
        onClick={toggle}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle() } }}
      >
        <span>{titulo}</span>
        <span className="d-flex align-items-center gap-2">
          {resumen && <span className="text-muted fw-normal">{resumen}</span>}
          <i className={`bi ${abierta ? 'bi-chevron-up' : 'bi-chevron-down'}`} />
        </span>
      </div>
      {abierta && <div className="card-body card-body-tinted">{children}</div>}
    </div>
  )
}

// --- Reversión controlada del diagnóstico producido (ADR-033 §5, #678) --------
// Guarda de los tres puntos de persistencia reales (Vincular/Desvincular
// documental, Guardar ítem técnico, Guardar cambios del shuttle). Sin
// diagnóstico producido, `ejecutar` corre la acción directo (escalón 1, sin
// fricción). Producido y no consumido (escalón 2): confirmación destructiva
// inline — al confirmar, revierte el diagnóstico (DELETE .../analizar) y solo
// entonces ejecuta la acción original con los datos que el técnico ya tenía
// preparados. Consumido por un ELABORAR (escalón 3): la reversión devuelve
// 422 con `puede_escapar:false` — puerta cerrada, se sustituye la confirmación
// por el motivo (qué deshacer antes) en vez de un toast transitorio.
//
// #714 añade un 422 con `puede_escapar:true` (diagnóstico superado por una vuelta
// posterior, con todo aún en casa): no es puerta cerrada sino freno — se pide
// justificación y se reintenta el mismo DELETE con ella, que queda en bitácora.
function useReversionDiagnostico({ expedienteId, tareaId, producido, onRevertido }) {
  const [confirmando, setConfirmando] = React.useState(false)
  const [revirtiendo, setRevirtiendo] = React.useState(false)
  const [bloqueo, setBloqueo] = React.useState(null)   // {motivo, puedeEscapar}
  const accionPendienteRef = React.useRef(null)

  const ejecutar = (accion) => {
    if (!producido) return accion()
    accionPendienteRef.current = accion
    setBloqueo(null)
    setConfirmando(true)
  }

  const confirmar = async (justificacion) => {
    setRevirtiendo(true)
    try {
      await revertirDiagnostico(expedienteId, tareaId, justificacion)
      showToast(
        justificacion
          ? 'Diagnóstico revertido con justificación — queda en la bitácora'
          : 'Diagnóstico revertido — vuelto a Borrador defectos',
        'warning',
      )
      setConfirmando(false)
      setBloqueo(null)
      await onRevertido()
      const accion = accionPendienteRef.current
      accionPendienteRef.current = null
      if (accion) await accion()
    } catch (e) {
      if (e && e.status === 422 && e.payload && e.payload.puede_escapar !== undefined) {
        setBloqueo({
          motivo: e.payload.motivo || 'No se puede revertir el diagnóstico.',
          puedeEscapar: e.payload.puede_escapar === true,
        })
      } else {
        showToast((e && e.message) || 'No se pudo revertir el diagnóstico', 'danger')
        setConfirmando(false)
      }
    } finally {
      setRevirtiendo(false)
    }
  }

  const cancelar = () => {
    accionPendienteRef.current = null
    setConfirmando(false)
    setBloqueo(null)
  }

  return { confirmando, revirtiendo, bloqueo, ejecutar, confirmar, cancelar }
}

// Caja inline (patrón ADR-023, no diálogo nativo): confirmación destructiva
// (escalón 2), puerta cerrada con el motivo (escalón 3) o freno con justificación
// (#714: superado por una vuelta posterior, nada ha salido fuera).
function AvisoReversionDiagnostico({ confirmando, revirtiendo, bloqueo, onConfirmar, onCancelar }) {
  const [justificacion, setJustificacion] = React.useState('')

  if (!confirmando) return null

  if (bloqueo && !bloqueo.puedeEscapar) {
    return (
      <div className="alert alert-danger py-2 px-3 mb-2 small">
        <div className="fw-semibold mb-1">No se puede revertir el diagnóstico</div>
        <div className="mb-2">{bloqueo.motivo}</div>
        <button type="button" className="btn btn-sm btn-outline-secondary" onClick={onCancelar}>
          Entendido
        </button>
      </div>
    )
  }

  if (bloqueo) {
    // Mismo régimen que el bypass del motor y que el gate de completitud al producir:
    // no se cierra la puerta, se obliga a parar y dejar dicho por qué.
    return (
      <div className="alert alert-warning py-2 px-3 mb-2 small">
        <div className="fw-semibold mb-1">Esta reversión necesita justificación</div>
        <div className="mb-2">{bloqueo.motivo}</div>
        <textarea
          className="form-control form-control-sm mb-2"
          rows={2}
          placeholder="Motivo por el que se revierte igualmente"
          value={justificacion}
          onChange={(e) => setJustificacion(e.target.value)}
        />
        <div className="d-flex gap-2">
          <button
            type="button"
            className="btn btn-sm btn-warning"
            disabled={revirtiendo || !justificacion.trim()}
            onClick={() => onConfirmar(justificacion.trim())}
          >
            {revirtiendo ? 'Revirtiendo…' : 'Revertir igualmente'}
          </button>
          <button type="button" className="btn btn-sm btn-outline-secondary" disabled={revirtiendo} onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="border rounded p-2 mb-2 bg-warning-subtle border-warning-subtle small">
      <div className="mb-2">
        Al modificar los defectos con el diagnóstico producido, se invalidará el
        resultado y el diagnóstico se eliminará. ¿Continuar?
      </div>
      <div className="d-flex gap-2">
        <button type="button" className="btn btn-sm btn-warning" disabled={revirtiendo} onClick={() => onConfirmar()}>
          {revirtiendo ? 'Revirtiendo…' : 'Continuar'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={revirtiendo} onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </div>
  )
}

// --- Modificar un check ya exigido en una vuelta notificada (#724) ------------
// A diferencia de useReversionDiagnostico, aquí la tarea actual NO tiene
// diagnóstico propio que revertir — el 422 viene de tocar (desvincular
// documental, guardar técnico, guardar shuttle) un ítem que ya figuraba en un
// diagnóstico de una vuelta ANTERIOR ya notificada al titular. Mismo look&feel
// que AvisoReversionDiagnostico (textarea + "continuar igualmente"), pero
// reintenta la MISMA llamada con `justificacion` en vez de revertir nada.
// `accion` (por llamada a `ejecutar`) recibe `justificacion` (null la primera
// vez) y debe relanzar cualquier error que no maneje ella misma — este hook es
// quien decide si el 422 pide justificación o es un fallo genérico (toast).
function useConfirmacionJustificada() {
  const [pidiendo, setPidiendo] = React.useState(false)
  const [enviando, setEnviando] = React.useState(false)
  const [motivo, setMotivo] = React.useState(null)
  const accionRef = React.useRef(null)

  const intentar = async (justificacion) => {
    setEnviando(true)
    try {
      await accionRef.current(justificacion)
      setPidiendo(false)
      setMotivo(null)
      accionRef.current = null
    } catch (e) {
      if (e && e.status === 422 && e.payload && e.payload.puede_escapar === true) {
        setMotivo(e.payload.motivo || 'Este ítem ya se exigió al titular en una vuelta anterior.')
        setPidiendo(true)
      } else {
        showToast((e && e.message) || 'No se pudo guardar', 'danger')
        setPidiendo(false)
        accionRef.current = null
      }
    } finally {
      setEnviando(false)
    }
  }

  const ejecutar = (accion) => {
    accionRef.current = accion
    intentar(null)
  }

  return { pidiendo, enviando, motivo, ejecutar, confirmar: intentar, cancelar: () => {
    accionRef.current = null
    setPidiendo(false)
    setMotivo(null)
  } }
}

function AvisoJustificacion({ pidiendo, enviando, motivo, onConfirmar, onCancelar }) {
  const [justificacion, setJustificacion] = React.useState('')

  if (!pidiendo) return null

  return (
    <div className="alert alert-warning py-2 px-3 mb-2 small">
      <div className="fw-semibold mb-1">Esto necesita justificación</div>
      <div className="mb-2">{motivo}</div>
      <textarea
        className="form-control form-control-sm mb-2"
        rows={2}
        placeholder="Motivo por el que se exige de nuevo"
        value={justificacion}
        onChange={(e) => setJustificacion(e.target.value)}
      />
      <div className="d-flex gap-2">
        <button
          type="button"
          className="btn btn-sm btn-warning"
          disabled={enviando || !justificacion.trim()}
          onClick={() => onConfirmar(justificacion.trim())}
        >
          {enviando ? 'Guardando…' : 'Confirmar igualmente'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={enviando} onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </div>
  )
}

// Fila de un requisito documental (#495): estado + selector de documento del pool.
function FilaRequisitoDocumental({ item, expedienteId, tareaId, pool, producido, onRecargar }) {
  const [seleccionando, setSeleccionando] = React.useState(false)
  const [documentoId, setDocumentoId] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)
  const reversion = useReversionDiagnostico({ expedienteId, tareaId, producido, onRevertido: onRecargar })
  const justificacion = useConfirmacionJustificada()

  const vincular = async () => {
    if (!documentoId) return
    setEnviando(true)
    try {
      await vincularRequisitoDocumental(expedienteId, tareaId, item.requisito_id, Number(documentoId))
      setSeleccionando(false)
      setDocumentoId('')
      showToast('Documento vinculado', 'success')
      await onRecargar()
    } catch (e) {
      showToast((e && e.message) || 'No se pudo vincular el documento', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  // Desvincular es la única mutación documental que puede crear un defecto
  // nuevo (vincular siempre resuelve) — puede necesitar justificación si el
  // requisito ya se exigió al titular en una vuelta notificada anterior (#724).
  // Sin `just` (null en el primer intento) el hook decide si reintentar.
  const desvincular = async (just) => {
    setEnviando(true)
    try {
      await desvincularRequisitoDocumental(expedienteId, tareaId, item.requisito_id, just)
      showToast('Documento desvinculado', 'success')
      await onRecargar()
    } finally {
      setEnviando(false)
    }
  }

  const cita = [item.articulo, item.norma].filter(Boolean).join(', ')

  return (
    <div className="border-bottom pb-2 mb-2">
      <div className="d-flex justify-content-between align-items-start gap-2 mb-1">
        <div className="small">
          <div className="fw-semibold">{item.tipo_documento || 'Documento'}</div>
          {item.descripcion_legal && <div className="text-muted">{item.descripcion_legal}</div>}
          {cita && <div className="text-muted fst-italic">{cita}</div>}
        </div>
        <span className={`badge ${item.cubierto ? 'text-bg-success' : 'text-bg-warning'}`}>
          {item.cubierto ? 'Cubierto' : 'Pendiente'}
        </span>
      </div>

      {item.documento && (
        <div className="d-flex align-items-center gap-2 small mb-1">
          <span className="text-truncate">{item.documento.nombre}</span>
          <button
            type="button"
            className="btn btn-sm btn-link text-danger p-0 lh-1"
            disabled={enviando}
            onClick={() => reversion.ejecutar(() => justificacion.ejecutar(desvincular))}
          >
            Quitar
          </button>
        </div>
      )}

      <AvisoReversionDiagnostico
        confirmando={reversion.confirmando}
        revirtiendo={reversion.revirtiendo}
        bloqueo={reversion.bloqueo}
        onConfirmar={reversion.confirmar}
        onCancelar={reversion.cancelar}
      />
      <AvisoJustificacion
        pidiendo={justificacion.pidiendo}
        enviando={justificacion.enviando}
        motivo={justificacion.motivo}
        onConfirmar={justificacion.confirmar}
        onCancelar={justificacion.cancelar}
      />

      {seleccionando ? (
        <div className="d-flex gap-1">
          <select
            className="form-select form-select-sm"
            value={documentoId}
            onChange={(e) => setDocumentoId(e.target.value)}
          >
            <option value="">Selecciona un documento…</option>
            {pool.map((d) => (
              <option key={d.id} value={d.id}>{d.nombre}</option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-sm btn-primary"
            disabled={!documentoId || enviando}
            onClick={() => reversion.ejecutar(vincular)}
          >
            Vincular
          </button>
          <button
            type="button"
            className="btn btn-sm btn-outline-secondary"
            disabled={enviando}
            onClick={() => { setSeleccionando(false); setDocumentoId('') }}
          >
            Cancelar
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setSeleccionando(true)}
        >
          {item.documento ? 'Cambiar documento' : 'Vincular documento'}
        </button>
      )}
    </div>
  )
}

function SeccionDocumental({ checklist, expedienteId, tareaId, producido, onRecargar, abiertaInicial }) {
  const pool = useArbolStore((s) => s.pool)
  const cargarPool = useArbolStore((s) => s.cargarPool)

  React.useEffect(() => { cargarPool() }, [cargarPool])

  const cubiertos = checklist.filter((it) => it.cubierto).length
  const resumen = checklist.length > 0 ? `${cubiertos}/${checklist.length} cubiertos` : null

  return (
    <Acordeon titulo="Check documental" resumen={resumen} abiertaInicial={abiertaInicial}>
      {checklist.length === 0 ? (
        <div className="text-muted small fst-italic">No hay requisitos documentales aplicables.</div>
      ) : (
        checklist.map((item) => (
          <FilaRequisitoDocumental
            key={item.requisito_id}
            item={item}
            expedienteId={expedienteId}
            tareaId={tareaId}
            pool={pool}
            producido={producido}
            onRecargar={onRecargar}
          />
        ))
      )}
    </Acordeon>
  )
}

// Fila de un ítem técnico (#581): checkbox (deshabilitado sin texto) + texto de
// justificación/ubicación. Máquina de 3 estados de CoberturaItemTecnico
// (app/models/items_tecnicos.py): sin texto = no revisado; texto+cubierto=false =
// desfavorable; texto+cubierto=true = favorable.
function FilaItemTecnico({ item, expedienteId, tareaId, producido, onRecargar }) {
  const [texto, setTexto] = React.useState(item.texto || '')
  const [cubierto, setCubierto] = React.useState(item.cubierto)
  const [enviando, setEnviando] = React.useState(false)
  const reversion = useReversionDiagnostico({ expedienteId, tareaId, producido, onRevertido: onRecargar })
  const justificacion = useConfirmacionJustificada()

  const hayCambios = texto !== (item.texto || '') || cubierto !== item.cubierto

  // Puede necesitar justificación (#724) si este guardado marca el ítem "no
  // cumple" y ya se exigió al titular en una vuelta notificada anterior.
  const guardar = async (just) => {
    setEnviando(true)
    try {
      await guardarCoberturaTecnica(expedienteId, tareaId, item.item_tecnico_id, {
        texto: texto.trim(), cubierto, justificacion: just || undefined,
      })
      showToast('Verificación guardada', 'success')
      await onRecargar()
    } finally {
      setEnviando(false)
    }
  }

  const estado = !texto.trim() ? 'no_revisado' : (cubierto ? 'favorable' : 'desfavorable')
  const ETIQUETA_ESTADO = { favorable: 'Favorable', desfavorable: 'Desfavorable', no_revisado: 'No revisado' }
  const BADGE_ESTADO = { favorable: 'text-bg-success', desfavorable: 'text-bg-warning', no_revisado: 'text-bg-secondary' }
  const cita = [item.articulo, item.norma].filter(Boolean).join(', ')

  return (
    <div className="border-bottom pb-2 mb-2">
      <div className="d-flex justify-content-between align-items-start gap-2 mb-1">
        <div className="small">
          <div className="fw-semibold">{item.descripcion}</div>
          {cita && <div className="text-muted fst-italic">{cita}</div>}
        </div>
        <span className={`badge ${BADGE_ESTADO[estado]}`}>{ETIQUETA_ESTADO[estado]}</span>
      </div>

      <div className="form-check mb-1">
        <input
          type="checkbox"
          className="form-check-input"
          id={`tecnico-cubierto-${item.item_tecnico_id}`}
          checked={cubierto}
          disabled={!texto.trim()}
          onChange={(e) => setCubierto(e.target.checked)}
        />
        <label className="form-check-label small" htmlFor={`tecnico-cubierto-${item.item_tecnico_id}`}>
          Cumple
        </label>
      </div>

      <textarea
        className="form-control form-control-sm mb-1"
        rows={2}
        placeholder="Ubicación si cumple, o justificación de por qué falta…"
        value={texto}
        onChange={(e) => {
          const v = e.target.value
          setTexto(v)
          if (!v.trim()) setCubierto(false)
        }}
      />

      <AvisoReversionDiagnostico
        confirmando={reversion.confirmando}
        revirtiendo={reversion.revirtiendo}
        bloqueo={reversion.bloqueo}
        onConfirmar={reversion.confirmar}
        onCancelar={reversion.cancelar}
      />
      <AvisoJustificacion
        pidiendo={justificacion.pidiendo}
        enviando={justificacion.enviando}
        motivo={justificacion.motivo}
        onConfirmar={justificacion.confirmar}
        onCancelar={justificacion.cancelar}
      />

      <button
        type="button"
        className="btn btn-sm btn-outline-secondary"
        disabled={!hayCambios || enviando}
        onClick={() => reversion.ejecutar(() => justificacion.ejecutar(guardar))}
      >
        {enviando ? 'Guardando…' : 'Guardar'}
      </button>
    </div>
  )
}

function SeccionTecnica({ checklist, expedienteId, tareaId, producido, onRecargar, abiertaInicial }) {
  const revisados = checklist.filter((it) => (it.texto || '').trim()).length
  const resumen = checklist.length > 0 ? `${revisados}/${checklist.length} revisados` : null

  return (
    <Acordeon titulo="Check técnico" resumen={resumen} abiertaInicial={abiertaInicial}>
      {checklist.length === 0 ? (
        <div className="text-muted small fst-italic">No hay ítems técnicos aplicables.</div>
      ) : (
        checklist.map((item) => (
          <FilaItemTecnico
            key={item.item_tecnico_id}
            item={item}
            expedienteId={expedienteId}
            tareaId={tareaId}
            producido={producido}
            onRecargar={onRecargar}
          />
        ))
      )}
    </Acordeon>
  )
}

// Selector de requerimientos — panel shuttle (#440, DISEÑO_ANALISIS_SOLICITUD.md §6).
// Estado en memoria mientras el técnico trabaja (añadir/quitar/reordenar/editar);
// se persiste completo con un único "Guardar cambios" (POST reemplaza la lista).
const CATEGORIAS_REQUERIMIENTO = [
  ['documental', 'Documental'],
  ['tecnica', 'Técnica'],
  ['administrativa', 'Administrativa'],
  ['tasas', 'Tasas'],
]
const ETIQUETA_CATEGORIA = Object.fromEntries(CATEGORIAS_REQUERIMIENTO)

// El modo de la fila depende del tipo de trámite de la tarea actual, no de si
// el ítem ya está guardado (#695): en ANÁLISIS_DOCUMENTAL se está redactando
// el defecto por primera vez — no puede estar "resuelto" algo que aún no se ha
// notificado, así que ahí solo caben editar/quitar (igual que Documental y
// Técnico, con el mismo mecanismo de reversión si hay diagnóstico producido).
// En REQUERIMIENTO_SUBSANACIÓN se coteja lo heredado de una vuelta ya
// producida — ahí el juicio es "resuelto o no", editar/quitar quedan
// deshabilitados (ADR-033 §7: un requerimiento libre no tiene contra qué casar
// automáticamente, borrarlo sin más pierde el juicio del técnico sin rastro).
function FilaSeleccionado({ item, idx, total, esRondaSubsanacion, onQuitar, onMover, onEditar, onToggleResuelto }) {
  const [editando, setEditando] = React.useState(false)
  const [texto, setTexto] = React.useState(item.texto)

  const empezarEdicion = () => { setTexto(item.texto); setEditando(true) }

  const confirmarEdicion = () => {
    const t = texto.trim()
    if (t) onEditar(idx, t)
    setEditando(false)
  }

  return (
    <div className="d-flex align-items-start gap-1 border-bottom pb-1 mb-1">
      <span className="text-muted" style={{ cursor: 'grab' }} title="Arrastrar para reordenar">⠿</span>
      {esRondaSubsanacion && (
        <div className="form-check mt-1" title="Marcar como resuelto">
          <input
            type="checkbox"
            className="form-check-input"
            checked={Boolean(item.resuelto)}
            onChange={() => onToggleResuelto(idx)}
          />
        </div>
      )}
      <div className={`flex-grow-1 small ${item.resuelto ? 'text-muted text-decoration-line-through' : ''}`}>
        {editando ? (
          <div className="d-flex gap-1">
            <textarea
              className="form-control form-control-sm"
              rows={2}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              autoFocus
            />
            <button type="button" className="btn btn-sm btn-primary" onClick={confirmarEdicion}>✓</button>
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary"
              onClick={() => { setTexto(item.texto); setEditando(false) }}
            >
              ✕
            </button>
          </div>
        ) : (
          <span>{item.texto}</span>
        )}
      </div>
      {!editando && !item.catalogo_requerimientos_id && !esRondaSubsanacion && (
        <button
          type="button"
          className="btn btn-sm btn-link p-0 lh-1"
          title="Editar"
          onClick={empezarEdicion}
        >
          ✏️
        </button>
      )}
      <div className="d-flex flex-column">
        <button
          type="button"
          className="btn btn-sm btn-link p-0 lh-1"
          disabled={idx === 0}
          title="Subir"
          onClick={() => onMover(idx, -1)}
        >
          ↑
        </button>
        <button
          type="button"
          className="btn btn-sm btn-link p-0 lh-1"
          disabled={idx === total - 1}
          title="Bajar"
          onClick={() => onMover(idx, 1)}
        >
          ↓
        </button>
      </div>
      <button
        type="button"
        className="btn btn-sm btn-link text-danger p-0 lh-1"
        title={esRondaSubsanacion ? 'No se puede quitar en una ronda de subsanación — márcalo resuelto' : 'Quitar'}
        disabled={esRondaSubsanacion}
        onClick={() => onQuitar(idx)}
      >
        ✕
      </button>
    </div>
  )
}

function SeccionRequerimientos({ expedienteId, tareaId, producido, esRondaSubsanacion, onRecargarConsolidado, abiertaInicial }) {
  const [catalogo, setCatalogo] = React.useState([])
  const [seleccionados, setSeleccionados] = React.useState([])
  const [cargando, setCargando] = React.useState(true)
  const [guardando, setGuardando] = React.useState(false)
  const [hayCambiosShuttle, setHayCambiosShuttle] = React.useState(false)
  const [filtro, setFiltro] = React.useState('')
  const [textoLibre, setTextoLibre] = React.useState('')
  const [guardarEnCatalogo, setGuardarEnCatalogo] = React.useState(false)
  const [categoriaNueva, setCategoriaNueva] = React.useState('administrativa')
  const [anadiendoLibre, setAnadiendoLibre] = React.useState(false)
  const nextKeyRef = React.useRef(0)
  const nuevaKey = () => `k${nextKeyRef.current++}`
  const reversion = useReversionDiagnostico({
    expedienteId, tareaId, producido, onRevertido: onRecargarConsolidado,
  })
  const justificacion = useConfirmacionJustificada()

  const cargar = React.useCallback(async () => {
    setCargando(true)
    try {
      const data = await getRequerimientos(expedienteId, tareaId)
      setCatalogo(data.catalogo || [])
      setSeleccionados((data.seleccionados || []).map((s) => ({ ...s, _key: nuevaKey() })))
      setHayCambiosShuttle(false)
    } catch (e) {
      showToast((e && e.message) || 'No se pudo cargar el selector de requerimientos', 'danger')
    } finally {
      setCargando(false)
    }
  }, [expedienteId, tareaId])

  React.useEffect(() => { cargar() }, [cargar])

  const marcarCambio = (fn) => (...args) => { fn(...args); setHayCambiosShuttle(true) }

  const idsCatalogoSeleccionados = new Set(
    seleccionados.filter((s) => s.catalogo_requerimientos_id).map((s) => s.catalogo_requerimientos_id)
  )
  const catalogoDisponible = catalogo.filter(
    (c) => !idsCatalogoSeleccionados.has(c.id)
      && (!filtro.trim() || c.texto.toLowerCase().includes(filtro.trim().toLowerCase()))
  )
  const catalogoPorCategoria = CATEGORIAS_REQUERIMIENTO
    .map(([cod, etiqueta]) => [cod, etiqueta, catalogoDisponible.filter((c) => c.categoria === cod)])
    .filter(([, , items]) => items.length > 0)

  const anadirDelCatalogo = marcarCambio((item) => {
    setSeleccionados((prev) => [...prev, {
      catalogo_requerimientos_id: item.id, texto_libre: null, texto: item.texto,
      resuelto: false, _key: nuevaKey(),
    }])
  })

  const quitar = marcarCambio((idx) => {
    setSeleccionados((prev) => prev.filter((_, i) => i !== idx))
  })

  const mover = marcarCambio((idx, delta) => {
    setSeleccionados((prev) => {
      const j = idx + delta
      if (j < 0 || j >= prev.length) return prev
      const next = [...prev]
      ;[next[idx], next[j]] = [next[j], next[idx]]
      return next
    })
  })

  const editarInline = marcarCambio((idx, nuevoTexto) => {
    setSeleccionados((prev) => prev.map(
      (s, i) => (i === idx ? { ...s, texto_libre: nuevoTexto, texto: nuevoTexto } : s)
    ))
  })

  const toggleResuelto = marcarCambio((idx) => {
    setSeleccionados((prev) => prev.map(
      (s, i) => (i === idx ? { ...s, resuelto: !s.resuelto } : s)
    ))
  })

  const anadirTextoLibre = async () => {
    const texto = textoLibre.trim()
    if (!texto) return
    setAnadiendoLibre(true)
    try {
      if (guardarEnCatalogo) {
        const data = await crearRequerimientoCatalogo(expedienteId, tareaId, texto, categoriaNueva)
        setCatalogo((prev) => [...prev, data.requerimiento])
        setSeleccionados((prev) => [...prev, {
          catalogo_requerimientos_id: data.requerimiento.id, texto_libre: null, texto: data.requerimiento.texto,
          resuelto: false, _key: nuevaKey(),
        }])
      } else {
        setSeleccionados((prev) => [...prev, {
          catalogo_requerimientos_id: null, texto_libre: texto, texto, resuelto: false, _key: nuevaKey(),
        }])
      }
      setHayCambiosShuttle(true)
      setTextoLibre('')
    } catch (e) {
      showToast((e && e.message) || 'No se pudo añadir el requerimiento', 'danger')
    } finally {
      setAnadiendoLibre(false)
    }
  }

  // Puede necesitar justificación en lote (#724): si alguno de los ítems ya
  // resueltos deja de estarlo (o desaparece de `seleccionados`) y ya se exigió
  // al titular en una vuelta notificada anterior, el 422 trae el motivo con
  // todos los afectados listados.
  const guardarShuttle = async (just) => {
    setGuardando(true)
    try {
      await postRequerimientos(expedienteId, tareaId, seleccionados.map((s) => ({
        catalogo_requerimientos_id: s.catalogo_requerimientos_id,
        texto_libre: s.texto_libre,
        resuelto: Boolean(s.resuelto),
      })), just)
      showToast('Requerimientos guardados', 'success')
      await cargar()
      await onRecargarConsolidado()
    } finally {
      setGuardando(false)
    }
  }

  const resumen = seleccionados.length > 0 ? `${seleccionados.length} seleccionados` : null
  const botonGuardar = (
    <button
      type="button"
      className="btn btn-sm btn-primary"
      disabled={!hayCambiosShuttle || guardando || cargando}
      onClick={() => reversion.ejecutar(() => justificacion.ejecutar(guardarShuttle))}
    >
      {guardando ? 'Guardando…' : 'Guardar cambios'}
    </button>
  )

  return (
    <Acordeon
      titulo="Requerimientos"
      resumen={resumen}
      abiertaInicial={abiertaInicial}
    >
      {cargando ? (
        <div className="text-muted small fst-italic">Cargando…</div>
      ) : (
        <>
        <AvisoReversionDiagnostico
          confirmando={reversion.confirmando}
          revirtiendo={reversion.revirtiendo}
          bloqueo={reversion.bloqueo}
          onConfirmar={reversion.confirmar}
          onCancelar={reversion.cancelar}
        />
        <AvisoJustificacion
          pidiendo={justificacion.pidiendo}
          enviando={justificacion.enviando}
          motivo={justificacion.motivo}
          onConfirmar={justificacion.confirmar}
          onCancelar={justificacion.cancelar}
        />
        <div className="row g-2">
          {/* Columna izquierda: catálogo */}
          <div className="col-6">
            <input
              type="text"
              className="form-control form-control-sm mb-2"
              placeholder="Filtrar catálogo…"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
            />
            <div style={{ maxHeight: 220, overflowY: 'auto' }}>
              {catalogoPorCategoria.length === 0 ? (
                <div className="text-muted small fst-italic">Sin ítems disponibles.</div>
              ) : (
                catalogoPorCategoria.map(([cod, etiqueta, items]) => (
                  <div key={cod} className="mb-2">
                    <div className="text-muted small fw-semibold">{etiqueta}</div>
                    {items.map((c) => (
                      <div key={c.id} className="d-flex align-items-start gap-1 small mb-1">
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-secondary lh-1"
                          title="Añadir"
                          onClick={() => anadirDelCatalogo(c)}
                        >
                          →
                        </button>
                        <span className="flex-grow-1">{c.texto}</span>
                      </div>
                    ))}
                  </div>
                ))
              )}
            </div>

            <div className="border-top pt-2 mt-2">
              <textarea
                className="form-control form-control-sm mb-1"
                rows={2}
                placeholder="Requerimiento no catalogado…"
                value={textoLibre}
                onChange={(e) => setTextoLibre(e.target.value)}
              />
              <div className="d-flex align-items-center gap-2 mb-1">
                <div className="form-check mb-0">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="req-guardar-catalogo"
                    checked={guardarEnCatalogo}
                    onChange={(e) => setGuardarEnCatalogo(e.target.checked)}
                  />
                  <label className="form-check-label small" htmlFor="req-guardar-catalogo">
                    Guardar en catálogo
                  </label>
                </div>
                {guardarEnCatalogo && (
                  <select
                    className="form-select form-select-sm w-auto"
                    value={categoriaNueva}
                    onChange={(e) => setCategoriaNueva(e.target.value)}
                  >
                    {CATEGORIAS_REQUERIMIENTO.map(([cod, etiqueta]) => (
                      <option key={cod} value={cod}>{etiqueta}</option>
                    ))}
                  </select>
                )}
              </div>
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                disabled={!textoLibre.trim() || anadiendoLibre}
                onClick={anadirTextoLibre}
              >
                {anadiendoLibre ? 'Añadiendo…' : '→ Añadir'}
              </button>
            </div>
          </div>

          {/* Columna derecha: seleccionados */}
          <div className="col-6">
            <div className="text-muted small fw-semibold mb-2">Seleccionados</div>
            {seleccionados.length === 0 ? (
              <div className="text-muted small fst-italic">Sin requerimientos seleccionados todavía.</div>
            ) : (
              seleccionados.map((item, idx) => (
                <FilaSeleccionado
                  key={item._key}
                  item={item}
                  idx={idx}
                  total={seleccionados.length}
                  esRondaSubsanacion={esRondaSubsanacion}
                  onQuitar={quitar}
                  onMover={mover}
                  onEditar={editarInline}
                  onToggleResuelto={toggleResuelto}
                />
              ))
            )}
          </div>
        </div>
        <div className="mt-2">{botonGuardar}</div>
        </>
      )}
    </Acordeon>
  )
}

// Bloque único que muta de nombre y naturaleza al producir (ADR-033 §1): antes
// de producir es "Borrador defectos" — agregado vivo, sin avisos, cambia libre
// al editar cualquier sección. Tras producir es "Resultado diagnóstico" — foto
// congelada de Diagnostico.defectos, con el resultado ya fijado.
function BloqueDefectos({ producido, items, resueltos, resultado }) {
  const titulo = producido ? 'Resultado diagnóstico' : 'Borrador defectos'

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">{titulo}</div>
      <div className="card-body card-body-tinted">
        {producido && (
          <div className="mb-2">
            <span className="badge text-bg-light border">
              {ETIQUETA_RESULTADO[resultado] || resultado}
            </span>
          </div>
        )}
        {items.length === 0 && (!resueltos || resueltos.length === 0) ? (
          <div className="text-muted small fst-italic">
            {producido ? 'Sin defectos.' : 'Sin defectos detectados todavía.'}
          </div>
        ) : (
          <ul className="list-unstyled small mb-0">
            {items.map((it, i) => <li key={`p${i}`} className="mb-1">{it.texto}</li>)}
            {/* Resueltos (ADR-033 §7): requerimientos libres ya cerrados por el
                técnico — progreso visible en subsanación, no cuentan como defecto. */}
            {(resueltos || []).map((it, i) => (
              <li key={`r${i}`} className="mb-1 text-muted text-decoration-line-through">{it.texto}</li>
            ))}
          </ul>
        )}
        {producido && (
          <div className="text-muted small mt-2">Documento producido — el resultado queda bloqueado.</div>
        )}
      </div>
    </div>
  )
}

// Núcleo (siempre presente): resultado + confirmación de dos pasos + producir.
// `derivado` (secciones extendidas, ADR-033 §3): sin radio — el resultado no es
// una elección libre, es un reflejo confirmado del borrador (favorable si vacío,
// desfavorable si hay defectos); solo texto informativo + botón. `resultado` no
// viaja en el body: lo fija el backend. En ANALIZAR simple se mantiene el radio
// libre de siempre, incluido "Condicionado".
function NucleoResultado({ expedienteId, tareaId, completo, derivado, resultadoPrevisto, onProducido }) {
  const [resultado, setResultado] = React.useState('favorable')
  const [confirmando, setConfirmando] = React.useState(false)
  const [justificacion, setJustificacion] = React.useState('')
  const [enviando, setEnviando] = React.useState(false)

  const producir = async () => {
    setEnviando(true)
    try {
      const body = {}
      if (!derivado) body.resultado = resultado
      const just = justificacion.trim()
      if (just) body.justificacion = just
      await postAnalizar(expedienteId, tareaId, body)
      showToast('Documento de diagnóstico producido', 'success')
      await onProducido()
    } catch (e) {
      showToast((e && e.payload && e.payload.motivo) || (e && e.message) || 'No se pudo producir el documento', 'danger')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="card mb-3">
      <div className="card-header card-header-accent fw-semibold small">Resultado</div>
      <div className="card-body card-body-tinted">
        {derivado ? (
          <div className="mb-3 small">
            Sentido calculado: <span className="fw-semibold">{ETIQUETA_RESULTADO[resultadoPrevisto]}</span>
          </div>
        ) : (
          <div className="mb-3">
            {['favorable', 'condicionado', 'desfavorable'].map((r) => (
              <div className="form-check" key={r}>
                <input
                  type="radio"
                  className="form-check-input"
                  id={`analizar-resultado-${r}`}
                  name="analizar-resultado"
                  checked={resultado === r}
                  disabled={confirmando}
                  onChange={() => setResultado(r)}
                />
                <label className="form-check-label small" htmlFor={`analizar-resultado-${r}`}>
                  {ETIQUETA_RESULTADO[r]}
                </label>
              </div>
            ))}
          </div>
        )}

        {!confirmando ? (
          <button type="button" className="btn btn-primary btn-sm w-100" onClick={() => setConfirmando(true)}>
            Producir documento de diagnóstico
          </button>
        ) : (
          <div className="border rounded p-2 bg-warning-subtle border-warning-subtle">
            <div className="small mb-2">
              Esta acción es <strong>irreversible</strong>: una vez producido, el resultado
              queda bloqueado. ¿Confirmas?
            </div>
            {!completo && (
              <div className="mb-2">
                <label className="form-label small text-muted mb-1">
                  Quedan ítems sin revisar — justifica para producir igualmente
                </label>
                <textarea
                  className="form-control form-control-sm"
                  rows={2}
                  value={justificacion}
                  onChange={(e) => setJustificacion(e.target.value)}
                />
              </div>
            )}
            <div className="d-flex gap-2">
              <button
                type="button"
                className="btn btn-sm btn-warning"
                disabled={enviando || (!completo && !justificacion.trim())}
                onClick={producir}
              >
                {enviando ? 'Produciendo…' : 'Confirmar producción'}
              </button>
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                disabled={enviando}
                onClick={() => { setConfirmando(false); setJustificacion('') }}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AnalizarEditor({ tareaId }) {
  const expedienteId = useArbolStore((s) => s.expedienteId)
  const seleccion = useArbolStore((s) => s.seleccion)
  const cargarDetalle = useArbolStore((s) => s.cargarDetalle)
  const setAnalizarSeccionesExtendidas = useArbolStore((s) => s.setAnalizarSeccionesExtendidas)

  const [payload, setPayload] = React.useState(null)
  const [cargando, setCargando] = React.useState(true)
  const [error, setError] = React.useState(null)

  const cargar = React.useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const data = await getAnalizar(expedienteId, tareaId)
      setPayload(data)
      setAnalizarSeccionesExtendidas(data.secciones_extendidas)
    } catch (e) {
      setError(e)
    } finally {
      setCargando(false)
    }
  }, [expedienteId, tareaId, setAnalizarSeccionesExtendidas])

  // Al cambiar de tarea (no al recargar la misma por una mutación puntual),
  // se limpia el payload para que el gate de abajo muestre "Cargando…" — evita
  // el flash de datos de la tarea anterior mientras llega la nueva (#693/#697).
  React.useEffect(() => {
    setPayload(null)
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expedienteId, tareaId])

  // Con payload ya cargado, una recarga por mutación (onRecargar/onRecargarConsolidado
  // de las secciones) no debe reemplazar el árbol entero — solo refresca los datos
  // ya montados (#693, #697: remount completo en cada vinculación/guardado puntual).
  if (cargando && !payload) return <div className="text-muted small">Cargando…</div>
  if (error) {
    return <div className="text-danger small">No se pudo cargar: {String((error && error.message) || error)}</div>
  }
  if (!payload) return null

  const onProducido = async () => {
    // Refresca el detalle de lectura del árbol (Documentos, rol Producido) y
    // el propio payload local (pasa a modo solo lectura). El pool de la
    // despensa no se invalida aquí (cacheado por vida de la isla, #517) — en
    // secciones extendidas la Despensa ya no se monta (ver Inspector.jsx).
    await cargarDetalle(seleccion)
    await cargar()
  }

  const producido = !!payload.documento_producido
  // Fuerza remount de los acordeones al cruzar la frontera no-producido→producido
  // (o al entrar ya producido): "colapsado al entrar en edición" (ADR-033 §6).
  const claveColapso = String(producido)

  return (
    <div>
      {payload.secciones_extendidas && (
        <>
          <SeccionDocumental
            key={`doc-${claveColapso}`}
            checklist={payload.checklist_documental || []}
            expedienteId={expedienteId}
            tareaId={tareaId}
            producido={producido}
            onRecargar={cargar}
            abiertaInicial={!producido}
          />
          <SeccionTecnica
            key={`tec-${claveColapso}`}
            checklist={payload.checklist_tecnico || []}
            expedienteId={expedienteId}
            tareaId={tareaId}
            producido={producido}
            onRecargar={cargar}
            abiertaInicial={!producido}
          />
          <SeccionRequerimientos
            key={`req-${claveColapso}`}
            expedienteId={expedienteId}
            tareaId={tareaId}
            producido={producido}
            esRondaSubsanacion={payload.es_ronda_subsanacion}
            onRecargarConsolidado={cargar}
            abiertaInicial={!producido}
          />
        </>
      )}

      {/* Bloque mutante (ADR-033 §1): "Borrador defectos" en secciones extendidas
          mientras se trabaja; "Resultado diagnóstico" tras producir, para
          cualquier tipo de ANALIZAR (también el simple, que antes de producir
          no tiene nada que agregar y no muestra este bloque). */}
      {(payload.secciones_extendidas || producido) && (
        <BloqueDefectos
          producido={producido}
          items={producido ? payload.documento_producido.defectos : payload.defectos_consolidado}
          resueltos={producido ? [] : (payload.defectos_resueltos || [])}
          resultado={producido ? payload.documento_producido.resultado : payload.resultado_previsto}
        />
      )}

      {!producido && (
        <NucleoResultado
          expedienteId={expedienteId}
          tareaId={tareaId}
          completo={payload.completo}
          derivado={payload.secciones_extendidas}
          resultadoPrevisto={payload.resultado_previsto}
          onProducido={onProducido}
        />
      )}

      <BloqueNotas />
    </div>
  )
}
