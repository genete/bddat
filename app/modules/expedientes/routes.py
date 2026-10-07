"""Blueprint para gestión de expedientes.

RUTAS:
    GET  /expedientes/                          → listado (shell V2, datos vía API)
    GET  /expedientes/<id>                      → redirect a /expedientes/?sel=<id> (ADR-023 #543)
    GET  /expedientes/<id>/fragmento            → parcial lectura para el inspector (ADR-023 #543)
    GET  /expedientes/<id>/editar-fragmento     → parcial edición para el inspector (ADR-023 §5 #543)
    GET  /expedientes/<id>/editar               → redirect a /expedientes/?sel=<id> (ADR-023 #543)
    POST /expedientes/<id>/editar               → guardar cambios; JSON si XHR, redirect si no (#543)
    GET  /expedientes/<id>/gestionar-municipios → parcial modal grande municipios (ADR-023 §6 #543)
    POST /expedientes/<id>/municipios           → guardar municipios; JSON si XHR (#543)
    GET  /expedientes/<id>/fases/<fase_id>/certificado-cumplimiento → vista del certificado (#947)
    GET  /expedientes/<id>/solicitudes/<sol_id>/certificado-cierre → vista del cierre de la solicitud (#996)
    (otros: arbol, pool_documentos, cert_pdf…)

    Seguimiento se movió a seguimiento_y_huerfanos (#630, ADR-038) — ya no vive aquí.

VERSIÓN: 2.0
FECHA: 2026-06-11
ISSUE: #543
"""
import json
from datetime import date
from flask import g
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.expedientes import Expediente
from app.models.proyectos import Proyecto
from app.models.usuarios import Usuario
from app.services.usuarios import usuarios_tramitadores
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.fases import Fase
from app.models.solicitudes import Solicitud
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services.almacenamiento.adaptador import AlmacenNoDisponible, MENSAJE_ALMACEN_NO_DISPONIBLE
from app.services.almacenamiento.contenido import (
    ContenidoNoUtilizable, servir_descarga, tiene_contenido_propio,
)
from app.services.almacenamiento.formatos import FormatoNoAdmitido
from app.services.ingesta_pool import (
    FicheroAIngestar, comprobar_rectificacion_url, exigir_url_externa, ingestar_en_pool,
    rectificar_url_externa,
)
from app.services.consolidacion_defectos import agrupar_defectos_por_origen
from app.services.detalle_nodo import info_apertura_documento
from app.services.parser_justificante_notifica import parsear_justificante_notifica
from app.services.notificaciones import fecha_sugerida
from app.services.assembler import build_sujeto
from app.services.reformados import (
    RAMA_PRINCIPAL,
    anclar_principal,
    declarar_desde_metadatos,
    es_doc_proyecto,
    motivo_fases_enganchadas,
    rama_de_la_ingesta,
    revertir_reformado,
    sincronizar_principal,
    sincronizar_reformado,
    ultimo_reformado,
)
from app.services import bitacora as bitacora_svc
from app.services import sellos
from app.services.invariantes_esftt import es_documento_critico
from app.utils.permisos import (
    puede_cambiar_responsable,
    verificar_acceso_expediente,
    tiene_permiso,
)
from app.utils.metadata import cargar_metadata
from app.utils.formularios import (
    aplicar_checkbox,
    aplicar_fecha_obligatoria,
    aplicar_fk,
    aplicar_numero,
    aplicar_texto_obligatorio,
    form_completo,
)

# template_folder apunta a app/modules/expedientes/templates/
bp = Blueprint('expedientes', __name__,
               url_prefix='/expedientes',
               template_folder='templates')


@bp.route('/')
@login_required
def listado_v2():
    """
    Listado de expedientes con scroll infinito (Fase 2).

    Usa estructura CSS v2 (Grid A/B/C) con carga dinámica de datos
    mediante JavaScript + API /api/expedientes.

    Características:
    - Scroll infinito con paginación cursor
    - Filtros dinámicos (búsqueda, estado)
    - Header/Footer sticky
    - Tabla con thead sticky
    - Botón scroll-to-top

    Nota: Esta ruta NO carga expedientes iniciales, solo renderiza
          la estructura HTML. Los datos se cargan vía AJAX.
    """
    meta = cargar_metadata('expedientes')
    columns = meta.get('listado_v2', {}).get('columns', [])
    puede_cambiar_resp = puede_cambiar_responsable()
    usuarios = usuarios_tramitadores() if puede_cambiar_resp else []
    tipos_exp = [
        {'v': str(t.id), 't': t.tipo}
        for t in TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    ]
    tipos_ia = [
        {'v': str(t.id), 't': t.siglas}
        for t in TipoIA.query.order_by(TipoIA.siglas).all()
    ]
    return render_template(
        'expedientes/listado_v2.html',
        columns=columns,
        puede_cambiar_resp=puede_cambiar_resp,
        usuarios=usuarios,
        tipos_exp=tipos_exp,
        tipos_ia=tipos_ia,
    )


@bp.route('/<int:id>')
@login_required
def detalle(id):
    """Redirige al listado con el inspector abierto en ese expediente (ADR-023 §9 / #543)."""
    return redirect(url_for('expedientes.listado_v2', sel=id))


# =============================================================================
# FRAGMENTO INSPECTOR — lectura y edición (ADR-023 §5, ADR-024 §4 / #543)
# =============================================================================

