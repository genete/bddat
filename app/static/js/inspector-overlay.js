/**
 * inspector-overlay.js — API de shell para el inspector overlay (ADR-023 / #534).
 *
 * Expone window.AppInspector con los métodos:
 *   open({ selId, fragmentUrl })  — abre/swap; carga fragmento HTML si procede
 *                                   (parámetro title aceptado pero ignorado — sin cabecera)
 *   mountReact({ selId })         — abre sin tocar el body (islas React)
 *   close()                       — cierra; emite inspector:closed
 *   refresh()                     — re-fetch del último fragmentUrl
 *   setLocked(bool)               — backdrop bloqueante (modo edición)
 *   isOpen()                      — true si el panel está visible
 *   currentSel()                  — selId activo o null
 *
 * Eventos emitidos en document:
 *   inspector:opened  { detail: { selId } }
 *   inspector:swapped { detail: { selId } }
 *   inspector:closed  { detail: { selId } }  (selId = el que estaba activo)
 *   inspector:saved   { detail: { selId } }  (guardado de edición con éxito, #681)
 */
(function () {
  'use strict';

  var LS_WIDTH  = 'bddat.inspector.width';
  var MIN_WIDTH = 320;

  var _selId        = null;
  var _lastCache    = null;  // { selId, html } — retención del último fragmento de lectura
  var _editCache    = null;  // { selId, html } — caché del fragmento de edición
  var _lastFragUrl  = null;  // última fragmentUrl usada (para refresh)
  var _locked       = false;
  var _formDirty    = false;

  // ── Accesores DOM ─────────────────────────────────────────────────────────

  function getShell() { return document.querySelector('.app-shell'); }
  function getAside() { return document.getElementById('app-inspector'); }
  function getBody()  { return document.getElementById('app-inspector-body'); }

  // ── Estado ────────────────────────────────────────────────────────────────

  function isOpen() {
    var shell = getShell();
    return shell ? shell.classList.contains('is-inspector-open') : false;
  }

  function currentSel() { return _selId; }

  // ── Mostrar / ocultar panel ───────────────────────────────────────────────

  function _show() {
    var shell = getShell();
    if (shell) shell.classList.add('is-inspector-open');
  }

  function _hide() {
    var shell = getShell();
    if (shell) {
      shell.classList.remove('is-inspector-open');
      shell.classList.remove('is-inspector-locked');
    }
    _locked    = false;
    _formDirty = false;
  }

  // ── API pública ───────────────────────────────────────────────────────────

  function open(opts) {
    var selId      = opts.selId;
    var title      = opts.title || '';
    var fragmentUrl = opts.fragmentUrl || null;

    var wasOpen   = isOpen();
    var isSameId  = wasOpen && _selId === selId;
    var eventName = wasOpen ? 'inspector:swapped' : 'inspector:opened';

    _selId     = selId;
    _formDirty = false;
    _editCache = null;

    if (fragmentUrl) {
      _lastFragUrl = fragmentUrl;
      // Retención: mismo selId → no refetchear
      if (isSameId && _lastCache && _lastCache.selId === selId) {
        // contenido ya en el DOM, no hacer nada
      } else if (_lastCache && _lastCache.selId === selId) {
        var body = getBody();
        if (body) body.innerHTML = _lastCache.html;
      } else {
        _loadFragment(fragmentUrl, selId);
      }
    }

    _show();
    document.dispatchEvent(new CustomEvent(eventName, { detail: { selId: selId } }));
  }

  function mountReact(opts) {
    var selId = opts.selId;
    var title = opts.title || '';

    var wasOpen   = isOpen();
    var eventName = wasOpen ? 'inspector:swapped' : 'inspector:opened';

    _selId = selId;
    _show();
    document.dispatchEvent(new CustomEvent(eventName, { detail: { selId: selId } }));
  }

  function close() {
    if (!isOpen()) return;
    var prevSelId = _selId;
    _selId = null;
    _hide();
    document.dispatchEvent(new CustomEvent('inspector:closed', { detail: { selId: prevSelId } }));
  }

  function refresh() {
    if (!_lastFragUrl || !_selId) return;
    _lastCache = null;  // invalida caché para forzar refetch
    open({ selId: _selId, fragmentUrl: _lastFragUrl });
  }

  function setLocked(bool) {
    _locked = !!bool;
    var shell = getShell();
    if (shell) shell.classList.toggle('is-inspector-locked', _locked);
  }

  // ── Carga de fragmento HTML ───────────────────────────────────────────────

  function _loadFragment(url, selId) {
    var body = getBody();
    if (!body) return;
    // No limpiar el body antes del fetch: el contenido anterior permanece
    // visible hasta que llega el nuevo (evita flash blanco en swap y en editar).
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (html) {
        // Solo aplicar si la selección no cambió mientras cargaba
        if (_selId !== selId) return;
        _lastCache = { selId: selId, html: html };
        var b = getBody();
        if (b) b.innerHTML = html;
      })
      .catch(function () {
        if (_selId !== selId) return;
        var b = getBody();
        if (b) b.innerHTML = '<div class="p-3 text-danger small">No se pudo cargar el detalle.</div>';
      });
  }

  // ── Carga de fragmento de edición (sin borrar body hasta que llegue) ─────

  function _loadEditFragment(url, selId) {
    var body = getBody();
    if (!body) return;
    // Caché hit: instantáneo, sin flash
    if (_editCache && _editCache.selId === selId) {
      body.innerHTML = _editCache.html;
      return;
    }
    // Caché miss: fetch; mantener contenido actual hasta que llegue
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (html) {
        if (_selId !== selId) return;
        _editCache = { selId: selId, html: html };
        var b = getBody();
        if (b) b.innerHTML = html;
      })
      .catch(function () {
        if (_selId !== selId) return;
        var b = getBody();
        if (b) b.innerHTML = '<div class="p-3 text-danger small">No se pudo cargar el formulario.</div>';
      });
  }

  // ── Light-dismiss ─────────────────────────────────────────────────────────

  document.addEventListener('pointerdown', function (e) {
    if (!isOpen() || _locked) return;
    // Mientras hay un modal Bootstrap abierto encima, no hacer light-dismiss
    if (document.querySelector('.modal.show')) return;
    var aside = getAside();
    if (!aside || aside.contains(e.target)) return;
    // Las islas React gestionan su propia selección; no cerrar desde aquí
    if (e.target.closest('[data-react-island]')) return;
    // Filas/nodos seleccionables (Fase 2+): la vista llama open() directamente
    if (e.target.closest('[data-inspector-sel]')) return;
    close();
  });

  // Escape cierra (si no está bloqueado)
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen() && !_locked) close();
  });

  // ── Restaurar fragmento de lectura desde caché (sin flash) ──────────────

  function _restoreReadFragment() {
    var body = getBody();
    if (!body) return;
    if (_lastCache && _lastCache.selId === _selId) {
      body.innerHTML = _lastCache.html;
    } else {
      refresh();  // fallback: refetch si la caché no está
    }
  }

  // ── Errores de formulario inline ─────────────────────────────────────────

  function _showFormErrors(form, errors) {
    var box = form ? form.querySelector('#inspector-form-errors') : null;
    if (!box) return;
    if (!errors || errors.length === 0) {
      box.style.display = 'none';
      box.innerHTML = '';
    } else {
      box.innerHTML = errors.map(function (msg) {
        return '<div>' + msg + '</div>';
      }).join('');
      box.style.display = '';
      box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // ── Botón cierre, editar y cancelar edición ───────────────────────────────

  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-app-inspector-close]')) {
      close();
      return;
    }
    // Clic en backdrop con lock activo → aviso
    if (_locked && e.target.closest('[data-inspector-backdrop]')) {
      if (window.mostrar_toast) {
        window.mostrar_toast('warning', 'Estás editando este elemento — Guarda o cancela primero.');
      }
      return;
    }
    // Botón "Gestionar…" del fragmento de lectura → abre modal grande
    var modalBtn = e.target.closest('[data-modal-large-url]');
    if (modalBtn && window.AppModalLarge) {
      AppModalLarge.open(modalBtn.dataset.modalLargeUrl, { title: modalBtn.dataset.modalLargeTitle || '' });
      return;
    }
    // Botón "Editar" del fragmento de lectura
    var editBtn = e.target.closest('[data-inspector-edit]');
    if (editBtn) {
      var editUrl = editBtn.dataset.editUrl;
      if (editUrl) {
        _loadEditFragment(editUrl, _selId);
        setLocked(true);
        _formDirty = false;
      }
      return;
    }
    // Botón "Cancelar" del formulario de edición
    if (e.target.closest('[data-inspector-cancel-edit]')) {
      setLocked(false);
      _formDirty = false;
      _restoreReadFragment();
      if (window.mostrar_toast) window.mostrar_toast('info', 'Cambios descartados.');
      return;
    }
  });

  // ── Submit del formulario de edición (interceptado via XHR) ──────────────

  document.addEventListener('submit', function (e) {
    var form = e.target.closest('form[data-inspector-form]');
    if (!form) return;
    e.preventDefault();
    var action = form.dataset.action || form.action;
    var data   = new FormData(form);
    fetch(action, {
      method:  'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body:    data,
    })
      .then(function (r) { return r.json(); })
      .then(function (json) {
        if (json.ok) {
          _formDirty = false;
          setLocked(false);
          _lastCache = null;   // invalida retención para forzar refetch de lectura
          _editCache = null;   // invalida caché de edición (datos cambiaron)
          refresh();
          // La fila del listado no se repinta sola (#681): solo refresh() la vería
          // si el listado la re-leyera; ScrollInfinito la escucha para recargarse.
          document.dispatchEvent(new CustomEvent('inspector:saved', { detail: { selId: _selId } }));
          if (window.mostrar_toast) {
            window.mostrar_toast('success', json.message || 'Guardado correctamente.');
            // Avisos de canonicidad (#727): no bloquean el guardado, se enseñan aparte.
            (json.warnings || []).forEach(function (aviso) {
              window.mostrar_toast('warning', aviso);
            });
          }
        } else {
          _showFormErrors(form, json.errors || []);
        }
      })
      .catch(function () {
        if (window.mostrar_toast) {
          window.mostrar_toast('danger', 'Error al guardar. Inténtalo de nuevo.');
        }
      });
  });

  // ── Seguimiento de cambios en el formulario (dirty) ───────────────────────

  function _markDirty(e) {
    var form = e.target.closest('form[data-inspector-form]');
    if (!form) return;
    _formDirty = true;
    var btn = form.querySelector('[type=submit]');
    if (btn && btn.disabled) btn.disabled = false;
  }

  document.addEventListener('input',  _markDirty);
  document.addEventListener('change', _markDirty);

  // ── beforeunload cuando hay cambios sin guardar ───────────────────────────

  window.addEventListener('beforeunload', function (e) {
    if (_locked && _formDirty) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // ── Resize por arrastre del borde izquierdo ───────────────────────────────

  function _initResize() {
    var aside  = getAside();
    if (!aside) return;
    var handle = aside.querySelector('[data-inspector-resize]');
    if (!handle) return;

    // Restaurar ancho guardado
    try {
      var saved = parseInt(localStorage.getItem(LS_WIDTH), 10);
      if (saved && saved >= MIN_WIDTH) {
        document.documentElement.style.setProperty('--inspector-width', saved + 'px');
      }
    } catch (e) { /* ignore */ }

    var startX, startWidth, dragged;

    handle.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      startX     = e.clientX;
      startWidth = aside.getBoundingClientRect().width;
      dragged    = false;
      handle.setPointerCapture(e.pointerId);
    });

    handle.addEventListener('pointermove', function (e) {
      if (startX === undefined) return;
      var delta = startX - e.clientX;  // arrastrar ← aumenta ancho
      if (Math.abs(delta) >= 4) {
        dragged = true;
        var newWidth = Math.max(MIN_WIDTH, startWidth + delta);
        document.documentElement.style.setProperty('--inspector-width', newWidth + 'px');
      }
    });

    handle.addEventListener('pointerup', function (e) {
      if (startX === undefined) return;
      var wasDragged = dragged;
      startX = dragged = undefined;
      if (!wasDragged) {
        // Clic sin arrastre: colapsar el inspector
        close();
        return;
      }
      try {
        var w = parseInt(getComputedStyle(document.documentElement)
                  .getPropertyValue('--inspector-width'), 10);
        if (w && w >= MIN_WIDTH) localStorage.setItem(LS_WIDTH, String(w));
      } catch (ex) { /* ignore */ }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _initResize);
  } else {
    _initResize();
  }

  // ── Exportar API ─────────────────────────────────────────────────────────

  window.AppInspector = {
    open:        open,
    mountReact:  mountReact,
    close:       close,
    refresh:     refresh,
    setLocked:   setLocked,
    isOpen:      isOpen,
    currentSel:  currentSel
  };

})();
