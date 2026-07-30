"""
Blueprint para administración de plantillas de escritos administrativos.

Sin exclusividad de ADMIN (lectura universal, `acceder_plantillas`) — el prefijo
`/admin` se retira en #590 (ADR-029 §4): no hay contenido aquí exclusivo del rol
ADMIN, solo un patrón heredado de antes de ADR-013/017/028. El nombre interno
del blueprint (`admin_plantillas`) no cambia — mismo criterio que ya aplicó #588
a `supervisor` (cambiar `url_prefix` no rompe `url_for()`).

Rutas de formulario:
- GET  /plantillas/             — Listado de plantillas
- GET  /plantillas/nueva/       — Formulario alta nueva plantilla
- POST /plantillas/nueva/       — Guardar nueva plantilla
- GET  /plantillas/<id>/        — Detalle (solo lectura) + panel tokens
- GET  /plantillas/<id>/editar  — Formulario edición pre-rellenado
- POST /plantillas/<id>/editar  — Guardar cambios
- GET  /plantillas/<id>/descargar — Descarga del fichero de plantilla registrado
- POST /plantillas/<id>/activar — Activar/desactivar plantilla

Endpoints AJAX:
- GET  /plantillas/api/tokens           — Tokens Capa 1 (stub — Capa 2 en Fase 5)
- GET  /plantillas/api/fs               — Explorador de servidor restringido a PLANTILLAS_BASE/plantillas/
"""
import os

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.plantillas import Plantilla
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tramites import TipoTramite
from app.services.generador_escritos import (TIPOS_CONTENIDO,
                                             advertencias_plantilla,
                                             validar_plantilla)
from app.services.plantilla_canonica_odt import leer_marca
from app.utils.permisos import tiene_permiso

# Formatos de plantilla admitidos, los mismos que tienen motor de render
# (ADR-035 §2). Una sola fuente: si mañana se retira el .docx, desaparece de
# aquí solo.
EXTENSIONES = tuple(sorted(TIPOS_CONTENIDO))

bp = Blueprint(
    'admin_plantillas',
    __name__,
    url_prefix='/plantillas',
    template_folder='templates',
)

# Campos fijos del ContextoBaseExpediente — siempre disponibles en cualquier plantilla
CAMPOS_BASE = [
    {'campo': 'numero_at',              'descripcion': 'Número administrativo (AT-XXXX)'},
    {'campo': 'expediente_id',          'descripcion': 'ID técnico interno del expediente'},
    {'campo': 'titular_nombre',         'descripcion': 'Nombre / Razón Social del titular'},
    {'campo': 'titular_nif',            'descripcion': 'NIF del titular'},
    {'campo': 'titular_dir.calle',      'descripcion': 'Dirección postal (calle y número)'},
    {'campo': 'titular_dir.cp',         'descripcion': 'Código postal'},
    {'campo': 'titular_dir.municipio',  'descripcion': 'Municipio de notificación'},
    {'campo': 'titular_dir.provincia',  'descripcion': 'Provincia de notificación'},
    {'campo': 'titular_dir.nif',        'descripcion': 'NIF para notificación (puede diferir del NIF principal)'},
    {'campo': 'titular_dir.email',      'descripcion': 'Email de notificación electrónica'},
    {'campo': 'proyecto_titulo',        'descripcion': 'Título del proyecto técnico'},
    {'campo': 'proyecto_finalidad',     'descripcion': 'Finalidad de la instalación'},
    {'campo': 'proyecto_emplazamiento', 'descripcion': 'Emplazamiento descriptivo'},
    {'campo': 'instrumento_ambiental',  'descripcion': 'Siglas del instrumento ambiental (AAI, AAU, EXENTO...)'},
    {'campo': 'responsable_nombre',     'descripcion': 'Nombre completo del tramitador asignado'},
    {'campo': 'responsable_siglas_escritos', 'descripcion': 'Siglas del redactor para firma (Usuario.siglas_escritos)'},
    {'campo': 'municipios',             'descripcion': 'Lista de municipios afectados', 'tipo': 'lista'},
    {'campo': 'fecha_hoy',              'descripcion': 'Fecha actual en formato DD/MM/YYYY'},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plantillas_dir():
    """Directorio absoluto de plantillas."""
    base = current_app.config.get('PLANTILLAS_BASE', '')
    return os.path.join(base, 'plantillas') if base else ''


def _fragmentos_dir():
    """Directorio absoluto de fragmentos."""
    base = current_app.config.get('PLANTILLAS_BASE', '')
    return os.path.join(base, 'fragmentos') if base else ''


def _listar_fragmentos() -> list[str]:
    """Devuelve los ficheros de fragmento en PLANTILLAS_BASE/fragmentos/.

    Lista los dos formatos: un fragmento solo sirve para plantillas de su mismo
    formato, pero el panel no sabe cuál es la plantilla en curso y ocultarlos
    confundiría más que mostrarlos.
    """
    d = _fragmentos_dir()
    if not d or not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.lower().endswith(EXTENSIONES))


