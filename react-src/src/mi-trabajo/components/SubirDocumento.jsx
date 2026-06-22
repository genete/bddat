// SubirDocumento.jsx — subida puntual al pool del expediente (#501, ADR-017 §4).
//
// No hay subida multipart en BDDAT: se reutiliza el flujo del pool ya existente.
//   - "URL externa" (BOE/BOJA/Notifica…) se registra inline → POST pool_registrar_url_externa.
//   - Ficheros del servidor → enlaza a la página de pool del expediente (explorador completo).
// El admin elige primero el expediente (reutiliza /api/search, el de Ctrl+K). El toast
// de confirmación muestra el AT destino para detectar de un vistazo un error de expediente.
// El histórico NO persiste: solo un log efímero de lo subido en esta sesión (hablado, #501).
import React, { useRef, useState } from 'react'
import { api } from '../../shared/api.js'
import { showToast } from '../../shared/ui/toast.js'

export default function SubirDocumento({ tiposDoc }) {
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState([])
  const [exp, setExp] = useState(null)           // {id, label}
  const [url, setUrl] = useState('')
  const [tipoDoc, setTipoDoc] = useState('')
  const [fecha, setFecha] = useState('')
  const [asunto, setAsunto] = useState('')
  const [registrando, setRegistrando] = useState(false)
  const [log, setLog] = useState([])             // efímero (sesión); no BD, no persiste
  const buscarTimer = useRef(null)

  const buscar = (texto) => {
    setQ(texto)
    setExp(null)
    clearTimeout(buscarTimer.current)
    if (texto.trim().length < 2) { setResultados([]); return }
    buscarTimer.current = setTimeout(async () => {
      try {
        const data = await api.get(
          `/api/search?tipos=expedientes&q=${encodeURIComponent(texto)}&limit=8`,
        )
        const grupo = (data.grupos || []).find((g) => g.tipo === 'expedientes')
        setResultados(grupo ? grupo.resultados : [])
      } catch {
        setResultados([])
      }
    }, 250)
  }

  const elegir = (r) => {
    setExp({ id: r.id, label: r.label })
    setResultados([])
    setQ(r.label)
  }

  const registrarUrl = async () => {
    if (!exp || !url.trim()) return
    setRegistrando(true)
    try {
      await api.post(`/expedientes/${exp.id}/documentos/url-externa`, {
        url: url.trim(),
        tipo_doc_id: tipoDoc || 1,
        fecha_administrativa: fecha || null,
        asunto: asunto.trim(),
      })
      showToast(`Documento registrado en ${exp.label}`, 'success')
      setLog((prev) => [
        { k: Date.now(), txt: `${exp.label} · ${asunto.trim() || url.trim()}` },
        ...prev,
      ])
      setUrl(''); setAsunto(''); setFecha(''); setTipoDoc('')
    } catch (e) {
      showToast(e.message || 'No se pudo registrar el documento', 'danger')
    } finally {
      setRegistrando(false)
    }
  }

  return (
    <div className="p-3" style={{ maxWidth: 760, overflowY: 'auto' }}>
      {/* Selector de expediente destino */}
      <label className="form-label fw-semibold">Expediente destino</label>
      <div className="position-relative mb-3">
        <input className="form-control" placeholder="Nº AT, titular o proyecto…"
               value={q} onChange={(e) => buscar(e.target.value)} />
        {resultados.length > 0 && (
          <div className="list-group position-absolute w-100 shadow-sm" style={{ zIndex: 5 }}>
            {resultados.map((r) => (
              <button type="button" key={r.id}
                      className="list-group-item list-group-item-action py-1"
                      onClick={() => elegir(r)}>
                <div className="fw-semibold small">{r.label}</div>
                {r.breadcrumb && (
                  <div className="text-secondary" style={{ fontSize: '.78em' }}>{r.breadcrumb}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {!exp ? (
        <p className="text-secondary small">Elige primero el expediente destino.</p>
      ) : (
        <>
          <div className="alert alert-light border py-2 px-3 small">
            Destino: <strong>{exp.label}</strong>
          </div>

          {/* Vía 1 — URL externa (inline) */}
          <div className="card mb-3">
            <div className="card-body">
              <h6 className="card-title"><i className="fas fa-link me-1" /> Añadir URL externa</h6>
              <p className="text-secondary small">
                BOE, BOJA, Notifica, sede electrónica… No se sube fichero; se registra el enlace.
              </p>
              <input className="form-control form-control-sm mb-2" placeholder="https://…"
                     value={url} onChange={(e) => setUrl(e.target.value)} />
              <div className="row g-2 mb-2">
                <div className="col-sm-6">
                  <select className="form-select form-select-sm" value={tipoDoc}
                          onChange={(e) => setTipoDoc(e.target.value)}>
                    <option value="">— Tipo de documento —</option>
                    {tiposDoc.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                  </select>
                </div>
                <div className="col-sm-6">
                  <input type="date" className="form-control form-control-sm"
                         value={fecha} onChange={(e) => setFecha(e.target.value)} />
                </div>
              </div>
              <input className="form-control form-control-sm mb-2" placeholder="Asunto (opcional)"
                     value={asunto} onChange={(e) => setAsunto(e.target.value)} />
              <button className="btn btn-primary btn-sm"
                      disabled={registrando || !url.trim()} onClick={registrarUrl}>
                <i className="fas fa-save me-1" /> Registrar URL
              </button>
            </div>
          </div>

          {/* Vía 2 — ficheros del servidor (reutiliza el explorador del pool) */}
          <div className="card mb-3">
            <div className="card-body d-flex justify-content-between align-items-center gap-3">
              <div>
                <h6 className="card-title mb-1"><i className="fas fa-server me-1" /> Ficheros del servidor</h6>
                <p className="text-secondary small mb-0">
                  Explorador del servidor corporativo (descargas de BandeJA, carpetas…).
                </p>
              </div>
              <a className="btn btn-outline-primary btn-sm flex-shrink-0"
                 href={`/expedientes/${exp.id}/documentos`}>
                Abrir explorador <i className="fas fa-arrow-right ms-1" />
              </a>
            </div>
          </div>
        </>
      )}

      {/* Log efímero de la sesión (no persiste) */}
      {log.length > 0 && (
        <div className="mt-3">
          <div className="fw-semibold small mb-1">Subido en esta sesión</div>
          <ul className="list-unstyled small mb-0">
            {log.map((l) => (
              <li key={l.k} className="text-secondary">
                <i className="fas fa-check text-success me-1" />{l.txt}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
