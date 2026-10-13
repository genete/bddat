/**
 * inspector-overlay.js — API de shell para el inspector overlay (ADR-023 / #534).
 *
 * Expone window.AppInspector con los métodos:
 *   open({ selId, fragmentUrl, title })
 *                                 — abre/swap; carga fragmento HTML si procede.
 *                                   `title` es la cabecera de reserva del marco (la
 *                                   que pasa el listado); el fragmento puede sustituirla.
 *   mountReact({ selId })         — abre sin tocar el body (islas React)
 *   close()                       — cierra; emite inspector:closed
 *   refresh()                     — re-fetch del último fragmentUrl
 *   setLocked(bool)               — backdrop bloqueante (modo edición)
 *   setFrame(desc | null)         — marco que alimenta una isla React (el puente del árbol)
 *   isOpen()                      — true si el panel está visible
 *   currentSel()                  — selId activo o null
 *
 * Eventos emitidos en document:
 *   inspector:opened  { detail: { selId } }
 *   inspector:swapped { detail: { selId } }
 *   inspector:closed  { detail: { selId } }  (selId = el que estaba activo)
 *   inspector:saved   { detail: { selId } }  (guardado de edición con éxito, #681)
 *
 * MARCO ÚNICO (ADR-053 §A, #1042). El shell pinta una sola barra (#app-inspector-bar) con
 * la cabecera y los gestos de ver / editar / guardar / cancelar / cerrar. La alimenta una
 * de dos fuentes:
 *
 *  1) Un fragmento Jinja, con atributos en su raíz (el DOM que hay en el cuerpo es la verdad):
 *       <div class="p-3" data-inspector-frame="ver" data-edit-url="…">       lectura
 *       <div class="p-3" data-inspector-frame="editar">                      edición
 *     Opcionales: data-title (sustituye al título del listado; ponerlo cuando el título es
 *     editable, o la cabecera queda desactualizada tras guardar), data-edit-label
 *     (rótulo de «Editar», p. ej. «Resolver»), data-save-label (rótulo de «Guardar») y
 *     data-min-width (ancho mínimo del cuerpo en px: por debajo, scroll horizontal del cuerpo).
 *     Sin data-edit-url no hay «Editar». En edición, el formulario es el único
 *     form[data-inspector-form] del fragmento y «Guardar» lo envía con requestSubmit().
 *     Un fragmento sin data-inspector-frame no tiene barra (los de solo lectura: cola,
 *     seguimiento y huérfanos, hasta que adopten el marco).
 *
 *  2) El árbol del expediente (React), con AppInspector.setFrame(desc): { modo, titulo, tipo,
 *     estado, candado, semaforo: { color, titulo }, puedeEditar, minWidth, hayCambios,
 *     guardando, onEditar, onGuardar, onSalir }.
 *
 * «Guardar» está deshabilitado mientras no haya cambios; el botón de salida dice «Cerrar» si
 * no los hay y «Cancelar» si los hay (ADR-023 §5 bis). En un fragmento Jinja hay cambios
 * cuando el usuario ha tocado el formulario: eventos input/change dentro del form. Todo
 * script que cambie campos sin que el usuario teclee (añadir o quitar una fila, escribir un
 * campo oculto) debe disparar un `change` que burbujee, o «Guardar» no se enciende.
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
  var _title        = '';    // título que pasó el listado al abrir (cabecera de reserva)
  var _frame        = null;  // estado del marco pintado, o null (barra oculta)

  var FRAME_DEFECTOS = {
    modo: 'ver', titulo: '', tipo: '', estado: '', candado: false, semaforo: null,
    puedeEditar: false, rotuloEditar: 'Editar', rotuloGuardar: 'Guardar',
    hayCambios: false, guardando: false, sinFormulario: false,
    minWidth: 0,   // ancho mínimo del cuerpo en px; 0 = sin mínimo (el cuerpo se encoge)
    onEditar: null, onGuardar: null, onSalir: null
  };

  // ── Accesores DOM ─────────────────────────────────────────────────────────

  function getShell() { return document.querySelector('.app-shell'); }
  function getAside() { return document.getElementById('app-inspector'); }
  function getBody()  { return document.getElementById('app-inspector-body'); }
  function getBar()   { return document.getElementById('app-inspector-bar'); }

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
    _frame     = null;
    _renderFrame();
  }

  // ── Marco: estado y pintado ───────────────────────────────────────────────

  function _q(bar, sel) { return bar.querySelector(sel); }

  function _renderFrame() {
    var bar = getBar();
    if (!bar) return;
    // Ancho mínimo del cuerpo (ADR-053 §B): por debajo, scroll horizontal del cuerpo, nunca
    // de la barra. Sin marco no hay mínimo.
    var body = getBody();
    if (body) body.style.setProperty('--inspector-min', ((_frame && _frame.minWidth) || 0) + 'px');
    if (!_frame) { bar.hidden = true; return; }
    var f = _frame;
    bar.hidden = false;

    // El título se trunca con puntos suspensivos si no cabe; el texto completo, en el tooltip.
    var titulo = _q(bar, '[data-frame-titulo]');
    titulo.textContent = f.titulo || '';
    titulo.title = f.titulo || '';

    var tipo = _q(bar, '[data-frame-tipo]');
    tipo.hidden = !f.tipo;
    tipo.textContent = f.tipo || '';

    var sem = _q(bar, '[data-frame-semaforo]');
    sem.hidden = !f.semaforo;
    if (f.semaforo) {
      sem.setAttribute('data-color', f.semaforo.color || 'gris');
      sem.title = f.semaforo.titulo || '';
    }

    var estado = _q(bar, '[data-frame-estado]');
    estado.hidden = !f.estado;
    _q(bar, '[data-frame-estado-texto]').textContent = f.estado || '';
    _q(bar, '[data-frame-candado]').hidden = !f.candado;

    var editar = _q(bar, '[data-frame-editar]');
    editar.hidden = !(f.modo === 'ver' && f.puedeEditar);
    editar.textContent = f.rotuloEditar || 'Editar';

    var guardar = _q(bar, '[data-frame-guardar]');
    guardar.hidden = f.modo !== 'editar';
    guardar.disabled = !!(f.guardando || !f.hayCambios || f.sinFormulario);
    guardar.textContent = f.guardando ? 'Guardando…' : (f.rotuloGuardar || 'Guardar');

    var salir = _q(bar, '[data-frame-salir]');
    salir.hidden = f.modo !== 'editar';
    salir.disabled = !!f.guardando;
    salir.textContent = f.hayCambios ? 'Cancelar' : 'Cerrar';
  }

  // Mezcla un cambio parcial en el marco ya pintado (no hace nada si no hay marco).
  function _patchFrame(parcial) {
    if (!_frame) return;
    _frame = Object.assign({}, _frame, parcial);
    _renderFrame();
  }

  // Marco que alimenta una isla React (el puente del árbol): el descriptor completo
  // sustituye al anterior; null oculta la barra.
  function setFrame(desc) {
    _frame = desc ? Object.assign({}, FRAME_DEFECTOS, desc) : null;
    _renderFrame();
  }

  // Lee el marco que declara el fragmento Jinja que acaba de entrar en el cuerpo.
  // El DOM es la verdad: tras cada inyección, lo que se pinta sale de aquí.
  function _aplicarMarco() {
    var body = getBody();
    if (!body) return;
    var root = body.querySelector('[data-inspector-frame]');
    if (!root) {
      // Fragmento sin marco (aún no migrado, o sin edición): sin barra, como antes.
      _frame = null;
      _renderFrame();
      return;
    }
    var d = root.dataset;
    var modo = d.inspectorFrame === 'editar' ? 'editar' : 'ver';
    var editUrl = d.editUrl || '';
    var sinFormulario = false;
    if (modo === 'editar') {
      var n = body.querySelectorAll('form[data-inspector-form]').length;
      if (n !== 1) {
        sinFormulario = true;
        // Guarda: «Guardar» no puede elegir entre varios formularios ni enviar ninguno.
        if (window.console) console.error('inspector: el fragmento de edición debe tener un único form[data-inspector-form] y tiene ' + n);
      }
    }
    _formDirty = false;
    _frame = Object.assign({}, FRAME_DEFECTOS, {
      modo: modo,
      titulo: d.title || _title,
      puedeEditar: modo === 'ver' && !!editUrl,
      rotuloEditar: d.editLabel || 'Editar',
      rotuloGuardar: d.saveLabel || 'Guardar',
      minWidth: parseInt(d.minWidth, 10) || 0,
      sinFormulario: sinFormulario,
      onEditar: function () { _entrarEdicion(editUrl); },
      onGuardar: _guardarFormulario,
      onSalir: _salirEdicion
    });
    _renderFrame();
    // El marco es quien bloquea el panel: en edición sí, en lectura no.
    setLocked(modo === 'editar');
  }

  function _entrarEdicion(editUrl) {
    if (!editUrl) return;
    _loadEditFragment(editUrl, _selId);
    setLocked(true);
    _formDirty = false;
  }

  // «Cerrar» (formulario limpio) y «Cancelar» (con cambios): vuelven a lectura. Solo avisa de
  // descarte si de verdad había algo que perder (ADR-023 §5 bis).
  function _salirEdicion() {
    var habiaCambios = !!(_frame && _frame.hayCambios);
    setLocked(false);
    _formDirty = false;
    _restoreReadFragment();
    if (habiaCambios && window.mostrar_toast) window.mostrar_toast('info', 'Cambios descartados.');
  }

  function _guardarFormulario() {
    var body = getBody();
    var forms = body ? body.querySelectorAll('form[data-inspector-form]') : [];
    if (forms.length !== 1) {
      if (window.mostrar_toast) window.mostrar_toast('danger', 'No se puede guardar: el formulario de edición no es válido.');
      return;
    }
    var form = forms[0];
    // requestSubmit (no submit): pasa por la validación HTML5 y dispara el evento
    // `submit` que este fichero intercepta para enviar por XHR.
    if (typeof form.requestSubmit === 'function') {
      form.requestSubmit();
    } else {
      form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    }
  }

  // ── API pública ───────────────────────────────────────────────────────────

  function open(opts) {
    var selId      = opts.selId;
    var fragmentUrl = opts.fragmentUrl || null;

    var wasOpen   = isOpen();
    var isSameId  = wasOpen && _selId === selId;
    var eventName = wasOpen ? 'inspector:swapped' : 'inspector:opened';

    _selId     = selId;
    _formDirty = false;
    _editCache = null;
    // refresh() reabre sin título: se conserva el del mismo elemento.
    _title     = opts.title || (isSameId ? _title : '');

    if (fragmentUrl) {
      _lastFragUrl = fragmentUrl;
      // Retención: mismo selId → no refetchear
      if (isSameId && _lastCache && _lastCache.selId === selId) {
        // contenido ya en el DOM, no hacer nada
      } else if (_lastCache && _lastCache.selId === selId) {
        var body = getBody();
        if (body) body.innerHTML = _lastCache.html;
        _aplicarMarco();
      } else {
        // Hasta que llegue el fragmento nuevo, la cabecera ya es la del elemento nuevo y
        // sin gestos (los del anterior no valen); el cuerpo conserva su ancho mínimo, que
        // sigue siendo el del contenido que todavía hay en él. Si no había barra, no se
        // enseña ninguna.
        if (_frame) _frame = Object.assign({}, FRAME_DEFECTOS, { titulo: _title, minWidth: _frame.minWidth });
        _renderFrame();
        _loadFragment(fragmentUrl, selId);
      }
    }

    _show();
    document.dispatchEvent(new CustomEvent(eventName, { detail: { selId: selId } }));
  }

  function mountReact(opts) {
    var selId = opts.selId;

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
        _aplicarMarco();
      })
      .catch(function () {
        if (_selId !== selId) return;
        var b = getBody();
        if (b) b.innerHTML = '<div class="p-3 text-danger small">No se pudo cargar el detalle.</div>';
        _aplicarMarco();
      });
  }

  // ── Carga de fragmento de edición (sin borrar body hasta que llegue) ─────

  function _loadEditFragment(url, selId) {
    var body = getBody();
    if (!body) return;
    // Caché hit: instantáneo, sin flash
    if (_editCache && _editCache.selId === selId) {
      body.innerHTML = _editCache.html;
      _aplicarMarco();
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
        _aplicarMarco();
      })
      .catch(function () {
        if (_selId !== selId) return;
        // El fragmento de edición no llegó (403/404/500, #550): no dejar el
        // inspector bloqueado en modo edición sin salida — volver a lectura,
        // igual que "Cancelar".
        setLocked(false);
        _formDirty = false;
        _restoreReadFragment();
        if (window.mostrar_toast) {
          window.mostrar_toast('danger', 'No se pudo abrir el formulario de edición.');
        }
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

  // Intro dentro de un campo de texto del formulario de edición = Guardar (si hay cambios).
  // El fragmento ya no lleva botón de envío propio, así que el navegador no lo hace solo.
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' || e.isComposing || !_frame || _frame.modo !== 'editar') return;
    var t = e.target;
    if (!t || t.tagName !== 'INPUT') return;
    var tipo = (t.type || '').toLowerCase();
    if (['checkbox', 'radio', 'button', 'submit', 'reset', 'file'].indexOf(tipo) >= 0) return;
    if (!t.closest('form[data-inspector-form]')) return;
    e.preventDefault();
    if (_frame.hayCambios && !_frame.guardando) _guardarFormulario();
  });

  // ── Restaurar fragmento de lectura desde caché (sin flash) ──────────────

  function _restoreReadFragment() {
    var body = getBody();
    if (!body) return;
    if (_lastCache && _lastCache.selId === _selId) {
      body.innerHTML = _lastCache.html;
      _aplicarMarco();
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

  // ── Botones del marco, cierre, editar y cancelar edición ──────────────────

  document.addEventListener('click', function (e) {
    // Gestos del marco (la barra del shell). Cada fuente decide qué hace cada gesto.
    if (_frame) {
      if (e.target.closest('[data-frame-editar]')) {
        if (_frame.onEditar) _frame.onEditar();
        return;
      }
      if (e.target.closest('[data-frame-guardar]')) {
        if (_frame.onGuardar) _frame.onGuardar();
        return;
      }
      if (e.target.closest('[data-frame-salir]')) {
        if (_frame.onSalir) _frame.onSalir();
        return;
      }
    }
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
  });

  // ── Submit del formulario de edición (interceptado via XHR) ──────────────

  document.addEventListener('submit', function (e) {
    var form = e.target.closest('form[data-inspector-form]');
    if (!form) return;
    e.preventDefault();
    var action = form.dataset.action || form.action;
    var data   = new FormData(form);
    _patchFrame({ guardando: true });
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
          _patchFrame({ guardando: false });
          _showFormErrors(form, json.errors || []);
        }
      })
      .catch(function () {
        _patchFrame({ guardando: false });
        if (window.mostrar_toast) {
          window.mostrar_toast('danger', 'Error al guardar. Inténtalo de nuevo.');
        }
      });
  });

  // ── Seguimiento de cambios en el formulario (dirty) ───────────────────────

  function _markDirty(e) {
    var form = e.target.closest ? e.target.closest('form[data-inspector-form]') : null;
    if (!form) return;
    _formDirty = true;
    // Con marco, «Guardar» se enciende y «Cerrar» pasa a «Cancelar».
    if (_frame && _frame.modo === 'editar' && !_frame.hayCambios) _patchFrame({ hayCambios: true });
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
    setFrame:    setFrame,
    isOpen:      isOpen,
    currentSel:  currentSel
  };

})();