def _tokens_context_builder(contexto_clase) -> list:
    """Manifiesto TOKENS del Context Builder declarado, o [] si no existe.

    El supervisor puede teclear una clase inexistente; en ese caso no hay
    tokens de Capa 2 que ofrecer y el panel no se rompe (ADR-025).
    """
    if not contexto_clase:
        return []
    try:
        from app.services.escritos import cargar_context_builder
        cls = cargar_context_builder(contexto_clase)
    except Exception:
        return []
    return list(getattr(cls, 'TOKENS', []) or [])


def _build_tokens(contexto_clase=None) -> dict:
    """
    Construye el contexto de tokens para el panel del supervisor.

    campos:     CAMPOS_BASE (Capa 1 fija, universal)
    consultas:  ConsultaNombrada activas (universal, nivel expediente)
    fragmentos: ficheros de fragmento en PLANTILLAS_BASE/fragmentos/ (universal)
    cb_tokens:  manifiesto TOKENS del Context Builder en contexto_clase (Capa 2).
                Vacío si la plantilla no usa CB. Es lo único que varía por
                plantilla — se ancla a contexto_clase, no al ESFT (ADR-025).
    cb_clase:   nombre de la clase del Context Builder, para la cabecera de la sección.
    """
    consultas = (
        ConsultaNombrada.query
        .filter_by(activo=True)
        .order_by(ConsultaNombrada.nombre)
        .all()
    )
    fragmentos = _listar_fragmentos()
    return {
        'campos': list(CAMPOS_BASE),
        'consultas': consultas,
        'fragmentos': fragmentos,
        'cb_tokens': _tokens_context_builder(contexto_clase),
        'cb_clase': contexto_clase or None,
    }




def _ruta_registrable(ruta_relativa: str) -> str:
    """
    Ruta que se guarda en `plantilla.ruta_plantilla`, relativa a
    PLANTILLAS_BASE/plantillas/ y con '/' como separador.

    Conserva el subdirectorio. Guardar solo el nombre de fichero daba de alta
    plantillas que luego no se encontraban al generar: el explorador permite
    navegar carpetas, y `escritos/resolucion.odt` se registraba como
    `resolucion.odt`, que no existe en la raíz.
    """
    return ruta_relativa.replace('\\', '/').strip('/')


def _path_seguro_plantillas(ruta_relativa: str) -> str | None:
    """
    Valida que ruta_relativa (con '/' como separador) no escape de PLANTILLAS_BASE/plantillas/.
    Devuelve la ruta absoluta o None si hay path traversal.
    """
    base = _plantillas_dir()
    if not base:
        return None
    base_norm = os.path.normpath(os.path.abspath(base))
    if ruta_relativa:
        ruta_full = os.path.normpath(os.path.join(base, ruta_relativa.replace('/', os.sep)))
    else:
        ruta_full = base_norm
    if ruta_full != base_norm and not ruta_full.startswith(base_norm + os.sep):
        return None
    return ruta_full


