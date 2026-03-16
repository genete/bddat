"""
Blueprint para administración de plantillas de escritos administrativos.

Rutas de formulario:
- GET  /admin/plantillas/             — Listado de plantillas
- GET  /admin/plantillas/nueva/       — Formulario alta nueva plantilla
- POST /admin/plantillas/nueva/       — Guardar nueva plantilla
- GET  /admin/plantillas/<id>/        — Detalle (solo lectura) + panel tokens
- GET  /admin/plantillas/<id>/editar  — Formulario edición pre-rellenado
- POST /admin/plantillas/<id>/editar  — Guardar cambios
- GET  /admin/plantillas/<id>/descargar — Descarga del .docx registrado
- POST /admin/plantillas/<id>/activar — Activar/desactivar plantilla

Endpoints AJAX (cascada ESFTT):
- GET  /admin/plantillas/api/tipos-solicitud  — Tipos solicitud (filtrar=1: solo whitelist por exp)
- GET  /admin/plantillas/api/tipos-fase       — Tipos fase (filtrar=1: solo whitelist por sol)
- GET  /admin/plantillas/api/tipos-tramite    — Tipos trámite (filtrar=1: solo whitelist por fase)
- GET  /admin/plantillas/api/tokens           — Tokens Capa 1 (stub — Capa 2 en Fase 5)
"""
import os

import werkzeug.utils
from docxtpl import DocxTemplate
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)
from flask_login import login_required

from app import db
from app.decorators import role_required
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.expedientes_solicitudes import ExpedienteSolicitud
from app.models.fases_tramites import FaseTramite
from app.models.plantillas import Plantilla
from app.models.solicitudes_fases import SolicitudFase
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tramites import TipoTramite

bp = Blueprint(
    'admin_plantillas',
    __name__,
    url_prefix='/admin/plantillas',
    template_folder='templates',
)

# Campos fijos del ContextoBaseExpediente — siempre disponibles en cualquier plantilla
CAMPOS_BASE = [
    {'campo': 'numero_at',              'descripcion': 'Número administrativo (AT-XXXX)'},
    {'campo': 'expediente_id',          'descripcion': 'ID técnico interno del expediente'},
    {'campo': 'titular_nombre',         'descripcion': 'Nombre / Razón Social del titular'},
    {'campo': 'titular_nif',            'descripcion': 'NIF del titular'},
    {'campo': 'titular_direccion',      'descripcion': 'Dirección de notificación preferente'},
    {'campo': 'proyecto_titulo',        'descripcion': 'Título del proyecto técnico'},
    {'campo': 'proyecto_finalidad',     'descripcion': 'Finalidad de la instalación'},
    {'campo': 'proyecto_emplazamiento', 'descripcion': 'Emplazamiento descriptivo'},
    {'campo': 'instrumento_ambiental',  'descripcion': 'Siglas del instrumento ambiental (AAI, AAU, EXENTO...)'},
    {'campo': 'responsable_nombre',     'descripcion': 'Nombre completo del tramitador asignado'},
    {'campo': 'municipios',             'descripcion': 'Lista de municipios afectados', 'tipo': 'lista'},
    {'campo': 'fecha_hoy',              'descripcion': 'Fecha actual en formato DD/MM/YYYY'},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plantillas_dir():
    """Directorio absoluto de plantillas .docx."""
    base = current_app.config.get('PLANTILLAS_BASE', '')
    return os.path.join(base, 'plantillas') if base else ''


def _fragmentos_dir():
    """Directorio absoluto de fragmentos .docx."""
    base = current_app.config.get('PLANTILLAS_BASE', '')
    return os.path.join(base, 'fragmentos') if base else ''


def _listar_fragmentos() -> list[str]:
    """Devuelve nombres de fichero .docx en PLANTILLAS_BASE/fragmentos/."""
    d = _fragmentos_dir()
    if not d or not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith('.docx'))


