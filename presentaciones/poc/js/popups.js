/* popups.js — Sistema genérico de popups para presentación Reveal.js
 *
 * Uso: cualquier elemento con data-popup="X" abre el div #popup-X.
 * No requiere clase específica — funciona en cualquier slide.
 *
 * Dependencias: tema-ja.css (clases ja-popup-*)
 */
(function () {
  // --- Crear infraestructura una sola vez ---
  var overlay = document.createElement('div');
  overlay.className = 'ja-popup-overlay';
  overlay.innerHTML =
    '<div class="ja-popup-box">' +
      '<button class="ja-popup-cerrar" aria-label="Cerrar">&times;</button>' +
      '<div class="ja-popup-contenido"></div>' +
    '</div>';
  document.body.appendChild(overlay);

  var box      = overlay.querySelector('.ja-popup-box');
  var contenido = overlay.querySelector('.ja-popup-contenido');
  var btnCerrar = overlay.querySelector('.ja-popup-cerrar');

  // --- Escala de Reveal: lee el transform real de .slides ---
  function getRevealScale() {
    var el = document.querySelector('.reveal .slides');
    if (!el) return 1;
    var t = window.getComputedStyle(el).transform;
    var m = t && t.match(/matrix\(([^,]+)/);
    return m ? parseFloat(m[1]) : 1;
  }

  function aplicarEscala() {
    var s = getRevealScale();
    box.style.transform = 'scale(' + s + ')';
    box.style.transformOrigin = 'center center';
  }

  // --- Abrir / cerrar ---
  function abrirPopup(nombre) {
    var data = document.getElementById('popup-' + nombre);
    if (!data) return;
    var esImg = data.classList.contains('img-popup-data');
    contenido.innerHTML = data.innerHTML;
    if (esImg) {
      box.classList.add('img-popup');
      var wrap = contenido.querySelector('.imgpopup-wrap');
      var img  = wrap && wrap.querySelector('img');
      if (wrap && img && typeof makePanzoom === 'function') {
        makePanzoom(wrap, img);
      }
    } else {
      box.classList.remove('img-popup');
    }
    aplicarEscala();
    overlay.classList.add('activo');
  }

  function cerrarPopup() {
    overlay.classList.remove('activo');
    box.classList.remove('img-popup');
  }

  // --- Eventos ---

  // Trigger: cualquier elemento con data-popup (capture para preceder a Reveal)
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest('[data-popup]');
    if (trigger) {
      e.stopPropagation();
      abrirPopup(trigger.dataset.popup);
    }
  }, true);

  // Cerrar en clic fuera del box
  overlay.addEventListener('click', function (e) {
    if (!box.contains(e.target)) cerrarPopup();
  });

  // Botón ×
  btnCerrar.addEventListener('click', cerrarPopup);

  // ESC
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') cerrarPopup();
  });

  // Reescalar si la ventana cambia de tamaño con el popup abierto
  window.addEventListener('resize', function () {
    if (overlay.classList.contains('activo')) aplicarEscala();
  });

  // Cerrar al cambiar de slide
  if (window.Reveal) {
    Reveal.on('slidechanged', cerrarPopup);
  }
})();
