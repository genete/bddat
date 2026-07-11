"""
Blueprint para administración de catálogos estructurales ESFTT (#171).

Módulo único con pestañas — Expediente / Solicitud / Fase / Trámite / Tarea
(ADR-029 §1: tarjeta del hub del supervisor, sin metadata.json propio).

Regla común a las 5 tablas (ver config.py): el campo identificador se fija
al crear y no se edita nunca. Ninguna fila es borrable.

Rutas:
- GET  /tablas_maestras/                            — Shell con las 5 pestañas
- POST /tablas_maestras/<tipo>/crear                 — Alta
- GET  /tablas_maestras/<tipo>/<id>/fragmento        — Fragmento de lectura (inspector)
- GET  /tablas_maestras/<tipo>/<id>/editar-fragmento — Fragmento de edición
- POST /tablas_maestras/<tipo>/<id>/editar           — Guardar cambios
"""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.modules.tablas_maestras.config import TIPOS
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'tablas_maestras',
    __name__,
    url_prefix='/tablas_maestras',
    template_folder='templates',
)


def _config(tipo):
    cfg = TIPOS.get(tipo)
    if cfg is None:
        abort(404)
    return cfg


def _rellenar_campos(obj, cfg, es_alta):
    """Rellena los campos editables de `obj` desde request.form.

    El id_field solo se acepta en alta; en edición ni se lee del form (es
    inmutable, #171). Devuelve la lista de errores de validación.
    """
    errores = []

    if es_alta:
        id_field = cfg['id_field']
        valor_id = request.form.get(id_field, '').strip()
        if not valor_id:
            errores.append(f"{cfg['id_label']} es obligatorio.")
        elif cfg['id_maxlen'] and len(valor_id) > cfg['id_maxlen']:
            errores.append(f"{cfg['id_label']} no puede superar {cfg['id_maxlen']} caracteres.")
        else:
            setattr(obj, id_field, valor_id)

    for campo, label, tipo_campo, requerido, maxlen in cfg['campos']:
        if tipo_campo == 'bool':
            setattr(obj, campo, request.form.get(campo) == 'on')
            continue
        valor = request.form.get(campo, '').strip()
        if requerido and not valor:
            errores.append(f'{label} es obligatorio.')
            continue
        if maxlen and len(valor) > maxlen:
            errores.append(f'{label} no puede superar {maxlen} caracteres.')
            continue
        setattr(obj, campo, valor or None)

    return errores


@bp.route('/')
@login_required
@require_permiso('acceder_tablas_maestras')
def listado():
    return render_template('tablas_maestras/listado.html', tipos=TIPOS)


@bp.route('/<tipo>/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_tablas_maestras')
def crear(tipo):
    cfg = _config(tipo)
    if not cfg['permite_alta']:
        abort(404)

    obj = cfg['model']()
    errores = _rellenar_campos(obj, cfg, es_alta=True)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('tablas_maestras.listado', tab=tipo))

    db.session.add(obj)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return redirect(url_for('tablas_maestras.listado', tab=tipo))

    flash(f"{cfg['singular']} creado correctamente.", 'success')
    return redirect(url_for('tablas_maestras.listado', tab=tipo, sel=obj.id))


@bp.route('/<tipo>/<int:id>/fragmento')
@login_required
@require_permiso('acceder_tablas_maestras')
def fragmento(tipo, id):
    cfg = _config(tipo)
    obj = cfg['model'].query.get_or_404(id)
    valor_id = getattr(obj, cfg['id_field'])
    return render_template(
        'tablas_maestras/_detalle_fragmento.html',
        obj=obj, cfg=cfg, tipo=tipo, valor_id=valor_id,
        protegido=valor_id in cfg['protegidos'],
        puede_editar=tiene_permiso('gestionar_tablas_maestras'),
    )


@bp.route('/<tipo>/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_tablas_maestras')
def editar_fragmento(tipo, id):
    cfg = _config(tipo)
    obj = cfg['model'].query.get_or_404(id)
    valor_id = getattr(obj, cfg['id_field'])
    return render_template(
        'tablas_maestras/_editar_fragmento.html',
        obj=obj, cfg=cfg, tipo=tipo, valor_id=valor_id,
        protegido=valor_id in cfg['protegidos'],
    )


@bp.route('/<tipo>/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_tablas_maestras')
def editar(tipo, id):
    cfg = _config(tipo)
    obj = cfg['model'].query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    errores = _rellenar_campos(obj, cfg, es_alta=False)
    if errores:
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('tablas_maestras.listado', tab=tipo, sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('tablas_maestras.listado', tab=tipo, sel=id))

    msg = f"{cfg['singular']} actualizado correctamente."
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('tablas_maestras.listado', tab=tipo, sel=id))
