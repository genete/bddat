// Wrapper de fetch para las islas React (#499, ADR-015 §3).
//
// - Envía la cookie de sesión Flask (credentials: 'same-origin').
// - 401 → toast + redirección a /auth/login.
// - 403 → toast de permiso denegado.
// - POST/PUT/DELETE → añade X-CSRFToken leyéndolo del meta tag csrf-token.
//
// Nota CSRF (#499): el backend aún no tiene Flask-WTF/CSRFProtect. El meta tag de
// base_app.html emite token vacío hasta que se instale (ADR-015 §3: "setup mínimo
// cuando llegue la primera API mutante desde React"). Mientras esté vacío, el
// header no se añade; el cliente ya queda preparado para cuando exista el token.

import { showToast } from './ui/toast.js'

export class ApiError extends Error {
  constructor(status, message, payload = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

const METODOS_SIN_CSRF = new Set(['GET', 'HEAD', 'OPTIONS'])

function csrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]')
  return meta ? meta.getAttribute('content') : ''
}

async function request(url, { method = 'GET', body, headers = {}, ...rest } = {}) {
  const m = method.toUpperCase()
  const opts = {
    method: m,
    credentials: 'same-origin', // cookie de sesión Flask
    headers: { Accept: 'application/json', ...headers },
    ...rest,
  }

  if (body !== undefined && body !== null) {
    if (typeof FormData !== 'undefined' && body instanceof FormData) {
      opts.body = body // sin Content-Type explícito: el navegador fija el boundary multipart
    } else {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = typeof body === 'string' ? body : JSON.stringify(body)
    }
  }

  if (!METODOS_SIN_CSRF.has(m)) {
    const token = csrfToken()
    if (token) opts.headers['X-CSRFToken'] = token
  }

  const resp = await fetch(url, opts)

  if (resp.status === 401) {
    showToast('Tu sesión ha caducado. Redirigiendo al inicio de sesión…', 'warning')
    window.location = '/auth/login'
    throw new ApiError(401, 'No autenticado')
  }
  if (resp.status === 403) {
    showToast('No tienes permisos para realizar esta acción.', 'danger')
    throw new ApiError(403, 'Prohibido')
  }
  if (!resp.ok) {
    let payload = null
    try { payload = await resp.json() } catch { /* sin cuerpo JSON */ }
    const msg = (payload && payload.error) || resp.statusText || `HTTP ${resp.status}`
    throw new ApiError(resp.status, msg, payload)
  }

  if (resp.status === 204) return null
  const ct = resp.headers.get('Content-Type') || ''
  return ct.includes('application/json') ? resp.json() : resp.text()
}

export const api = {
  get:    (url, opts)       => request(url, { ...opts, method: 'GET' }),
  post:   (url, body, opts) => request(url, { ...opts, method: 'POST', body }),
  put:    (url, body, opts) => request(url, { ...opts, method: 'PUT', body }),
  patch:  (url, body, opts) => request(url, { ...opts, method: 'PATCH', body }),
  delete: (url, opts)       => request(url, { ...opts, method: 'DELETE' }),
}
