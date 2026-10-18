// AccionesNodo.jsx — Acciones propias de algunos nodos del árbol, en edición (#1047, ADR-053 §C).
//
// Salieron de `Inspector.jsx` sin cambios para que el registro de editores (`registroEditores.jsx`) pueda
// importarlas sin un ciclo de imports. De la solicitud: la bisagra instrucción → resolución, el cierre de la
// solicitud y el informe de la revisión; de la fase, la reapertura, el envío de consultas, el cumplimiento del
// plazo, el cierre y la confirmación del cierre.
import React from 'react'
import { createPortal } from 'react-dom'
import { useArbolStore } from '../store.js'
import ModalConfirmacionFrase from './ModalConfirmacionFrase.jsx'

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

// Bloque de reapertura (#720, ADR-036 §6 capa 4): única vía para tocar el interior
// de una fase cerrada. Justificación siempre obligatoria (validada también
// server-side) — mismo patrón visual que el forzado de creación (Despensa.jsx).
export function ReabrirFase() {
  const [justificacion, setJustificacion] = React.useState('')
  const reabriendo  = useArbolStore((s) => s.reabriendoFase)
  const reabrirFase = useArbolStore((s) => s.reabrirFase)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-warning-subtle border-warning-subtle mb-3">
      <span className="small">
        <i className="bi bi-lock-fill me-1" /><strong>Fase cerrada.</strong> Su interior está congelado.
      </span>
      <span className="small text-muted">
        Para modificarla, reábrala primero. La reapertura queda registrada en bitácora.
      </span>
      <textarea
        className="form-control form-control-sm"
        rows={2}
        placeholder="Justificación obligatoria para reabrir la fase"
        value={justificacion}
        onChange={(e) => setJustificacion(e.target.value)}
        disabled={reabriendo}
      />
      <button
        type="button"
        className="btn btn-sm btn-warning"
        disabled={reabriendo || !justificacion.trim()}
        onClick={() => reabrirFase(justificacion.trim())}
      >
        {reabriendo ? 'Reabriendo…' : '🔓 Reabrir fase'}
      </button>
    </div>
  )
}

// Organismos vía consulta de la fase sin ninguna CONSULTA_SEPARATA vinculada
// (ADR-042 §C, #396 bloque 5) — mismo criterio estructural que el backend
// (consultas_organismos.organismos_pendientes_separata), derivado aquí del
// payload del árbol ya cargado (fase.organismos[].tramite_ids + fase.tramites)
// en vez de pedir un recuento aparte al backend.
export function organismosPendientesSeparata(fase) {
  const tramitesPorId = new Map((fase.tramites || []).map((t) => [t.id, t]))
  return (fase.organismos || []).filter((org) => {
    if (org.via !== 'consulta') return false
    return !(org.tramite_ids || []).some((tid) => {
      const t = tramitesPorId.get(tid)
      return t && t.tipo_codigo === 'CONSULTA_SEPARATA'
    })
  })
}

// Acción de fase CONSULTAS en modo edición (ADR-042 §C, #396 bloque 5): vive
// en la zona de acciones, junto a las demás — resultado_fase_id/documento_
// resultado_id de esta fase siguen editándose igual que en cualquier otra.
// Oculto sin organismos pendientes: el botón no tiene nada útil que decir.
export function AccionesFaseConsultas({ nodo }) {
  const enviarConsultas = useArbolStore((s) => s.enviarConsultas)
  const enviando = useArbolStore((s) => s.enviandoConsultas)
  const pendientes = organismosPendientesSeparata(nodo)
  if (pendientes.length === 0) return null
  return (
    <div className="mb-3">
      <button type="button" className="btn btn-sm btn-primary"
              disabled={enviando} onClick={enviarConsultas}>
        {enviando ? 'Enviando…' : `📤 Enviar consultas pendientes (${pendientes.length})`}
      </button>
    </div>
  )
}