def _rellenar_plantilla(plantilla: Plantilla) -> list[str]:
    """
    Rellena los campos de una Plantilla desde request.form.
    Devuelve la lista de errores de validación (vacía si todo OK).

    No flashea: el llamador decide cómo mostrarlos (flash en la página de alta,
    JSON en el inspector XHR — ADR-023 §5).
    """
    errores = []
    codigo = request.form.get('codigo', '').strip().upper()
    nombre = request.form.get('nombre', '').strip()
    tipo_documento_id = request.form.get('tipo_documento_id') or None

    if not codigo:
        errores.append('El código es obligatorio.')
    if not nombre:
        errores.append('El nombre es obligatorio.')
    if not tipo_documento_id:
        errores.append('El tipo de documento es obligatorio.')

    # Unicidad del código (uq_plantillas_codigo), excluyendo la propia plantilla en edición
    if codigo:
        q = Plantilla.query.filter(Plantilla.codigo == codigo)
        if plantilla.id:
            q = q.filter(Plantilla.id != plantilla.id)
        if q.first():
            errores.append(f'El código «{codigo}» ya está en uso por otra plantilla.')

    if errores:
        return errores

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
    return []


def _plantilla_form_provisional():
    """Plantilla NO persistida con los valores del formulario de alta.

    Repinta el alta tras un error de validación sin perder lo ya tecleado.
    No valida ni toca BD (#552). La plantilla Jinja ya lee de `plantilla.X`,
    así que con esto los campos sobreviven al re-render.
    """
    def _int(v):
        return int(v) if v else None
    p = Plantilla()
    p.codigo             = request.form.get('codigo', '').strip().upper() or None
    p.nombre             = request.form.get('nombre', '').strip() or None
    p.descripcion        = request.form.get('descripcion', '').strip() or None
    p.variante           = request.form.get('variante', '').strip() or None
    p.tipo_documento_id  = _int(request.form.get('tipo_documento_id'))
    p.tipo_expediente_id = _int(request.form.get('tipo_expediente_id'))
    p.tipo_solicitud_id  = _int(request.form.get('tipo_solicitud_id'))
    p.tipo_fase_id       = _int(request.form.get('tipo_fase_id'))
    p.tipo_tramite_id    = _int(request.form.get('tipo_tramite_id'))
    p.contexto_clase     = request.form.get('contexto_clase', '').strip() or None
    p.activo             = 'activo' in request.form
    return p


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
# Endpoints AJAX
# ---------------------------------------------------------------------------

@bp.route('/api/fs')
@login_required
@require_permiso('gestionar_plantillas')
def api_explorador_fs():
    """
    Explorador de ficheros del servidor restringido a PLANTILLAS_BASE/plantillas/.
    GET ?ruta=<subruta>  →  JSON {ok, partes, directorios, ficheros}
    Solo expone ficheros de plantilla (.docx, .odt) y subdirectorios.
    """
    base = _plantillas_dir()
    if not base or not os.path.isdir(base):
        return jsonify({'ok': False, 'error': 'Directorio de plantillas no accesible'}), 503

    ruta_rel = request.args.get('ruta', '').strip('/\\ ')
    ruta_abs = _path_seguro_plantillas(ruta_rel)
    if not ruta_abs or not os.path.isdir(ruta_abs):
        return jsonify({'ok': False, 'error': 'Ruta no válida'}), 400

    try:
        dirs, files = [], []
        for e in sorted(os.scandir(ruta_abs), key=lambda x: (not x.is_dir(), x.name.lower())):
            rel = os.path.relpath(e.path, base).replace(os.sep, '/')
            if e.is_dir(follow_symlinks=False):
                dirs.append({'nombre': e.name, 'ruta': rel})
            elif e.is_file(follow_symlinks=False) and e.name.lower().endswith(EXTENSIONES):
                files.append({'nombre': e.name, 'ruta': rel, 'tamano': e.stat().st_size})
    except PermissionError:
        return jsonify({'ok': False, 'error': 'Sin permisos en esta carpeta'}), 403

    partes = ruta_rel.split('/') if ruta_rel else []
    return jsonify({'ok': True, 'partes': partes, 'directorios': dirs, 'ficheros': files})


