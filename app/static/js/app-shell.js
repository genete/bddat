/**
 * app-shell.js — toggles del layout y persistencia de estado (ADR-014 / #498).
 *
 * Responsabilidades:
 *   - Colapsar/expandir sidebar y persistir en localStorage + cookie
 *     (cookie permite que el server renderice el estado correcto sin flash).
 *   - Abrir sidebar como overlay en mobile (<768px).
 *   - Toggle inspector / dock (persistido en localStorage).
 *   - Atajos: Ctrl+B colapsa sidebar; Ctrl+K enfoca buscador.
 *
 * Convenciones (NOMENCLATURA_LAYOUT.md):
 *   - localStorage:
 *       bddat.sidebar.collapsed (string "true"/"false")
 *       bddat.inspector.open    (string "true"/"false")
 *       bddat.dock.open         (string "true"/"false")
 *   - Cookie: bddat_sidebar_collapsed (=1 cuando colapsado)
 *   - Atributos data-app-shell-toggle="sidebar|sidebar-mobile|inspector|dock"
 */
(function () {
  'use strict';

  var LS = {
    sidebarCollapsed: 'bddat.sidebar.collapsed',
    inspectorOpen:    'bddat.inspector.open',
    dockOpen:         'bddat.dock.open'
  };
  var SS_BANNER   = 'bddat.banner.dismissed';
  var COOKIE_SIDEBAR = 'bddat_sidebar_collapsed';
  var BREAKPOINT_COLLAPSED = 1280;
  var BREAKPOINT_MOBILE    = 768;

  function getShell() { return document.querySelector('.app-shell'); }

  function setCookie(name, value) {
    document.cookie = name + '=' + value + ';path=/;max-age=31536000;samesite=lax';
  }

  function readLS(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function writeLS(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* ignore */ }
  }

  function isMobile() {
    return window.matchMedia('(max-width: ' + (BREAKPOINT_MOBILE - 1) + 'px)').matches;
  }

  // -- Sidebar (desktop: clase is-sidebar-collapsed; mobile: is-sidebar-open)

  function applySidebarState(shell) {
    if (isMobile()) return; // En mobile no aplica colapso, sino overlay
    var stored = readLS(LS.sidebarCollapsed);
    var collapsed;
    if (stored !== null) {
      collapsed = stored === 'true';
    } else {
      collapsed = window.matchMedia('(max-width: ' + BREAKPOINT_COLLAPSED + 'px)').matches;
    }
    shell.classList.toggle('is-sidebar-collapsed', collapsed);
    setCookie(COOKIE_SIDEBAR, collapsed ? '1' : '0');
  }

  function toggleSidebar(shell) {
    if (isMobile()) { toggleSidebarMobile(shell); return; }
    var collapsed = !shell.classList.contains('is-sidebar-collapsed');
    shell.classList.toggle('is-sidebar-collapsed', collapsed);
    writeLS(LS.sidebarCollapsed, String(collapsed));
    setCookie(COOKIE_SIDEBAR, collapsed ? '1' : '0');
  }

  function toggleSidebarMobile(shell) {
    shell.classList.toggle('is-sidebar-open');
  }

  // -- Banner admin (sessionStorage — persiste dentro de la sesión del navegador)

  function applyBannerState() {
    try {
      if (sessionStorage.getItem(SS_BANNER) !== '1') return;
      var banner = document.getElementById('js-alert-banner');
      if (banner) banner.remove();
    } catch (e) { /* ignore */ }
  }

  function initBannerDismiss() {
    var banner = document.getElementById('js-alert-banner');
    if (!banner) return;
    banner.addEventListener('close.bs.alert', function () {
      try { sessionStorage.setItem(SS_BANNER, '1'); } catch (e) { /* ignore */ }
    });
  }

  // -- Inspector / Dock (estado solo en localStorage — el server no lo necesita)

  function applyPanelStates(shell) {
    var insp = readLS(LS.inspectorOpen);
    if (insp === 'false') shell.classList.add('is-inspector-closed');
    var dock = readLS(LS.dockOpen);
    if (dock === 'false') shell.classList.add('is-dock-closed');
  }

  function togglePanel(shell, klass, storageKey) {
    var closed = !shell.classList.contains(klass);
    shell.classList.toggle(klass, closed);
    writeLS(storageKey, String(!closed));
  }

  // -- Listeners

  function onClick(e) {
    var btn = e.target.closest('[data-app-shell-toggle]');
    if (!btn) {
      var bd = e.target.closest('[data-app-shell-backdrop]');
      if (bd) { var s = getShell(); if (s) s.classList.remove('is-sidebar-open'); }
      return;
    }
    var shell = getShell();
    if (!shell) return;
    var action = btn.getAttribute('data-app-shell-toggle');
    if (action === 'sidebar')        toggleSidebar(shell);
    else if (action === 'sidebar-mobile') toggleSidebarMobile(shell);
    else if (action === 'inspector') togglePanel(shell, 'is-inspector-closed', LS.inspectorOpen);
    else if (action === 'dock')      togglePanel(shell, 'is-dock-closed', LS.dockOpen);
  }

  function onKeydown(e) {
    var ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && (e.key === 'k' || e.key === 'K')) {
      var inp = document.querySelector('[data-app-shell-search]');
      if (inp) { e.preventDefault(); inp.focus(); inp.select(); }
    } else if (ctrl && (e.key === 'b' || e.key === 'B')) {
      var s = getShell();
      if (s) { e.preventDefault(); toggleSidebar(s); }
    } else if (e.key === 'Escape') {
      var sh = getShell();
      if (sh && sh.classList.contains('is-sidebar-open')) sh.classList.remove('is-sidebar-open');
    }
  }

  function init() {
    var shell = getShell();
    if (!shell) return;
    applySidebarState(shell);
    applyPanelStates(shell);
    applyBannerState();
    initBannerDismiss();
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKeydown);
    // Re-aplicar al cambiar de tamaño (mobile ↔ desktop)
    window.addEventListener('resize', function () {
      if (!isMobile()) shell.classList.remove('is-sidebar-open');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
