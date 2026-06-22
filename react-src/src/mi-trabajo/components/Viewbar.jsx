// Viewbar.jsx — título + conmutador de modo de "Mi trabajo" (#501).
// Se portala sobre la viewbar del shell (app-viewbar__*), igual que el árbol.
// Estándar JdA/Bootstrap: btn-group con btn-outline-primary + iconos FontAwesome
// (nada de emoji, que quedaban fuera de lugar respecto al CDN de la Junta).
import React from 'react'

const TABS = [
  { id: 'cola',  label: 'Tareas pendientes', icon: 'fa-tasks' },
  { id: 'subir', label: 'Subir documento',   icon: 'fa-upload' },
]

export default function Viewbar({ tab, onTab }) {
  return (
    <>
      <div className="app-viewbar__title">
        <i className="fas fa-inbox me-2" aria-hidden="true" />
        <strong>Mi trabajo</strong>
      </div>
      <div className="app-viewbar__spacer" />
      <div className="btn-group btn-group-sm" role="group" aria-label="Modo de Mi trabajo">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`btn btn-outline-primary${tab === t.id ? ' active' : ''}`}
            aria-pressed={tab === t.id}
            onClick={() => onTab(t.id)}
          >
            <i className={`fas ${t.icon} me-1`} aria-hidden="true" />
            {t.label}
          </button>
        ))}
      </div>
    </>
  )
}
