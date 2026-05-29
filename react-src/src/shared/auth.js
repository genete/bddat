// Lectura de usuario / permisos / rol activo desde el HTML inicial (#499, ADR-015 §3).
//
// El template Jinja inyecta el contexto con {{ user_ctx_attrs() }} en el
// contenedor de la isla:
//   <div data-react-island="..."
//        data-user='{"id":1,"siglas":"CLG","nombre_completo":"..."}'
//        data-permisos='["acceder_expediente","editar_expediente"]'
//        data-rol="TRAMITADOR">
//
// No hay auth en cliente: la sesión Flask manda. Esto solo sirve para condicionar
// la UI (mostrar/ocultar botones). La autorización real la imponen los decoradores
// del backend en cada ruta/API.

function ctxEl() {
  // El contenedor de isla lleva los data-attributes; si no, se cae a <body>.
  return document.querySelector('[data-user]') || document.body
}

function parseJSON(attr, fallback) {
  const raw = ctxEl().getAttribute(attr)
  if (!raw) return fallback
  try {
    return JSON.parse(raw)
  } catch {
    console.warn(`[auth] ${attr} no es JSON válido`)
    return fallback
  }
}

export function getUser() {
  return parseJSON('data-user', null)
}

export function getPermisos() {
  return parseJSON('data-permisos', [])
}

export function getRolActivo() {
  return ctxEl().getAttribute('data-rol') || null
}

export function tienePermiso(nombre) {
  return getPermisos().includes(nombre)
}