@bp.route('/<int:id>/fragmento')
@login_required
def fragmento(id):
    """Fragmento HTML de lectura para el inspector (ADR-024 §4 / #543)."""
    expediente = Expediente.query.get_or_404(id)
    g.expediente_actual = expediente
    if not tiene_permiso('acceder_expediente'):
        return '', 403

    num_solicitudes = len(expediente.solicitudes) if expediente.solicitudes else 0
    num_activas = sum(1 for s in expediente.solicitudes if s.activa)
    if num_solicitudes == 0:
        estado_tramitacion = 'SIN_SOLICITUDES'
    elif num_activas > 0:
        estado_tramitacion = 'EN_TRAMITE'
    else:
        estado_tramitacion = 'RESUELTO'

    return render_template(
        'expedientes/_inspector_expediente.html',
        expediente=expediente,
        estado_tramitacion=estado_tramitacion,
        num_solicitudes=num_solicitudes,
        num_activas=num_activas,
        puede_cambiar_resp=puede_cambiar_responsable(),
        puede_editar=tiene_permiso('editar_expediente'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
def editar_fragmento(id):
    """Fragmento HTML de edición para el inspector (ADR-023 §5 / #543)."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return '', 403

    tipos_expedientes = TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    tipos_ia = TipoIA.query.order_by(TipoIA.siglas).all()
    usuarios = usuarios_tramitadores()

    return render_template(
        'expedientes/_editar_fragmento_expediente.html',
        expediente=expediente,
        tipos_expedientes=tipos_expedientes,
        tipos_ia=tipos_ia,
        usuarios=usuarios,
        puede_cambiar_resp=puede_cambiar_responsable(),
    )


@bp.route('/<int:id>/gestionar-municipios')
@login_required
def gestionar_municipios(id):
    """Fragmento modal grande — gestión de municipios del proyecto (ADR-023 §6 / #543)."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return '', 403

    return render_template(
        'expedientes/_modal_municipios_expediente.html',
        expediente=expediente,
    )


@bp.route('/<int:id>/municipios', methods=['POST'])
@login_required
def actualizar_municipios(id):
    """Reemplaza los municipios del proyecto. JSON si XHR, redirect si no (#543)."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if resultado:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Sin permiso para editar este expediente']}), 403
        return resultado

    municipios_ids_raw = request.form.getlist('municipios[]')
    try:
        municipios_ids = [int(mid) for mid in municipios_ids_raw if mid]
    except ValueError:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['IDs de municipios inválidos']}), 400
        flash('IDs de municipios inválidos', 'danger')
        return redirect(url_for('expedientes.listado_v2', sel=id))

    if not municipios_ids:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Debe añadir al menos un municipio afectado']}), 400
        flash('Debe añadir al menos un municipio afectado', 'danger')
        return redirect(url_for('expedientes.listado_v2', sel=id))

    try:
        proyecto = expediente.proyecto
        MunicipioProyecto.query.filter_by(proyecto_id=proyecto.id).delete()
        for municipio_id in municipios_ids:
            db.session.add(MunicipioProyecto(municipio_id=municipio_id, proyecto_id=proyecto.id))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': [str(e)]}), 500
        flash(f'Error al actualizar municipios: {str(e)}', 'danger')
        return redirect(url_for('expedientes.listado_v2', sel=id))

    if is_xhr:
        return jsonify({'ok': True, 'message': 'Municipios actualizados correctamente.'})
    flash('Municipios actualizados correctamente.', 'success')
    return redirect(url_for('expedientes.listado_v2', sel=id))


@bp.route('/<int:id>/arbol')
@login_required
def arbol(id):
    """Vista de árbol del expediente (#500, ADR-016): isla React 'expediente-arbol'.

    El árbol y su detalle se sirven vía API (/api/expedientes/<id>/arbol). Aquí solo
    se renderiza el contenedor de la isla; el control de acceso real lo imponen tanto
    esta ruta como cada endpoint de la API.
    """
    expediente = Expediente.query.get_or_404(id)

    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    return render_template('expedientes/arbol.html', expediente=expediente)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edición de expediente y proyecto asociado (ADR-023 §5 / #543).

    GET  → redirect al listado con inspector abierto (ya no es página).
    POST → JSON si X-Requested-With:XMLHttpRequest; redirect si no (fallback).
    Municipios se gestionan en endpoint separado /municipios (modal grande).

    Contrato del cuerpo (#832): edición PARCIAL — solo se escriben los campos que
    viajan en el formulario. Enviarlos vacíos sí los vacía, salvo los NOT NULL del
    proyecto (título, descripción, finalidad, emplazamiento, fecha), que devuelven
    error de validación con los mismos mensajes del alta. Las casillas solo se
    escriben si el formulario declara el centinela `_form_completo`.
    """
    expediente = Expediente.query.get_or_404(id)

    if request.method == 'GET':
        return redirect(url_for('expedientes.listado_v2', sel=id))

    # --- POST ---
    resultado = verificar_acceso_expediente(expediente, 'editar')
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if resultado:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Sin permiso para editar este expediente']}), 403
        return resultado

    # Campo AUSENTE ≠ campo VACÍO (#832): antes, cualquier cuerpo parcial vaciaba
    # en silencio todo lo que no mencionaba —así se perdieron tipo_expediente_id,
    # ia_id, los tres flags técnicos y la tensión de varios expedientes—. Ahora un
    # campo que no viaja no se toca; uno que viaja vacío se vacía (o da error si su
    # columna es NOT NULL). Las casillas necesitan además el centinela de
    # formulario completo: desmarcada y no enviada son indistinguibles en HTML.
    completo = form_completo(request.form)
    errores = []

    proyecto = expediente.proyecto

    aplicar_fk(request.form, 'tipo_expediente_id', expediente)
    aplicar_checkbox(request.form, 'heredado', expediente, completo)

    if puede_cambiar_responsable():
        aplicar_fk(request.form, 'responsable_id', expediente)

    # Los cinco NOT NULL del proyecto — mismas exigencias y mismos mensajes que el
    # alta (alta_expediente.nuevo), que es de donde salen estas filas.
    aplicar_texto_obligatorio(request.form, 'titulo', proyecto,
                              'El título del proyecto es obligatorio.', errores)
    aplicar_texto_obligatorio(request.form, 'descripcion', proyecto,
                              'La descripción del proyecto es obligatoria.', errores)
    aplicar_texto_obligatorio(request.form, 'finalidad', proyecto,
                              'La finalidad del proyecto es obligatoria.', errores)
    aplicar_texto_obligatorio(request.form, 'emplazamiento', proyecto,
                              'El emplazamiento es obligatorio.', errores)
    aplicar_fecha_obligatoria(request.form, 'fecha', proyecto,
                              'Fecha de proyecto inválida (formato esperado: YYYY-MM-DD).',
                              errores)

    aplicar_fk(request.form, 'ia_id', proyecto)
    aplicar_numero(request.form, 'max_tension_nominal_kv', proyecto,
                   'Tensión máxima inválida.', errores)
    aplicar_checkbox(request.form, 'es_modificacion', proyecto, completo)
    aplicar_checkbox(request.form, 'sin_linea_aerea', proyecto, completo)
    aplicar_checkbox(request.form, 'solo_suelo_urbano_urbanizable', proyecto, completo)

    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores}), 400
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('expedientes.listado_v2', sel=id))

    try:
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': [str(e)]}), 500
        flash(f'Error al actualizar expediente: {str(e)}', 'danger')
        return redirect(url_for('expedientes.listado_v2', sel=id))

    if is_xhr:
        return jsonify({
            'ok': True,
            'message': f'Expediente AT-{expediente.numero_at} actualizado correctamente.',
        })
    flash(f'Expediente AT-{expediente.numero_at} actualizado correctamente.', 'success')
    return redirect(url_for('expedientes.listado_v2', sel=id))


@bp.route('/asignacion-masiva', methods=['POST'])
@login_required
def asignacion_masiva():
    """Asigna un técnico a varios expedientes huérfanos a la vez (#612 / N034).

    Solo actúa sobre expedientes SIN responsable — nunca reasigna uno que ya
    tiene técnico (eso sigue siendo exclusivamente individual, vía /editar).
    El filtro server-side por responsable_id IS NULL es defensa en profundidad:
    aunque el listado ya solo muestra huérfanos, evita pisar una asignación
    hecha por otra persona entre la carga de la lista y el envío del formulario.
    """
    if not puede_cambiar_responsable():
        return jsonify({'ok': False, 'errors': ['Sin permiso para asignar expedientes']}), 403

    data = request.get_json(silent=True) or {}
    ids_raw = data.get('expediente_ids') or []
    responsable_id_raw = data.get('responsable_id')

    try:
        ids = [int(i) for i in ids_raw]
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'errors': ['Identificadores de expediente inválidos']}), 400

    if not ids or not responsable_id_raw:
        return jsonify({'ok': False, 'errors': ['Selecciona expedientes y un técnico']}), 400

    try:
        responsable_id = int(responsable_id_raw)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'errors': ['Técnico inválido']}), 400

    tecnico = Usuario.query.get(responsable_id)
    if not tecnico or not tecnico.tiene_rol('TRAMITADOR'):
        return jsonify({'ok': False, 'errors': ['Técnico no válido']}), 400

    expedientes = Expediente.query.filter(
        Expediente.id.in_(ids), Expediente.responsable_id.is_(None)
    ).all()
    omitidos = sorted(set(ids) - {e.id for e in expedientes})

    for e in expedientes:
        e.responsable_id = responsable_id

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'errors': [f'Error al guardar: {e}']}), 500

    return jsonify({'ok': True, 'actualizados': len(expedientes), 'omitidos': omitidos})


