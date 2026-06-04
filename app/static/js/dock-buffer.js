// Buffer de avisos para el dock global (#506).
// Captura mensajes antes de que los toasts se autodestruyan.
// Expone window.DockBuffer.push({ tipo, texto }) y DockBuffer.getAll() / clear().
(function () {
  'use strict';

  var SS_KEY    = 'bddat.dock.avisos';
  var UNREAD_KEY = 'bddat.dock.avisos.unread';

  var _listeners = [];

  function _load() {
    try { return JSON.parse(sessionStorage.getItem(SS_KEY) || '[]'); } catch (e) { return []; }
  }

  function _save(items) {
    try { sessionStorage.setItem(SS_KEY, JSON.stringify(items)); } catch (e) { /* ignore */ }
  }

  function _loadUnread() {
    try { return parseInt(sessionStorage.getItem(UNREAD_KEY) || '0', 10); } catch (e) { return 0; }
  }

  function _saveUnread(n) {
    try { sessionStorage.setItem(UNREAD_KEY, String(n)); } catch (e) { /* ignore */ }
  }

  window.DockBuffer = {
    push: function (tipo, texto) {
      var now  = new Date();
      var hora = now.getHours().toString().padStart(2, '0') + ':' +
                 now.getMinutes().toString().padStart(2, '0');
      var item = { tipo: tipo, texto: texto, hora: hora };

      var items = _load();
      items.unshift(item);   // más reciente primero
      if (items.length > 100) items = items.slice(0, 100);
      _save(items);

      _saveUnread(_loadUnread() + 1);

      _listeners.forEach(function (fn) { fn(item); });
    },

    getAll: function () { return _load(); },

    getUnread: function () { return _loadUnread(); },

    markRead: function () { _saveUnread(0); },

    clear: function () {
      _save([]);
      _saveUnread(0);
      _listeners.forEach(function (fn) { fn(null); });
    },

    onChange: function (fn) { _listeners.push(fn); },
  };
}());
