"""
Control de acceso centralizado (#174).

PERMISOS es la única fuente de verdad de qué rol puede hacer qué.
Cambiar un permiso = una línea en este dict.
Añadir un permiso nuevo = una entrada aquí + el check en el endpoint.

La evaluación usa siempre el rol ACTIVO de sesión, no todos los roles del usuario,
para que el cambio de rol tenga efecto real.
"""
from flask import flash, g, redirect, session, url_for
from flask_login import current_user

from app.services import bitacora

PERMISOS = {
    # Expedientes (ADR-012)
    'acceder_expediente':        {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'editar_expediente':         {'ADMIN', 'SUPERVISOR', 'TRAMITADOR'},
    'cambiar_responsable':       {'ADMIN', 'SUPERVISOR'},
    'ver_todos_proyectos':       {'ADMIN', 'SUPERVISOR', 'ADMINISTRATIVO'},

    # Áreas administrativas — patrón acceder/gestionar (ADR-013)
    'acceder_plantillas':        {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_plantillas':      {'ADMIN', 'SUPERVISOR'},

    'acceder_usuarios':          {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_usuarios':        {'ADMIN', 'SUPERVISOR'},

    # Sin UI aún — reservados para #170/#171
    'acceder_reglas_motor':      {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_reglas_motor':    {'ADMIN', 'SUPERVISOR'},

    'acceder_catalogo_plazos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_catalogo_plazos': {'ADMIN', 'SUPERVISOR'},

    'acceder_tablas_maestras':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_tablas_maestras': {'ADMIN', 'SUPERVISOR'},
}


def tiene_permiso(nombre):
    """True si el rol activo de sesión tiene el permiso indicado."""
    rol_activo = session.get('rol_activo_nombre')
    if not rol_activo:
        return False
    return rol_activo in PERMISOS.get(nombre, set())


def es_expediente_ajeno(expediente):
    """
    True si el rol activo es TRAMITADOR y el expediente no está asignado al usuario.

    Solo aplica a TRAMITADOR: ADMIN/SUPERVISOR tienen acceso pleno por diseño,
    ADMINISTRATIVO no es elegible como responsable de expediente.
    """
    return (
        session.get('rol_activo_nombre') == 'TRAMITADOR'
        and expediente.responsable_id != current_user.id
    )


# ---------------------------------------------------------------------------
# Wrappers de compatibilidad — los call sites existentes no cambian
# ---------------------------------------------------------------------------

def puede_acceder_expediente(expediente):
    return tiene_permiso('acceder_expediente')


def puede_editar_expediente(expediente):
    return tiene_permiso('editar_expediente')


def puede_cambiar_responsable():
    return tiene_permiso('cambiar_responsable')


def verificar_acceso_expediente(expediente, accion='acceder'):
    """
    Verifica acceso al expediente y gestiona el indicador de asignación.

    - Establece g.expediente_actual para que el context processor
      pueda inyectar el indicador de bombilla en el layout.
    - Si la acción es 'editar' y el expediente es ajeno, registra
      en bitácora (sin commit — responsabilidad del consumidor).
    - Devuelve None si el acceso es correcto, o un redirect si no.
    """
    g.expediente_actual = expediente

    permiso = 'editar_expediente' if accion == 'editar' else 'acceder_expediente'
    if not tiene_permiso(permiso):
        flash(f'No tienes permisos para {accion} este expediente', 'danger')
        return redirect(url_for('expedientes.listado_v2'))

    if accion == 'editar' and es_expediente_ajeno(expediente):
        bitacora.registrar(
            usuario_id=current_user.id,
            operacion='ALTERAR',
            tabla='expedientes',
            registro_id=expediente.id,
            detalle={'actuacion_fuera_asignacion': True, 'accion': accion},
        )

    return None