def _build_tokens(plantilla=None) -> dict:
    """
    Construye el contexto de tokens para el panel del supervisor.

    campos:     CAMPOS_BASE (Capa 1 fija)
    consultas:  ConsultaNombrada activas (ordenadas por nombre)
    fragmentos: ficheros .docx en PLANTILLAS_BASE/fragmentos/
    """
    consultas = (
        ConsultaNombrada.query
        .filter_by(activo=True)
        .order_by(ConsultaNombrada.nombre)
        .all()
    )
    fragmentos = _listar_fragmentos()
    return {'campos': list(CAMPOS_BASE), 'consultas': consultas, 'fragmentos': fragmentos}


def _validar_plantilla_docx(ruta_abs: str) -> str | None:
    """Intenta parsear el .docx con DocxTemplate. Devuelve mensaje de error o None si ok."""
    try:
        DocxTemplate(ruta_abs)
        return None
    except Exception as e:
        return str(e)


def _guardar_docx(archivo) -> str | None:
    """
    Guarda el fichero .docx subido en PLANTILLAS_BASE/plantillas/.
    Devuelve el nombre de fichero (ruta_plantilla) o None si hay error.
    """
    if not archivo or not archivo.filename:
        return None

    base = current_app.config.get('PLANTILLAS_BASE', '')
    if not base:
        flash('PLANTILLAS_BASE no está configurado en el servidor.', 'danger')
        return None

    filename = werkzeug.utils.secure_filename(archivo.filename)
    if not filename.lower().endswith('.docx'):
        flash('Solo se admiten ficheros .docx.', 'danger')
        return None

    destino_dir = _plantillas_dir()
    os.makedirs(destino_dir, exist_ok=True)
    archivo.save(os.path.join(destino_dir, filename))
    return filename


def _form_data_to_plantilla(plantilla: Plantilla) -> bool:
    """
    Rellena los campos de una Plantilla desde request.form.
    Devuelve False si hay errores de validación (con flash).
    """
    codigo = request.form.get('codigo', '').strip().upper()
    nombre = request.form.get('nombre', '').strip()

    if not codigo:
        flash('El código es obligatorio.', 'danger')
        return False
    if not nombre:
        flash('El nombre es obligatorio.', 'danger')
        return False

    tipo_documento_id = request.form.get('tipo_documento_id') or None
    if not tipo_documento_id:
        flash('El tipo de documento es obligatorio.', 'danger')
        return False

    plantilla.codigo           = codigo
    plantilla.nombre           = nombre
    plantilla.descripcion      = request.form.get('descripcion', '').strip() or None
    plantilla.variante         = request.form.get('variante', '').strip() or None
    plantilla.tipo_documento_id   = int(tipo_documento_id)
    plantilla.tipo_expediente_id  = int(request.form['tipo_expediente_id']) if request.form.get('tipo_expediente_id') else None
    plantilla.tipo_solicitud_id   = int(request.form['tipo_solicitud_id'])  if request.form.get('tipo_solicitud_id')  else None
    plantilla.tipo_fase_id        = int(request.form['tipo_fase_id'])       if request.form.get('tipo_fase_id')       else None
    plantilla.tipo_tramite_id     = int(request.form['tipo_tramite_id'])    if request.form.get('tipo_tramite_id')    else None
    plantilla.contexto_clase      = request.form.get('contexto_clase', '').strip() or None
    plantilla.activo              = 'activo' in request.form
    return True


def _selects_context():
    """Devuelve los querysets para los selects del formulario."""
    return {
        'tipos_expediente': TipoExpediente.query.order_by(TipoExpediente.tipo).all(),
        'tipos_solicitud':  TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'tipos_fase':       TipoFase.query.order_by(TipoFase.nombre).all(),
        'tipos_tramite':    TipoTramite.query.order_by(TipoTramite.nombre).all(),
        # Solo tipos producidos internamente (excluir EXTERNO — documentos aportados por el interesado)
        'tipos_documento':  (
            TipoDocumento.query
            .filter(TipoDocumento.origen != 'EXTERNO')
            .order_by(TipoDocumento.nombre)
            .all()
        ),
    }


