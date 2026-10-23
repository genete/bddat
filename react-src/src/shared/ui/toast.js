// Thin wrapper sobre window.mostrar_toast (#521).
// La implementación real está en app/static/js/toast.js.
export function showToast(mensaje, categoria = 'info') {
  window.mostrar_toast(categoria, mensaje)
}

// Los avisos de una misma acción (#1038). Con uno, un toast como siempre. Con varios, un solo toast que
// dice cuántos son y cada aviso como línea propia del panel Avisos (la campana), donde se leen enteros, a
// su ritmo y con el contador de no leídos: un toast caduca a los 8 s y varios apilados tapan la pantalla.
// Se registran en orden inverso, porque el panel pone arriba lo último y así quedan en el orden en que
// se dieron, justo debajo del resumen. Sin el panel (la isla suelta, sin el shell), un toast por aviso.
export function showAvisos(avisos, categoria = 'warning') {
  if (avisos.length <= 1 || !window.DockBuffer) {
    avisos.forEach((a) => showToast(a, categoria))
    return
  }
  const alReves = [...avisos].reverse()
  alReves.forEach((a) => window.DockBuffer.push(categoria, a))
  showToast(`${avisos.length} avisos sobre este cambio: léelos en el panel Avisos (la campana)`, categoria)
}
