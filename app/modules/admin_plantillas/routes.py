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
- POST /plantillas/<id>/editar  — Guardar cambios (y, si se sube, el fichero nuevo)
- GET  /plantillas/<id>/descargar — Descarga del fichero de la plantilla, como <código>.<ext>
- POST /plantillas/<id>/activar — Activar/desactivar plantilla (no se activa sin fichero)
- GET  /plantillas/base/<clave>/descargar — Descarga de una plantilla base canónica (#727)

El fichero de la plantilla se sube desde el navegador y vive en el almacén (ADR-050 §J, #1009):
ninguna ruta ve una `ref` ni una ruta de disco, todo pasa por `almacenamiento.contenido`.

Fragmentos (#1009) — segunda pestaña del hub `/plantillas/?tab=fragmentos`:
- POST /plantillas/fragmentos/crear                  — Alta (modal): nombre, descripción, fichero
- GET  /plantillas/fragmentos/<id>/fragmento         — Lectura para el inspector
- GET  /plantillas/fragmentos/<id>/editar-fragmento  — Edición para el inspector
- POST /plantillas/fragmentos/<id>/guardar           — Guardar la edición (XHR → JSON)
- POST /plantillas/fragmentos/<id>/activar           — Pausar / devolver
- GET  /plantillas/fragmentos/<id>/descargar         — Descargar el fichero

Endpoints AJAX:
- GET  /plantillas/api/tokens           — Tokens Capa 1 (stub — Capa 2 en Fase 5)
"""
import io
import os

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_file, url_for)
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.consultas_nombradas import ConsultaNombrada
from app.models.fragmentos import Fragmento
from app.models.plantillas import Plantilla
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tramites import TipoTramite
from app.services.almacenamiento import contenido
from app.services.almacenamiento.adaptador import (AlmacenNoDisponible,
                                                   MENSAJE_ALMACEN_NO_DISPONIBLE)
from app.services.almacenamiento.contenido import (ContenidoNoUtilizable,
                                                   PlantillaNoUsable,
                                                   PlantillaSinFichero)
from app.services.generador_escritos import (advertencias_plantilla,
                                             validar_plantilla)
from app.services.plantilla_canonica_odt import leer_marca
from app.utils.formularios import (
    AUSENTE, aplicar_checkbox, aplicar_fk, aplicar_texto, form_completo, leer,
)
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'admin_plantillas',
    __name__,
    url_prefix='/plantillas',
    template_folder='templates',
)

MENSAJE_ACTIVAR_SIN_FICHERO = ('No se puede activar una plantilla sin fichero. '
                               'Sube el fichero desde «Editar» y actívala.')

# Campos fijos del ContextoBaseExpediente — siempre disponibles en cualquier plantilla
CAMPOS_BASE = [
    {'campo': 'numero_at',              'descripcion': 'Número administrativo (AT-XXXX)'},
    {'campo': 'expediente_id',          'descripcion': 'ID técnico interno del expediente'},
    {'campo': 'titular_nombre',         'descripcion': 'Nombre / Razón Social del titular'},
    {'campo': 'titular_nif',            'descripcion': 'NIF del titular'},
    {'campo': 'titular_dir.calle',      'descripcion': 'Dirección postal (calle y número): la sede de la solicitud, o la de la ficha'},
    {'campo': 'titular_dir.cp',         'descripcion': 'Código postal'},
    {'campo': 'titular_dir.municipio',  'descripcion': 'Municipio de notificación'},
    {'campo': 'titular_dir.provincia',  'descripcion': 'Provincia de notificación'},
    {'campo': 'titular_dir.nif',        'descripcion': 'NIF del titular (el de la ficha)'},
    {'campo': 'titular_dir.email',      'descripcion': 'Correo de la sede de la solicitud, o el de la ficha'},
    # Destinatario del escrito (#968, ADR-051 §H): el del trámite, del servicio de
    # destinatarios. Vacíos si el trámite no tiene un destinatario único. Al
    # solicitante, el oficio va siempre a él, a su sede o su ficha (#989, §K).
    {'campo': 'destinatario_nombre',    'descripcion': 'A quién va el escrito (al solicitante, siempre él aunque tenga representante)'},
    {'campo': 'destinatario_nif',       'descripcion': 'NIF del destinatario'},
    {'campo': 'destinatario_dir.calle', 'descripcion': 'Dirección postal del destinatario (calle y número)'},
    {'campo': 'destinatario_dir.cp',    'descripcion': 'Código postal del destinatario'},
    {'campo': 'destinatario_dir.municipio', 'descripcion': 'Municipio del destinatario'},
    {'campo': 'destinatario_dir.provincia', 'descripcion': 'Provincia del destinatario'},
    {'campo': 'destinatario_dir.nif',   'descripcion': 'NIF del destinatario para notificación'},
    {'campo': 'destinatario_dir.email', 'descripcion': 'Correo de aviso de la notificación del destinatario'},
    {'campo': 'destinatario_en_nombre_de', 'descripcion': 'Representado, si el escrito va a su representante; vacío si va directo'},
    {'campo': 'destinatario_representante', 'descripcion': 'Quien recibe la notificación en nombre del solicitante (autorizado o apoderado); vacío si no hay'},
    {'campo': 'proyecto_titulo',       'descripcion': 'Título del proyecto técnico'},
    {'campo': 'proyecto_finalidad',     'descripcion': 'Finalidad de la instalación'},
    {'campo': 'proyecto_emplazamiento', 'descripcion': 'Emplazamiento descriptivo'},
    {'campo': 'instrumento_ambiental',  'descripcion': 'Siglas del instrumento ambiental (AAI, AAU, EXENTO...)'},
    {'campo': 'responsable_nombre',     'descripcion': 'Nombre completo del tramitador asignado'},
    {'campo': 'responsable_siglas_escritos', 'descripcion': 'Siglas del redactor para firma (Usuario.siglas_escritos)'},
    {'campo': 'organo_nombre',          'descripcion': 'Delegación Territorial del responsable, p.ej. "Delegación Territorial de X y de Y en <provincia>" (#728)'},
    {'campo': 'organo_sede_direccion',  'descripcion': 'Dirección postal de la sede del órgano (#728)'},
    {'campo': 'organo_sede_telefono',   'descripcion': 'Teléfono de la sede del órgano (#728)'},
    {'campo': 'organo_sede_correo',     'descripcion': 'Correo de la sede del órgano (#728)'},
    {'campo': 'municipios',             'descripcion': 'Lista de municipios afectados', 'tipo': 'lista'},
    {'campo': 'fecha_hoy',              'descripcion': 'Fecha actual en formato DD/MM/YYYY'},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Plantillas base canónicas (#727 / ADR-035 §5): viven en el repo, versionadas (son código),
# NO en el almacén — de ahí una ruta de descarga propia en vez de reusar `descargar`, que
# sirve el contenido de una plantilla registrada.
BASES_CANONICAS = {
    'carta':      'carta_base.odt',
    'resolucion': 'resolucion_base.odt',
    'fragmento':  'fragmento_base.odt',
}


def _plantillas_base_dir():
    """Directorio de las plantillas base canónicas, empaquetado en el repo."""
    return os.path.join(current_app.root_path, 'data', 'plantillas_base')


def _listar_fragmentos() -> list[dict]:
    """Los fragmentos activos, para el panel de tokens: `[{nombre, extension}]`.

    Lista los dos formatos: un fragmento solo sirve para plantillas de su mismo
    formato, pero el panel no sabe cuál es la plantilla en curso y ocultarlos
    confundiría más que mostrarlos. Los desactivados no salen: no se pueden citar.
    """
    return [
        {'nombre': f.nombre, 'extension': contenido.extension_de_formato(f.formato)}
        for f in (Fragmento.query.filter_by(activo=True)
                  .order_by(Fragmento.nombre, Fragmento.formato).all())
    ]


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
    fragmentos: los fragmentos activos de la tabla `fragmentos` (universal)
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


def _marca_de_plantilla(plantilla) -> dict | None:
    """Las marcas `BDDAT:*` de la plantilla (de qué base deriva), o `None` si no hay: sin fichero,
    contenido no disponible, un `.docx` o un `.odt` sin ellas. Leer el contenido puede marcar la
    fila del almacén como ausente o dañada (§G): es lo que adelanta el fallo desde el inspector."""
    try:
        return leer_marca(contenido.leer_plantilla(plantilla).datos)
    except (PlantillaNoUsable, ContenidoNoUtilizable, AlmacenNoDisponible):
        return None


def _extension_de(plantilla) -> str | None:
    """`.odt` o `.docx` de la plantilla, o `None` si todavía no tiene fichero."""
    if not contenido.tiene_fichero(plantilla):
        return None
    return contenido.extension_de_plantilla(plantilla)


def _rellenar_plantilla(plantilla: Plantilla) -> list[str]:
    """
    Rellena los campos de una Plantilla desde request.form.
    Devuelve la lista de errores de validación (vacía si todo OK).

    Ausente vs vacío (#834, mismo criterio que #832): un campo que no viaja en
    la petición no se toca —una edición parcial legítima—; presente y vacío sí
    valida/vacía. En el alta (`nueva()`) el formulario siempre viaja completo
    (con `_form_completo`), así que el comportamiento no cambia ahí; lo que
    cambia es que una edición parcial ya no puede vaciar en silencio lo que no
    menciona.

    No flashea: el llamador decide cómo mostrarlos (flash en la página de alta,
    JSON en el inspector XHR — ADR-023 §5).
    """
    errores = []

    codigo_in = leer(request.form, 'codigo')
    if codigo_in is not AUSENTE:
        codigo = (codigo_in or '').strip().upper()
        if not codigo:
            errores.append('El código es obligatorio.')
        else:
            # Unicidad del código (uq_plantillas_codigo), excluyendo la propia plantilla
            q = Plantilla.query.filter(Plantilla.codigo == codigo)
            if plantilla.id:
                q = q.filter(Plantilla.id != plantilla.id)
            if q.first():
                errores.append(f'El código «{codigo}» ya está en uso por otra plantilla.')

    nombre_in = leer(request.form, 'nombre')
    if nombre_in is not AUSENTE and not (nombre_in or '').strip():
        errores.append('El nombre es obligatorio.')

    tipo_documento_in = leer(request.form, 'tipo_documento_id')
    if tipo_documento_in is not AUSENTE and not tipo_documento_in:
        errores.append('El tipo de documento es obligatorio.')

    if errores:
        return errores

    if codigo_in is not AUSENTE:
        plantilla.codigo = codigo
    if nombre_in is not AUSENTE:
        plantilla.nombre = nombre_in.strip()
    if tipo_documento_in is not AUSENTE:
        plantilla.tipo_documento_id = int(tipo_documento_in)

    aplicar_texto(request.form, 'descripcion', plantilla)
    aplicar_texto(request.form, 'variante', plantilla)
    aplicar_fk(request.form, 'tipo_expediente_id', plantilla)
    aplicar_fk(request.form, 'tipo_solicitud_id', plantilla)
    aplicar_fk(request.form, 'tipo_fase_id', plantilla)
    aplicar_fk(request.form, 'tipo_tramite_id', plantilla)
    aplicar_texto(request.form, 'contexto_clase', plantilla)
    aplicar_checkbox(request.form, 'activo', plantilla, form_completo(request.form))
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
        'fragmentos': [f"{f['nombre']}{f['extension']}" for f in tokens['fragmentos']],
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
        puede_gestionar=tiene_permiso('gestionar_plantillas'),
    )


@bp.route('/nueva/', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_plantillas')
def nueva():
    if request.method == 'POST':
        def repintar():
            """El alta con lo ya tecleado (el fichero no se conserva: hay que volver a elegirlo)."""
            return render_template(
                'admin_plantillas/form.html',
                modo='nueva', plantilla=_plantilla_form_provisional(),
                tokens=_build_tokens(request.form.get('contexto_clase')),
                **_selects_context(),
            )

        archivo = _fichero_subido()
        if archivo is None:
            flash('Debes subir el fichero de la plantilla (.odt o .docx).', 'danger')
            return repintar()

        # Se valida con el motor ANTES de guardar nada: una plantilla que no valida no deja
        # ni fila ni contenido en el almacén.
        try:
            avisos = _validar_contenido_subido(archivo, 'una plantilla')
        except ValueError as e:      # FormatoNoAdmitido incluido
            flash(str(e), 'danger')
            return repintar()

        p = Plantilla()
        errores = _rellenar_plantilla(p)
        if errores:
            for msg in errores:
                flash(msg, 'danger')
            return repintar()

        try:
            contenido.guardar_plantilla(p, archivo.stream, archivo.filename)
        except AlmacenNoDisponible:
            flash(MENSAJE_ALMACEN_NO_DISPONIBLE, 'danger')
            return repintar()
        except ValueError as e:
            flash(str(e), 'danger')
            return repintar()

        db.session.add(p)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {e}', 'danger')
            return repintar()

        flash(f'Plantilla «{p.nombre}» registrada correctamente.', 'success')
        for aviso in avisos:
            flash(aviso, 'warning')
        return redirect(url_for('admin_plantillas.detalle', id=p.id))

    return render_template(
        'admin_plantillas/form.html',
        modo='nueva', plantilla=None,
        tokens=_build_tokens(),
        **_selects_context(),
    )


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
    # La marca se lee antes que el motivo: leer el contenido puede descubrir que está ausente
    # o dañado, y entonces el motivo ya lo cuenta.
    marca = _marca_de_plantilla(plantilla)
    return render_template(
        'admin_plantillas/_detalle_fragmento.html',
        plantilla=plantilla, marca=marca,
        extension=_extension_de(plantilla),
        motivo=contenido.motivo_no_usable(plantilla),
        puede_editar=tiene_permiso('gestionar_plantillas'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_plantillas')
def editar_fragmento(id):
    """Fragmento HTML de edición para el inspector (ADR-023 §5 / #545).

    Metadatos con selects planos (sin cascada ESFTT: los endpoints api_tipos_* no
    filtran hoy) y, si se quiere cambiar, el fichero nuevo (#1009).
    """
    plantilla = Plantilla.query.get_or_404(id)
    return render_template(
        'admin_plantillas/_editar_fragmento.html',
        plantilla=plantilla,
        extension=_extension_de(plantilla),
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
        """Errores como JSON (XHR) o flash + redirect al inspector (fallback sin JS).
        Descarta lo que el formulario ya hubiera cambiado en la plantilla."""
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('admin_plantillas.listado', sel=id))

    # Si el supervisor sube un fichero, se valida con el motor ANTES de tocar nada: una
    # plantilla que no valida no sustituye a la vigente (ADR-050 §J).
    archivo = _fichero_subido()
    avisos = []
    if archivo is not None:
        try:
            avisos = _validar_contenido_subido(archivo, 'una plantilla')
        except ValueError as e:      # FormatoNoAdmitido incluido
            return _responder_errores([str(e)])

    errores = _rellenar_plantilla(plantilla)
    if errores:
        return _responder_errores(errores)

    if archivo is not None:
        try:
            contenido.guardar_plantilla(plantilla, archivo.stream, archivo.filename)
        except AlmacenNoDisponible:
            return _responder_errores([MENSAJE_ALMACEN_NO_DISPONIBLE])
        except ValueError as e:
            return _responder_errores([str(e)])

    # Una plantilla sin fichero no se activa (ADR-050 §J; luego lo garantiza la BD). Subir el
    # fichero en esta misma petición sí vale.
    if plantilla.activo and not contenido.tiene_fichero(plantilla):
        return _responder_errores([MENSAJE_ACTIVAR_SIN_FICHERO])

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
    """Descarga el fichero de la plantilla, activa o no, para editarlo en el PC (ADR-050 §J).

    El almacén no guarda nombres: el fichero se llama como el código de la plantilla."""
    plantilla = Plantilla.query.get_or_404(id)
    try:
        leida = contenido.leer_plantilla(plantilla)
    except PlantillaSinFichero as e:
        abort(404, str(e))
    except AlmacenNoDisponible:
        abort(503, MENSAJE_ALMACEN_NO_DISPONIBLE)
    except ContenidoNoUtilizable as e:
        abort(409, str(e))
    nombre = f'{plantilla.codigo}{contenido.extension_de_formato(leida.formato)}'
    return send_file(io.BytesIO(leida.datos), as_attachment=True, download_name=nombre,
                     mimetype=leida.formato)


@bp.route('/base/<clave>/descargar')
@login_required
@require_permiso('acceder_plantillas')
def descargar_base(clave):
    """Descarga de una plantilla base canónica, para que el supervisor parta de
    ella en vez de un .odt en blanco (#727)."""
    nombre = BASES_CANONICAS.get(clave)
    if not nombre:
        abort(404)
    ruta_abs = os.path.join(_plantillas_base_dir(), nombre)
    if not os.path.isfile(ruta_abs):
        abort(404, f'Plantilla base no encontrada: {nombre}')
    return send_file(ruta_abs, as_attachment=True, download_name=nombre)


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_plantillas')
def activar(id):
    plantilla = Plantilla.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not plantilla.activo and not contenido.tiene_fichero(plantilla):
        if is_xhr:
            return jsonify({'ok': False, 'errors': [MENSAJE_ACTIVAR_SIN_FICHERO]})
        flash(MENSAJE_ACTIVAR_SIN_FICHERO, 'danger')
        return redirect(url_for('admin_plantillas.listado', sel=id))
    plantilla.activo = not plantilla.activo
    db.session.commit()
    estado = 'activada' if plantilla.activo else 'desactivada'
    msg = f'Plantilla «{plantilla.nombre}» {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': plantilla.activo})
    flash(msg, 'success')
    return redirect(url_for('admin_plantillas.listado', sel=id))


# ---------------------------------------------------------------------------
# Fragmentos (#1009, ADR-050 §J) — la segunda pestaña del hub
#
# Un fragmento es una fila de `fragmentos` con su contenido en el almacén. Aquí solo se
# habla con el módulo de contenido: ninguna ruta ve una `ref`.
# ---------------------------------------------------------------------------

def _volver_a_fragmentos(**parametros):
    return redirect(url_for('admin_plantillas.listado', tab='fragmentos', **parametros))


def _fichero_subido():
    """El fichero del campo `fichero`, o None si no se ha elegido ninguno."""
    archivo = request.files.get('fichero')
    return archivo if archivo is not None and archivo.filename else None


def _validar_contenido_subido(archivo, que: str) -> list[str]:
    """Valida lo subido con el motor de su formato y devuelve los avisos de canonicidad.

    El formato sale del contenido (§E), no de la extensión. Lanza `ValueError` (mensaje
    para el usuario) si no es un `.odt` o `.docx` de verdad o el motor no lo acepta.
    """
    formato = contenido.formato_de_escrito(archivo.filename, archivo.stream, que)
    datos = archivo.stream.read()
    archivo.stream.seek(0)
    error = validar_plantilla(datos, formato)
    if error:
        raise ValueError(f'El fichero no es válido: {error}')
    return advertencias_plantilla(datos, formato)


@bp.route('/fragmentos/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_plantillas')
def frag_crear():
    """Alta de un fragmento: nombre, descripción y fichero (modal de la pestaña)."""
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip() or None
    archivo = _fichero_subido()
    if archivo is None:
        flash('Elige el fichero del fragmento (.odt o .docx).', 'danger')
        return _volver_a_fragmentos()

    try:
        avisos = _validar_contenido_subido(archivo, 'un fragmento')
        fragmento, resultado = contenido.guardar_fragmento(
            nombre, archivo.stream, archivo.filename, descripcion=descripcion)
    except AlmacenNoDisponible:
        flash(MENSAJE_ALMACEN_NO_DISPONIBLE, 'danger')
        return _volver_a_fragmentos()
    except ValueError as e:      # FormatoNoAdmitido incluido
        flash(str(e), 'danger')
        return _volver_a_fragmentos()

    if resultado != contenido.CREADO:
        # El alta no sustituye: pisar un fragmento que usan las plantillas es otra decisión.
        db.session.rollback()
        flash(f'Ya existe el fragmento «{nombre}» en ese formato. Ábrelo y sustituye su fichero.',
              'danger')
        return _volver_a_fragmentos()

    db.session.add(fragmento)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return _volver_a_fragmentos()

    flash(f'Fragmento «{fragmento.nombre}» creado.', 'success')
    for aviso in avisos:
        flash(aviso, 'warning')
    return _volver_a_fragmentos(sel=fragmento.id)


@bp.route('/fragmentos/<int:id>/fragmento')
@login_required
@require_permiso('acceder_plantillas')
def frag_lectura(id):
    """Fragmento HTML de lectura para el inspector."""
    fragmento = Fragmento.query.get_or_404(id)
    return render_template(
        'admin_plantillas/_frag_lectura.html',
        fragmento=fragmento,
        extension=contenido.extension_de_formato(fragmento.formato),
        motivo=contenido.motivo_no_usable_fragmento(fragmento),
        puede_editar=tiene_permiso('gestionar_plantillas'),
    )


@bp.route('/fragmentos/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_plantillas')
def frag_edicion(id):
    """Fragmento HTML de edición para el inspector."""
    fragmento = Fragmento.query.get_or_404(id)
    return render_template(
        'admin_plantillas/_frag_edicion.html',
        fragmento=fragmento,
        extension=contenido.extension_de_formato(fragmento.formato),
    )


@bp.route('/fragmentos/<int:id>/guardar', methods=['POST'])
@login_required
@require_permiso('gestionar_plantillas')
def frag_guardar(id):
    """Guardar la edición de un fragmento (XHR → JSON): descripción, pausa y, si se elige,
    otro fichero del mismo formato. El nombre no se cambia: es la clave que citan las
    plantillas."""
    fragmento = Fragmento.query.get_or_404(id)

    def con_errores(errores):
        db.session.rollback()
        return jsonify({'ok': False, 'errors': errores})

    avisos = []
    archivo = _fichero_subido()
    resultado = None
    if archivo is not None:
        try:
            avisos = _validar_contenido_subido(archivo, 'un fragmento')
            resultado = contenido.sustituir_fragmento(fragmento, archivo.stream, archivo.filename)
        except AlmacenNoDisponible:
            return con_errores([MENSAJE_ALMACEN_NO_DISPONIBLE])
        except ValueError as e:
            return con_errores([str(e)])

    aplicar_texto(request.form, 'descripcion', fragmento)
    aplicar_checkbox(request.form, 'activo', fragmento, form_completo(request.form))

    try:
        db.session.commit()
    except Exception as e:
        return con_errores([f'Error al guardar: {e}'])

    msg = f'Fragmento «{fragmento.nombre}» actualizado correctamente.'
    if resultado == contenido.SUSTITUIDO:
        msg = f'Fragmento «{fragmento.nombre}» actualizado: el fichero se ha sustituido.'
    return jsonify({'ok': True, 'message': msg, 'warnings': avisos})


@bp.route('/fragmentos/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_plantillas')
def frag_activar(id):
    """Pausar o devolver un fragmento. Pausado cuenta como ausente: las plantillas que lo
    citan no generan hasta que se devuelva (ADR-050 §J)."""
    fragmento = Fragmento.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    fragmento.activo = not fragmento.activo
    db.session.commit()
    estado = 'activado' if fragmento.activo else 'desactivado'
    msg = f'Fragmento «{fragmento.nombre}» {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': fragmento.activo})
    flash(msg, 'success')
    return _volver_a_fragmentos(sel=id)


@bp.route('/fragmentos/<int:id>/descargar')
@login_required
@require_permiso('acceder_plantillas')
def frag_descargar(id):
    """Descarga del fichero del fragmento, esté activo o no (para editarlo en el PC)."""
    fragmento = Fragmento.query.get_or_404(id)
    try:
        datos = contenido.contenido_de_fragmento(fragmento)
    except AlmacenNoDisponible:
        abort(503, MENSAJE_ALMACEN_NO_DISPONIBLE)
    except ContenidoNoUtilizable as e:
        abort(409, str(e))
    nombre = f'{fragmento.nombre}{contenido.extension_de_formato(fragmento.formato)}'
    return send_file(io.BytesIO(datos), as_attachment=True, download_name=nombre,
                     mimetype=fragmento.formato)
