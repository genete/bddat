// Aviso «este fichero ya está en el expediente» antes de subir (ADR-050 §H, N077; #1007).
//
// El navegador calcula el SHA-256 del fichero elegido, a trozos y con una librería que sirve
// BDDAT (app/static/vendor/sha256/, sin CDN), y pregunta al servidor si el expediente ya lo
// tiene, antes de enviar los bytes. Si ya está, el fichero no se sube salvo que se marque
// «Subir igualmente». La librería se carga a demanda: la Despensa no la necesita hasta que
// alguien elige un fichero.
//
// Es solo un aviso. El servidor sigue calculando su propia huella al subir (la del navegador
// nunca es el `contenido_sha256`), y si la comprobación falla —la librería no carga, el
// fichero no se puede leer, la consulta da error— no se avisa y se sube como siempre.
// Solo mira el mismo expediente: «ya está en otro expediente» espera a «Aportar desde otro
// expediente» (diferido).
//
// Gemelo del aviso de pool_documentos.html (JS plano): el texto es el mismo. Si cambia uno,
// cambiar el otro.
import React from 'react'
import { api } from './api.js'

const RUTA_LIBRERIA = '/static/vendor/sha256/sha256.min.js'
const TROZO = 4 * 1024 * 1024

let _carga = null

function cargarLibreria() {
  if (window.sha256) return Promise.resolve()
  if (!_carga) {
    _carga = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = RUTA_LIBRERIA
      s.onload = resolve
      s.onerror = () => { _carga = null; reject(new Error('No se ha podido cargar la librería de huellas')) }
      document.head.appendChild(s)
    })
  }
  return _carga
}

// SHA-256 del fichero en hexadecimal, a trozos (un fichero de 300 MB no cabe entero en memoria).
async function huellaDeFichero(fichero, alProgreso) {
  await cargarLibreria()
  const hasher = window.sha256.create()
  for (let pos = 0; pos < fichero.size; pos += TROZO) {
    const trozo = await fichero.slice(pos, pos + TROZO).arrayBuffer()
    hasher.update(new Uint8Array(trozo))
    alProgreso(Math.min(100, Math.round((100 * (pos + TROZO)) / fichero.size)))
    await new Promise((r) => setTimeout(r, 0))   // deja respirar a la interfaz entre trozo y trozo
  }
  return hasher.hex()
}

function fechaLegible(iso) {
  if (!iso) return 'sin fecha'
  const [a, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${a}`
}

// La «X» del aviso: nombre, tipo y fecha administrativa; con varios, hasta tres y «y N más».
function describirCoincidencias(docs) {
  const vistos = docs.slice(0, 3).map(
    (d) => `«${d.nombre}» (${d.tipo || 'sin tipo'}, ${fechaLegible(d.fecha)})`)
  const resto = docs.length - vistos.length
  const texto = vistos.length > 1
    ? vistos.slice(0, -1).join(', ') + (resto > 0 ? ', ' : ' y ') + vistos[vistos.length - 1]
    : vistos[0]
  return resto > 0 ? `${texto} y ${resto} más` : texto
}

const SIN_AVISO = { calculando: false, pct: 0, coincidencias: [] }

// Estado del aviso de un formulario de subida de un solo fichero. `bloqueaSubida` es lo que
// el botón de subir ha de mirar: espera a la comprobación y no deja subir un duplicado sin
// «Subir igualmente».
export function useAvisoYaExiste(expedienteId) {
  const [estado, setEstado] = React.useState(SIN_AVISO)
  const [subirIgualmente, setSubirIgualmente] = React.useState(false)
  const token = React.useRef(0)    // una respuesta tardía de otro fichero se ignora

  const comprobar = React.useCallback(async (fichero) => {
    const mio = ++token.current
    setSubirIgualmente(false)
    if (!fichero) { setEstado(SIN_AVISO); return }
    setEstado({ ...SIN_AVISO, calculando: true })
    try {
      const huella = await huellaDeFichero(fichero, (pct) => {
        if (mio === token.current) setEstado((e) => ({ ...e, pct }))
      })
      const data = await api.post(`/expedientes/${expedienteId}/documentos/ya-existe`, { hashes: [huella] })
      if (mio !== token.current) return
      setEstado({ ...SIN_AVISO, coincidencias: (data && data.coincidencias && data.coincidencias[huella]) || [] })
    } catch {
      if (mio === token.current) setEstado(SIN_AVISO)   // sin aviso: se sube como siempre
    }
  }, [expedienteId])

  const reiniciar = React.useCallback(() => {
    token.current += 1
    setEstado(SIN_AVISO)
    setSubirIgualmente(false)
  }, [])

  return {
    ...estado,
    subirIgualmente,
    setSubirIgualmente,
    comprobar,
    reiniciar,
    bloqueaSubida: estado.calculando || (estado.coincidencias.length > 0 && !subirIgualmente),
  }
}

export function AvisoYaExiste({ aviso }) {
  const { calculando, pct, coincidencias, subirIgualmente, setSubirIgualmente } = aviso
  if (calculando) {
    return <div className="small text-muted">Comprobando si ya está en el expediente… {pct} %</div>
  }
  if (coincidencias.length === 0) return null
  return (
    <div className="small p-2 rounded border border-warning bg-warning-subtle text-warning-emphasis">
      <i className="bi bi-exclamation-triangle me-1" />
      Este fichero ya está en el expediente como {describirCoincidencias(coincidencias)}.
      Si lo subes igualmente se creará otro documento con el mismo contenido, sin guardar otra
      copia, y con sus propios datos, que deberás indicar.
      <label className="d-flex align-items-center gap-1 mt-1 fw-semibold">
        <input
          type="checkbox"
          className="form-check-input mt-0"
          checked={subirIgualmente}
          onChange={(e) => setSubirIgualmente(e.target.checked)}
        />
        Subir igualmente
      </label>
    </div>
  )
}
