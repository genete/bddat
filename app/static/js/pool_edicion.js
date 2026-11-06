/**
 * pool_edicion.js — comportamiento del formulario de edición del inspector del pool (#881,
 * ADR-053 §E): la fecha obligatoria según el tipo (#1036) y los dos controles del proyecto, el
 * ancla y el corte de un reformado (ADR-044 §C y §D).
 *
 * El inspector inyecta el fragmento con `innerHTML` y no ejecuta sus `<script>` (ADR-023): el
 * estado inicial llega ya pintado desde `_editar_fragmento_documento.html` y esto solo reacciona
 * a los cambios, por delegación a nivel `document`. Lo que el servidor sabe del documento va en
 * `data-*` del formulario (`data-principal-original`, `data-reformado-original`,
 * `data-reformado-bloqueado`, `data-rama`).
 *
 * Contrato con el marco: todo script que cambie un campo sin que el usuario teclee dispara un
 * `change` que burbujee, o «Guardar» no se enciende (GUIA_COMPONENTES_INTERACTIVOS).
 */
(function () {
  'use strict';

  function aviso_cambio(campo) {
    campo.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // Habilita o deshabilita un bloque entero de controles (un deshabilitado no viaja en el
  // formulario: es lo que le dice al servidor «el usuario no pudo tocar esto»). El bloque es un
  // `<fieldset>`: un solo `disabled` cubre a la vez el marcador y los controles, de modo que no
  // puede quedar el marcador enviado y la casilla sin enviar, que el servidor leería como
  // «el usuario la desmarcó».
  function activar(bloque, activo) {
    bloque.disabled = !activo;
  }

  // Pinta los controles según el tipo elegido. Misma lógica que el estado inicial de Jinja.
  function pintar(form) {
    var select    = form.querySelector('[name="tipo_doc_id"]');
    var opcion    = select.selectedOptions[0];
    var proyecto  = !!(opcion && opcion.dataset.codigo === 'DOC_PROYECTO');
    var rama      = form.dataset.rama;
    var ver_principal = proyecto && rama === 'PRINCIPAL';
    var ver_reformado = proyecto && rama === 'REFORMADO';
    var bloqueado = !!form.dataset.reformadoBloqueado;

    // La fecha: obligatoria si el tipo la exige, y se dice qué fecha es (#1036).
    var exige = !!(opcion && opcion.dataset.fechaObligatoria === '1');
    var fecha = form.querySelector('[name="fecha_administrativa"]');
    var ayuda = form.querySelector('[data-pool-fecha-ayuda]');
    fecha.required = exige;
    ayuda.classList.toggle('d-none', !exige);
    if (exige) {
      ayuda.innerHTML = '<span class="text-danger">*</span> ';
      ayuda.appendChild(document.createTextNode(opcion.dataset.ayudaFecha));
    }

    // El ancla del proyecto. Si el documento ya es el principal (#1040) el control se enseña
    // marcado y bloqueado —el principal sale del alta y no se suelta ni se reclasifica, solo se
    // sustituye su fichero—, y entonces el selector de tipo tampoco se toca (ya viene deshabilitado).
    var principal = form.querySelector('[data-pool-bloque="principal"]');
    var check_p   = principal.querySelector('[name="es_principal"]');
    var principal_bloqueado = !!form.dataset.principalOriginal;
    principal.classList.toggle('d-none', !ver_principal);
    activar(principal, ver_principal && !principal_bloqueado);
    principal.querySelector('[data-pool-aviso]')
      .classList.toggle('d-none', !(check_p.checked && !form.dataset.principalOriginal));
    principal.querySelector('[data-pool-bloqueo]')
      .classList.toggle('d-none', !(principal_bloqueado && ver_principal));

    // El corte de un reformado
    var reformado = form.querySelector('[data-pool-bloque="reformado"]');
    var check_r   = reformado.querySelector('[name="abre_reformado"]');
    reformado.classList.toggle('d-none', !ver_reformado);
    activar(reformado, ver_reformado && !bloqueado);
    reformado.querySelector('[data-pool-detalle]').classList.toggle('d-none', !check_r.checked);
    reformado.querySelector('[data-pool-aviso]')
      .classList.toggle('d-none', !(check_r.checked && !form.dataset.reformadoOriginal));
    reformado.querySelector('[data-pool-bloqueo]').classList.toggle('d-none', !(bloqueado && ver_reformado));
  }

  document.addEventListener('change', function (e) {
    var form = e.target.closest && e.target.closest('form[data-pool-form]');
    if (!form) return;
    var campo = e.target;

    if (campo.name === 'tipo_doc_id') {
      // Al cambiar el tipo, la marca no se hereda: el acto debe ser consciente. Solo conserva lo
      // que el documento ya era, y solo si sigue siendo un proyecto.
      var proyecto = campo.selectedOptions[0].dataset.codigo === 'DOC_PROYECTO';
      var check_p = form.querySelector('[name="es_principal"]');
      var check_r = form.querySelector('[name="abre_reformado"]');
      var era_p = proyecto && !!form.dataset.principalOriginal;
      var era_r = proyecto && !!form.dataset.reformadoOriginal;
      if (check_p.checked !== era_p) { check_p.checked = era_p; aviso_cambio(check_p); }
      if (check_r.checked !== era_r) { check_r.checked = era_r; aviso_cambio(check_r); }
    }

    if (campo.name === 'abre_reformado' && !campo.checked && form.dataset.reformadoOriginal) {
      // Desmarcar un corte que existe destruye un dato: se pregunta una vez.
      if (!confirm('Este documento abre un reformado de proyecto.\n\n' +
                   'Al desmarcarlo, el proyecto vuelve a tener una versión menos y ' +
                   'las fases dejan de poder colgar de ella. ¿Continuar?')) {
        campo.checked = true;
      }
    }

    pintar(form);
  });

}());
