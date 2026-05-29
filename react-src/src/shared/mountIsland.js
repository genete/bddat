import React from 'react'
import { createRoot } from 'react-dom/client'

// Punto de montaje común de todas las islas (#499, ADR-015).
//
// Convención: el template Jinja coloca el contenedor con
//   <div data-react-island="<nombre>" {{ user_ctx_attrs() }}>...</div>
// y la isla, al cargar su bundle, se auto-monta dentro de ese contenedor.
// No expone globals ni requiere <script> inline en el template.
export function mountIsland(nombre, Component) {
  const el = document.querySelector(`[data-react-island="${nombre}"]`)
  if (!el) {
    // Isla cargada en una página sin su contenedor: no es un error fatal,
    // solo no hay nada que montar (p. ej. bundle compartido entre vistas).
    console.warn(`[isla:${nombre}] No se encontró [data-react-island="${nombre}"]`)
    return
  }
  createRoot(el).render(
    React.createElement(React.StrictMode, null, React.createElement(Component)),
  )
}
