// Viewbar.jsx — título + tabs de "Mi trabajo" (#501). Se portala sobre la viewbar
// del shell. Solo clases Bootstrap (ADR-015).
import React from 'react'

const TABS = [
  { id: 'cola',  label: '📋 Cola' },
  { id: 'subir', label: '📤 Subir documento' },
]

export default function Viewbar({ tab, onTab }) {
  return (
    <div className="d-flex align-items-center gap-3 w-100">
      <span className="fw-semibold text-nowrap">
        <i className="fas fa-inbox me-1" /> Mi trabajo
      </span>
      <ul className="nav nav-pills gap-1 mb-0">
        {TABS.map((t) => (
          <li className="nav-item" key={t.id}>
            <button
              type="button"
              className={`nav-link py-1 px-2 ${tab === t.id ? 'active' : ''}`}
              onClick={() => onTab(t.id)}
            >
              {t.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