// Cumplimiento del plazo de resolver (#947, ADR-049 §F): el botón de la fase
// finalizadora. Mismo gesto que el fin de instrucción —siempre activo, nunca un
// error—, pero la respuesta no es un informe propio: es la vista HTML del
// certificado, la misma para el borrador calculado (qué documento se citaría, o qué
// falta) y para el emitido, que se abre en el modal grande. Por eso aquí no hay
// modal que montar (a diferencia de ModalInformeFinInstruccion).
//
// Aparece con la fase abierta y también cerrada: emitir con la fase cerrada se
// permite (sella lo que ADR-036 ya sella); deshacer, no, y el backend lo explica.
export function CertCumplimientoFase() {
  const detalle      = useArbolStore((s) => s.detalle)
  const certificando = useArbolStore((s) => s.certificandoCumplimiento)
  const certificar   = useArbolStore((s) => s.certificarCumplimiento)

  const cert = detalle && detalle.cert_cumplimiento
  if (!cert) return null

  if (cert.emitido) return <SelloCumplimiento cert={cert} />

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-light mb-3">
      <span className="small">
        <i className="bi bi-hourglass-split me-1" />
        <strong>Cumplimiento del plazo sin certificar.</strong> El plazo de resolver de
        los actos de esta fase se calcula en cada lectura desde la notificación al titular.
      </span>
      <span className="small text-muted">
        Si consta la notificación, el certificado se emite en el acto y fija el documento
        que la acredita; si no, verá qué falta y no se creará ningún documento.
      </span>
      <button type="button" className="btn btn-sm btn-primary"
              disabled={certificando} onClick={certificar}>
        {certificando ? 'Revisando…' : '📜 Certificar el cumplimiento'}
      </button>
    </div>
  )
}

