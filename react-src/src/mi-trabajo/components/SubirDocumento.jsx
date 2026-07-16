// SubirDocumento.jsx — alta de documentos al pool del expediente (#501, ADR-017 §4).
//
// La subida multipart (#666) vive en el gestor de documentos del pool
// (pool_documentos.html), junto a "elegir del servidor" y "URL externa". Esta
// pestaña solo aporta lo que faltaba: ELEGIR el expediente (reutiliza /api/search,
// el de Ctrl+K) y entrar a su gestor — un único método, un único sitio (feedback #4).
import React, { useRef, useState } from 'react'
import { api } from '../../shared/api.js'

export default function SubirDocumento() {
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState([])
  const [exp, setExp] = useState(null)        // {id, label}
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

  return (
    <div className="p-3" style={{ maxWidth: 760 }}>
      <label className="form-label fw-semibold">Expediente destino</label>
      <div className="position-relative mb-3">
        <input className="form-control" placeholder="Nº AT, titular o proyecto…"
               value={q} onChange={(e) => buscar(e.target.value)} />
        {resultados.length > 0 && (
          <div className="list-group position-absolute w-100 shadow" style={{ zIndex: 1050 }}>
            {resultados.map((r) => (
              <button type="button" key={r.id}
                      className="list-group-item list-group-item-action py-2"
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
        <div className="card tabla-bloque">
          <div className="card-body d-flex justify-content-between align-items-center gap-3">
            <div>
              <h6 className="mb-1"><i className="fas fa-folder-open me-1" /> {exp.label}</h6>
              <p className="text-secondary small mb-0">
                Gestor de documentos del expediente: subir ficheros del servidor corporativo
                (descargas de BandeJA, carpetas…) y registrar URLs externas (BOE, BOJA, Notifica…).
              </p>
            </div>
            <a className="btn btn-primary flex-shrink-0" href={`/expedientes/${exp.id}/documentos`}>
              Abrir gestor <i className="fas fa-arrow-right ms-1" />
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
