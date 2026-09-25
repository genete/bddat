// ModalConfirmacionFrase.jsx — confirmación bloqueante de un acto (#956, ADR-049 §F, D5).
//
// Nace para el cierre de la fase finalizadora, reutilizable por cualquier otro acto
// que lo necesite (p. ej. el certificado de cierre de la solicitud, N6). Dos modos:
//
//   - con `frase`: el botón de aceptar solo se habilita cuando se escribe la frase
//     exacta (sin distinguir mayúsculas ni espacios de los extremos), como al borrar
//     un repositorio en GitHub. Para los actos irreversibles: obliga a leer y a
//     parar, no solo a hacer clic.
//   - sin `frase`: una confirmación normal, con el mismo aspecto.
//
// Bloqueante de verdad: ni el backdrop ni Escape lo cierran mientras se está
// enviando, y el foco va al campo de la frase. La frase es solo fricción de
// interfaz: el backend la exige por su cuenta para que no se salte llamando a la
// API.
//
// Por `createPortal` a <body>, por el mismo motivo que ModalInformeFinInstruccion:
// montado en su sitio, el `position: fixed` se resolvería respecto al panel del
// inspector. Clases de Bootstrap sin su JS (la isla no carga bootstrap.js).
import React from 'react'
import { createPortal } from 'react-dom'

export default function ModalConfirmacionFrase({
  abierto, titulo, frase = null, textoAccion, variante = 'danger',
  enviando = false, onConfirmar, onCancelar, children,
}) {
  const [escrito, setEscrito] = React.useState('')
  const campoRef = React.useRef(null)

  // Cada apertura empieza con el campo vacío: la frase no se recuerda de una vez
  // para otra.
  React.useEffect(() => {
    if (!abierto) return undefined
    setEscrito('')
    const t = setTimeout(() => { if (campoRef.current) campoRef.current.focus() }, 0)
    return () => clearTimeout(t)
  }, [abierto])

  React.useEffect(() => {
    if (!abierto) return undefined
    const alEscape = (e) => { if (e.key === 'Escape' && !enviando) onCancelar() }
    document.addEventListener('keydown', alEscape)
    return () => document.removeEventListener('keydown', alEscape)
  }, [abierto, enviando, onCancelar])

  if (!abierto) return null

  const coincide = !frase || escrito.trim().toLowerCase() === frase.toLowerCase()
  const confirmar = () => { if (coincide && !enviando) onConfirmar(frase ? escrito.trim() : null) }

  return createPortal(
    <>
      <div className="modal-backdrop fade show" />
      <div className="modal fade show d-block" role="dialog" aria-modal="true" aria-label={titulo}>
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title h6 mb-0">{titulo}</h5>
              <button type="button" className="btn-close" aria-label="Cancelar"
                      disabled={enviando} onClick={onCancelar} />
            </div>
            <form onSubmit={(e) => { e.preventDefault(); confirmar() }}>
              <div className="modal-body small">
                {children}
                {frase && (
                  <div className="mt-3">
                    <label className="form-label small mb-1" htmlFor="confirmacion-frase">
                      Para confirmar, escriba <strong className="user-select-all">{frase}</strong>
                    </label>
                    <input id="confirmacion-frase" ref={campoRef} type="text"
                           className="form-control form-control-sm" autoComplete="off"
                           value={escrito} disabled={enviando}
                           onChange={(e) => setEscrito(e.target.value)} />
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-sm btn-outline-secondary"
                        disabled={enviando} onClick={onCancelar}>
                  Cancelar
                </button>
                <button type="submit" className={`btn btn-sm btn-${variante}`}
                        disabled={!coincide || enviando}>
                  {enviando ? 'Enviando…' : textoAccion}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>,
    document.body,
  )
}