@bp.route('/tarea/<int:tarea_id>/generar_cert', methods=['POST'])
@login_required
def generar_cert(tarea_id):
    """Genera el certificado de plazo cumplido para una tarea ESPERAR_PLAZO."""
    from app.services.certificados import crear_cert
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'gestionar_tarea')
    if resultado:
        return resultado
    try:
        crear_cert(tarea)
        flash('Certificado de plazo cumplido generado.', 'success')
    except (ValueError, NotImplementedError) as exc:
        flash(str(exc), 'danger')
    return redirect(request.referrer or url_for('expedientes.listado_v2'))


@bp.route('/cert/<int:cert_id>/pdf')
@login_required
def cert_pdf(cert_id):
    """Genera y devuelve el PDF de un certificado interno (bddat://)."""
    from app.models.certificados import Certificado
    from app.services.cert_pdf import generar_pdf_certificado

    cert = Certificado.query.get_or_404(cert_id)
    expediente = cert.documento.solicitud_expediente if hasattr(cert.documento, 'solicitud_expediente') else None

    # Acceder al expediente vía documento → expediente
    from app.models.expedientes import Expediente
    expediente = Expediente.query.get_or_404(cert.documento.expediente_id)

    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    tipo_cert = cert.tipo
    try:
        pdf_bytes = generar_pdf_certificado(cert, expediente, tipo_cert)
    except NotImplementedError:
        # CERT_CUMPLIMIENTO_FASE (#947) y CERT_CIERRE_FASE (#956) no tienen PDF: se
        # consultan en su vista HTML.
        # Solo se llega aquí por acceso directo — `info_apertura_documento` ya lo
        # manda al modal —, y un 400 explícito es mejor que un 500.
        abort(400, description='Este certificado no tiene PDF: se consulta en su vista.')

    from flask import Response
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'inline; filename="cert_{tipo_cert}_{cert.id}.pdf"'
        },
    )


# Conjuntos de tipos de tarea que requieren documentos (espejo de invariantes_esftt.py)
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALIZAR', 'NOTIFICAR'}
_TIPOS_DOC_USADO_OPCIONAL      = {'ELABORAR'}   # visible en UI pero no obligatorio al finalizar
_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO'}


# ===========================================================================
# POOL DE DOCUMENTOS — issue #180
# Gestión masiva del pool documental de un expediente (Vía 1)
# ===========================================================================

