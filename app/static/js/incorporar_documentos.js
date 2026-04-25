// incorporar_documentos.js — issue #290
// Gestiona el listado multi-doc y el selector de vincular en tareas INCORPORAR.
//
// Depende de: selector_busqueda.js
// Datos de entrada: window.INCORPORAR_CONFIG (inyectado por el template)

document.addEventListener('DOMContentLoaded', function () {

  const cfg = window.INCORPORAR_CONFIG;
  if (!cfg) return;

  const lista     = document.getElementById('incorporar-lista');
  const alertEl   = document.getElementById('alert-incorporar');
  const sbContenedor = document.getElementById('sb-incorporar');
  const btnVincular  = document.getElementById('btn-vincular-incorporar');
  if (!lista || !sbContenedor || !btnVincular) return;

  // ── SelectorBusqueda para elegir documento del pool ───────────────────────
  const sel = new SelectorBusqueda('#sb-incorporar', [], {
    placeholder: '— Seleccione documento del pool —',
    onChange: function (v) {
      btnVincular.disabled = !v;
    }
  });

  // Cargar opciones del pool al iniciar
  fetch(cfg.urlApiDocs)
    .then(r => r.json())
    .then(json => { if (json.ok) sel.setOpciones(json.docs); })
    .catch(() => {});

  // ── Vincular ──────────────────────────────────────────────────────────────
  btnVincular.addEventListener('click', async function () {
    const docId = sel.getValue();
    if (!docId) return;

    btnVincular.disabled = true;
    _alerta('', '');

    try {
      const fd = new FormData();
      fd.append('documento_id', docId);
      const resp = await fetch(cfg.urlVincular, { method: 'POST', body: fd });
      const json = await resp.json();

      if (!json.ok) {
        _alerta('danger', json.error || 'Error al vincular el documento.');
        return;
      }

      _añadir_fila(json);
      sel.clear();
      _ocultar_vacio();
    } catch (_e) {
      _alerta('danger', 'Error de red. Inténtelo de nuevo.');
    } finally {
      btnVincular.disabled = !sel.getValue();
    }
  });

  // ── Desvincular (delegación de eventos) ──────────────────────────────────
  lista.addEventListener('click', async function (e) {
    const btn = e.target.closest('.btn-desvincular-incorporar');
    if (!btn) return;

    const vinculoId = btn.dataset.vinculoId;
    const url = cfg.urlDesvincularBase + vinculoId + '/desvincular';

    btn.disabled = true;
    _alerta('', '');

    try {
      const resp = await fetch(url, { method: 'POST' });
      const json = await resp.json();

      if (!json.ok) {
        _alerta('danger', json.error || 'Error al desvincular.');
        btn.disabled = false;
        return;
      }

      const fila = lista.querySelector('.incorporar-fila[data-vinculo-id="' + vinculoId + '"]');
      if (fila) fila.remove();
      _mostrar_vacio_si_vacia();
    } catch (_e) {
      _alerta('danger', 'Error de red. Inténtelo de nuevo.');
      btn.disabled = false;
    }
  });

  // ── Helpers DOM ───────────────────────────────────────────────────────────

  function _añadir_fila(data) {
    const fila = document.createElement('div');
    fila.className = 'd-flex align-items-center gap-2 flex-wrap mb-2 incorporar-fila';
    fila.dataset.vinculoId = data.vinculo_id;

    const meta = [data.tipo_nombre, data.fecha].filter(Boolean).join(' — ');
    fila.innerHTML =
      '<i class="fas fa-file-import text-secondary"></i>' +
      '<span class="fw-semibold">' + _esc(data.nombre_display) + '</span>' +
      (meta ? '<small class="text-secondary">— ' + _esc(meta) + '</small>' : '') +
      '<a href="' + _esc(data.url_descargar) + '" class="btn btn-sm btn-outline-secondary ms-auto"' +
        ' target="_blank" rel="noopener"><i class="fas fa-download me-1"></i>Descargar</a>' +
      '<button type="button" class="btn btn-sm btn-outline-danger btn-desvincular-incorporar"' +
        ' data-vinculo-id="' + data.vinculo_id + '"' +
        ' data-url="' + _esc(cfg.urlDesvincularBase + data.vinculo_id + '/desvincular') + '">' +
        '<i class="fas fa-times"></i></button>';

    lista.appendChild(fila);
  }

  function _ocultar_vacio() {
    const vacio = document.getElementById('incorporar-vacio');
    if (vacio) vacio.remove();
  }

  function _mostrar_vacio_si_vacia() {
    const filas = lista.querySelectorAll('.incorporar-fila');
    if (filas.length === 0 && !document.getElementById('incorporar-vacio')) {
      const p = document.createElement('p');
      p.id = 'incorporar-vacio';
      p.className = 'fst-italic text-secondary small mb-2';
      p.textContent = 'Sin documentos vinculados.';
      lista.appendChild(p);
    }
  }

  function _alerta(tipo, msg) {
    if (!tipo) { alertEl.classList.add('d-none'); return; }
    alertEl.className = 'alert alert-' + tipo + ' mt-2 py-2 mb-0';
    alertEl.textContent = msg;
  }

  function _esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

});
