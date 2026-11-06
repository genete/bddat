// AltaOrganismo.jsx — «Añadir organismo» en la fase CONSULTAS, en modo edición (#1078, ADR-042 §C).
//
// El alta NO es «crear hijo» por despensa: `OrganismoExpediente` no es un tipo de catálogo. Es una
// acción de la fase, junto a «Enviar consultas pendientes»: un formulario corto —la entidad
// consultada, la vía y, si es declaración responsable, el documento que la acredita— y nada más.
// Sin plazo: lo calcula el servidor al enviar la separata (`calcular_plazo_consulta`).
//
// Guarda por su cuenta (no pasa por el borrador del marco): refresca el árbol en silencio y avisa
// al marco de lo que lleva sin guardar con `useInteriorSucio` (GUIA_REACT_ISLAS.md, «Un bloque que
// guarda por su cuenta»). Tras el alta se queda abierto y limpio, para dar de alta el siguiente.
//
// Los errores del servidor se quedan en el formulario: organismo ya registrado en la ronda, entidad
// sin rol de consultado, documento ajeno o un bloqueo del motor (motivo + norma). Si el bloqueo es
// forzable (`puede_escapar`) aparece la justificación y «Añadir de todos modos», que queda en
// bitácora; la fase sellada se rechaza igual desde el servidor y no ofrece escape.
import React from 'react'
import { useArbolStore } from '../store.js'
import { buscarEntidadesConsultadas } from '../api.js'
import { useInteriorSucio } from '../interiorSucio.js'

const MIN_CARACTERES = 2
const ESPERA_BUSQUEDA_MS = 250

const VIAS = [
  { valor: 'consulta', texto: 'Consulta', ayuda: 'Se le enviará una separata con «Enviar consultas pendientes».' },
  { valor: 'declaracion_responsable', texto: 'Declaración responsable',
    ayuda: 'Queda exonerado desde el inicio; hace falta el documento que lo acredita.' },
]

