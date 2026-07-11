/**
 * tablas-maestras-pasos.js — Editor anidado de la secuencia de tareas de un
 * Trámite (tramites_tareas + tramites_tareas_documentos, #171).
 *
 * El fragmento de edición del inspector se inyecta con innerHTML — los
 * <script> que lleve dentro NO se ejecutan (ver
 * project_inspector_vs_modal_scripts.md). Por eso este script vive fuera del
 * fragmento (cargado una sola vez desde listado.html) y actúa por delegación
 * de eventos sobre document, más un MutationObserver sobre el body del
 * inspector para serializar el estado inicial en cuanto el fragmento aparece
 * en el DOM (no hay evento propio de "fragmento de edición cargado").
 *
 * El DOM es la fuente de verdad — no hay estado JS en memoria: cada acción
 * (añadir/quitar/mover fila, cambiar un select) vuelve a leer el DOM entero
 * dentro de [data-pasos-editor] y reescribe el input oculto pasos_json.
 */
(function () {
    function root() {
        return document.querySelector('[data-pasos-editor]');
    }

    function renumerar(r) {
        r.querySelectorAll('[data-pasos-list] > [data-paso]').forEach(function (paso, i) {
            var badge = paso.querySelector('[data-paso-orden]');
            if (badge) badge.textContent = String(i + 1);
        });
    }

    function serializar(r) {
        var listEl = r.querySelector('[data-pasos-list]');
        var jsonEl = r.querySelector('[data-pasos-json]');
        if (!listEl || !jsonEl) return;

        var pasos = [];
        listEl.querySelectorAll(':scope > [data-paso]').forEach(function (pasoEl) {
            var tareaSel = pasoEl.querySelector('[data-paso-tarea]');
            var documentos = [];
            pasoEl.querySelectorAll('[data-paso-docs] > [data-doc-row]').forEach(function (docEl) {
                var tipoSel = docEl.querySelector('[data-doc-tipo]');
                documentos.push({
                    rol: docEl.querySelector('[data-doc-rol]').value,
                    tipo_documento_id: tipoSel.value ? parseInt(tipoSel.value, 10) : null,
                    obligatorio: docEl.querySelector('[data-doc-obligatorio]').checked,
                });
            });
            pasos.push({
                tipo_tarea_id: tareaSel && tareaSel.value ? parseInt(tareaSel.value, 10) : null,
                documentos: documentos,
            });
        });
        jsonEl.value = JSON.stringify(pasos);
    }

    function clonar(nombrePlantilla) {
        var tpl = document.querySelector('[data-pasos-editor] template[' + nombrePlantilla + ']');
        if (!tpl || !tpl.content.firstElementChild) return null;
        return tpl.content.firstElementChild.cloneNode(true);
    }

    document.addEventListener('click', function (e) {
        var r = root();
        if (!r || !r.contains(e.target)) return;

        if (e.target.closest('[data-paso-add]')) {
            var nuevoPaso = clonar('data-paso-template');
            var listEl = r.querySelector('[data-pasos-list]');
            if (nuevoPaso && listEl) {
                listEl.appendChild(nuevoPaso);
                renumerar(r);
                serializar(r);
            }
            return;
        }

        var pasoRemoveBtn = e.target.closest('[data-paso-remove]');
        if (pasoRemoveBtn) {
            var pasoElR = pasoRemoveBtn.closest('[data-paso]');
            if (pasoElR) { pasoElR.remove(); renumerar(r); serializar(r); }
            return;
        }

        var pasoUpBtn = e.target.closest('[data-paso-up]');
        if (pasoUpBtn) {
            var pasoElU = pasoUpBtn.closest('[data-paso]');
            var prev = pasoElU && pasoElU.previousElementSibling;
            if (pasoElU && prev) {
                pasoElU.parentNode.insertBefore(pasoElU, prev);
                renumerar(r);
                serializar(r);
            }
            return;
        }

        var pasoDownBtn = e.target.closest('[data-paso-down]');
        if (pasoDownBtn) {
            var pasoElD = pasoDownBtn.closest('[data-paso]');
            var next = pasoElD && pasoElD.nextElementSibling;
            if (pasoElD && next) {
                pasoElD.parentNode.insertBefore(next, pasoElD);
                renumerar(r);
                serializar(r);
            }
            return;
        }

        var docAddBtn = e.target.closest('[data-doc-add]');
        if (docAddBtn) {
            var pasoElDoc = docAddBtn.closest('[data-paso]');
            var nuevoDoc = clonar('data-doc-template');
            if (pasoElDoc && nuevoDoc) {
                pasoElDoc.querySelector('[data-paso-docs]').appendChild(nuevoDoc);
                serializar(r);
            }
            return;
        }

        var docRemoveBtn = e.target.closest('[data-doc-remove]');
        if (docRemoveBtn) {
            var docEl = docRemoveBtn.closest('[data-doc-row]');
            if (docEl) { docEl.remove(); serializar(r); }
            return;
        }
    });

    document.addEventListener('change', function (e) {
        var r = root();
        if (r && r.contains(e.target)) serializar(r);
    });

    // Serializa el estado inicial en cuanto el editor aparece en el DOM
    // (inyección por innerHTML, sin evento propio que lo señale).
    var inspectorBody = document.getElementById('app-inspector-body');
    if (inspectorBody && window.MutationObserver) {
        new MutationObserver(function () {
            var r = root();
            if (r) serializar(r);
        }).observe(inspectorBody, { childList: true });
    }
})();