# ---------------------------------------------------------------------------
# Endpoints AJAX (cascada ESFTT)
# ---------------------------------------------------------------------------

@bp.route('/api/tipos-solicitud')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def api_tipos_solicitud():
    """
    Devuelve tipos de solicitud disponibles.
    Si filtrar=1 y tipo_expediente_id dado: solo los de la whitelist expedientes_solicitudes.
    Sin filtro: todos.
    """
    tipo_expediente_id = request.args.get('tipo_expediente_id', type=int)
    filtrar = request.args.get('filtrar') == '1'

    if filtrar and tipo_expediente_id:
        tipos = (
            TipoSolicitud.query
            .join(ExpedienteSolicitud,
                  ExpedienteSolicitud.tipo_solicitud_id == TipoSolicitud.id)
            .filter(ExpedienteSolicitud.tipo_expediente_id == tipo_expediente_id)
            .order_by(TipoSolicitud.siglas)
            .all()
        )
    else:
        tipos = TipoSolicitud.query.order_by(TipoSolicitud.siglas).all()

    return jsonify([
        {'id': t.id, 'texto': f'{t.siglas} — {t.descripcion}'}
        for t in tipos
    ])


@bp.route('/api/tipos-fase')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def api_tipos_fase():
    """
    Devuelve tipos de fase disponibles.
    Si filtrar=1 y tipo_solicitud_id dado: solo los de la whitelist solicitudes_fases.
    """
    tipo_solicitud_id = request.args.get('tipo_solicitud_id', type=int)
    filtrar = request.args.get('filtrar') == '1'

    if filtrar and tipo_solicitud_id:
        tipos = (
            TipoFase.query
            .join(SolicitudFase,
                  SolicitudFase.tipo_fase_id == TipoFase.id)
            .filter(SolicitudFase.tipo_solicitud_id == tipo_solicitud_id)
            .order_by(TipoFase.nombre)
            .all()
        )
    else:
        tipos = TipoFase.query.order_by(TipoFase.nombre).all()

    return jsonify([
        {'id': t.id, 'texto': t.nombre}
        for t in tipos
    ])


@bp.route('/api/tipos-tramite')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def api_tipos_tramite():
    """
    Devuelve tipos de trámite disponibles.
    Si filtrar=1 y tipo_fase_id dado: solo los de la whitelist fases_tramites.
    """
    tipo_fase_id = request.args.get('tipo_fase_id', type=int)
    filtrar = request.args.get('filtrar') == '1'

    if filtrar and tipo_fase_id:
        tipos = (
            TipoTramite.query
            .join(FaseTramite,
                  FaseTramite.tipo_tramite_id == TipoTramite.id)
            .filter(FaseTramite.tipo_fase_id == tipo_fase_id)
            .order_by(TipoTramite.nombre)
            .all()
        )
    else:
        tipos = TipoTramite.query.order_by(TipoTramite.nombre).all()

    return jsonify([
        {'id': t.id, 'texto': t.nombre}
        for t in tipos
    ])


@bp.route('/api/tokens')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def api_tokens():
    """
    Stub para refresco dinámico de tokens (Capa 2 — Fase 5+).
    Hoy devuelve siempre los tokens de Capa 1 independientemente del contexto ESFTT.
    """
    tokens = _build_tokens()
    return jsonify({
        'campos': tokens['campos'],
        'consultas': [
            {'nombre': c.nombre, 'descripcion': getattr(c, 'descripcion', '')}
            for c in tokens['consultas']
        ],
        'fragmentos': tokens['fragmentos'],
    })


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def listado():
    plantillas = Plantilla.query.order_by(Plantilla.nombre).all()
    return render_template('admin_plantillas/listado.html', plantillas=plantillas)


