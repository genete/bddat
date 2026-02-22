"""Blueprint entidades - Vistas HTML para gestión de entidades.

RUTAS:
    GET  /entidades/                                   → listado (shell V2, datos vía API)
    GET  /entidades/nueva                              → formulario nueva entidad
    POST /entidades/nueva                              → crear entidad
    GET  /entidades/<id>                               → detalle entidad V4 solo lectura (#134)
    GET  /entidades/<id>/editar                        → edición V4 mismo template (#135)
    POST /entidades/<id>/editar                        → guardar cambios entidad (#135)
    POST /entidades/<id>/direcciones/nueva             → añadir dirección de notificación (#136)
    POST /entidades/<id>/direcciones/<dir_id>/editar   → editar dirección (#136)
    POST /entidades/<id>/direcciones/<dir_id>/toggle   → activar/desactivar dirección (#136)

VERSIÓN: 1.2
FECHA: 2026-02-22
ISSUE: #136
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.entidad import Entidad
from app.models.autorizados_titular import AutorizadoTitular
from app.models.direccion_notificacion import DireccionNotificacion

# template_folder apunta a app/modules/entidades/templates/
bp = Blueprint('entidades', __name__,
               url_prefix='/entidades',
               template_folder='templates')


# =============================================================================
# LISTADO  (shell V2 — datos cargados por ScrollInfinito vía API)
# =============================================================================

@bp.route('/')
@login_required
def index():
    """Vista listado de entidades. Sin datos de BD en Jinja2."""
    return render_template('entidades/index.html')


# =============================================================================
# NUEVA ENTIDAD
# =============================================================================

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    """Formulario de alta de entidad (GET muestra, POST crea)."""

    if request.method == 'GET':
        return render_template('entidades/nueva.html')

    # --- POST: recoger y validar ---
    nombre_completo = request.form.get('nombre_completo', '').strip()
    nif_raw         = request.form.get('nif', '').strip()
    rol_titular     = 'rol_titular'     in request.form
    rol_consultado  = 'rol_consultado'  in request.form
    rol_publicador  = 'rol_publicador'  in request.form
    email           = request.form.get('email',    '').strip() or None
    telefono        = request.form.get('telefono', '').strip() or None
    notas           = request.form.get('notas',    '').strip() or None
    activo          = 'activo' in request.form

    errores = []

    if not nombre_completo:
        errores.append('El nombre / razón social es obligatorio.')

    if not (rol_titular or rol_consultado or rol_publicador):
        errores.append('Debe asignarse al menos un rol a la entidad.')

    # Normalizar y comprobar NIF duplicado
    nif = Entidad.normalizar_nif(nif_raw) if nif_raw else None
    if nif and Entidad.query.filter_by(nif=nif).first():
        errores.append(f'Ya existe una entidad con el NIF {nif}.')

    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template('entidades/nueva.html')

    # --- Crear ---
    entidad = Entidad(
        nombre_completo=nombre_completo,
        nif=nif,
        rol_titular=rol_titular,
        rol_consultado=rol_consultado,
        rol_publicador=rol_publicador,
        email=email,
        telefono=telefono,
        notas=notas,
        activo=activo,
    )

    db.session.add(entidad)
    db.session.commit()

    flash(f'Entidad "{entidad.nombre_completo}" creada correctamente.', 'success')
    return redirect(url_for('entidades.index'))


# =============================================================================
# DETALLE  V4 solo lectura (#134)
# =============================================================================

@bp.route('/<int:entidad_id>')
@login_required
def detalle(entidad_id):
    """Vista detalle de entidad — patrón V4 solo lectura."""
    entidad = Entidad.query.get_or_404(entidad_id)

    # Cargar historial completo de autorizaciones si es titular
    autorizaciones = []
    if entidad.rol_titular:
        autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(
            entidad_id, solo_activos=False
        )

    return render_template(
        'entidades/detalle.html',
        entidad=entidad,
        autorizaciones=autorizaciones,
        modo='ver',
    )


@bp.route('/<int:entidad_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(entidad_id):
    """Edición de entidad — patrón V4 mismo template con modo='editar' (#135)."""
    entidad = Entidad.query.get_or_404(entidad_id)

    if request.method == 'GET':
        autorizaciones = []
        if entidad.rol_titular:
            autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(
                entidad_id, solo_activos=False
            )
        return render_template(
            'entidades/detalle.html',
            entidad=entidad,
            autorizaciones=autorizaciones,
            modo='editar',
        )

    # --- POST: recoger y validar ---
    nombre_completo = request.form.get('nombre_completo', '').strip()
    nif_raw         = request.form.get('nif', '').strip()
    rol_titular     = 'rol_titular'     in request.form
    rol_consultado  = 'rol_consultado'  in request.form
    rol_publicador  = 'rol_publicador'  in request.form
    email           = request.form.get('email',    '').strip() or None
    telefono        = request.form.get('telefono', '').strip() or None
    notas           = request.form.get('notas',    '').strip() or None
    activo          = 'activo' in request.form
    direccion       = request.form.get('direccion',          '').strip() or None
    codigo_postal   = request.form.get('codigo_postal',      '').strip() or None
    dir_fallback    = request.form.get('direccion_fallback', '').strip() or None

    errores = []

    if not nombre_completo:
        errores.append('El nombre / razón social es obligatorio.')

    if not (rol_titular or rol_consultado or rol_publicador):
        errores.append('Debe asignarse al menos un rol a la entidad.')

    nif = Entidad.normalizar_nif(nif_raw) if nif_raw else None
    if nif:
        duplicado = Entidad.query.filter_by(nif=nif).first()
        if duplicado and duplicado.id != entidad_id:
            errores.append(f'Ya existe otra entidad con el NIF {nif}.')

    if errores:
        for msg in errores:
            flash(msg, 'danger')
        autorizaciones = []
        if entidad.rol_titular:
            autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(
                entidad_id, solo_activos=False
            )
        return render_template(
            'entidades/detalle.html',
            entidad=entidad,
            autorizaciones=autorizaciones,
            modo='editar',
        )

    # --- Actualizar ---
    entidad.nombre_completo    = nombre_completo
    entidad.nif                = nif
    entidad.rol_titular        = rol_titular
    entidad.rol_consultado     = rol_consultado
    entidad.rol_publicador     = rol_publicador
    entidad.email              = email
    entidad.telefono           = telefono
    entidad.notas              = notas
    entidad.activo             = activo
    entidad.direccion          = direccion
    entidad.codigo_postal      = codigo_postal
    entidad.direccion_fallback = dir_fallback

    db.session.commit()

    flash(f'Entidad "{entidad.nombre_completo}" actualizada correctamente.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


# =============================================================================
# DIRECCIONES DE NOTIFICACIÓN  (#136)
# =============================================================================

def _recoger_datos_direccion(form, entidad):
    """Extrae y valida campos del formulario de dirección. Devuelve (datos, errores)."""
    datos = {
        'descripcion':        form.get('descripcion', '').strip() or None,
        'es_titular':         'rol_titular'    in form,
        'es_consultado':      'rol_consultado' in form,
        'es_publicador':      'rol_publicador' in form,
        'email':              form.get('email',        '').strip() or None,
        'telefono':           form.get('telefono',     '').strip() or None,
        'direccion':          form.get('direccion',    '').strip() or None,
        'codigo_postal':      form.get('codigo_postal','').strip() or None,
        'direccion_fallback': form.get('direccion_fallback','').strip() or None,
        'notas':              form.get('notas',        '').strip() or None,
    }

    errores = []

    if not (datos['es_titular'] or datos['es_consultado'] or datos['es_publicador']):
        errores.append('Debe seleccionarse al menos un rol para la dirección.')

    if not (datos['email'] or datos['direccion'] or datos['direccion_fallback']):
        errores.append('Debe indicarse al menos un canal: email o dirección postal.')

    # Filtrar solo roles disponibles en la entidad
    if datos['es_titular']   and not entidad.rol_titular:
        errores.append('La entidad no tiene rol Titular.')
    if datos['es_consultado'] and not entidad.rol_consultado:
        errores.append('La entidad no tiene rol Consultado.')
    if datos['es_publicador'] and not entidad.rol_publicador:
        errores.append('La entidad no tiene rol Publicador.')

    datos['tipo_rol'] = DireccionNotificacion.calcular_tipo_rol(
        datos['es_titular'], datos['es_consultado'], datos['es_publicador']
    )

    return datos, errores


@bp.route('/<int:entidad_id>/direcciones/nueva', methods=['POST'])
@login_required
def nueva_direccion(entidad_id):
    """Añade una nueva dirección de notificación a la entidad."""
    entidad = Entidad.query.get_or_404(entidad_id)
    datos, errores = _recoger_datos_direccion(request.form, entidad)

    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    dir_nueva = DireccionNotificacion(
        entidad_id=entidad_id,
        descripcion=datos['descripcion'],
        tipo_rol=datos['tipo_rol'],
        email=datos['email'],
        telefono=datos['telefono'],
        direccion=datos['direccion'],
        codigo_postal=datos['codigo_postal'],
        direccion_fallback=datos['direccion_fallback'],
        notas=datos['notas'],
        activo=True,
    )
    db.session.add(dir_nueva)
    db.session.commit()

    flash('Dirección de notificación añadida.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


@bp.route('/<int:entidad_id>/direcciones/<int:dir_id>/editar', methods=['POST'])
@login_required
def editar_direccion(entidad_id, dir_id):
    """Edita una dirección de notificación existente."""
    entidad = Entidad.query.get_or_404(entidad_id)
    direccion = DireccionNotificacion.query.filter_by(
        id=dir_id, entidad_id=entidad_id
    ).first_or_404()

    datos, errores = _recoger_datos_direccion(request.form, entidad)

    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    direccion.descripcion        = datos['descripcion']
    direccion.tipo_rol           = datos['tipo_rol']
    direccion.email              = datos['email']
    direccion.telefono           = datos['telefono']
    direccion.direccion          = datos['direccion']
    direccion.codigo_postal      = datos['codigo_postal']
    direccion.direccion_fallback = datos['direccion_fallback']
    direccion.notas              = datos['notas']

    db.session.commit()
    flash('Dirección de notificación actualizada.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


@bp.route('/<int:entidad_id>/direcciones/<int:dir_id>/toggle', methods=['POST'])
@login_required
def toggle_direccion(entidad_id, dir_id):
    """Activa o desactiva una dirección de notificación (borrado lógico)."""
    Entidad.query.get_or_404(entidad_id)
    direccion = DireccionNotificacion.query.filter_by(
        id=dir_id, entidad_id=entidad_id
    ).first_or_404()

    direccion.activo = not direccion.activo
    db.session.commit()

    estado = 'activada' if direccion.activo else 'desactivada'
    flash(f'Dirección "{direccion.descripcion or dir_id}" {estado}.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


# =============================================================================
# AUTORIZACIONES  (#137)
# =============================================================================

@bp.route('/<int:entidad_id>/autorizados/nueva', methods=['POST'])
@login_required
def nueva_autorizacion(entidad_id):
    """Crea una nueva autorización para que otra entidad actúe en nombre del titular."""
    entidad = Entidad.query.get_or_404(entidad_id)
    if not entidad.rol_titular:
        flash('Esta entidad no tiene rol Titular.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    autorizado_id_str = request.form.get('autorizado_id', '').strip()
    if not autorizado_id_str or not autorizado_id_str.isdigit():
        flash('Debe seleccionar una entidad autorizada.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    autorizado_id = int(autorizado_id_str)

    if autorizado_id == entidad_id:
        flash('Una entidad no puede autorizarse a sí misma.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    # Comprobar que no existe ya una autorización activa
    existente = AutorizadoTitular.query.filter_by(
        titular_entidad_id=entidad_id,
        autorizado_entidad_id=autorizado_id,
    ).first()

    if existente:
        if existente.activo:
            flash('Ya existe una autorización activa con esa entidad.', 'warning')
            return redirect(url_for('entidades.detalle', entidad_id=entidad_id))
        # Reutilizar la revocada en vez de crear un duplicado
        existente.restaurar()
        db.session.commit()
        flash(f'Autorización restaurada para "{existente.autorizado.nombre_completo}".', 'success')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    try:
        nueva = AutorizadoTitular.crear_autorizacion(entidad_id, autorizado_id)
        db.session.add(nueva)
        db.session.commit()
        flash(f'Autorización concedida a "{nueva.autorizado.nombre_completo}".', 'success')
    except ValueError as e:
        flash(str(e), 'danger')

    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


@bp.route('/<int:entidad_id>/autorizados/<int:aut_id>/revocar', methods=['POST'])
@login_required
def revocar_autorizacion(entidad_id, aut_id):
    """Revoca una autorización (borrado lógico)."""
    Entidad.query.get_or_404(entidad_id)
    aut = AutorizadoTitular.query.filter_by(
        id=aut_id, titular_entidad_id=entidad_id
    ).first_or_404()

    aut.revocar()
    db.session.commit()
    flash(f'Autorización de "{aut.autorizado.nombre_completo}" revocada.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))


@bp.route('/<int:entidad_id>/autorizados/<int:aut_id>/restaurar', methods=['POST'])
@login_required
def restaurar_autorizacion(entidad_id, aut_id):
    """Restaura una autorización revocada."""
    Entidad.query.get_or_404(entidad_id)
    aut = AutorizadoTitular.query.filter_by(
        id=aut_id, titular_entidad_id=entidad_id
    ).first_or_404()

    aut.restaurar()
    db.session.commit()
    flash(f'Autorización de "{aut.autorizado.nombre_completo}" restaurada.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))
