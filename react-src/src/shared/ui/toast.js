// Thin wrapper sobre window.mostrar_toast (#521).
// La implementación real está en app/static/js/toast.js.
export function showToast(mensaje, categoria = 'info') {
  window.mostrar_toast(categoria, mensaje)
}
