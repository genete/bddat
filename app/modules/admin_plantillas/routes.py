"""
Blueprint para administración de plantillas de escritos administrativos.

Rutas:
- GET  /admin/plantillas/             — Listado de tipos_escritos
- GET  /admin/plantillas/nueva/       — Formulario alta nueva plantilla
- POST /admin/plantillas/nueva/       — Guardar nueva plantilla
- GET  /admin/plantillas/<id>/        — Detalle (solo lectura) + panel tokens
- GET  /admin/plantillas/<id>/editar  — Formulario edición pre-rellenado
- POST /admin/plantillas/<id>/editar  — Guardar cambios
- GET  /admin/plantillas/<id>/descargar — Descarga del .docx registrado
- POST /admin/plantillas/<id>/activar — Activar/desactivar plantilla
"""
import json
import os

import werkzeug.utils
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_file, url_for)
from flask_login import login_required

from app import db
from app.decorators import role_required
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_escritos import TipoEscrito
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
    {'campo': 'municipios',             'descripcion': 'Lista de municipios afectados (list[str], usar en bucle)'},
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


def _build_tokens(tipo_escrito=None) -> dict:
    """
    Construye el contexto de tokens para el panel del supervisor.

    campos:    CAMPOS_BASE + campos_catalogo del tipo (si existe y tiene context builder)
    consultas: ConsultaNombrada activas (ordenadas por nombre)
    fragmentos: ficheros .docx en PLANTILLAS_BASE/fragmentos/
    """
    campos = list(CAMPOS_BASE)
    if tipo_escrito and tipo_escrito.campos_catalogo:
        campos = campos + tipo_escrito.campos_catalogo

    consultas = (
        ConsultaNombrada.query
        .filter_by(activo=True)
        .order_by(ConsultaNombrada.nombre)
        .all()
    )
    fragmentos = _listar_fragmentos()

    return {'campos': campos, 'consultas': consultas, 'fragmentos': fragmentos}


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


def _form_data_to_tipo(tipo: TipoEscrito) -> bool:
    """
    Rellena los campos de un TipoEscrito desde request.form.
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

    # campos_catalogo viene como JSON en textarea
    campos_raw = request.form.get('campos_catalogo', '').strip()
    campos_catalogo = None
    if campos_raw:
        try:
            campos_catalogo = json.loads(campos_raw)
            if not isinstance(campos_catalogo, list):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            flash('El catálogo de campos adicionales no es JSON válido (debe ser una lista).', 'danger')
            return False

    tipo.codigo = codigo
    tipo.nombre = nombre
    tipo.descripcion = request.form.get('descripcion', '').strip() or None
    tipo.tipo_documento_id = int(tipo_documento_id)
    tipo.tipo_solicitud_id  = int(request.form['tipo_solicitud_id']) if request.form.get('tipo_solicitud_id') else None
    tipo.tipo_fase_id       = int(request.form['tipo_fase_id'])      if request.form.get('tipo_fase_id')      else None
    tipo.tipo_tramite_id    = int(request.form['tipo_tramite_id'])   if request.form.get('tipo_tramite_id')   else None
    tipo.contexto_clase     = request.form.get('contexto_clase', '').strip() or None
    tipo.campos_catalogo    = campos_catalogo
    tipo.activo             = 'activo' in request.form
    return True


def _selects_context():
    """Devuelve los querysets para los selects del formulario."""
    return {
        'tipos_solicitud':  TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'tipos_fase':       TipoFase.query.order_by(TipoFase.nombre).all(),
        'tipos_tramite':    TipoTramite.query.order_by(TipoTramite.nombre).all(),
        'tipos_documento':  TipoDocumento.query.order_by(TipoDocumento.nombre).all(),
    }


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def listado():
    tipos = TipoEscrito.query.order_by(TipoEscrito.nombre).all()
    return render_template('admin_plantillas/listado.html', tipos=tipos)


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
                modo='nueva', tipo=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        tipo = TipoEscrito()
        if not _form_data_to_tipo(tipo):
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', tipo=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        if ruta:
            tipo.ruta_plantilla = ruta

        db.session.add(tipo)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', tipo=None,
                tokens=_build_tokens(),
                **_selects_context(),
            )

        flash(f'Plantilla «{tipo.nombre}» registrada correctamente.', 'success')
        return redirect(url_for('admin_plantillas.detalle', id=tipo.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='nueva', tipo=None,
        tokens=_build_tokens(),
        **_selects_context(),
    )


@bp.route('/<int:id>/')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def detalle(id):
    tipo = TipoEscrito.query.get_or_404(id)
    tokens = _build_tokens(tipo)
    # Ruta absoluta en disco para que el supervisor pueda abrirla directamente
    d = _plantillas_dir()
    ruta_absoluta = os.path.join(d, tipo.ruta_plantilla).replace('/', '\\') if d else None
    return render_template('admin_plantillas/detalle.html', tipo=tipo, tokens=tokens,
                           ruta_absoluta=ruta_absoluta)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def editar(id):
    tipo = TipoEscrito.query.get_or_404(id)

    if request.method == 'POST':
        archivo = request.files.get('archivo_plantilla')
        ruta = _guardar_docx(archivo)

        if not _form_data_to_tipo(tipo):
            return render_template(
                'admin_plantillas/form.html',
                modo='editar', tipo=tipo,
                tokens=_build_tokens(tipo),
                **_selects_context(),
            )

        if ruta:
            tipo.ruta_plantilla = ruta

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='editar', tipo=tipo,
                tokens=_build_tokens(tipo),
                **_selects_context(),
            )

        flash(f'Plantilla «{tipo.nombre}» actualizada correctamente.', 'success')
        return redirect(url_for('admin_plantillas.detalle', id=tipo.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='editar', tipo=tipo,
        tokens=_build_tokens(tipo),
        **_selects_context(),
    )


@bp.route('/<int:id>/descargar')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def descargar(id):
    tipo = TipoEscrito.query.get_or_404(id)
    d = _plantillas_dir()
    if not d:
        abort(503, 'PLANTILLAS_BASE no configurado.')
    ruta_abs = os.path.join(d, tipo.ruta_plantilla)
    if not os.path.isfile(ruta_abs):
        abort(404, f'Fichero no encontrado: {tipo.ruta_plantilla}')
    return send_file(ruta_abs, as_attachment=True, download_name=tipo.ruta_plantilla)


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def activar(id):
    tipo = TipoEscrito.query.get_or_404(id)
    tipo.activo = not tipo.activo
    db.session.commit()
    estado = 'activada' if tipo.activo else 'desactivada'
    flash(f'Plantilla «{tipo.nombre}» {estado}.', 'success')
    return redirect(url_for('admin_plantillas.detalle', id=tipo.id))
