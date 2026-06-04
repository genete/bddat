// Implementación única del sistema de toasts BDDAT (#521).
// Expone window.mostrar_toast(tipo, mensaje).
// Cargado en base_app.html tras Bootstrap; todos los contextos vanilla lo usan directamente.
// El módulo React (react-src/shared/ui/toast.js) actúa como thin wrapper.
(function () {
  'use strict';

  var ESTILOS = {
    success: { icon: 'fas fa-check-circle',         label: 'Correcto'     },
    danger:  { icon: 'fas fa-exclamation-circle',   label: 'Error'        },
    warning: { icon: 'fas fa-exclamation-triangle', label: 'Atención'     },
    info:    { icon: 'fas fa-info-circle',          label: 'Información'  },
  };

  window.mostrar_toast = function (tipo, mensaje) {
    if (window.DockBuffer) window.DockBuffer.push(tipo, mensaje);

    var estilo    = ESTILOS[tipo] || ESTILOS.info;
    var container = document.querySelector('.toast-container');
    if (!container || !window.bootstrap) return;

    var el = document.createElement('div');
    el.className = 'toast toast-' + tipo;
    el.setAttribute('role', 'alert');
    el.setAttribute('aria-live', 'assertive');
    el.setAttribute('aria-atomic', 'true');
    el.dataset.bsAutohide = 'true';
    el.dataset.bsDelay    = '8000';

    var fila   = document.createElement('div');
    fila.className = 'd-flex align-items-center p-3';

    var cuerpo = document.createElement('div');
    cuerpo.className = 'flex-grow-1';
    var i      = document.createElement('i');
    i.className = estilo.icon + ' me-2';
    var strong = document.createElement('strong');
    strong.textContent = estilo.label + ':';
    cuerpo.appendChild(i);
    cuerpo.appendChild(strong);
    cuerpo.appendChild(document.createTextNode(' ' + mensaje));

    var cerrar = document.createElement('button');
    cerrar.type = 'button';
    cerrar.className = 'btn-close ms-3';
    cerrar.setAttribute('data-bs-dismiss', 'toast');
    cerrar.setAttribute('aria-label', 'Cerrar');

    fila.appendChild(cuerpo);
    fila.appendChild(cerrar);
    el.appendChild(fila);
    container.appendChild(el);

    el.classList.add('showing');
    var t = new bootstrap.Toast(el);
    t.show();
    setTimeout(function () { el.classList.remove('showing'); }, 300);
    el.addEventListener('hide.bs.toast',   function () { el.classList.add('hide'); });
    el.addEventListener('hidden.bs.toast', function () { el.remove(); });
    el.addEventListener('click',           function (e) {
      if (!e.target.closest('.btn-close')) { t.hide(); }
    });
  };
}());