def _documento_es_referenciado(doc):
    """
    True si el documento tiene referencias activas que impiden su borrado.

    Usa únicamente backrefs SQLAlchemy — NO hardcodear SQL directo.
    Si en el futuro se añade una nueva tabla con FK a documentos.id:
      1. Añadir el backref en el modelo correspondiente.
      2. Añadir un check aquí.

    Backrefs consultados:
      doc.reformado_proyecto           → ReformadoProyecto.documento_id  (uselist=False)
      doc.anclado_como_proyecto_principal → Proyecto.documento_principal_id
      doc.vinculos_tarea               → DocumentoTarea.documento_id     (lista, con rol)
      doc.notificacion                 → Notificacion.documento_id       (uselist=False, ADR-034)
      doc.anclado_en_solicitud         → Solicitud.documento_solicitud_id
      doc.anclado_en_fin_instruccion   → Solicitud.documento_fin_instruccion_id
      doc.anclado_en_cierre            → Solicitud.documento_cierre_id
      doc.fases_resultado              → Fase.documento_resultado_id     (lista, #947)
      doc.certificado                  → Certificado.documento_id        (uselist=False, #947)

    `doc.notificacion` (#738 punto 2): sin este check, un justificante que ya
    perdió su vínculo `DocumentoTarea` (desvinculado, ver punto 1) parece libre
    aunque la fila `Notificacion` siga viva apuntando a él — y esa fila tiene
    `ondelete='CASCADE'`, así que borrar el documento se lleva por delante toda
    la evidencia de la notificación (canal, resultado, fecha).

    Las tres anclas de solicitud (#838): la guarda del pool es «si algo lo usa, no
    se borra», y a estos tres los usa la solicitud —no una tarea— a través de una FK
    propia (ADR-041 §D bis, ADR-043 §D). Faltaban desde que se creó cada una, así
    que el pool los daba por libres: la FK es `NO ACTION` y el borrado moría en un
    IntegrityError con traza, en vez de decir quién lo estaba usando. El caso que lo
    destapa es el CERT_FIN_INSTRUCCION, que además no lo consume ninguna tarea
    mientras la fase que resuelve no exista — con lo que ninguna de las tres
    referencias anteriores lo veía.

    Las dos últimas (#947), el mismo agujero por otras dos FK sin `ON DELETE`: el
    documento de un certificado emitido (`certificados.documento_id`) no cuelga de
    ninguna tarea —el de cumplimiento de la fase, por diseño—, y el que cierra una
    fase (`fases.documento_resultado_id`) puede no colgar de ninguna si se eligió
    así al cerrarla. En los dos casos el pool los daba por libres y el borrado
    moría en un IntegrityError con un 500.
    """
    if doc.reformado_proyecto:
        return True
    if doc.anclado_como_proyecto_principal:
        return True
    if doc.vinculos_tarea:
        return True
    if doc.notificacion:
        return True
    if doc.anclado_en_solicitud or doc.anclado_en_fin_instruccion or doc.anclado_en_cierre:
        return True
    if doc.fases_resultado:
        return True
    if sellos.es_certificado_emitido(doc):
        return True
    return False


# Qué decirle a quien intenta borrar del pool un documento que ancla una solicitud.
# El mensaje genérico —«está referenciado en tramitación»— es cierto pero deja al
# usuario sin saber qué lo referencia ni qué hacer, y en el caso del certificado de
# fin de instrucción hay un gesto propio que sí lo deshace (#838, ADR-043 §F).
_MOTIVO_ANCLA = {
    'anclado_en_fin_instruccion': (
        'Este documento es el certificado de fin de instrucción de la solicitud '
        '#{sol}: mientras conste, su instrucción está sellada. Para retirarlo, '
        'deshaga el certificado desde la solicitud — no se borra desde el pool.'
    ),
    'anclado_en_solicitud': (
        'Este documento es el escrito de solicitud de la solicitud #{sol}, del que '
        'cuelga la fecha de inicio del plazo para resolver. No puede eliminarse '
        'mientras la solicitud lo tenga por ancla.'
    ),
    # Desde #996 lo dice antes `sellos.motivo_sellado`, porque el certificado tiene su
    # fila en `certificados`. Queda por si un documento ancla el cierre sin ella.
    'anclado_en_cierre': (
        'Este documento es el certificado de cierre de la solicitud #{sol}. No puede '
        'eliminarse mientras la solicitud lo tenga por ancla: retírelo desde el '
        'inspector de la solicitud, con justificación.'
    ),
}


def _motivo_ancla(doc):
    """Explicación de por qué no se borra, si el documento ancla alguna solicitud.

    El corte del proyecto va aparte del diccionario: las tres anclas de solicitud
    comparten forma —una lista de solicitudes de la que sale el número— y esta no,
    porque el backref es escalar y lo que hay que explicar no es de quién es el
    documento, sino qué gesto lo suelta.

    Los sellos van primero (#947): el documento que cita un certificado cuelga
    además de su tarea, y el mensaje genérico de «referenciado» no diría que la
    salida es deshacer el certificado. El texto es el de `sellos.motivo_sellado`,
    el mismo que da `editar_tarea` al intentar desvincularlo.
    """
    motivo = sellos.motivo_sellado(doc)
    if motivo is not None:
        return motivo
    if doc.fases_resultado:
        fase = doc.fases_resultado[0]
        nombre = fase.tipo_fase.nombre if fase.tipo_fase else f'#{fase.id}'
        return (
            f'Este documento cierra la fase «{nombre}»: es su documento de resultado. '
            f'No puede eliminarse mientras la fase lo tenga; para soltarlo, reabra la '
            f'fase desde su inspector.'
        )
    if doc.reformado_proyecto is not None:
        # Mismo motivo que niega revertir_reformado (R3, #895): si ya lo tiene, decirlo
        # aquí evita mandar al usuario a un gesto que va a fallar igual al intentarlo.
        motivo_fases = motivo_fases_enganchadas(doc.reformado_proyecto)
        if motivo_fases is not None:
            return motivo_fases
        return (
            'Este documento abre un reformado de proyecto: mientras conste, el '
            'proyecto tiene una versión más. Para retirarlo, desmarque «Produce un '
            'reformado de proyecto» al editar sus metadatos — y solo si es el último '
            'reformado del expediente.'
        )
    if doc.anclado_como_proyecto_principal:
        return (
            'Este documento es el proyecto de la instalación: de él cuelga saber '
            'sobre qué versión se instruye. Para retirarlo, desmarque «Es el proyecto '
            'principal» al editar sus metadatos, o ancle otro documento en su lugar.'
        )
    for atributo, plantilla in _MOTIVO_ANCLA.items():
        solicitudes = getattr(doc, atributo, None) or []
        if solicitudes:
            return plantilla.format(sol=solicitudes[0].id)
    return None