@bp.route('/nueva/', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def nueva():
    if request.method == 'POST':
        archivo = request.files.get('archivo_plantilla')
        ruta = _guardar_docx(archivo)
        if ruta is None and not archivo.filename:
            flash('Debes subir el fichero .docx de la plantilla.', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        if ruta:
            error_docx = _validar_plantilla_docx(os.path.join(_plantillas_dir(), ruta))
            if error_docx:
                flash(f'El fichero .docx tiene errores de sintaxis: {error_docx}', 'danger')
                return render_template(
                    'admin_plantillas/form.html',
                    modo='nueva', plantilla=None,
                    tokens=_build_tokens(),
                    **_selects_context(),
                )

        p = Plantilla()
        if not _form_data_to_plantilla(p):
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        if ruta:
            p.ruta_plantilla = ruta

        db.session.add(p)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        flash(f'Plantilla «{p.nombre}» registrada correctamente.', 'success')
        return redirect(url_for('admin_plantillas.detalle', id=p.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='nueva', plantilla=None,
        tokens=_build_tokens(),
        **_selects_context(),
    )


@bp.route('/<int:id>/')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def detalle(id):
    plantilla = Plantilla.query.get_or_404(id)
    tokens = _build_tokens(plantilla)
    d = _plantillas_dir()
    ruta_absoluta = os.path.join(d, plantilla.ruta_plantilla).replace('/', '\\') if d else None
    uri_explorador = (
        'bddat-explorador://' + ruta_absoluta.replace('\\', '/').replace(':', '%3A')
    ) if ruta_absoluta else None
    return render_template(
        'admin_plantillas/detalle.html',
        plantilla=plantilla, tokens=tokens,
        ruta_absoluta=ruta_absoluta, uri_explorador=uri_explorador,
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def editar(id):
    plantilla = Plantilla.query.get_or_404(id)

    if request.method == 'POST':
        archivo = request.files.get('archivo_plantilla')
        ruta = _guardar_docx(archivo)

        if ruta:
            error_docx = _validar_plantilla_docx(os.path.join(_plantillas_dir(), ruta))
            if error_docx:
                flash(f'El fichero .docx tiene errores de sintaxis: {error_docx}', 'danger')
                return render_template(
                    'admin_plantillas/form.html',
                    modo='editar', plantilla=plantilla,
                    tokens=_build_tokens(plantilla),
                    **_selects_context(),
                )

        if not _form_data_to_plantilla(plantilla):
            return render_template(
                'admin_plantillas/form.html',
                modo='editar', plantilla=plantilla,
                tokens=_build_tokens(plantilla),
                **_selects_context(),
            )

        if ruta:
            plantilla.ruta_plantilla = ruta

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='editar', plantilla=plantilla,
                tokens=_build_tokens(plantilla),
                **_selects_context(),
            )

        flash(f'Plantilla «{plantilla.nombre}» actualizada correctamente.', 'success')
        return redirect(url_for('admin_plantillas.detalle', id=plantilla.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='editar', plantilla=plantilla,
        tokens=_build_tokens(plantilla),
        **_selects_context(),
    )


@bp.route('/<int:id>/descargar')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def descargar(id):
    plantilla = Plantilla.query.get_or_404(id)
    d = _plantillas_dir()
    if not d:
        abort(503, 'PLANTILLAS_BASE no configurado.')
    ruta_abs = os.path.join(d, plantilla.ruta_plantilla)
    if not os.path.isfile(ruta_abs):
        abort(404, f'Fichero no encontrado: {plantilla.ruta_plantilla}')
    return send_file(ruta_abs, as_attachment=True, download_name=plantilla.ruta_plantilla)


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def activar(id):
    plantilla = Plantilla.query.get_or_404(id)
    plantilla.activo = not plantilla.activo
    db.session.commit()
    estado = 'activada' if plantilla.activo else 'desactivada'
    flash(f'Plantilla «{plantilla.nombre}» {estado}.', 'success')
    return redirect(url_for('admin_plantillas.detalle', id=plantilla.id))