@bp.route('/api/tokens')
@login_required
@require_permiso('gestionar_plantillas')
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
@require_permiso('acceder_plantillas')
def listado():
    """Listado de plantillas — scroll infinito + inspector overlay (ADR-023 / #545).

    Las filas las sirve la API /api/admin-plantillas; aquí solo se pasan las
    opciones de los filtros (tipo de documento y fase) para los SelectorFiltro.
    """
    tipos_documento = (
        TipoDocumento.query
        .filter(TipoDocumento.origen != 'EXTERNO')
        .order_by(TipoDocumento.nombre)
        .all()
    )
    tipos_fase = TipoFase.query.order_by(TipoFase.nombre).all()
    return render_template(
        'admin_plantillas/listado.html',
        tipos_documento=tipos_documento,
        tipos_fase=tipos_fase,
    )


@bp.route('/nueva/', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_plantillas')
def nueva():
    if request.method == 'POST':
        ruta_rel = request.form.get('ruta_plantilla', '').strip()
        if not ruta_rel:
            flash('Debes seleccionar el fichero de la plantilla desde el servidor.', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        ruta_abs = _path_seguro_plantillas(ruta_rel)
        if not ruta_abs or not os.path.isfile(ruta_abs):
            flash('La ruta del fichero seleccionado no es válida.', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        error_plantilla = validar_plantilla(ruta_abs)
        if error_plantilla:
            flash(f'La plantilla no es válida: {error_plantilla}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        p = Plantilla()
        errores = _rellenar_plantilla(p)
        if errores:
            for msg in errores:
                flash(msg, 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        p.ruta_plantilla = _ruta_registrable(ruta_rel)

        db.session.add(p)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        flash(f'Plantilla «{p.nombre}» registrada correctamente.', 'success')
        for aviso in advertencias_plantilla(ruta_abs):
            flash(aviso, 'warning')
        return redirect(url_for('admin_plantillas.detalle', id=p.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='nueva', plantilla=None,
        tokens=_build_tokens(),
        **_selects_context(),
    )


def _rutas_fichero(plantilla):
    """Calcula la ruta absoluta y el URI bddat-explorador:// del fichero de la plantilla."""
    d = _plantillas_dir()
    ruta_absoluta = os.path.join(d, plantilla.ruta_plantilla).replace('/', '\\') if d else None
    uri_explorador = (
        'bddat-explorador://' + ruta_absoluta.replace('\\', '/').replace(':', '%3A')
    ) if ruta_absoluta else None
    return ruta_absoluta, uri_explorador


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_plantillas')
def detalle(id):
    """Redirige al listado con el inspector abierto en esta plantilla (ADR-023 §9 / #545).

    La ruta se conserva para no romper enlaces externos/marcadores; el detalle
    de página deja de ser un destino de navegación.
    """
    Plantilla.query.get_or_404(id)
    return redirect(url_for('admin_plantillas.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_plantillas')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector (ADR-023 §9 / #545)."""
    plantilla = Plantilla.query.get_or_404(id)
    ruta_absoluta, uri_explorador = _rutas_fichero(plantilla)
    marca = leer_marca(ruta_absoluta) if ruta_absoluta and os.path.isfile(ruta_absoluta) else None
    return render_template(
        'admin_plantillas/_detalle_fragmento.html',
        plantilla=plantilla, marca=marca,
        ruta_absoluta=ruta_absoluta, uri_explorador=uri_explorador,
        puede_editar=tiene_permiso('gestionar_plantillas'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_plantillas')
def editar_fragmento(id):
    """Fragmento HTML de edición para el inspector (ADR-023 §5 / #545).

    Solo metadatos escalares con selects planos (sin cascada ESFTT: los endpoints
    api_tipos_* no filtran hoy). El cambio del fichero se delega al modal grande
    del explorador (ADR-023 §6).
    """
    plantilla = Plantilla.query.get_or_404(id)
    return render_template(
        'admin_plantillas/_editar_fragmento.html',
        plantilla=plantilla,
        **_selects_context(),
    )


@bp.route('/tokens/fragmento')
@login_required
@require_permiso('acceder_plantillas')
def tokens_fragmento():
    """Panel de tokens para el modal grande (ADR-023 §6 / #545).

    Contextual por ?contexto_clase (ADR-025 / #553): Capa 1, consultas y
    fragmentos son universales; los tokens de Capa 2 dependen del Context
    Builder declarado en la plantilla.
    """
    contexto_clase = request.args.get('contexto_clase', '').strip() or None
    return render_template(
        'admin_plantillas/_tokens_fragmento.html',
        tokens=_build_tokens(contexto_clase),
    )


@bp.route('/<int:id>/explorador-fragmento')
@login_required
@require_permiso('gestionar_plantillas')
def explorador_fragmento(id):
    """Explorador de ficheros del servidor como modal grande (ADR-023 §6 / #545).

    Reusa la API /api/fs. El JS del fragmento (re-ejecutado por modal-large.js)
    escribe la ruta elegida en el input oculto del form de edición del inspector.
    """
    plantilla = Plantilla.query.get_or_404(id)
    return render_template('admin_plantillas/_explorador_fragmento.html', plantilla=plantilla)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_plantillas')
def editar(id):
    plantilla = Plantilla.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector (ADR-023 §5); el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('admin_plantillas.listado', sel=id))

    def _responder_errores(errores):
        """Errores como JSON (XHR) o flash + redirect al inspector (fallback sin JS)."""
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('admin_plantillas.listado', sel=id))

    ruta_rel = request.form.get('ruta_plantilla', '').strip()
    avisos = []
    if ruta_rel:
        # El supervisor ha seleccionado un nuevo fichero en el servidor
        ruta_abs = _path_seguro_plantillas(ruta_rel)
        if not ruta_abs or not os.path.isfile(ruta_abs):
            return _responder_errores(['La ruta del fichero seleccionado no es válida.'])
        error_plantilla = validar_plantilla(ruta_abs)
        if error_plantilla:
            return _responder_errores([f'La plantilla no es válida: {error_plantilla}'])
        avisos = advertencias_plantilla(ruta_abs)

    errores = _rellenar_plantilla(plantilla)
    if errores:
        return _responder_errores(errores)

    if ruta_rel:
        plantilla.ruta_plantilla = _ruta_registrable(ruta_rel)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al guardar: {e}'])

    msg = f'Plantilla «{plantilla.nombre}» actualizada correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'warnings': avisos})
    flash(msg, 'success')
    for aviso in avisos:
        flash(aviso, 'warning')
    return redirect(url_for('admin_plantillas.listado', sel=id))


@bp.route('/<int:id>/descargar')
@login_required
@require_permiso('acceder_plantillas')
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
@require_permiso('gestionar_plantillas')
def activar(id):
    plantilla = Plantilla.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    plantilla.activo = not plantilla.activo
    db.session.commit()
    estado = 'activada' if plantilla.activo else 'desactivada'
    msg = f'Plantilla «{plantilla.nombre}» {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': plantilla.activo})
    flash(msg, 'success')
    return redirect(url_for('admin_plantillas.listado', sel=id))
