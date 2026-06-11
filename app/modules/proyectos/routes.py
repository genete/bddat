"""Blueprint proyectos — Todos los accesos redirigen al listado unificado de expedientes.

RUTAS:
    GET /proyectos/           → 302 a /expedientes/ (ADR-024 §1 / #543)
    GET /proyectos/<id>       → 302 a /expedientes/?sel=<expediente.id> (#543)
    GET /proyectos/<id>/editar → 302 a /expedientes/?sel=<expediente.id> (#543)

El listado de proyectos quedó fusionado con expedientes (ADR-024).
Este blueprint solo conserva las rutas para que los bookmarks externos sigan vivos.

VERSIÓN: 3.0
FECHA: 2026-06-11
ISSUE: #543
"""

from flask import Blueprint, redirect, url_for, abort
from flask_login import login_required
from app import db
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente

bp = Blueprint('proyectos', __name__,
               url_prefix='/proyectos',
               template_folder='templates')


@bp.route('/')
@login_required
def index():
    """Listado de proyectos → redirige al listado unificado de expedientes (ADR-024 §1)."""
    return redirect(url_for('expedientes.listado_v2'))


@bp.route('/<int:id>')
@login_required
def detalle(id):
    """Detalle de proyecto → redirige al listado con el inspector abierto (ADR-024 §1)."""
    proyecto = db.session.query(Proyecto).join(Expediente).filter(Proyecto.id == id).first()
    if not proyecto:
        abort(404)
    return redirect(url_for('expedientes.listado_v2', sel=proyecto.expediente.id))


@bp.route('/<int:id>/editar')
@login_required
def editar_proyecto(id):
    """Editar proyecto → redirige al listado con inspector (ADR-024 §1)."""
    proyecto = db.session.query(Proyecto).join(Expediente).filter(Proyecto.id == id).first()
    if not proyecto:
        abort(404)
    return redirect(url_for('expedientes.listado_v2', sel=proyecto.expediente.id))