export function AccionAltaOrganismo() {
  const pool = useArbolStore((s) => s.pool)
  const poolCargado = useArbolStore((s) => s.poolCargado)
  const poolCargando = useArbolStore((s) => s.poolCargando)
  const cargarPool = useArbolStore((s) => s.cargarPool)
  const anadiendo = useArbolStore((s) => s.anadiendoOrganismo)
  const altaOrganismo = useArbolStore((s) => s.altaOrganismo)

  const [abierto, setAbierto] = React.useState(false)
  const [texto, setTexto] = React.useState('')
  const [resultados, setResultados] = React.useState([])
  const [buscando, setBuscando] = React.useState(false)
  const [entidad, setEntidad] = React.useState(null) // { id, text }
  const [via, setVia] = React.useState('consulta')
  const [documentoId, setDocumentoId] = React.useState('')
  const [justificacion, setJustificacion] = React.useState('')
  const [error, setError] = React.useState(null) // { texto, url_norma, puede_escapar }

  const esDeclaracion = via === 'declaracion_responsable'
  const sucio = abierto && (!!entidad || texto.trim() !== '' || documentoId !== '' || justificacion.trim() !== '')
  useInteriorSucio('alta-organismo', 'Alta de organismo consultado', sucio)

  // El pool solo se necesita para elegir el documento de la declaración responsable.
  React.useEffect(() => {
    if (abierto && esDeclaracion) cargarPool()
  }, [abierto, esDeclaracion, cargarPool])

  // Búsqueda con espera y cancelación: al seguir tecleando se descarta la petición anterior.
  React.useEffect(() => {
    const q = texto.trim()
    if (entidad || q.length < MIN_CARACTERES) { setResultados([]); setBuscando(false); return undefined }
    const ctrl = new AbortController()
    setBuscando(true)
    const espera = setTimeout(async () => {
      try {
        const data = await buscarEntidadesConsultadas(q, { signal: ctrl.signal })
        setResultados((data && data.results) || [])
        setBuscando(false)
      } catch (e) {
        if (e.name === 'AbortError') return
        setResultados([])
        setBuscando(false)
      }
    }, ESPERA_BUSQUEDA_MS)
    return () => { clearTimeout(espera); ctrl.abort() }
  }, [texto, entidad])

  const limpiar = () => {
    setTexto(''); setResultados([]); setEntidad(null); setDocumentoId(''); setJustificacion(''); setError(null)
  }

  const elegir = (r) => { setEntidad(r); setTexto(''); setResultados([]); setError(null) }

  const enviar = async (forzando) => {
    const body = { organismo_id: entidad.id, via }
    if (esDeclaracion) body.documento_id = Number(documentoId)
    if (forzando) { body.bypass = true; body.justificacion = justificacion.trim() }
    const res = await altaOrganismo(body)
    if (res.ok) { limpiar(); return }
    if (res.abortado) return
    setError({ texto: res.error, url_norma: res.url_norma, puede_escapar: res.puede_escapar })
  }

  if (!abierto) {
    return (
      <div className="mb-3">
        <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => setAbierto(true)}>
          <i className="bi bi-plus-lg me-1" />Añadir organismo
        </button>
      </div>
    )
  }

  const falta = !entidad || (esDeclaracion && !documentoId)
  const forzable = !!(error && error.puede_escapar)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-light mb-3">
      <span className="small">
        <i className="bi bi-building-add me-1" />
        <strong>Añadir organismo.</strong> Entidad con rol de organismo consultado en esta ronda de consultas.
      </span>

      <div>
        <label className="form-label small text-muted mb-1" htmlFor="alta-organismo-entidad">Entidad</label>
        {entidad ? (
          <div className="d-flex align-items-center gap-2">
            <span className="badge text-bg-secondary text-wrap text-start">{entidad.text}</span>
            <button type="button" className="btn btn-sm btn-link p-0" disabled={anadiendo}
                    onClick={() => { setEntidad(null); setError(null) }}>
              Cambiar
            </button>
          </div>
        ) : (
          <>
            <input id="alta-organismo-entidad" type="search" className="form-control form-control-sm"
                   value={texto} autoComplete="off" disabled={anadiendo}
                   placeholder={`Nombre o NIF (mín. ${MIN_CARACTERES} letras)…`}
                   onChange={(e) => { setTexto(e.target.value); setError(null) }} />
            {resultados.length > 0 && (
              <div className="list-group list-group-flush border rounded mt-1">
                {resultados.map((r) => (
                  <button key={r.id} type="button" className="list-group-item list-group-item-action small py-1"
                          onClick={() => elegir(r)}>
                    {r.text}
                  </button>
                ))}
              </div>
            )}
            {buscando && <div className="small text-muted fst-italic mt-1">Buscando…</div>}
            {!buscando && resultados.length === 0 && texto.trim().length >= MIN_CARACTERES && (
              <div className="small text-muted fst-italic mt-1">
                Ningún organismo consultado coincide. Si la entidad existe, comprueba que tiene el rol de consultado.
              </div>
            )}
          </>
        )}
      </div>

      <fieldset disabled={anadiendo} className="border-0 p-0 m-0">
        <legend className="form-label small text-muted mb-1 float-none fs-6">Vía</legend>
        {VIAS.map((v) => (
          <div className="form-check" key={v.valor}>
            <input className="form-check-input" type="radio" name="alta-organismo-via"
                   id={`alta-organismo-via-${v.valor}`} checked={via === v.valor}
                   onChange={() => { setVia(v.valor); setDocumentoId(''); setError(null) }} />
            <label className="form-check-label small" htmlFor={`alta-organismo-via-${v.valor}`}>
              {v.texto} <span className="text-muted">— {v.ayuda}</span>
            </label>
          </div>
        ))}
      </fieldset>

      {esDeclaracion && (
        <div>
          <label className="form-label small text-muted mb-1" htmlFor="alta-organismo-documento">
            Documento de la declaración responsable
          </label>
          <select id="alta-organismo-documento" className="form-select form-select-sm" value={documentoId}
                  disabled={anadiendo || !poolCargado}
                  onChange={(e) => { setDocumentoId(e.target.value); setError(null) }}>
            <option value="">
              {poolCargado ? '— Selecciona un documento del expediente —'
                : poolCargando ? 'Cargando documentos…' : 'No se pudieron cargar los documentos'}
            </option>
            {pool.map((d) => <option key={d.id} value={d.id}>{d.texto_opcion || d.nombre}</option>)}
          </select>
          {poolCargado && pool.length === 0 && (
            <div className="small text-muted fst-italic mt-1">
              El expediente no tiene documentos: sube antes el que acredita la declaración.
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="alert alert-danger small py-2 mb-0" role="alert">
          {error.texto}
          {error.url_norma && (
            <> <a href={error.url_norma} target="_blank" rel="noopener noreferrer">Ver la norma</a></>
          )}
        </div>
      )}

      {forzable && (
        <>
          <span className="small text-muted">
            Este bloqueo se puede forzar. Queda registrado en bitácora con la justificación.
          </span>
          <textarea className="form-control form-control-sm" rows={2} value={justificacion}
                    placeholder="Justificación obligatoria para añadirlo de todos modos"
                    disabled={anadiendo} onChange={(e) => setJustificacion(e.target.value)} />
        </>
      )}

      <div className="d-flex gap-2">
        {forzable ? (
          <button type="button" className="btn btn-sm btn-warning"
                  disabled={anadiendo || falta || !justificacion.trim()} onClick={() => enviar(true)}>
            {anadiendo ? 'Añadiendo…' : 'Añadir de todos modos'}
          </button>
        ) : (
          <button type="button" className="btn btn-sm btn-primary"
                  disabled={anadiendo || falta} onClick={() => enviar(false)}>
            {anadiendo ? 'Añadiendo…' : 'Añadir organismo'}
          </button>
        )}
        <button type="button" className="btn btn-sm btn-outline-secondary" disabled={anadiendo}
                onClick={() => { limpiar(); setVia('consulta'); setAbierto(false) }}>
          Cerrar
        </button>
      </div>
    </div>
  )
}
