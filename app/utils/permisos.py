"""
Control de acceso centralizado (#174).

PERMISOS es la única fuente de verdad de qué rol puede hacer qué.
Cambiar un permiso = una línea en este dict.
Añadir un permiso nuevo = una entrada aquí + el check en el endpoint.

La evaluación usa siempre el rol ACTIVO de sesión, no todos los roles del usuario,
para que el cambio de rol tenga efecto real.
"""
from flask import flash, g, redirect, request, session, url_for
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

    # Vista del supervisor — hub de dos bloques (ADR-028, #579). Permiso de grano
    # grueso de entrada; los permisos finos por bloque (generar_informes,
    # configurar_sistema, operar_masivo) se concretan al construir cada bloque.
    'acceder_supervision':       {'ADMIN', 'SUPERVISOR'},

    # Sin UI aún — reservados para #170/#171
    'acceder_reglas_motor':      {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_reglas_motor':    {'ADMIN', 'SUPERVISOR'},

    'acceder_catalogo_plazos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_catalogo_plazos': {'ADMIN', 'SUPERVISOR'},

    'acceder_tablas_maestras':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_tablas_maestras': {'ADMIN', 'SUPERVISOR'},

    # CRUD admin de requisitos_documentales (#583) — catálogo normativo del checklist
    'acceder_requisitos_documentales':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_requisitos_documentales': {'ADMIN', 'SUPERVISOR'},
    # Baja física (DELETE real) — más restrictivo que gestionar: solo ADMIN.
    # El SUPERVISOR sigue pudiendo crear/editar/activar-desactivar (baja lógica).
    'eliminar_requisitos_documentales':  {'ADMIN'},

    # CRUD admin de catalogo_requerimientos (#593) — catálogo de defectos tipo
    # reutilizables en la tarea ANALIZAR. Tabla plana, sin condiciones anidadas
    # (gemelo simplificado de requisitos_documentales, #583).
    'acceder_catalogo_requerimientos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_catalogo_requerimientos': {'ADMIN', 'SUPERVISOR'},
    # Baja lógica (activo=False) — a diferencia de #583, aquí es exclusiva de
    # ADMIN: el SUPERVISOR puede crear/editar pero no archivar (criterio del issue).
    'archivar_catalogo_requerimientos':  {'ADMIN'},

    # Árbol del expediente — frontera hoja / estructura (ADR-017 §6, #501).
    # "Puerta abierta": gestionar_tareas habilita COMPLETAR cualquier tarea ya
    # prevista (incluye ADMINISTRATIVO); la bitácora es la rendición de cuentas.
    # gestionar_estructura_expediente (crear/editar/borrar solicitudes, fases,
    # trámites) es "tramitar" → propio del TRAMITADOR, NO del ADMINISTRATIVO.
    'gestionar_tareas':              {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_estructura_expediente': {'ADMIN', 'SUPERVISOR', 'TRAMITADOR'},
}

# Mapa acción → permiso para verificar_acceso_expediente. Las acciones de mutación
# (todas menos 'acceder') comprueban su permiso específico; el resto cae a acceder.
# 'subir_documento' es acceder_expediente a propósito: aportar un documento al pool
# NO edita el expediente (nace con vínculos indirectos, ADR-027) — sin limitación de
# rol. El borrado del pool sí es del técnico (usa 'editar').
_PERMISO_POR_ACCION = {
    'editar':               'editar_expediente',
    'gestionar_tarea':      'gestionar_tareas',
    'gestionar_estructura': 'gestionar_estructura_expediente',
    'subir_documento':      'acceder_expediente',
}

# Acciones que, si las ejecuta un TRAMITADOR sobre un expediente ajeno, dejan traza
# en bitácora (actuación fuera de asignación). Subir al pool no cuenta: no toca el
# expediente.
_ACCIONES_CON_TRAZA_AJENA = {'editar', 'gestionar_tarea', 'gestionar_estructura'}


def tiene_permiso(nombre):
    """True si el rol activo de sesión tiene el permiso indicado."""
    rol_activo = session.get('rol_activo_nombre')
    if not rol_activo:
        return False
    return rol_activo in PERMISOS.get(nombre, set())


def _es_peticion_json():
    """True si la petición es de una API/isla (espera JSON), no una navegación HTML."""
    return (
        'application/json' in request.headers.get('Accept', '')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.is_json
    )


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

    `accion` ∈ {'acceder'/'ver', 'editar', 'gestionar_tarea',
    'gestionar_estructura', 'subir_documento'} → cada una comprueba su permiso
    según _PERMISO_POR_ACCION (las desconocidas caen a acceder_expediente).

    - Establece g.expediente_actual para que el context processor
      pueda inyectar el indicador de bombilla en el layout.
    - Si la acción muta el expediente y este es ajeno (TRAMITADOR), registra
      en bitácora (sin commit — responsabilidad del consumidor).
    - Devuelve None si el acceso es correcto, o un redirect si no.
    """
    g.expediente_actual = expediente

    permiso = _PERMISO_POR_ACCION.get(accion, 'acceder_expediente')
    if not tiene_permiso(permiso):
        # En peticiones JSON/XHR (API de islas React) NO encolar flash: se quedaría
        # colgado para la siguiente página HTML. El front muestra su propio aviso y
        # el endpoint debe devolver 403 JSON (no este redirect, que el fetch seguiría).
        if not _es_peticion_json():
            flash(f'No tienes permisos para {accion} este expediente', 'danger')
        return redirect(url_for('expedientes.listado_v2'))

    if accion in _ACCIONES_CON_TRAZA_AJENA and es_expediente_ajeno(expediente):
        bitacora.registrar(
            usuario_id=current_user.id,
            operacion='ALTERAR',
            tabla='expedientes',
            registro_id=expediente.id,
            detalle={'actuacion_fuera_asignacion': True, 'accion': accion},
        )

    return None
