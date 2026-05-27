// tarea_documentos.js — gestión documental de la tarea (ADR-010, #420)
//
// Documento producido: selección única (SelectorBusqueda).
// Documentos consumidos: lista de N documentos (selector + lista con quitar).
//
// Depende de: selector_busqueda.js, v3-breadcrumbs-edicion.js
// Datos de entrada: window.TAREA_DOCS_CONFIG (inyectado por el template)
//   docsConsumidos: [id, ...]   docProducidoId: id|null
// Las opciones del API tienen forma {v: id, t: texto}.

document.addEventListener('DOMContentLoaded', function () {

  const cfg = window.TAREA_DOCS_CONFIG;
  if (!cfg) return;

  const contenedor = document.querySelector('[data-bc-editable]');
  if (!contenedor) return;
  const btn_editar   = contenedor.querySelector('.btn-editar-bc');
  const btn_cancelar = contenedor.querySelector('.btn-cancelar-bc');
  const btn_guardar  = contenedor.querySelector('.btn-guardar-bc');
  const form         = contenedor.querySelector('form[data-url]');
  if (!btn_editar || !form) return;

  // ── Visibilidad ver/editar de la card de documentos ──────────────────────
  const bloques_ver    = document.querySelectorAll('#card-documentos .doc-modo-ver');
  const bloques_editar = document.querySelectorAll('#card-documentos .doc-modo-editar');

  function mostrar_ver() {
    bloques_ver.forEach(el => el.classList.remove('d-none'));
    bloques_editar.forEach(el => el.classList.add('d-none'));
  }
  function mostrar_editar() {
    bloques_ver.forEach(el => el.classList.add('d-none'));
    bloques_editar.forEach(el => el.classList.remove('d-none'));
  }

  // ── Estado en memoria ────────────────────────────────────────────────────
  function _ids_iniciales() {
    return Array.isArray(cfg.docsConsumidos) ? cfg.docsConsumidos.map(Number) : [];
  }
  let ids_consumidos = _ids_iniciales();
  let opciones_docs = [];   // [{v, t}] cargadas del API

  const usa_consumidos = (cfg.requiereDocUsado || cfg.docUsadoOpcional);

  let sel_consumido = null;
  let sel_producido = null;

  if (usa_consumidos && document.getElementById('sb-doc-consumido')) {
    sel_consumido = new SelectorBusqueda('#sb-doc-consumido', [], {
      placeholder: '— Seleccione documento de entrada —'
    });
  }
  if (cfg.requiereDocProducido && document.getElementById('sb-doc-producido')) {
    sel_producido = new SelectorBusqueda('#sb-doc-producido', [], {
      placeholder: '— Seleccione documento producido —'
    });
  }

  // ── Lista de documentos consumidos ───────────────────────────────────────
  function _nombre_doc(id) {
    const o = opciones_docs.find(d => Number(d.v) === Number(id));
    return o ? o.t : ('Documento ' + id);
  }

  function _render_lista_consumidos() {
    const lista = document.getElementById('lista-docs-consumidos');
    if (!lista) return;
    lista.innerHTML = '';
    if (ids_consumidos.length === 0) {
      const p = document.createElement('p');
      p.className = 'fst-italic text-secondary small mb-2';
      p.textContent = 'Ningún documento de entrada seleccionado';
      lista.appendChild(p);
      return;
    }
    ids_consumidos.forEach(function (id) {
      const fila = document.createElement('div');
      fila.className = 'd-flex align-items-center gap-2 mb-1';
      const span = document.createElement('span');
      span.className = 'badge text-bg-light border text-wrap text-start';
      span.textContent = _nombre_doc(id);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-sm btn-outline-danger py-0';
      btn.innerHTML = '<i class="fas fa-times"></i>';
      btn.addEventListener('click', function () {
        ids_consumidos = ids_consumidos.filter(x => x !== id);
        _render_lista_consumidos();
      });
      fila.appendChild(span);
      fila.appendChild(btn);
      lista.appendChild(fila);
    });
  }

  const btn_add = document.getElementById('btn-add-consumido');
  if (btn_add && sel_consumido) {
    btn_add.addEventListener('click', function () {
      const val = sel_consumido.getValue();
      if (!val) return;
      const id = Number(val);
      if (!ids_consumidos.includes(id)) {
        ids_consumidos.push(id);
        _render_lista_consumidos();
      }
      sel_consumido.setValue('', '');
    });
  }

  // ── Inyectar campos en el form antes de enviar ───────────────────────────
  // capture:true → se ejecuta antes que el handler de v3-breadcrumbs-edicion.js
  btn_guardar.addEventListener('click', function () {
    form.querySelectorAll(
      'input[name="documentos_consumidos_ids"], input[name="documento_producido_id"]'
    ).forEach(el => el.remove());

    ids_consumidos.forEach(function (id) {
      const inp = document.createElement('input');
      inp.type = 'hidden';
      inp.name = 'documentos_consumidos_ids';
      inp.value = String(id);
      form.appendChild(inp);
    });

    const inp_prod = document.createElement('input');
    inp_prod.type = 'hidden';
    inp_prod.name = 'documento_producido_id';
    inp_prod.value = sel_producido ? (sel_producido.getValue() || '') : '';
    form.appendChild(inp_prod);
  }, true);

  // ── Editar: mostrar selectores + cargar opciones ─────────────────────────
  btn_editar.addEventListener('click', async function () {
    mostrar_editar();
    try {
      const resp = await fetch(cfg.urlApiDocs);
      const json = await resp.json();
      if (json.ok) {
        opciones_docs = json.docs || [];
        if (sel_consumido) sel_consumido.setOpciones(opciones_docs);
        if (sel_producido) {
          sel_producido.setOpciones(opciones_docs);
          if (cfg.docProducidoId) {
            sel_producido.setValue(String(cfg.docProducidoId),
                                   _texto_actual('disp-doc-producido'));
          }
        }
      }
    } catch (_e) {
      // Silencioso: los selectores quedan vacíos; reintentar guardando de nuevo
    }
    _render_lista_consumidos();
  });

  // ── Cancelar: restaurar estado inicial ───────────────────────────────────
  btn_cancelar.addEventListener('click', function () {
    ids_consumidos = _ids_iniciales();
    mostrar_ver();
  });

  // ── Tras guardar: recargar para reflejar la lista actualizada ────────────
  form.addEventListener('bc:guardado', function () {
    window.location.reload();
  });

  function _texto_actual(span_id) {
    const el = document.getElementById(span_id);
    return el ? el.textContent.trim() : '';
  }

});
