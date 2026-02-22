"""Blueprint proyectos — Listado V2 + detalle + editar.

RUTAS:
    GET /proyectos/           → listado V2 (shell, datos vía API)
    GET /proyectos/<id>       → redirige al detalle del expediente asociado (#128)
    GET /proyectos/<id>/editar → redirige a edición del expediente asociado

VERSIÓN: 2.1
FECHA: 2026-02-22
ISSUE: #128
"""

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.usuarios import Usuario
from app.models.tipos_ia import TipoIA

# template_folder apunta a app/modules/proyectos/templates/
bp = Blueprint('proyectos', __name__,
               url_prefix='/proyectos',
               template_folder='templates')


# =============================================================================
# LISTADO  (shell V2 — datos cargados por ScrollInfinito vía API)
# =============================================================================

@bp.route('/')
@login_required
def index():
    """Vista listado de proyectos. Pasa tipos_ia para poblar el filtro."""
    tipos_ia = TipoIA.query.order_by(TipoIA.siglas).all()
    return render_template('proyectos/index.html', tipos_ia=tipos_ia)


# =============================================================================
# DETALLE
# =============================================================================

@bp.route('/<int:id>')
@login_required
def detalle(id):
    """
    Vista detallada de un proyecto.

    Permisos:
        TRAMITADOR puro: solo ve proyectos de sus expedientes asignados.
        ADMIN/SUPERVISOR: ven cualquier proyecto.
    """
    proyecto = (
        db.session.query(Proyecto)
        .join(Expediente)
        .outerjoin(Usuario, Expediente.responsable_id == Usuario.id)
        .outerjoin(TipoIA, Proyecto.ia_id == TipoIA.id)
        .filter(Proyecto.id == id)
        .first()
    )

    if not proyecto:
        abort(404)

    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        if proyecto.expediente.responsable_id != current_user.id:
            abort(403)

    # La Vista V4 de expediente contiene toda la info del proyecto → redirigir
    return redirect(url_for('expedientes.detalle', id=proyecto.expediente.id))


# =============================================================================
# EDITAR  (redirección a expediente)
# =============================================================================

@bp.route('/<int:id>/editar')
@login_required
def editar_proyecto(id):
    """
    Redirige a la edición del expediente asociado con scroll a #proyecto.

    Estrategia: Opción A — Redirección inteligente (issue #41).
    Reutiliza el formulario de expediente en lugar de duplicar lógica.
    """
    proyecto = (
        db.session.query(Proyecto)
        .join(Expediente)
        .filter(Proyecto.id == id)
        .first()
    )

    if not proyecto:
        abort(404)

    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        if proyecto.expediente.responsable_id != current_user.id:
            abort(403)

    return redirect(url_for('expedientes.editar', id=proyecto.expediente.id) + '#proyecto')