@bp.route('/<int:id>/documentos')
@login_required
def pool_documentos(id):
    """Pool de documentos — listado del expediente."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    documentos_raw = Documento.query.filter_by(
        expediente_id=id
    ).order_by(Documento.id.desc()).all()

    # El único corte reversible es el último (ADR-044 §C), y se calcula aquí una
    # vez: la interfaz necesita saberlo para dejar desmarcar o explicar por qué no.
    corte_reversible = ultimo_reformado(id)
    # Y qué se le pregunta a un DOC_PROYECTO que entre ahora (§C): mientras el
    # proyecto no tenga principal anclado, la pregunta es si lo es.
    rama_ingesta = rama_de_la_ingesta(expediente)

    docs_lista = []
    for doc in documentos_raw:
        nombre = doc.nombre_visible()
        # La extensión sale del nombre, salvo en los bddat://: su nombre es el del
        # tipo («Informe n.º 2») y lo que haya tras el último punto no es una extensión.
        partes = nombre.rsplit('.', 1)
        extension = ('' if (doc.url or '').startswith('bddat://')
                     else partes[1].lower() if len(partes) == 2 and partes[1] else '')
        es_url_externa = (doc.url or '').startswith(('http://', 'https://'))
        corte = doc.reformado_proyecto
        docs_lista.append({
            'doc':             doc,
            'nombre_display':  nombre,
            'extension':       extension,
            'es_url_externa':  es_url_externa,
            'es_referenciado': _documento_es_referenciado(doc),
            'apertura':        info_apertura_documento(id, doc, estricto=False),
            'reformado':       corte,
            'reformado_ultimo': (corte is not None and corte_reversible is not None
                                 and corte.id == corte_reversible.id),
            'es_principal':    bool(doc.anclado_como_proyecto_principal),
        })

    tipos_doc = TipoDocumento.query.order_by(TipoDocumento.nombre).all()

    return render_template(
        'expedientes/pool_documentos.html',
        expediente=expediente,
        docs_lista=docs_lista,
        tipos_doc=tipos_doc,
        rama_ingesta=rama_ingesta,
        rama_principal=RAMA_PRINCIPAL,
    )


@bp.route('/<int:id>/documentos/json')
@login_required
def pool_documentos_json(id):
    """API JSON — lista de documentos del expediente para SelectorBusqueda (issue #166).

    Devuelve: { "ok": true, "docs": [{"v": "42", "t": "informe.pdf — Informe técnico — 15/01/2026"}, ...] }
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    documentos = Documento.query.filter_by(
        expediente_id=id
    ).order_by(Documento.id.desc()).all()

    docs = []
    for doc in documentos:
        nombre = doc.nombre_visible()
        tipo_nombre = doc.tipo_doc.nombre if doc.tipo_doc else 'Sin tipo'
        if doc.fecha_administrativa:
            fecha_str = doc.fecha_administrativa.strftime('%d/%m/%Y')
        else:
            fecha_str = 'Sin fecha'
        texto = f'{nombre} — {tipo_nombre} — {fecha_str}'
        docs.append({'v': str(doc.id), 't': texto})

    return jsonify({'ok': True, 'docs': docs})


@bp.route('/<int:id>/documentos/subir', methods=['POST'])
@login_required
def pool_subir_documento(id):
    """
    Ingesta multipart al pool (#666, ADR-032 §1/§4, ADR-050 §B): sube ficheros reales
    (diálogo nativo del navegador) al almacén y crea un documento por cada uno. La
    Despensa usa esta misma ruta.

    Recibe multipart: 'ficheros' (N ficheros) + 'metadatos' (JSON, array
    paralelo por índice a 'ficheros'): [{tipo_doc_id, fecha_administrativa,
    asunto, prioridad}, ...].

    Todo o nada: se validan todos los ficheros antes de enviar el primero al almacén
    (un formato no admitido, 422; un fichero vacío cuenta como tal). Duplicado exacto
    (mismo contenido ya en el almacén): no se vuelve a guardar, pero sí se crea el
    Documento — el usuario ha pedido explícitamente añadirlo (ADR-032 §4, sin bloquear
    ni avisar).

    El envío al almacén y el armado de los Documento viven en
    `app/services/ingesta_pool.py`, porque el alta de expediente hace lo mismo y no
    puede llamarse a sí misma por HTTP. Aquí queda lo que solo tiene sentido hablando
    HTTP: el permiso, el parseo del JSON de metadatos, el commit del lote y la
    traducción del error a código de estado (422 formato, 503 almacén sin contestar).

    Permiso 'subir_documento' (ADR-027 / #501): aportar al pool no edita el
    expediente — el documento nace sin vínculo (huérfano) y es el técnico quien
    decide si lo encaja. Sin limitación de rol.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'subir_documento')
    if resultado:
        return resultado

    ficheros = request.files.getlist('ficheros')
    if not ficheros:
        return jsonify({'ok': False, 'error': 'Ningún fichero recibido'}), 400

    try:
        metadatos = json.loads(request.form.get('metadatos') or '[]')
    except ValueError:
        return jsonify({'ok': False, 'error': 'Metadatos inválidos'}), 400
    if not isinstance(metadatos, list):
        return jsonify({'ok': False, 'error': 'Metadatos inválidos'}), 400

    try:
        entrantes, items = [], []
        for i, fichero in enumerate(ficheros):
            if not fichero.filename:
                continue
            item = metadatos[i] if i < len(metadatos) else {}

            fecha_admin = None
            fecha_raw = item.get('fecha_administrativa') or None
            if fecha_raw:
                try:
                    fecha_admin = date.fromisoformat(fecha_raw)
                except ValueError:
                    pass

            entrantes.append(FicheroAIngestar(
                fichero.stream, fichero.filename,
                tipo_doc_id=int(item.get('tipo_doc_id') or 1),
                fecha_administrativa=fecha_admin,
                asunto=(item.get('asunto') or '').strip() or None,
                prioridad=bool(item.get('prioridad')),
            ))
            items.append(item)

        creados_docs = ingestar_en_pool(expediente, entrantes)
        # De uno en uno y en orden: la bifurcación de un lote de DOC_PROYECTO la decide el
        # estado del ancla tras el documento anterior (§C de ADR-044).
        for documento, item in zip(creados_docs, items):
            db.session.add(documento)
            db.session.flush()   # el corte necesita el id del documento
            declarar_desde_metadatos(documento, item, usuario_id=current_user.id)

        db.session.commit()
    except FormatoNoAdmitido as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 422
    except AlmacenNoDisponible:
        db.session.rollback()
        return jsonify({'ok': False, 'error': MENSAJE_ALMACEN_NO_DISPONIBLE}), 503
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({
        'ok': True,
        'creados': len(creados_docs),
        'documentos': [
            {
                'id':              d.id,
                'nombre':          d.nombre_visible(),
                'tipo_doc':        d.tipo_doc.nombre if d.tipo_doc else None,
                'tipo_doc_codigo': d.tipo_doc.codigo if d.tipo_doc else None,
                'fecha':           d.fecha_administrativa.isoformat() if d.fecha_administrativa else None,
            }
            for d in creados_docs
        ],
    })


@bp.route('/<int:id>/documentos/parsear_justificante', methods=['POST'])
@login_required
def pool_parsear_justificante(id):
    """
    POST .../documentos/parsear_justificante — enganche 1 de subida al pool
    (ADR-034 §6, #657): parseo especulativo y transitorio del justificante
    NOTIFICA elegido en el paso de metadatos (`.tipo-doc-select` código
    JUSTIFICANTE_NOTIFICA), disparado desde `pool_documentos.html` antes de
    confirmar la subida. Solo autorrelleno de UX (fecha_administrativa del
    propio Documento) — no escribe nada en `notificaciones` (eso ocurre en el
    hook de `editar_tarea` al vincular el documento a la tarea NOTIFICAR).

    Multipart: 'fichero' y, opcional, 'tipo_doc_codigo' (el tipo elegido).
    Nunca 404/422 por contenido no reconocido — mismo contrato que el parser
    (#655): devuelve `{reconocido: false}`. Además del parseo devuelve
    `fecha_sugerida` (AAAA-MM-DD o null, #928 §10): la fecha que corresponde
    al tipo elegido, decidida en el servidor (`notificaciones.fecha_sugerida`).
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'subir_documento')
    if resultado:
        return resultado

    fichero = request.files.get('fichero')
    if not fichero or not fichero.filename:
        return jsonify({'error': 'Ningún fichero recibido'}), 400

    parseo = parsear_justificante_notifica(fichero.stream)

    payload = parseo.to_dict()
    sugerida = fecha_sugerida(request.form.get('tipo_doc_codigo'), parseo)
    payload['fecha_sugerida'] = sugerida.isoformat() if sugerida else None
    return jsonify(payload)


@bp.route('/<int:id>/documentos/<int:doc_id>/fichero')
@login_required
def pool_descargar_documento(id, doc_id):
    """Sirve el contenido de un documento desde el almacén. Para URLs externas, redirige.

    bddat:// (ADR-006, #610): certificados redirige a su PDF; diagnósticos no
    tiene descarga posible (400 explícito, no 404 silencioso) — desde #629 la
    apertura real de un diagnóstico pasa por diagnostico_modal(), esta rama
    queda como defensa ante un acceso directo a esta URL; recurso no
    contemplado falla alto, igual que en info_apertura_documento().

    Contenido propio (`fichero_ref`, ADR-050 §E): lo sirve el módulo de contenido, con sus
    cabeceras de seguridad. Si el contenido está ausente o dañado, 409 con el mensaje para
    el usuario; si el almacén no contesta, 503 «inténtalo en unos minutos». No valen 404 ni
    500 para esos dos mensajes: sus manejadores pintan una plantilla fija y esconderían el
    texto. Un documento sin contenido ni enlace es 404.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    url = doc.url or ''
    if url.startswith(('http://', 'https://')):
        return redirect(url)

    if url.startswith('bddat://'):
        partes = url[len('bddat://'):].split('/')
        recurso = partes[0] if partes else ''
        if recurso == 'certificados':
            # Qué se pinta lo dice la fila, no la url (#947, D2): los certificados de
            # cumplimiento y de cierre de la fase no tienen PDF, se consultan en su
            # vista (como un diagnóstico).
            cert = doc.certificado
            if cert is not None and cert.tipo in (sellos.CERT_CUMPLIMIENTO_FASE,
                                                  sellos.CERT_CIERRE_FASE):
                abort(400, description='Este certificado no tiene PDF: se consulta en su vista.')
            return redirect(url_for('expedientes.cert_pdf', cert_id=int(partes[1])))
        if recurso == 'diagnosticos':
            abort(400, description='Este documento no tiene representación descargable.')
        raise NotImplementedError(f'Apertura no definida para recurso bddat://: {recurso!r}')

    if not tiene_contenido_propio(doc):
        abort(404)
    try:
        return servir_descarga(doc)
    except ContenidoNoUtilizable as exc:
        abort(409, description=str(exc))
    except AlmacenNoDisponible:
        abort(503, description=MENSAJE_ALMACEN_NO_DISPONIBLE)


@bp.route('/<int:id>/documentos/<int:doc_id>/diagnostico-modal')
@login_required
def diagnostico_modal(id, doc_id):
    """Fragmento modal grande — representación de solo lectura de un DIAGNOSTICO (#629).

    bddat://diagnosticos/<id> (ADR-006) no tiene fichero descargable — se consulta
    aquí, en un modal (ADR-023 §6, AppModalLarge) enganchado desde los puntos que
    resuelven la apertura vía info_apertura_documento(): inspector del árbol, menú
    contextual, despensa y este mismo pool.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return '', 403

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)
    diagnostico = doc.diagnostico
    if diagnostico is None:
        abort(404)

    return render_template(
        'expedientes/_diagnostico_modal_fragmento.html',
        resultado=diagnostico.resultado,
        grupos=agrupar_defectos_por_origen(diagnostico.defectos or []),
    )


@bp.route('/<int:id>/fases/<int:fase_id>/certificado-cumplimiento')
@login_required
def cert_cumplimiento_fase_vista(id, fase_id):
    """Fragmento modal grande — el certificado de cumplimiento de la fase (#947, D2).

    Vista única para los dos momentos: con el certificado emitido pinta lo sellado;
    sin él, el borrador calculado al vuelo (qué documento se citaría, o qué falta),
    sin guardar nada. Siempre de solo lectura: emitir y deshacer son gestos de la
    API del árbol. Se abre desde el botón de la fase y, emitido, desde el documento
    del certificado en el pool, la Despensa o el inspector
    (`info_apertura_documento`), igual que un diagnóstico.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return '', 403

    fase = Fase.query.get_or_404(fase_id)
    if fase.solicitud.expediente_id != id:
        abort(404)
    if fase.tipo_fase is None or not fase.tipo_fase.es_finalizadora:
        abort(404)

    from app.services.cert_cumplimiento_fase import vista
    return render_template('expedientes/_cert_cumplimiento_fase_fragmento.html',
                           vista=vista(fase))


@bp.route('/<int:id>/fases/<int:fase_id>/certificado-cierre')
@login_required
def cert_cierre_fase_vista(id, fase_id):
    """Fragmento modal grande — el certificado de cierre de la fase finalizadora (#956).

    Mismo patrón que `cert_cumplimiento_fase_vista`: vista única para los dos
    momentos y siempre de solo lectura. Sin emitir, el informe «¿cómo voy?»
    calculado al vuelo (hecho, pendiente, salvado), sin guardar nada; emitido, la
    foto fija de `certificados.datos` (D4), que no se recalcula, con su huella. Se
    abre desde el bloque «Cierre de la fase» del inspector y, emitido, desde su
    documento en el pool, la Despensa o el inspector (`info_apertura_documento`).
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return '', 403

    fase = Fase.query.get_or_404(fase_id)
    if fase.solicitud.expediente_id != id:
        abort(404)
    if fase.tipo_fase is None or not fase.tipo_fase.es_finalizadora:
        abort(404)

    from app.services.cert_cierre_fase import vista
    return render_template('expedientes/_cert_cierre_fase_fragmento.html',
                           vista=vista(fase))


@bp.route('/<int:id>/solicitudes/<int:sol_id>/certificado-cierre')
@login_required
def cert_cierre_solicitud_vista(id, sol_id):
    """Fragmento modal grande — el certificado de cierre de la solicitud (#996).

    Mismo patrón que los de la fase: vista única para los dos momentos y siempre de
    solo lectura. Sin emitir, lo que diría el certificado y qué falta, calculado al
    vuelo sin guardar nada; emitido, su foto fija, que no se recalcula. Se abre desde
    el bloque «Cierre de la solicitud» del inspector y, emitido, desde su documento
    en el pool, la Despensa o el inspector (`info_apertura_documento`).
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return '', 403

    solicitud = Solicitud.query.get_or_404(sol_id)
    if solicitud.expediente_id != id:
        abort(404)

    from app.services.cert_cierre_solicitud import vista
    return render_template('expedientes/_cert_cierre_solicitud_fragmento.html',
                           vista=vista(solicitud))


@bp.route('/<int:id>/documentos/url-externa', methods=['POST'])
@login_required
def pool_registrar_url_externa(id):
    """
    Registra una URL externa en el pool (BOE, Notifica, sede electrónica, etc.)
    sin subir ningún fichero. Recibe JSON, devuelve JSON.

    Solo admite `http://` y `https://` (ADR-050 §C, #1007): cualquier otra cosa —una ruta
    local, un `bddat://` escrito a mano, otro esquema— da 422 con el motivo. Los `bddat://`
    los crean solo los servicios de certificados y diagnósticos; una ruta local sería un
    escritor de rutas vivo tras la migración.

    Permiso 'subir_documento' (ADR-027 / #501): aportar al pool no edita el
    expediente; sin limitación de rol (igual que pool_subir_documento).
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'subir_documento')
    if resultado:
        return resultado

    datos = request.get_json(silent=True) or {}
    url = (datos.get('url') or '').strip()
    if not url:
        return jsonify({'ok': False, 'error': 'La URL es obligatoria'}), 400
    try:
        url = exigir_url_externa(url)
    except ValueError as e:
        return jsonify({'ok': False, 'error': str(e)}), 422

    fecha_admin = None
    fecha_raw = datos.get('fecha_administrativa') or None
    if fecha_raw:
        try:
            fecha_admin = date.fromisoformat(fecha_raw)
        except ValueError:
            pass

    try:
        doc = Documento(
            expediente_id=id,
            url=url,
            tipo_doc_id=int(datos.get('tipo_doc_id') or 1),
            fecha_administrativa=fecha_admin,
            asunto=(datos.get('asunto') or '').strip() or None,
            prioridad=1 if datos.get('prioridad') else 0,
        )
        db.session.add(doc)
        db.session.flush()   # el corte necesita el id del documento
        declarar_desde_metadatos(doc, datos, usuario_id=current_user.id)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


def _fecha_del_payload(fecha_raw):
    """Fecha administrativa del cuerpo JSON: ISO → `date`; vacía o mal formada →
    None. Solo el parseo — quien asigna el resultado recibe el ValueError de los
    validadores del modelo (#824)."""
    if not fecha_raw:
        return None
    try:
        return date.fromisoformat(fecha_raw)
    except ValueError:
        return None


def _cambia_lo_sellable(doc, datos) -> bool:
    """El cuerpo de `pool_editar_documento` cambia la fecha, el tipo o la URL
    de `doc` — lo que un sello protege (#947). Con la misma interpretación que
    aplica la ruta al escribir: url vacía no cambia nada; tipo vacío es OTROS (1)."""
    url_nueva = (datos.get('url') or '').strip()
    if url_nueva and url_nueva != doc.url:
        return True
    if 'tipo_doc_id' in datos:
        try:
            if int(datos['tipo_doc_id'] or 1) != doc.tipo_doc_id:
                return True
        except (TypeError, ValueError):
            return True   # valor ilegible: la escritura lo rechazará con 422
    if ('fecha_administrativa' in datos
            and _fecha_del_payload(datos['fecha_administrativa']) != doc.fecha_administrativa):
        return True
    return False


@bp.route('/<int:id>/documentos/<int:doc_id>/editar', methods=['POST'])
@login_required
def pool_editar_documento(id, doc_id):
    """Editar metadatos de un documento del pool — devuelve JSON.

    La `url` solo se rectifica en un documento de URL externa y por otra `http(s)://`, y la
    anterior queda en la bitácora (ADR-050 §M, #1007); en un fichero propio o un `bddat://`
    un cuerpo con una `url` distinta da 422. Una `url` vacía, igual a la actual o ausente no
    cambia nada: el formulario reenvía los campos aunque no cambien.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    datos = request.get_json(silent=True) or {}
    # Solo se actualizan los campos presentes en el payload.
    # Esto permite edición masiva parcial (p.ej. solo cambiar prioridad)
    # sin sobreescribir los demás metadatos.

    # La validez de la URL va ANTES que el sello: si fuera al revés, a quien intenta cambiar
    # la url de un fichero citado por un certificado se le diría «deshaga el certificado»
    # cuando, aun deshaciéndolo, no podría.
    url_nueva = str(datos.get('url') or '').strip()
    cambia_url = bool(url_nueva) and url_nueva != doc.url
    if cambia_url:
        try:
            comprobar_rectificacion_url(doc, url_nueva)
        except ValueError as e:
            return jsonify({'ok': False, 'error': str(e)}), 422

    # Sello (#947, ADR-049 §F): del documento que cita un certificado, o del propio
    # certificado, no se cambian la fecha, el tipo ni la URL. Se comparan
    # VALORES y no presencia de claves: el formulario completo del pool reenvía
    # todos los campos aunque no cambien, y bloquear por «viene la clave» impediría
    # editar el asunto de un documento citado. La consulta al sello solo se paga
    # si de verdad cambia alguno de los tres.
    if _cambia_lo_sellable(doc, datos):
        motivo = sellos.motivo_sellado(doc)
        if motivo is not None:
            return jsonify({'ok': False, 'error': motivo}), 422

    try:
        if cambia_url:
            rectificar_url_externa(doc, url_nueva, current_user.id)

        if 'tipo_doc_id' in datos:
            doc.tipo_doc_id = int(datos['tipo_doc_id'] or 1)

        if 'fecha_administrativa' in datos:
            # El parseo va aparte de la asignación: asignar dentro de su except
            # se tragaba también el ValueError del invariante de fecha futura
            # (#824), que quedaba en un borrado silencioso de la fecha. Las
            # otras tres rutas del pool ya asignan en el constructor, fuera de
            # su try de parseo, y por eso no tenían este agujero.
            doc.fecha_administrativa = _fecha_del_payload(datos['fecha_administrativa'])

        if 'asunto' in datos:
            doc.asunto = (datos['asunto'] or '').strip() or None

        if 'prioridad' in datos:
            doc.prioridad = 1 if datos['prioridad'] else 0

        if 'observaciones' in datos:
            doc.observaciones = (datos['observaciones'] or '').strip() or None

        # El corte del proyecto (ADR-044 §C). La marca solo se interpreta si viene
        # en el payload —clave ausente conserva, REGLAS_DESARROLLO §rutas que editan—
        # porque el control de la interfaz solo existe mientras el tipo elegido es
        # DOC_PROYECTO. El cambio de tipo, en cambio, sí actúa solo: un corte de un
        # documento que ha dejado de ser proyecto no significa nada, y retirarlo pasa
        # por las mismas reglas que el desmarcado.
        db.session.flush()
        db.session.expire(doc, ['tipo_doc'])   # el tipo puede acabar de cambiar
        if 'es_principal' in datos:
            sincronizar_principal(
                doc,
                es_principal=bool(datos.get('es_principal')),
                usuario_id=current_user.id,
            )
        if 'abre_reformado' in datos:
            sincronizar_reformado(
                doc,
                abre_reformado=bool(datos.get('abre_reformado')),
                origen=datos.get('origen_reformado'),
                usuario_id=current_user.id,
            )
        elif 'tipo_doc_id' in datos and not es_doc_proyecto(doc):
            # Dejar de ser proyecto suelta lo que el documento sostenía, con las
            # mismas reglas que desmarcarlo a mano.
            if doc.reformado_proyecto is not None:
                revertir_reformado(doc, usuario_id=current_user.id)
            if doc.anclado_como_proyecto_principal:
                sincronizar_principal(doc, es_principal=False, usuario_id=current_user.id)

        db.session.commit()
    except ValueError as e:
        # El invariante de fecha obligatoria (DOC_PROYECTO, justificantes de
        # notificación — #928 N1 §4) y el resto de validadores del modelo
        # lanzan ValueError: error del cliente, no del servidor (#928).
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


@bp.route('/<int:id>/documentos/<int:doc_id>/anclar-principal', methods=['POST'])
@login_required
def pool_anclar_principal(id, doc_id):
    """Ancla un documento del pool como proyecto principal (ADR-044 §D).

    Gesto propio porque hay dos sitios que lo necesitan: el aviso de divergencia del
    checklist documental —donde el técnico acaba de cubrir el requisito del proyecto
    con un documento distinto del anclado— y el propio pool. Si ya había otro
    anclado, mueve el ancla y la bitácora guarda de dónde a dónde.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    try:
        anclar_principal(doc, usuario_id=current_user.id)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 422

    return jsonify({'ok': True, 'documento_id': doc.id})


@bp.route('/<int:id>/documentos/<int:doc_id>/borrar', methods=['POST'])
@login_required
def pool_borrar_documento(id, doc_id):
    """Borrar un documento del pool si no está referenciado — devuelve JSON."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    if _documento_es_referenciado(doc):
        return jsonify({
            'ok': False,
            'error': _motivo_ancla(doc) or
                     'El documento está referenciado en tramitación y no puede eliminarse'
        }), 422

    es_critico = es_documento_critico(doc)
    tipo_documento = doc.tipo_doc.codigo if doc.tipo_doc else None
    documento_id = doc.id

    try:
        if es_critico:
            # #738 punto 3: borrar un justificante sin referencias activas se permite
            # (no cerramos la puerta), pero debe quedar rastro en bitácora.
            bitacora_svc.registrar(
                current_user.id, 'BORRAR', 'documentos', documento_id,
                detalle={'tipo_documento': tipo_documento, 'sujeto': build_sujeto(expediente)},
            )
        db.session.delete(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


