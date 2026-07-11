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
import json

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_tareas import TipoTarea
from app.models.tramites_tareas import TramiteTarea
from app.models.tramites_tareas_documentos import TramiteTareaDocumento
from app.modules.tablas_maestras.config import TIPOS
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'tablas_maestras',
    __name__,
    url_prefix='/tablas_maestras',
    template_folder='templates',
)

_ROLES_DOC_VALIDOS = {'ENTRADA', 'SALIDA'}


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


# ---------------------------------------------------------------------------
# Pasos del trámite (tramites_tareas + tramites_tareas_documentos, #171 fase 2)
#
# Editor anidado, tarea→documentos de dos niveles: se serializa como JSON en
# un input oculto (patrón simple para 2 niveles; el patrón de filas repetidas
# sin indexar de items_tecnicos solo cubre 1 nivel). Al guardar se reemplaza
# la secuencia completa del trámite (borrar todo + reinsertar en el orden del
# formulario) en vez de intentar reordenar in-place — evita la coordinación
# manual entre las dos tablas que motivó dejarlas congeladas hasta ahora.
# ---------------------------------------------------------------------------

def _tareas_disponibles():
    return TipoTarea.query.order_by(TipoTarea.codigo).all()


def _documentos_disponibles():
    return TipoDocumento.query.order_by(TipoDocumento.codigo).all()


def _serializar_pasos(tipo_tramite_id):
    """Pasos actuales de un trámite, listos para renderizar (lectura y edición)."""
    tareas = TramiteTarea.query.filter_by(tipo_tramite_id=tipo_tramite_id) \
        .order_by(TramiteTarea.orden).all()
    docs = TramiteTareaDocumento.query.filter_by(tipo_tramite_id=tipo_tramite_id).all()
    docs_por_orden = {}
    for d in docs:
        docs_por_orden.setdefault(d.orden_tarea, []).append(d)

    pasos = []
    for t in tareas:
        documentos = [
            {
                'rol': d.rol,
                'tipo_documento_id': d.tipo_documento_id,
                'tipo_documento_label': d.tipo_documento.codigo if d.tipo_documento else 'Cualquiera',
                'obligatorio': d.obligatorio,
            }
            for d in sorted(docs_por_orden.get(t.orden, []), key=lambda d: d.rol)
        ]
        pasos.append({
            'orden': t.orden,
            'tipo_tarea_id': t.tipo_tarea_id,
            'tipo_tarea_codigo': t.tipo_tarea.codigo,
            'documentos': documentos,
        })
    return pasos


def _guardar_pasos(tramite, pasos_json_raw):
    """Reemplaza la secuencia completa de pasos de `tramite` desde el JSON del form.

    Formato esperado: lista de {tipo_tarea_id, documentos: [{rol,
    tipo_documento_id, obligatorio}]}. Devuelve la lista de errores (vacía si
    todo OK) — no escribe nada en BD si hay algún error.
    """
    try:
        pasos_raw = json.loads(pasos_json_raw or '[]')
    except (TypeError, ValueError):
        return ['Secuencia de pasos: formato inválido.']

    if not isinstance(pasos_raw, list):
        return ['Secuencia de pasos: formato inválido.']

    tareas_validas = {t.id for t in _tareas_disponibles()}
    documentos_validos = {d.id for d in _documentos_disponibles()}

    filas_tarea = []
    filas_doc = []
    for i, paso in enumerate(pasos_raw, start=1):
        tipo_tarea_id = paso.get('tipo_tarea_id') if isinstance(paso, dict) else None
        if tipo_tarea_id not in tareas_validas:
            return [f'Paso {i}: tipo de tarea no válido.']

        filas_tarea.append({'orden': i, 'tipo_tarea_id': tipo_tarea_id})

        for doc in paso.get('documentos', []):
            rol = doc.get('rol')
            if rol not in _ROLES_DOC_VALIDOS:
                return [f'Paso {i}: rol de documento no válido ({rol!r}).']
            tipo_documento_id = doc.get('tipo_documento_id') or None
            if tipo_documento_id is not None and tipo_documento_id not in documentos_validos:
                return [f'Paso {i}: tipo de documento no válido.']
            filas_doc.append({
                'orden_tarea': i,
                'rol': rol,
                'tipo_documento_id': tipo_documento_id,
                'obligatorio': bool(doc.get('obligatorio', True)),
            })

    # Borrar hijos antes que padres (FK tramites_tareas_documentos -> tramites_tareas)
    TramiteTareaDocumento.query.filter_by(tipo_tramite_id=tramite.id).delete(synchronize_session=False)
    TramiteTarea.query.filter_by(tipo_tramite_id=tramite.id).delete(synchronize_session=False)
    db.session.flush()

    for fila in filas_tarea:
        db.session.add(TramiteTarea(tipo_tramite_id=tramite.id, **fila))
    db.session.flush()  # las filas de arriba deben existir antes de insertar hijos (FK)

    for fila in filas_doc:
        db.session.add(TramiteTareaDocumento(tipo_tramite_id=tramite.id, **fila))

    return []


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
        pasos=_serializar_pasos(obj.id) if tipo == 'tramite' else None,
    )


@bp.route('/<tipo>/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_tablas_maestras')
def editar_fragmento(tipo, id):
    cfg = _config(tipo)
    obj = cfg['model'].query.get_or_404(id)
    valor_id = getattr(obj, cfg['id_field'])
    extra = {}
    if tipo == 'tramite':
        extra = {
            'pasos': _serializar_pasos(obj.id),
            'tareas_opciones': [[t.id, t.codigo] for t in _tareas_disponibles()],
            'documentos_opciones': [[d.id, d.codigo] for d in _documentos_disponibles()],
        }
    return render_template(
        'tablas_maestras/_editar_fragmento.html',
        obj=obj, cfg=cfg, tipo=tipo, valor_id=valor_id,
        protegido=valor_id in cfg['protegidos'],
        **extra,
    )


@bp.route('/<tipo>/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_tablas_maestras')
def editar(tipo, id):
    cfg = _config(tipo)
    obj = cfg['model'].query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    errores = _rellenar_campos(obj, cfg, es_alta=False)
    if not errores and tipo == 'tramite':
        errores = _guardar_pasos(obj, request.form.get('pasos_json'))
    if errores:
        db.session.rollback()
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
