/**
 * pool_alta.js — las dos altas del pool de documentos: «Subir fichero» y «Añadir URL externa»
 * (#881, ADR-053 §E: crear sigue siendo modal; editar es del inspector).
 *
 * Salió del JS en línea de `pool_documentos.html`. La configuración llega por `data-*` de
 * `#pool-config` (las URL de las rutas del expediente, la rama de la ingesta de un proyecto y el
 * tope de «hoy» de las fechas administrativas), no por variables de Jinja.
 *
 * Depende de: bootstrap, `entrada_fecha.js` (EntradaFecha), `sha256.min.js`, y de los globales
 * `mostrar_toast` y `quitar_comprimidos` del shell.
 */
(function () {
  'use strict';

  var CFG = document.getElementById('pool-config').dataset;
  var URL_SUBIR                = CFG.urlSubir;
  var URL_URL_EXTERNA          = CFG.urlUrlExterna;
  var URL_PARSEAR_JUSTIFICANTE = CFG.urlParsear;
  var URL_YA_EXISTE            = CFG.urlYaExiste;

  // Qué se le pregunta a un DOC_PROYECTO que entre ahora (ADR-044 §C): el
  // discriminante es el estado del ancla del proyecto, calculado en el servidor.
  var RAMA_INGESTA   = CFG.ramaIngesta;
  var RAMA_PRINCIPAL = CFG.ramaPrincipal;

  // Todas las fechas recogen fecha administrativa, así que todas llevan el tope de hoy
  // (#824): la fecha de trabajo del sistema, que en desarrollo es la del reloj simulado.
  var EF_MAX_HOY  = CFG.maxHoy;
  var _ef_url_ext = null;

  var _modal_url_ext_bs = null;

  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('modal-url-externa').addEventListener('show.bs.modal', function () {
      if (!_ef_url_ext) _ef_url_ext = new EntradaFecha('#ef-url-ext-fecha', { name: '_f_url_ext', maxHoy: EF_MAX_HOY });
    });
  });

  // ================================================================
  // METADATOS DE LA SUBIDA
  // ================================================================
  // ----------------------------------------------------------------
  // Los dos controles del proyecto en el paso de metadatos (ADR-044 §C)
  // ----------------------------------------------------------------
  // Solo existen mientras el tipo elegido en esa fila es DOC_PROYECTO, y de los dos
  // se muestra el que toca según el estado del ancla: mientras el proyecto no tenga
  // principal la pregunta es si este documento lo es; en cuanto lo tiene, si produce
  // un reformado. Al cambiar de tipo se resetean, porque el acto debe ser
  // consciente y no heredado de lo que hubiera marcado antes para otro tipo.
  //
  // Dentro de un mismo lote la rama puede cambiar sin recargar: en cuanto una fila
  // se marca como principal, las demás pasan a la pregunta del reformado — que es
  // exactamente lo que hará el backend, porque procesa el lote en orden y la rama la
  // decide el estado del ancla en ese momento, no el cliente.
  function celda_reformado(prefijo, i) {
    var id_p = 'principal-' + prefijo + '-' + i;
    var id_r = 'reformado-' + prefijo + '-' + i;
    return '<td class="reformado-celda">' +
             '<div class="form-check d-none principal-control">' +
               '<input type="checkbox" class="form-check-input principal-check" id="' + id_p + '">' +
               '<label class="form-check-label small" for="' + id_p + '">Es el proyecto principal</label>' +
               '<div class="small text-secondary mt-1 d-none principal-aviso">' +
                 'Queda anclado como el proyecto de la instalación.' +
               '</div>' +
             '</div>' +
             '<div class="form-check d-none reformado-control">' +
               '<input type="checkbox" class="form-check-input reformado-check" id="' + id_r + '">' +
               '<label class="form-check-label small" for="' + id_r + '">Produce reformado</label>' +
               '<select class="form-select form-select-sm mt-1 d-none reformado-origen">' +
                 '<option value="VOLUNTARIO">Voluntario (art. 76.1)</option>' +
                 '<option value="REQUERIDO">Requerido (art. 68.3)</option>' +
               '</select>' +
               '<div class="small text-warning-emphasis mt-1 d-none reformado-aviso">' +
                 'Obliga a rehacer las fases preceptivas que correspondan.' +
               '</div>' +
             '</div>' +
             '<span class="text-secondary reformado-vacio">—</span>' +
           '</td>';
  }

  function fila_es_proyecto(tr) {
    var opt = tr.querySelector('.tipo-doc-select').selectedOptions[0];
    return !!(opt && opt.dataset.codigo === 'DOC_PROYECTO');
  }

  // Reparte las dos preguntas entre las filas de un lote (ver comentario de arriba).
  function repintar_proyecto(tbody) {
    var filas = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    var alguien_es_principal = filas.some(function (tr) {
      return fila_es_proyecto(tr) && tr.querySelector('.principal-check').checked;
    });

    filas.forEach(function (tr) {
      var proyecto = fila_es_proyecto(tr);
      var check_p  = tr.querySelector('.principal-check');
      // La rama del principal solo se ofrece si el expediente no tiene ancla y
      // nadie más del lote la ha reclamado ya.
      var rama_principal = (RAMA_INGESTA === RAMA_PRINCIPAL) &&
                           (!alguien_es_principal || check_p.checked);

      tr.querySelector('.principal-control').classList.toggle('d-none', !(proyecto && rama_principal));
      tr.querySelector('.reformado-control').classList.toggle('d-none', !(proyecto && !rama_principal));
      tr.querySelector('.reformado-vacio').classList.toggle('d-none', proyecto);
      tr.querySelector('.principal-aviso').classList.toggle('d-none', !check_p.checked);
    });
  }

  function enganchar_reformado(tr) {
    var select  = tr.querySelector('.tipo-doc-select');
    var tbody   = tr.parentNode;
    var check_p = tr.querySelector('.principal-check');
    var check   = tr.querySelector('.reformado-check');
    var origen  = tr.querySelector('.reformado-origen');
    var aviso   = tr.querySelector('.reformado-aviso');

    function al_cambiar_tipo() {
      check_p.checked = false;
      check.checked   = false;
      origen.value    = 'VOLUNTARIO';
      origen.classList.add('d-none');
      aviso.classList.add('d-none');
      repintar_proyecto(tbody);
    }

    select.addEventListener('change', al_cambiar_tipo);
    check_p.addEventListener('change', function () { repintar_proyecto(tbody); });
    check.addEventListener('change', function () {
      origen.classList.toggle('d-none', !check.checked);
      aviso.classList.toggle('d-none', !check.checked);
    });
    al_cambiar_tipo();
  }

  function datos_reformado(tr) {
    var control_p = tr.querySelector('.principal-control');
    var control   = tr.querySelector('.reformado-control');
    var check     = tr.querySelector('.reformado-check');
    // Cada marca viaja solo si su control estaba visible: lo que el usuario no pudo
    // ver, no lo declaró.
    return {
      es_principal:     !control_p.classList.contains('d-none') &&
                        tr.querySelector('.principal-check').checked,
      abre_reformado:   !control.classList.contains('d-none') && check.checked,
      origen_reformado: tr.querySelector('.reformado-origen').value,
    };
  }

  // ================================================================
  // URL EXTERNA
  // ================================================================
  window.abrir_modal_url_externa = function () {
    document.getElementById('url-ext-url').value    = '';
    document.getElementById('url-ext-tipo').value   = '';
    document.getElementById('url-ext-asunto').value = '';
    document.getElementById('url-ext-prioridad').checked = false;
    document.getElementById('url-ext-error').classList.add('d-none');
    if (!_modal_url_ext_bs) {
      _modal_url_ext_bs = new bootstrap.Modal(document.getElementById('modal-url-externa'));
    }
    _modal_url_ext_bs.show();
    setTimeout(function () { if (_ef_url_ext) _ef_url_ext.clear(); }, 150);
  };

  window.guardar_url_externa = function () {
    var url = document.getElementById('url-ext-url').value.trim();
    if (!url) {
      document.getElementById('url-ext-error').textContent = 'La URL es obligatoria.';
      document.getElementById('url-ext-error').classList.remove('d-none');
      return;
    }
    var payload = {
      url:                  url,
      tipo_doc_id:          document.getElementById('url-ext-tipo').value || 1,
      fecha_administrativa: _ef_url_ext ? _ef_url_ext.getValue() : null,
      asunto:               document.getElementById('url-ext-asunto').value.trim(),
      prioridad:            document.getElementById('url-ext-prioridad').checked,
    };
    fetch(URL_URL_EXTERNA, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        mostrar_toast('success', 'URL externa registrada correctamente.');
        setTimeout(function () { window.location.reload(); }, 1200);
      } else {
        document.getElementById('url-ext-error').textContent = data.error || 'Error al guardar.';
        document.getElementById('url-ext-error').classList.remove('d-none');
      }
    })
    .catch(function () {
      document.getElementById('url-ext-error').textContent = 'Error de red.';
      document.getElementById('url-ext-error').classList.remove('d-none');
    });
  };

  // ================================================================
  // SUBIR FICHERO (multipart, #666)
  // ================================================================
  var _modal_subir_bs = null;
  var _archivos_subir  = [];   // File[] elegidos en el input nativo
  var _ef_subida        = [];  // EntradaFecha por fila del paso 2

  window.abrir_modal_subir = function () {
    if (!_modal_subir_bs) {
      _modal_subir_bs = new bootstrap.Modal(document.getElementById('modal-subir'));
      document.getElementById('modal-subir').addEventListener('hidden.bs.modal', resetear_modal_subir);
      document.getElementById('subir-input-ficheros').addEventListener('change', function (e) {
        _archivos_subir = quitar_comprimidos(e.target);
        document.getElementById('btn-subir-siguiente').disabled = (_archivos_subir.length === 0);
      });
    }
    resetear_modal_subir();
    _modal_subir_bs.show();
  };

  window.ir_a_metadatos_subida = function () {
    if (_archivos_subir.length === 0) return;
    mostrar_paso_metadatos_subida();

    var tmpl_tipos = document.getElementById('tmpl-tipos-doc').innerHTML;
    var tbody = document.getElementById('subir-meta-tbody');
    tbody.innerHTML = '';
    _ef_subida = [];

    _archivos_subir.forEach(function (f, i) {
      var tr    = document.createElement('tr');
      var ef_id = 'ef-subir-fecha-' + i;
      tr.innerHTML =
        '<td class="small">' + escapar_html(f.name) + '<div class="aviso-duplicado small mt-1"></div></td>' +
        '<td class="small text-secondary text-nowrap">' + formatear_bytes(f.size) + '</td>' +
        '<td><select class="form-select form-select-sm tipo-doc-select">' + tmpl_tipos + '</select></td>' +
        '<td><div id="' + ef_id + '"></div></td>' +
        '<td class="text-center"><input type="checkbox" class="form-check-input prioridad-check"></td>' +
        celda_reformado('subir', i);
      tbody.appendChild(tr);
      _ef_subida.push(new EntradaFecha('#' + ef_id, { name: '_ef_subir_' + i, maxHoy: EF_MAX_HOY }));
      enganchar_reformado(tr);

      // Enganche 1 (ADR-034 §6, #657): autorrelleno de fecha_administrativa al elegir
      // JUSTIFICANTE_NOTIFICA — parseo transitorio, nunca escribe en notificaciones
      // (eso ocurre al vincular el documento a la tarea NOTIFICAR, ver hook de editar_tarea).
      var select = tr.querySelector('.tipo-doc-select');
      select.addEventListener('change', function () {
        var opt = select.selectedOptions[0];
        if (!opt || opt.dataset.codigo !== 'JUSTIFICANTE_NOTIFICA') return;
        parsear_justificante_especulativo(f, _ef_subida[i]);
      });
    });

    document.getElementById('subir-meta-error').classList.add('d-none');
    comprobar_ya_existentes();
  };

  // ----------------------------------------------------------------
  // Aviso «este fichero ya está en el expediente» (ADR-050 §H, N077; #1007)
  // ----------------------------------------------------------------
  // El navegador calcula el SHA-256 de cada fichero elegido, a trozos (con una librería que
  // sirve BDDAT) y pregunta al servidor si el expediente ya lo tiene, antes de enviar los
  // bytes. Los que ya están no se suben salvo que se marque «Subir igualmente». Es solo un
  // aviso: el servidor sigue calculando su propia huella al subir, y si la comprobación
  // falla por lo que sea, la subida sigue como siempre.
  var _comprobacion = 0;          // identifica la comprobación en curso: una respuesta tardía se ignora
  var _comprobando  = false;

  function huella_de_fichero(fichero, al_progreso) {
    return new Promise(function (resolve, reject) {
      var TROZO = 4 * 1024 * 1024;
      var hasher = window.sha256.create();
      var pos = 0;
      (function siguiente() {
        if (pos >= fichero.size) { resolve(hasher.hex()); return; }
        fichero.slice(pos, pos + TROZO).arrayBuffer().then(function (buf) {
          hasher.update(new Uint8Array(buf));
          pos += TROZO;
          if (al_progreso) al_progreso(Math.min(100, Math.round(100 * pos / fichero.size)));
          setTimeout(siguiente, 0);          // deja respirar a la interfaz entre trozo y trozo
        }).catch(reject);
      }());
    });
  }

  function fecha_legible(iso) {
    if (!iso) return 'sin fecha';
    var p = iso.slice(0, 10).split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }

  // «X» del aviso: nombre, tipo y fecha administrativa; con varios, hasta tres y «y N más».
  function describir_coincidencias(docs) {
    var vistos = docs.slice(0, 3).map(function (d) {
      return '«' + escapar_html(d.nombre) + '» (' + escapar_html(d.tipo || 'sin tipo') + ', ' +
             fecha_legible(d.fecha) + ')';
    });
    var resto = docs.length - vistos.length;
    var texto = vistos.length > 1
      ? vistos.slice(0, -1).join(', ') + (resto > 0 ? ', ' : ' y ') + vistos[vistos.length - 1]
      : vistos[0];
    return resto > 0 ? texto + ' y ' + resto + ' más' : texto;
  }

  function fila_incluida(tr) {
    if (tr.dataset.duplicado !== '1') return true;
    var marca = tr.querySelector('.subir-igualmente');
    return !!(marca && marca.checked);
  }

  function actualizar_boton_subir() {
    var filas = Array.prototype.slice.call(document.querySelectorAll('#subir-meta-tbody tr'));
    var incluidas = filas.filter(fila_incluida).length;
    var excluidas = filas.length - incluidas;
    document.getElementById('subir-meta-contador').textContent =
      filas.length + ' fichero(s) elegidos' +
      (excluidas ? ' — ' + excluidas + ' ya está(n) en el expediente y no se subirá(n) si no marcas «Subir igualmente».'
                 : ' — listos para subir.');
    document.getElementById('btn-subir-texto').textContent =
      incluidas ? 'Subir ' + incluidas + ' fichero(s)' : 'Nada que subir';
    document.getElementById('btn-subir-registrar').disabled = _comprobando || incluidas === 0;
  }

  function marcar_ya_existente(tr, docs, i) {
    tr.dataset.duplicado = '1';
    tr.classList.add('table-warning');
    tr.querySelector('.aviso-duplicado').innerHTML =
      '<div class="text-warning-emphasis"><i class="fas fa-triangle-exclamation me-1"></i>' +
      'Este fichero ya está en el expediente como ' + describir_coincidencias(docs) + '. ' +
      'Si lo subes igualmente se creará otro documento con el mismo contenido, sin guardar ' +
      'otra copia, y con sus propios datos, que deberás indicar.</div>' +
      '<div class="form-check mt-1"><input type="checkbox" class="form-check-input subir-igualmente" ' +
      'id="subir-igualmente-' + i + '">' +
      '<label class="form-check-label fw-semibold" for="subir-igualmente-' + i + '">Subir igualmente</label></div>';
    tr.querySelector('.subir-igualmente').addEventListener('change', actualizar_boton_subir);
  }

  function comprobar_ya_existentes() {
    var token = ++_comprobacion;
    var filas = Array.prototype.slice.call(document.querySelectorAll('#subir-meta-tbody tr'));
    _comprobando = true;
    actualizar_boton_subir();
    if (!window.sha256) { _comprobando = false; actualizar_boton_subir(); return; }

    var huellas = new Array(filas.length);
    var nota = function (i, texto) {
      if (token === _comprobacion) filas[i].querySelector('.aviso-duplicado').textContent = texto;
    };

    // Una a una: dos ficheros de 300 MB a la vez no caben en la memoria de un puesto.
    var cadena = Promise.resolve();
    _archivos_subir.forEach(function (f, i) {
      cadena = cadena.then(function () {
        if (token !== _comprobacion) return;
        nota(i, 'Comprobando si ya está en el expediente… 0 %');
        return huella_de_fichero(f, function (pct) {
          nota(i, 'Comprobando si ya está en el expediente… ' + pct + ' %');
        }).then(function (h) { huellas[i] = h; nota(i, ''); })
          .catch(function () { nota(i, ''); });          // sin huella, esa fila se sube como siempre
      });
    });

    cadena.then(function () {
      if (token !== _comprobacion) return;
      var lista = huellas.filter(Boolean);
      if (!lista.length) return;
      return fetch(URL_YA_EXISTE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hashes: lista }),
      }).then(function (r) { return r.json(); })
        .then(function (data) {
          if (token !== _comprobacion || !data.ok) return;
          huellas.forEach(function (h, i) {
            if (h && data.coincidencias[h]) marcar_ya_existente(filas[i], data.coincidencias[h], i);
          });
        });
    }).catch(function () { /* aviso best-effort: si falla, se sube como siempre */ })
      .then(function () {
        if (token !== _comprobacion) return;
        _comprobando = false;
        actualizar_boton_subir();
      });
  }

  // Parseo transitorio (sin persistir nada, #657): sube el fichero suelto al
  // endpoint de preview y, si es un justificante NOTIFICA reconocido,
  // autorrellena la fecha de puesta a disposición en la EntradaFecha de la fila.
  function parsear_justificante_especulativo(fichero, entradaFecha) {
    var formData = new FormData();
    formData.append('fichero', fichero);

    fetch(URL_PARSEAR_JUSTIFICANTE, { method: 'POST', body: formData })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.reconocido && data.fecha_puesta_disposicion) {
          entradaFecha.setValue(data.fecha_puesta_disposicion.slice(0, 10));
        }
      })
      .catch(function () { /* autorrelleno best-effort — sin bloquear la subida */ });
  }

  window.volver_a_elegir_subida = function () {
    _comprobacion++;            // deja de comprobar lo elegido: se va a elegir otra vez
    _comprobando = false;
    mostrar_paso_elegir_subida();
  };

  function mostrar_paso_elegir_subida() {
    document.getElementById('subir-paso-elegir').classList.remove('d-none');
    document.getElementById('subir-paso-metadatos').classList.add('d-none');
    document.getElementById('btn-subir-cancelar').classList.remove('d-none');
    document.getElementById('btn-subir-siguiente').classList.remove('d-none');
    document.getElementById('btn-subir-volver').classList.add('d-none');
    document.getElementById('btn-subir-registrar').classList.add('d-none');
  }

  function mostrar_paso_metadatos_subida() {
    document.getElementById('subir-paso-elegir').classList.add('d-none');
    document.getElementById('subir-paso-metadatos').classList.remove('d-none');
    document.getElementById('btn-subir-cancelar').classList.add('d-none');
    document.getElementById('btn-subir-siguiente').classList.add('d-none');
    document.getElementById('btn-subir-volver').classList.remove('d-none');
    document.getElementById('btn-subir-registrar').classList.remove('d-none');
  }

  window.subir_ficheros = function () {
    var metadatos = [];
    var formData = new FormData();
    document.querySelectorAll('#subir-meta-tbody tr').forEach(function (tr, i) {
      // Un fichero que ya está en el expediente no se envía salvo que se marque «Subir igualmente».
      if (!fila_incluida(tr)) return;
      metadatos.push(Object.assign({
        tipo_doc_id:          tr.querySelector('.tipo-doc-select').value || '1',
        fecha_administrativa: _ef_subida[i] ? _ef_subida[i].getValue() : null,
        prioridad:            tr.querySelector('.prioridad-check').checked,
      }, datos_reformado(tr)));
      formData.append('ficheros', _archivos_subir[i]);
    });
    formData.append('metadatos', JSON.stringify(metadatos));

    var btn = document.getElementById('btn-subir-registrar');
    btn.disabled = true;

    fetch(URL_SUBIR, { method: 'POST', body: formData })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        bootstrap.Modal.getInstance(document.getElementById('modal-subir')).hide();
        setTimeout(function () {
          mostrar_toast('success', 'Se han subido ' + data.creados + ' documento(s) al pool.');
          setTimeout(function () { window.location.reload(); }, 1800);
        }, 350);
      } else {
        document.getElementById('subir-meta-error').textContent = data.error || 'Error al subir.';
        document.getElementById('subir-meta-error').classList.remove('d-none');
        btn.disabled = false;
      }
    })
    .catch(function () {
      document.getElementById('subir-meta-error').textContent = 'Error de red.';
      document.getElementById('subir-meta-error').classList.remove('d-none');
      btn.disabled = false;
    });
  };

  function resetear_modal_subir() {
    _archivos_subir = [];
    _ef_subida = [];
    _comprobacion++;            // si había una comprobación en curso, su respuesta se ignora
    _comprobando = false;
    document.getElementById('subir-input-ficheros').value = '';
    document.getElementById('subir-meta-tbody').innerHTML = '';
    document.getElementById('subir-error-elegir').classList.add('d-none');
    document.getElementById('subir-meta-error').classList.add('d-none');
    document.getElementById('btn-subir-siguiente').disabled = true;
    mostrar_paso_elegir_subida();
  }

  // ================================================================
  // UTILIDADES
  // ================================================================
  function escapar_html(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatear_bytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

}());
