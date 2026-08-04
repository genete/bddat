"""Consultas compartidas sobre Usuario/Rol (#630)."""
from app.models.usuarios import Usuario, Rol


def usuarios_tramitadores():
    """Usuarios activos con rol TRAMITADOR — candidatos válidos a responsable
    de expediente (#612). Evita ofrecer ADMIN/SUPERVISOR/ADMINISTRATIVO en
    desplegables de asignación (individual, masiva) o de filtro por técnico
    (radar de huérfanos, #630).
    """
    return Usuario.query.filter_by(activo=True).join(Usuario.roles).filter(
        Rol.nombre == 'TRAMITADOR'
    ).order_by(Usuario.apellido1, Usuario.apellido2).all()