// El sello del cumplimiento, con su salida (#947). Mismo esquema que
// SelloInstruccion: el estado, qué implica, y el deshacer plegado — el estado
// normal es que el sello se quede puesto, y desplegarlo es ya parte del acto.
function SelloCumplimiento({ cert }) {
  const [abierto, setAbierto] = React.useState(false)
  const [justificacion, setJustificacion] = React.useState('')
  const deshaciendo = useArbolStore((s) => s.deshaciendoCumplimiento)
  const deshacer    = useArbolStore((s) => s.deshacerCumplimiento)

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border border-success-subtle bg-success-subtle mb-3">
      <span className="small">
        <i className="bi bi-patch-check-fill me-1" />
        <strong>Cumplimiento certificado.</strong> El plazo de resolver de los actos de
        esta fase se lee del certificado.
      </span>
      <span className="small text-muted">
        Mientras conste, el documento que cita no puede modificarse, desvincularse ni
        borrarse. El resto de la notificación sigue abierta a lo que llegue después.
      </span>
      <button type="button" className="btn btn-sm btn-outline-success align-self-start"
              onClick={() => window.AppModalLarge && window.AppModalLarge.open(
                cert.enlace_vista, { title: 'Certificado de cumplimiento de la fase' })}>
        <i className="bi bi-eye me-1" />Ver el certificado
      </button>

      {!abierto ? (
        <button type="button" className="btn btn-sm btn-link text-danger p-0 text-start"
                onClick={() => setAbierto(true)}>
          El documento citado no es el correcto: deshacer el certificado
        </button>
      ) : (
        <>
          <span className="small text-muted">
            Se borrará el certificado y el plazo volverá a calcularse. Solo con la fase
            abierta. Queda registrado en bitácora, con el documento que citaba.
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
            <button type="button" className="btn btn-sm btn-danger"
                    disabled={deshaciendo || !justificacion.trim()}
                    onClick={() => deshacer(justificacion.trim())}>
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

// Frase del cierre irreversible (D5). La compara también el backend
// (`cert_cierre_fase.FRASE_CONFIRMACION`): si se cambia aquí, cambiarla allí.
const FRASE_CIERRE_FINALIZADORA = 'cerrar finalizadora'

// Cierre de la fase finalizadora (#956, ADR-049 §F): se cierra con su certificado de
// cierre, no eligiendo un documento en el editor (D6). Junto a «Cumplimiento del
// plazo», con el mismo gesto: el botón pregunta y, si no falta nada, cierra; si
// falta, abre el informe con lo que falta y no crea nada. «Ver cómo va» abre ese
// mismo informe sin intentar cerrar.
//
// Emitido, solo queda verlo: reabrir la fase —que en una finalizadora es deshacer el
// certificado— sigue siendo ReabrirFase, sin cambios de interfaz.
export function CierreFase({ nodo }) {
  const detalle   = useArbolStore((s) => s.detalle)
  const cerrando  = useArbolStore((s) => s.cerrandoFase)
  const solicitar = useArbolStore((s) => s.solicitarCierreFase)

  const cert = detalle && detalle.cert_cierre
  if (!cert) return null

  const verVista = () => window.AppModalLarge && window.AppModalLarge.open(
    cert.enlace_vista, { title: 'Certificado de cierre de la fase' })

  // Cerrada antes de #956 con un documento del pool: no hay certificado que ver, y
  // para cerrarla con él hay que reabrirla (ReabrirFase, debajo).
  if (!cert.emitido && nodo && nodo.estado === 'FINALIZADA') {
    return (
      <div className="small text-muted px-2 py-2 rounded border bg-light mb-3">
        <i className="bi bi-info-circle me-1" />
        Esta fase se cerró antes de existir el certificado de cierre, con un documento
        de resultado. Para cerrarla con su certificado, reábrala.
      </div>
    )
  }

  if (cert.emitido) {
    return (
      <div className="d-flex flex-column gap-2 px-2 py-2 rounded border border-success-subtle bg-success-subtle mb-3">
        <span className="small">
          <i className="bi bi-lock-fill me-1" />
          <strong>Fase cerrada con su certificado de cierre.</strong> Consta hecho todo
          lo obligatorio, incluida la notificación al titular.
        </span>
        <button type="button" className="btn btn-sm btn-outline-success align-self-start"
                onClick={verVista}>
          <i className="bi bi-eye me-1" />Ver el certificado
        </button>
      </div>
    )
  }

  return (
    <div className="d-flex flex-column gap-2 px-2 py-2 rounded border bg-light mb-3">
      <span className="small">
        <i className="bi bi-flag me-1" />
        <strong>Cierre de la fase.</strong> Se cierra con su certificado de cierre, que
        exige el resultado fijado, los trámites completos y el cumplimiento certificado.
      </span>
      <span className="small text-muted">
        Si no falta nada, la fase se cierra en el acto; si falta algo, verá qué es y no
        se creará ningún documento. Los escapes se hacen en la tarea o el trámite, no aquí.
      </span>
      {cert.cierra_solicitud && (
        <span className="small text-danger">
          <i className="bi bi-exclamation-octagon me-1" />
          Cerrarla deja la solicitud resuelta: el cierre será irreversible.
        </span>
      )}
      <div className="d-flex gap-2">
        <button type="button" className="btn btn-sm btn-primary"
                disabled={cerrando} onClick={solicitar}>
          {cerrando ? 'Revisando…' : '🔒 Cerrar la fase'}
        </button>
        <button type="button" className="btn btn-sm btn-outline-secondary"
                disabled={cerrando} onClick={verVista}>
          Ver cómo va
        </button>
      </div>
    </div>
  )
}

// Las dos confirmaciones del cierre (D5), en el mismo modal reutilizable: normal si
// la solicitud sigue abierta después (se puede reabrir), con la frase escrita si el
// cierre la deja resuelta y ya no hay vuelta atrás dentro de BDDAT.
export function ModalConfirmacionCierre() {
  const modo     = useArbolStore((s) => s.confirmacionCierre)
  const cerrando = useArbolStore((s) => s.cerrandoFase)
  const cerrar   = useArbolStore((s) => s.cerrarFase)
  const cancelar = useArbolStore((s) => s.cancelarCierreFase)

  const irreversible = modo === 'frase'
  return (
    <ModalConfirmacionFrase
      abierto={modo !== null}
      titulo={irreversible ? 'Cerrar la fase y resolver la solicitud' : 'Cerrar la fase'}
      frase={irreversible ? FRASE_CIERRE_FINALIZADORA : null}
      textoAccion="Cerrar la fase"
      variante={irreversible ? 'danger' : 'primary'}
      enviando={cerrando}
      onConfirmar={(frase) => cerrar(frase)}
      onCancelar={cancelar}
    >
      {irreversible ? (
        <>
          <p className="mb-2">
            No falta nada: la fase puede cerrarse. Al hacerlo la solicitud queda
            <strong> resuelta</strong> y, como la resolución ya está notificada,
            <strong> ninguna de sus fases podrá reabrirse</strong> dentro de BDDAT.
          </p>
          <p className="mb-0 text-muted">
            Cualquier corrección posterior exigirá un acto administrativo expreso
            (revocación, rectificación…), fuera de este flujo.
          </p>
        </>
      ) : (
        <p className="mb-0">
          Se revisará la fase y, si no falta nada, quedará cerrada con su certificado
          de cierre. Si falta algo, verá qué es y no se cerrará. Podrá reabrirla después,
          con justificación.
        </p>
      )}
    </ModalConfirmacionFrase>
  )
}
