/**
 * inspector-overlay.js — API de shell para el inspector overlay (ADR-023 / #534).
 *
 * Expone window.AppInspector con los métodos:
 *   open({ selId, title, fragmentUrl })  — abre/swap; carga fragmento HTML si procede
 *   mountReact({ selId, title })         — abre sin tocar el body (islas React)
 *   close()                              — cierra; emite inspector:closed
 *   refresh()                            — re-fetch del último fragmentUrl
 *   setLocked(bool)                      — backdrop bloqueante (modo edición)
 *   isOpen()                             — true si el panel está visible
 *   currentSel()                         — selId activo o null
 *
 * Eventos emitidos en document:
 *   inspector:opened  { detail: { selId } }
 *   inspector:swapped { detail: { selId } }
 *   inspector:closed  { detail: { selId } }  (selId = el que estaba activo)
 */
(function () {
  'use strict';

  var LS_WIDTH  = 'bddat.inspector.width';
  var MIN_WIDTH = 320;

  var _selId        = null;
  var _lastCache    = null;  // { selId, html } — retención del último fragmento
  var _lastFragUrl  = null;  // última fragmentUrl usada (para refresh)
  var _locked       = false;

  // ── Accesores DOM ─────────────────────────────────────────────────────────

  function getShell()   { return document.querySelector('.app-shell'); }
  function getAside()   { return document.getElementById('app-inspector'); }
  function getBody()    { return document.getElementById('app-inspector-body'); }
  function getTitleEl() { return document.getElementById('app-inspector-title'); }

  function setTitle(title) {
    var el = getTitleEl();
    if (el) el.textContent = title || '';
  }

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
    _locked = false;
  }

  // ── API pública ───────────────────────────────────────────────────────────

  function open(opts) {
    var selId      = opts.selId;
    var title      = opts.title || '';
    var fragmentUrl = opts.fragmentUrl || null;

    var wasOpen   = isOpen();
    var isSameId  = wasOpen && _selId === selId;
    var eventName = wasOpen ? 'inspector:swapped' : 'inspector:opened';

    _selId = selId;
    setTitle(title);

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
    setTitle(title);
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
    var selId   = _selId;
    var title   = getTitleEl() ? getTitleEl().textContent : '';
    open({ selId: selId, title: title, fragmentUrl: _lastFragUrl });
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
    body.innerHTML = '<div class="p-3 text-muted small">Cargando…</div>';
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

  // ── Light-dismiss ─────────────────────────────────────────────────────────

  document.addEventListener('pointerdown', function (e) {
    if (!isOpen() || _locked) return;
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

  // Botón de cierre del panel
  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-app-inspector-close]')) {
      close();
      return;
    }
    // Clic en backdrop con lock activo → aviso
    if (_locked && e.target.closest('[data-inspector-backdrop]')) {
      if (window.showToast) {
        window.showToast('Estás editando este elemento — Guarda o cancela primero.', 'warning');
      }
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

    var startX, startWidth;

    handle.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      startX = e.clientX;
      startWidth = aside.getBoundingClientRect().width;
      handle.setPointerCapture(e.pointerId);
    });

    handle.addEventListener('pointermove', function (e) {
      if (startX === undefined) return;
      var delta    = startX - e.clientX;  // arrastrar ← aumenta ancho
      var newWidth = Math.max(MIN_WIDTH, startWidth + delta);
      document.documentElement.style.setProperty('--inspector-width', newWidth + 'px');
    });

    handle.addEventListener('pointerup', function (e) {
      if (startX === undefined) return;
      startX = undefined;
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
