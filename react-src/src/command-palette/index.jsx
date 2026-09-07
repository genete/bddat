// Entry de la isla "command-palette" (#532, ADR-018).
// Isla GLOBAL: el contenedor lo pone el shell (base_app.html), no una vista.
//
// Stub JS plano (#563): sin React ni cmdk en este módulo, así que el bundle
// que se carga en TODAS las páginas autenticadas no arrastra ese peso (~46 KB
// gzip de cmdk + el chunk de React) solo por tener la isla montada. Escucha
// los tres disparadores (Ctrl/Cmd+K, "/", clic en el buscador del topbar) con
// listeners planos; a la primera activación hace import() dinámico del
// componente real y lo monta ya abierto. Vite separa ese import en su propio
// chunk, descargado solo entonces — el resto de páginas nunca lo piden.
function focoEsEditable() {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable
}

const topbar = document.querySelector('[data-app-shell-search]')
let activando = null

function activar() {
  if (activando) return activando
  // A partir de aquí el componente real trae sus propios listeners
  // (useEffect, mismo criterio que antes de #563): los del stub sobran.
  document.removeEventListener('keydown', onKeydown)
  if (topbar) topbar.removeEventListener('mousedown', onTopbarMousedown)

  activando = Promise.all([
    import('../shared/mountIsland.js'),
    import('./CommandPalette.jsx'),
  ]).then(([{ mountIsland }, { default: CommandPalette }]) => {
    mountIsland('command-palette', CommandPalette, { abrirInicial: true })
  })
  return activando
}

function onKeydown(e) {
  const ctrl = e.ctrlKey || e.metaKey
  if (ctrl && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault()
    activar()
  } else if (e.key === '/' && !focoEsEditable()) {
    e.preventDefault()
    activar()
  }
}

function onTopbarMousedown(e) {
  e.preventDefault()
  activar()
}

document.addEventListener('keydown', onKeydown)
if (topbar) topbar.addEventListener('mousedown', onTopbarMousedown)
