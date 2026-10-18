// AccionesNodo.jsx — Acciones propias de algunos nodos del árbol, en edición (#1047, ADR-053 §C).
//
// Salieron de `Inspector.jsx` sin cambios para que el registro de editores (`registroEditores.jsx`) pueda
// importarlas sin un ciclo de imports. De la solicitud: la bisagra instrucción → resolución, el cierre de la
// solicitud y el informe de la revisión.
import React from 'react'
import { createPortal } from 'react-dom'
import { useArbolStore } from '../store.js'

// Bisagra instrucción → resolución (#827, ADR-043 §E): el gesto con el que el
// técnico pregunta cómo va la instrucción y, si no queda nada pendiente, la declara
// terminada. Hasta que el certificado consta, el motor bloquea la apertura de la
// fase finalizadora citando el art. 82.1 LPACAP.
//
// Vive en la zona de acciones, como AccionesFaseConsultas y ReabrirFase.
// Siempre visible en la solicitud, y con el botón SIEMPRE activo: el
// gesto dejó de ser una puerta que se concede o se deniega. Preguntar «¿cómo va
// esto?» no tiene precondiciones —se puede desde el primer día— y la respuesta es
// un informe, no un error. Por eso el inspector ya no trae el motivo del «todavía
// no»: lo dice el informe al pulsar, con mucho más detalle del que cabía aquí.
export function CertFinInstruccion() {
  const detalle      = useArbolStore((s) => s.detalle)
  const certificando = useArbolStore((s) => s.certificandoFinInstruccion)
  const certificar   = useArbolStore((s) => s.certificarFinInstruccion)

  const cert = detalle && detalle.cert_fin_instruccion
  if (!cert) return null

  if (cert.emitido) return <SelloInstruccion />

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-light mb-3">
      <span className="small">
        <i className="bi bi-hourglass-split me-1" />
        <strong>Instrucción en curso.</strong> La fase de resolución no puede abrirse
        hasta que conste terminada (art. 82.1 LPACAP).
      </span>
      <span className="small text-muted">
        Revise el estado cuando quiera: si no falta nada, el certificado se emite en
        el acto; si falta algo, verá qué es y no se creará ningún documento.
      </span>
      <button
        type="button"
        className="btn btn-sm btn-primary"
        disabled={certificando}
        onClick={certificar}
      >
        {certificando ? 'Revisando…' : '📜 Certificar fin de instrucción'}
      </button>
    </div>
  )
}

