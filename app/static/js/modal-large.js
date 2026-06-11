/**
 * modal-large.js — AppModalLarge: modal grande de shell (ADR-023 §6 / #534).
 *
 * API pública (window.AppModalLarge):
 *   open(fragmentUrl, { title, onSaved })
 *     Carga el fragmento, re-ejecuta sus <script> y muestra el modal.
 *     onSaved por defecto: AppInspector.refresh().
 *     Se llama al cerrar el modal (hidden.bs.modal), no al guardar sub-ítems.
 *   close()    — cierra el modal
 *   refresh()  — re-fetcha el fragmentUrl actual (refresca tabla tras mutación)
 *
 * Formularios con [data-modal-form] dentro del modal son interceptados:
 *   POST XHR → JSON { ok, message?, errors? }
 *   ok=true  → refresh()  (modal permanece abierto, tabla actualizada)
 *   ok=false → muestra errores en [data-modal-errors] del formulario
 */
(function () {
  'use strict';

  var MODAL_ID = 'app-modal-large';
  var _fragUrl = null;
  var _onSaved = null;

  // ── Crear el modal en el DOM (una sola vez) ───────────────────────────────

  function _getOrCreate() {
    var el = document.getElementById(MODAL_ID);
    if (el) return el;

    el = document.createElement('div');
    el.className = 'modal fade modal-app-xl';
    el.id        = MODAL_ID;
    el.tabIndex  = -1;
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('role',       'dialog');
    el.setAttribute('aria-labelledby', MODAL_ID + '-title');
    el.innerHTML =
      '<div class="modal-dialog modal-dialog-scrollable">' +
        '<div class="modal-content">' +
          '<div class="modal-header card-header-accent">' +
            '<h5 class="modal-title fw-semibold" id="' + MODAL_ID + '-title"></h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>' +
          '</div>' +
          '<div class="modal-body" id="' + MODAL_ID + '-body"></div>' +
        '</div>' +
      '</div>';

    document.body.appendChild(el);

    // Al cerrar el modal (X, backdrop, ESC) → llamar onSaved y limpiar estado
    el.addEventListener('hidden.bs.modal', function () {
      var cb = _onSaved;
      _onSaved = null;
      _fragUrl = null;
      if (cb) cb();
    });

    return el;
  }

  // ── Título ─────────────────────────────────────────────────────────────────

  function _setTitle(title) {
    var el = document.getElementById(MODAL_ID + '-title');
    if (el) el.textContent = title || '';
  }

  // ── Inyectar HTML + re-ejecutar scripts ────────────────────────────────────

  function _inject(html) {
    var body = document.getElementById(MODAL_ID + '-body');
    if (!body) return;
    body.innerHTML = html;
    // Re-ejecutar scripts del fragmento (innerHTML no los activa)
    body.querySelectorAll('script').forEach(function (orig) {
      var s = document.createElement('script');
      if (orig.src) {
        s.src = orig.src;
      } else {
        s.textContent = orig.textContent;
      }
      orig.parentNode.replaceChild(s, orig);
    });
  }

  // ── Cargar fragmento ───────────────────────────────────────────────────────

  function _load(url) {
    var body = document.getElementById(MODAL_ID + '-body');
    if (body) {
      body.innerHTML =
        '<div class="p-4 text-center text-secondary small">' +
        '<i class="fas fa-spinner fa-spin me-2"></i>Cargando...</div>';
    }
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (html) {
        _inject(html);
      })
      .catch(function () {
        var b = document.getElementById(MODAL_ID + '-body');
        if (b) b.innerHTML = '<div class="p-3 text-danger small">No se pudo cargar el contenido.</div>';
      });
  }

  // ── API pública ────────────────────────────────────────────────────────────

  function open(fragmentUrl, opts) {
    opts    = opts || {};
    _fragUrl = fragmentUrl;
    _onSaved = opts.onSaved || function () {
      if (window.AppInspector) window.AppInspector.refresh();
    };

    var el = _getOrCreate();
    _setTitle(opts.title || '');
    _load(fragmentUrl);
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  function close() {
    var el = document.getElementById(MODAL_ID);
    if (el) bootstrap.Modal.getOrCreateInstance(el).hide();
  }

  function refresh() {
    if (_fragUrl) _load(_fragUrl);
  }

  // ── Interceptar submits [data-modal-form] dentro del modal ─────────────────

  document.addEventListener('submit', function (e) {
    var modal = document.getElementById(MODAL_ID);
    if (!modal || !modal.contains(e.target)) return;
    var form = e.target.closest('form[data-modal-form]');
    if (!form) return;

    e.preventDefault();

    fetch(form.action, {
      method:  'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body:    new FormData(form),
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (json.ok) {
          if (window.mostrar_toast) window.mostrar_toast('success', json.message || 'Guardado correctamente.');
          refresh();
        } else {
          var errBox = form.querySelector('[data-modal-errors]');
          if (errBox) {
            errBox.innerHTML = (json.errors || []).map(function (m) {
              return '<div>' + m + '</div>';
            }).join('');
            errBox.style.display = (json.errors && json.errors.length) ? '' : 'none';
            errBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          } else if (window.mostrar_toast) {
            window.mostrar_toast('danger', (json.errors || ['Error al guardar.']).join(' '));
          }
        }
      })
      .catch(function () {
        if (window.mostrar_toast) window.mostrar_toast('danger', 'Error al guardar. Inténtalo de nuevo.');
      });
  });

  // ── Botón [data-modal-large-close] dentro del modal ───────────────────────

  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-modal-large-close]')) close();
  });

  window.AppModalLarge = { open: open, close: close, refresh: refresh };

})();
