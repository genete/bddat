// Thin wrapper sobre window.quitar_comprimidos (#1007, ADR-050 §E).
// La implementación real está en app/static/js/subida-comprimidos.js.
export function quitarComprimidos(input) {
  return window.quitar_comprimidos(input)
}
