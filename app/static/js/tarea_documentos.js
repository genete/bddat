// tarea_documentos.js — issue #166
// Gestiona los SelectorBusqueda de documento_usado y documento_producido en la
// vista de tarea (tramitacion_bc_tarea.html).
//
// Depende de: selector_busqueda.js, v3-breadcrumbs-edicion.js
// Datos de entrada: window.TAREA_DOCS_CONFIG (inyectado por el template)

document.addEventListener('DOMContentLoaded', function () {

  const cfg = window.TAREA_DOCS_CONFIG;
  if (!cfg) return;

  // Referencias a los botones de edición de C.1
  const contenedor   = document.querySelector('[data-bc-editable]');
  if (!contenedor) return;
  const btn_editar   = contenedor.querySelector('.btn-editar-bc');
  const btn_cancelar = contenedor.querySelector('.btn-cancelar-bc');
  const btn_guardar  = contenedor.querySelector('.btn-guardar-bc');
  const form         = contenedor.querySelector('form[data-url]');

  if (!btn_editar || !form) return;

  // ── Visibilidad de C.2 sincronizada con C.1 ───────────────────────────────
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

  // ── Instanciar SelectorBusqueda solo si el tipo de tarea lo requiere ──────
  let sel_usado = null;
  let sel_producido = null;

  if ((cfg.requiereDocUsado || cfg.docUsadoOpcional) && document.getElementById('sb-doc-usado')) {
    sel_usado = new SelectorBusqueda('#sb-doc-usado', [], {
      placeholder: '— Seleccione documento de entrada —',
      name: 'documento_usado_id'
    });
  }

  if (cfg.requiereDocProducido && document.getElementById('sb-doc-producido')) {
    sel_producido = new SelectorBusqueda('#sb-doc-producido', [], {
      placeholder: '— Seleccione documento producido —',
      name: 'documento_producido_id'
    });
  }

  // ── Inyectar hidden inputs en el form de C.1 antes de que se construya el FormData ──
  // capture:true garantiza que este handler se ejecuta antes que el de v3-breadcrumbs-edicion.js
  btn_guardar.addEventListener('click', function () {
    _inyectar_en_form('documento_usado_id',    sel_usado    ? (sel_usado.getValue()    || '') : '');
    _inyectar_en_form('documento_producido_id', sel_producido ? (sel_producido.getValue() || '') : '');
  }, true);

  function _inyectar_en_form(name, value) {
    let inp = form.querySelector('input[name="' + name + '"]');
    if (!inp) {
      inp = document.createElement('input');
      inp.type = 'hidden';
      inp.name = name;
      form.appendChild(inp);
    }
    inp.value = value;
  }

  // ── Evento Editar: mostrar selectores + cargar opciones dinámicamente ─────
  btn_editar.addEventListener('click', async function () {
    mostrar_editar();
    try {
      const resp = await fetch(cfg.urlApiDocs);
      const json = await resp.json();
      if (json.ok) {
        if (sel_usado)    sel_usado.setOpciones(json.docs);
        if (sel_producido) sel_producido.setOpciones(json.docs);
        // Preseleccionar el valor actual si existe
        if (sel_usado    && cfg.docUsadoId)    sel_usado.setValue(String(cfg.docUsadoId), _texto_actual('disp-doc-usado'));
        if (sel_producido && cfg.docProducidoId) sel_producido.setValue(String(cfg.docProducidoId), _texto_actual('disp-doc-producido'));
      }
    } catch (_e) {
      // Silencioso: los selectores quedan vacíos; el usuario puede intentar guardar de nuevo
    }
  });

  // ── Evento Cancelar ────────────────────────────────────────────────────────
  btn_cancelar.addEventListener('click', mostrar_ver);

  // ── Actualizar display tras guardar (CustomEvent 'bc:guardado' de v3-bc-edicion.js) ─
  form.addEventListener('bc:guardado', function () {
    mostrar_ver();

    // Actualizar texto visible y guardar nuevos IDs en config para la próxima apertura
    if (sel_usado) {
      const id_nuevo = sel_usado.getValue();
      const texto_nuevo = id_nuevo ? sel_usado._input.value : '';
      cfg.docUsadoId = id_nuevo ? parseInt(id_nuevo) : null;
      const span = document.getElementById('disp-doc-usado');
      if (span) span.textContent = texto_nuevo || 'Sin documento asociado';
    }
    if (sel_producido) {
      const id_nuevo = sel_producido.getValue();
      const texto_nuevo = id_nuevo ? sel_producido._input.value : '';
      cfg.docProducidoId = id_nuevo ? parseInt(id_nuevo) : null;
      const span = document.getElementById('disp-doc-producido');
      if (span) span.textContent = texto_nuevo || 'Sin documento asociado';
    }
  });

  // ── Helper: obtiene el texto visible del span de display ──────────────────
  function _texto_actual(span_id) {
    const el = document.getElementById(span_id);
    return el ? el.textContent.trim() : '';
  }

});
