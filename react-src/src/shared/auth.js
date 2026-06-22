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

// Permisos del árbol por tipo de nodo (ADR-017 §6 / #501). Frontera hoja/estructura:
// las tareas se gobiernan con gestionar_tareas (incluye ADMINISTRATIVO); la estructura
// (solicitud/fase/trámite) con gestionar_estructura_expediente; el expediente con
// editar_expediente. El backend impone lo mismo; esto solo oculta botones que darían 403.

export function puedeEditarNodo(tipo) {
  if (tipo === 'tarea') return tienePermiso('gestionar_tareas')
  if (tipo === 'expediente') return tienePermiso('editar_expediente')
  return tienePermiso('gestionar_estructura_expediente')  // solicitud / fase / tramite
}

export function puedeCrearHijoDe(tipoPadre) {
  // El permiso depende del tipo de HIJO: bajo trámite se crean tareas (hoja →
  // gestionar_tareas); bajo expediente/solicitud/fase se crea estructura.
  if (tipoPadre === 'tramite') return tienePermiso('gestionar_tareas')
  return tienePermiso('gestionar_estructura_expediente')
}