// El sello, con su vía de salida (#838, ADR-043 §F). Emitido el certificado, la
// instrucción queda declarada terminada y ninguna fase de instrucción se abre ni se
// reabre. Lo que este bloque tiene que decir es doble: que está sellada, y qué hacer
// si aun así falta algo.
//
// Las dos vías van escritas, no solo la que tiene botón: la primera —recabar algo
// más dentro de la fase que resuelve, art. 87— no necesita nada de aquí, y quien la
// necesite debe encontrarla antes que el botón de deshacer, que es la cara. Mismo
// motivo por el que el bloqueo del backend las nombra en vez de prohibir a secas.
//
// El formulario está plegado por defecto, al revés que ReabrirFase, que lo muestra
// siempre: allí la fase cerrada está pidiendo abrirse para poder trabajar, y aquí el
// estado normal es que el sello se quede puesto. Desplegarlo es ya parte del acto.
function SelloInstruccion() {
  const [abierto, setAbierto] = React.useState(false)
  const [justificacion, setJustificacion] = React.useState('')
  const deshaciendo = useArbolStore((s) => s.deshaciendoFinInstruccion)
  const deshacer    = useArbolStore((s) => s.deshacerFinInstruccion)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border border-success-subtle bg-success-subtle mb-3">
      <span className="small">
        <i className="bi bi-patch-check-fill me-1" />
        <strong>Instrucción terminada.</strong> El certificado de fin de instrucción
        está emitido y la fase de resolución puede abrirse.
      </span>
      <span className="small text-muted">
        Mientras conste, no se abre ninguna fase de instrucción nueva ni se reabre una
        cerrada. Si falta recabar algo antes de resolver, acuérdelo dentro de la fase
        que resuelve, sin volver a la instrucción (art. 87 LPACAP).
      </span>

      {!abierto ? (
        <button type="button" className="btn btn-sm btn-link text-danger p-0 text-start"
                onClick={() => setAbierto(true)}>
          La instrucción no estaba terminada: deshacer el certificado
        </button>
      ) : (
        <>
          <span className="small text-muted">
            Se borrará el certificado y volverá a haber instrucción abierta. Antes hay
            que haber deshecho y borrado la fase que resuelve, si ya se creó. Queda
            registrado en bitácora y el próximo certificado lo hará constar.
          </span>
          <textarea
            className="form-control form-control-sm"
            rows={2}
            placeholder="Justificación obligatoria para deshacer el certificado"
            value={justificacion}
            onChange={(e) => setJustificacion(e.target.value)}
            disabled={deshaciendo}
          />
          <div className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-sm btn-danger"
              disabled={deshaciendo || !justificacion.trim()}
              onClick={() => deshacer(justificacion.trim())}
            >
              {deshaciendo ? 'Deshaciendo…' : '↩️ Deshacer el certificado'}
            </button>
            <button type="button" className="btn btn-sm btn-outline-secondary"
                    disabled={deshaciendo}
                    onClick={() => { setAbierto(false); setJustificacion('') }}>
              Cancelar
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// Cierre de la solicitud (#996, ADR-049 §F): el certificado que cuenta cómo terminó la
// solicitud entera —el plazo de resolver de cada acto, la instrucción y copia de los
// certificados de cierre de sus fases—. Junto al fin de instrucción, con el gesto del
// cumplimiento de la fase: el botón siempre responde con la vista HTML en el modal
// grande, que dice qué falta o enseña el certificado.
export function CierreSolicitud() {
  const detalle      = useArbolStore((s) => s.detalle)
  const certificando = useArbolStore((s) => s.certificandoCierreSolicitud)
  const certificar   = useArbolStore((s) => s.certificarCierreSolicitud)

  const cert = detalle && detalle.cert_cierre
  if (!cert) return null

  if (cert.emitido) return <SelloCierreSolicitud cert={cert} />

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-light mb-3">
      <span className="small">
        <i className="bi bi-flag me-1" />
        <strong>Cierre de la solicitud.</strong> El certificado cuenta cómo terminó: el
        plazo de resolver de cada acto, la instrucción y los certificados de cierre de sus
        fases.
      </span>
      <span className="small text-muted">
        Se emite cuando cada acto tiene su fase de resolución cerrada con su certificado. Si
        falta algo, verá qué es y no se creará ningún documento.
      </span>
      <button type="button" className="btn btn-sm btn-primary"
              disabled={certificando} onClick={certificar}>
        {certificando ? 'Revisando…' : '📜 Certificar el cierre de la solicitud'}
      </button>
    </div>
  )
}

// El certificado emitido, con su salida (D4). Mismo esquema que SelloInstruccion: el
// estado normal es que se quede, y el formulario para retirarlo está plegado.
function SelloCierreSolicitud({ cert }) {
  const [abierto, setAbierto] = React.useState(false)
  const [justificacion, setJustificacion] = React.useState('')
  const retirando = useArbolStore((s) => s.retirandoCierreSolicitud)
  const retirar   = useArbolStore((s) => s.retirarCierreSolicitud)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border border-success-subtle bg-success-subtle mb-3">
      <span className="small">
        <i className="bi bi-patch-check-fill me-1" />
        <strong>Cierre de la solicitud certificado.</strong> Su contenido se fijó al
        emitirlo y no se recalcula.
      </span>
      <button type="button" className="btn btn-sm btn-outline-success align-self-start"
              onClick={() => window.AppModalLarge && window.AppModalLarge.open(
                cert.enlace_vista, { title: 'Certificado de cierre de la solicitud' })}>
        <i className="bi bi-eye me-1" />Ver el certificado
      </button>

      {!abierto ? (
        <button type="button" className="btn btn-sm btn-link text-danger p-0 text-start"
                onClick={() => setAbierto(true)}>
          El resumen del plazo no es correcto: retirar el certificado
        </button>
      ) : (
        <>
          <span className="small text-muted">
            Se borrará el certificado; después podrá corregir lo que fallaba y volver a
            emitirlo. No se puede si alguna tarea lo tiene vinculado. Queda registrado en
            bitácora y el próximo certificado lo hará constar.
          </span>
          <textarea
            className="form-control form-control-sm"
            rows={2}
            placeholder="Justificación obligatoria para retirar el certificado"
            value={justificacion}
            onChange={(e) => setJustificacion(e.target.value)}
            disabled={retirando}
          />
          <div className="d-flex gap-2">
            <button type="button" className="btn btn-sm btn-danger"
                    disabled={retirando || !justificacion.trim()}
                    onClick={() => retirar(justificacion.trim())}>
              {retirando ? 'Retirando…' : '↩️ Retirar el certificado'}
            </button>
            <button type="button" className="btn btn-sm btn-outline-secondary"
                    disabled={retirando}
                    onClick={() => { setAbierto(false); setJustificacion('') }}>
              Cancelar
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// El informe de la revisión cuando NO se consolidó (#827, ADR-043 §E). Modal propio
// con clases de Bootstrap y sin su JS: el bundle de la isla no carga bootstrap.js y
// el contenido viene de la respuesta del POST, no de una URL — así que ni
// AppModalLarge (capa 3, que abre una url) ni un data-attribute declarativo sirven.
//
// Va por `createPortal` a <body>: montado en su sitio del árbol de componentes, el
// `position: fixed` del modal se resolvía respecto al panel del inspector y no
// respecto a la ventana —basta un ancestro con `transform` para que eso ocurra—, de
// modo que el diálogo salía encajado en la mitad derecha y el backdrop no cubría el
// árbol. Verificado en navegador antes y después.
//
// Tres bloques, en el orden en que se leen: lo que falta (con el porqué), lo salvado
// bajo criterio propio, y el relato de lo instruido hasta ahora. Los tres llegan ya
// redactados por el backend — cada nodo del árbol escribe lo suyo (§E bis) — y aquí
// no se compone ninguna frase.
export function ModalInformeFinInstruccion() {
  const informe = useArbolStore((s) => s.informeFinInstruccion)
  const cerrar  = useArbolStore((s) => s.cerrarInformeFinInstruccion)
  const seleccionar = useArbolStore((s) => s.seleccionar)

  React.useEffect(() => {
    if (!informe) return undefined
    const alEscape = (e) => { if (e.key === 'Escape') cerrar() }
    document.addEventListener('keydown', alEscape)
    return () => document.removeEventListener('keydown', alEscape)
  }, [informe, cerrar])

  if (!informe) return null

  const pendientes = informe.pendientes || []
  const salvados   = informe.salvados || []
  const relato     = (informe.bloques || []).flatMap((b) => b.relato || [])

  // "Ir al nodo" cierra el modal y selecciona: el técnico venía a arreglar algo.
  const irAlNodo = (nodo) => {
    if (!nodo) return
    cerrar()
    seleccionar({ tipo: nodo.tipo, id: nodo.id })
  }

  return createPortal(
    <>
      <div className="modal-backdrop fade show" onClick={cerrar} />
      <div className="modal fade show d-block" role="dialog" aria-modal="true"
           aria-label="Informe de fin de instrucción">
        <div className="modal-dialog modal-lg modal-dialog-scrollable">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title h6 mb-0">
                <i className="bi bi-clipboard-check me-2" />
                La instrucción todavía no puede certificarse
              </h5>
              <button type="button" className="btn-close" aria-label="Cerrar"
                      onClick={cerrar} />
            </div>
            <div className="modal-body">
              <p className="small text-muted">
                No se ha creado ningún documento. Resuelva lo que falta y vuelva a
                pedir el certificado cuando quiera.
              </p>

              <h6 className="small text-uppercase text-muted mt-3">Qué falta</h6>
              <ul className="list-group list-group-flush mb-3">
                {pendientes.map((b, i) => (
                  <li className="list-group-item px-0 py-2" key={`p-${i}`}>
                    <div className="small fw-semibold">{b.titulo}</div>
                    {(b.pendiente || []).map((linea, j) => (
                      <div className="small" key={j}>{linea}</div>
                    ))}
                    {b.nodo && (
                      <button type="button"
                              className="btn btn-link btn-sm p-0 mt-1 small"
                              onClick={() => irAlNodo(b.nodo)}>
                        Ir al nodo →
                      </button>
                    )}
                  </li>
                ))}
              </ul>

              {salvados.length > 0 && (
                <>
                  <h6 className="small text-uppercase text-muted">
                    Actos salvados con criterio del tramitador
                  </h6>
                  <p className="small text-muted mb-2">
                    No impiden certificar. Constarán en el certificado, porque la
                    resolución que se dicte debe motivarlos.
                  </p>
                  <ul className="list-group list-group-flush mb-3">
                    {salvados.map((b, i) => (
                      <li className="list-group-item px-0 py-2" key={`s-${i}`}>
                        <div className="small fw-semibold">{b.titulo}</div>
                        {(b.salvado || []).map((linea, j) => (
                          <div className="small text-muted" key={j}>{linea}</div>
                        ))}
                      </li>
                    ))}
                  </ul>
                </>
              )}

              {relato.length > 0 && (
                <>
                  <h6 className="small text-uppercase text-muted">
                    Lo instruido hasta ahora
                  </h6>
                  {relato.map((linea, i) => (
                    <div className="small text-muted" key={`r-${i}`}>{linea}</div>
                  ))}
                </>
              )}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-sm btn-secondary" onClick={cerrar}>
                Cerrar
              </button>
            </div>
          </div>
        </div>
      </div>
    </>,
    document.body,
  )
}
