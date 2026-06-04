// Toast imperativo reutilizable (#499, ADR-015).
//
// Reutiliza el .toast-container y el bundle JS de Bootstrap (window.bootstrap)
// que base_app.html ya carga desde el CDN JdA. Mismo formato visual que los
// toasts de flash de Jinja (iconos + prefijo por categoría).
//
// Uso desde JS:    import { showToast } from '.../ui/toast.js'; showToast('Hecho', 'success')
// Uso desde React: <Toast mensaje="Hecho" categoria="success" />  (ui/Toast.jsx)

const ESTILOS = {
  success: { icon: 'fas fa-check-circle',        label: 'Correcto' },
  danger:  { icon: 'fas fa-exclamation-circle',  label: 'Error' },
  warning: { icon: 'fas fa-exclamation-triangle', label: 'Atención' },
  info:    { icon: 'fas fa-info-circle',         label: 'Información' },
}

function getContainer() {
  let c = document.querySelector('.toast-container')
  if (!c) {
    c = document.createElement('div')
    c.className = 'toast-container position-fixed bottom-0 end-0 p-3'
    document.body.appendChild(c)
  }
  return c
}

export function showToast(mensaje, categoria = 'info') {
  const { icon, label } = ESTILOS[categoria] || ESTILOS.info

  const el = document.createElement('div')
  el.className = `toast toast-${categoria}`
  el.setAttribute('role', 'alert')
  el.setAttribute('aria-live', 'assertive')
  el.setAttribute('aria-atomic', 'true')
  el.dataset.bsAutohide = 'true'
  el.dataset.bsDelay = '8000'

  const fila = document.createElement('div')
  fila.className = 'd-flex align-items-center p-3'

  const cuerpo = document.createElement('div')
  cuerpo.className = 'flex-grow-1'
  const i = document.createElement('i')
  i.className = `${icon} me-2`
  const strong = document.createElement('strong')
  strong.textContent = `${label}:`
  // mensaje como nodo de texto (evita inyección HTML)
  cuerpo.append(i, strong, ' ', document.createTextNode(mensaje))

  const cerrar = document.createElement('button')
  cerrar.type = 'button'
  cerrar.className = 'btn-close ms-3'
  cerrar.setAttribute('data-bs-dismiss', 'toast')
  cerrar.setAttribute('aria-label', 'Cerrar')

  fila.append(cuerpo, cerrar)
  el.appendChild(fila)
  getContainer().appendChild(el)

  const bs = window.bootstrap
  if (bs && bs.Toast) {
    el.classList.add('showing')
    const t = new bs.Toast(el)
    t.show()
    setTimeout(() => el.classList.remove('showing'), 300)
    el.addEventListener('hide.bs.toast',   () => el.classList.add('hide'))
    el.addEventListener('hidden.bs.toast', () => el.remove())
    el.addEventListener('click', e => { if (!e.target.closest('.btn-close')) t.hide() })
  } else {
    // Fallback si Bootstrap no estuviera cargado en la página.
    el.classList.add('show')
    setTimeout(() => el.remove(), 8000)
  }
  return el
}
