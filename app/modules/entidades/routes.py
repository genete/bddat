"""Blueprint entidades - Vistas HTML para gestión de entidades.

RUTAS:
    GET  /entidades/                                   → listado (shell V2, datos vía API)
    GET  /entidades/nueva                              → formulario nueva entidad
    POST /entidades/nueva                              → crear entidad
    GET  /entidades/<id>                               → redirect a /entidades/?sel=<id> (ADR-023 #534)
    GET  /entidades/<id>/fragmento                     → parcial lectura para el inspector (ADR-023 #534)
    GET  /entidades/<id>/editar-fragmento              → parcial edición para el inspector (ADR-023 §5 #534)
    GET  /entidades/<id>/editar                        → redirect a /entidades/?sel=<id> (ADR-023 #534)
    POST /entidades/<id>/editar                        → guardar cambios; JSON si XHR, redirect si no (#534)
    POST /entidades/<id>/direcciones/nueva             → añadir dirección; JSON si XHR, redirect si no (#136 #534)
    POST /entidades/<id>/direcciones/<dir_id>/editar   → editar dirección; JSON si XHR, redirect si no (#136 #534)
    POST /entidades/<id>/direcciones/<dir_id>/toggle   → activar/desactivar dirección; JSON si XHR (#136 #534)
    POST /entidades/<id>/autorizados/nueva             → nueva autorización; JSON si XHR (#137 #534)
    POST /entidades/<id>/autorizados/<aut_id>/revocar  → revocar autorización; JSON si XHR (#137 #534)
    POST /entidades/<id>/autorizados/<aut_id>/restaurar → restaurar autorización; JSON si XHR (#137 #534)

VERSIÓN: 1.5
FECHA: 2026-06-11
ISSUE: #534
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models.entidad import Entidad
from app.models.autorizados_titular import AutorizadoTitular
from app.models.direccion_notificacion import DireccionNotificacion
from app.utils.metadata import cargar_metadata

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
    meta = cargar_metadata('entidades')
    columns = meta.get('listado_v2', {}).get('columns', [])
    return render_template('entidades/index.html', columns=columns)


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
    """Redirige al listado con el inspector abierto en esa entidad (ADR-023 §9)."""
    return redirect(url_for('entidades.index', sel=entidad_id))


@bp.route('/<int:entidad_id>/fragmento')
@login_required
def fragmento(entidad_id):
    """Fragmento HTML de lectura para el inspector (ADR-023 §9 / #534)."""
    entidad = Entidad.query.get_or_404(entidad_id)
    autorizaciones = []
    if entidad.rol_titular:
        autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(
            entidad_id, solo_activos=False
        )
    return render_template(
        'entidades/_detalle_fragmento.html',
        entidad=entidad,
        autorizaciones=autorizaciones,
    )


@bp.route('/<int:entidad_id>/gestionar-direcciones')
@login_required
def gestionar_direcciones(entidad_id):
    """Fragmento modal grande — gestión de direcciones de notificación (ADR-023 §6 / #534)."""
    entidad = Entidad.query.get_or_404(entidad_id)
    return render_template(
        'entidades/_gestionar_direcciones_fragmento.html',
        entidad=entidad,
    )


@bp.route('/<int:entidad_id>/gestionar-autorizaciones')
@login_required
def gestionar_autorizaciones(entidad_id):
    """Fragmento modal grande — gestión de autorizaciones (ADR-023 §6 / #534). Solo titulares."""
    entidad = Entidad.query.get_or_404(entidad_id)
    if not entidad.rol_titular:
        return '', 403
    autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(
        entidad_id, solo_activos=False
    )
    return render_template(
        'entidades/_gestionar_autorizaciones_fragmento.html',
        entidad=entidad,
        autorizaciones=autorizaciones,
    )


@bp.route('/<int:entidad_id>/editar-fragmento')
@login_required
def editar_fragmento(entidad_id):
    """Fragmento HTML de edición para el inspector (ADR-023 §5 / #534)."""
    entidad = Entidad.query.get_or_404(entidad_id)
    return render_template('entidades/_editar_fragmento.html', entidad=entidad)


@bp.route('/<int:entidad_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(entidad_id):
    """Edición de entidad (ADR-023 §5 / #534).

    GET  → redirect al listado con inspector abierto (ya no es página).
    POST → JSON si X-Requested-With:XMLHttpRequest; redirect si no (fallback).
    """
    entidad = Entidad.query.get_or_404(entidad_id)

    if request.method == 'GET':
        return redirect(url_for('entidades.index', sel=entidad_id))

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

    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if errores:
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('entidades.index', sel=entidad_id))

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

    if is_xhr:
        return jsonify({
            'ok': True,
            'message': f'Entidad "{entidad.nombre_completo}" actualizada correctamente.',
        })
    flash(f'Entidad "{entidad.nombre_completo}" actualizada correctamente.', 'success')
    return redirect(url_for('entidades.index', sel=entidad_id))


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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if errores:
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
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

    if is_xhr:
        return jsonify({'ok': True, 'message': 'Dirección de notificación añadida.'})
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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if errores:
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
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
    if is_xhr:
        return jsonify({'ok': True, 'message': 'Dirección de notificación actualizada.'})
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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_xhr:
        return jsonify({'ok': True, 'message': f'Dirección "{direccion.descripcion or dir_id}" {estado}.'})
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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not entidad.rol_titular:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Esta entidad no tiene rol Titular.']})
        flash('Esta entidad no tiene rol Titular.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    autorizado_id_str = request.form.get('autorizado_id', '').strip()
    if not autorizado_id_str or not autorizado_id_str.isdigit():
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Debe seleccionar una entidad autorizada.']})
        flash('Debe seleccionar una entidad autorizada.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    autorizado_id = int(autorizado_id_str)

    if autorizado_id == entidad_id:
        if is_xhr:
            return jsonify({'ok': False, 'errors': ['Una entidad no puede autorizarse a sí misma.']})
        flash('Una entidad no puede autorizarse a sí misma.', 'danger')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    # Comprobar que no existe ya una autorización activa
    existente = AutorizadoTitular.query.filter_by(
        titular_entidad_id=entidad_id,
        autorizado_entidad_id=autorizado_id,
    ).first()

    if existente:
        if existente.activo:
            if is_xhr:
                return jsonify({'ok': False, 'errors': ['Ya existe una autorización activa con esa entidad.']})
            flash('Ya existe una autorización activa con esa entidad.', 'warning')
            return redirect(url_for('entidades.detalle', entidad_id=entidad_id))
        # Reutilizar la revocada en vez de crear un duplicado
        existente.restaurar()
        db.session.commit()
        if is_xhr:
            return jsonify({'ok': True, 'message': f'Autorización restaurada para "{existente.autorizado.nombre_completo}".'})
        flash(f'Autorización restaurada para "{existente.autorizado.nombre_completo}".', 'success')
        return redirect(url_for('entidades.detalle', entidad_id=entidad_id))

    try:
        nueva = AutorizadoTitular.crear_autorizacion(entidad_id, autorizado_id)
        db.session.add(nueva)
        db.session.commit()
        if is_xhr:
            return jsonify({'ok': True, 'message': f'Autorización concedida a "{nueva.autorizado.nombre_completo}".'})
        flash(f'Autorización concedida a "{nueva.autorizado.nombre_completo}".', 'success')
    except ValueError as e:
        if is_xhr:
            return jsonify({'ok': False, 'errors': [str(e)]})
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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_xhr:
        return jsonify({'ok': True, 'message': f'Autorización de "{aut.autorizado.nombre_completo}" revocada.'})
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
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_xhr:
        return jsonify({'ok': True, 'message': f'Autorización de "{aut.autorizado.nombre_completo}" restaurada.'})
    flash(f'Autorización de "{aut.autorizado.nombre_completo}" restaurada.', 'success')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))
