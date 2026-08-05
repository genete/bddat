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

    # Hub "Control y Gestión" — antes vista del supervisor, universalizada por
    # ADR-029 §2 (enmienda ADR-028 §1): no hay razón declarada para ocultarlo,
    # tampoco indirectamente por no darle puerta de entrada. Permiso de grano
    # grueso de entrada; los permisos finos por bloque (generar_informes,
    # configurar_sistema, operar_masivo) se concretan al construir cada bloque.
    'acceder_gestion_control':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},

    # Hub "Tareas y Subidas" — cola administrativa + subida al pool (ADR-017,
    # #501). Extraído de mi_trabajo como ruta universal propia (ADR-017 §deuda
    # conocida, resuelta en #588): la escritura (gestionar_tareas) ya era
    # universal, solo la navegación lo escondía tras el rol ADMINISTRATIVO.
    'acceder_tareas_y_subidas':  {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},

    # Hub "Seguimiento y Huérfanos" — cola del TRAMITADOR + radar de huérfanos
    # (#630, ADR-038). Resuelve el tercer caso de la "Deuda conocida" de
    # ADR-017: hub propio universal en lectura, mismo patrón que los dos
    # anteriores.
    'acceder_seguimiento_y_huerfanos': {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},

    # Sin UI aún — reservados para #170/#171
    'acceder_reglas_motor':      {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_reglas_motor':    {'ADMIN', 'SUPERVISOR'},

    'acceder_catalogo_plazos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_catalogo_plazos': {'ADMIN', 'SUPERVISOR'},

    # CRUD admin de efectos_plazo (#633) — catálogo plano (código + nombre) del
    # efecto de vencimiento, FK desde catalogo_plazos.efecto_vencimiento_id.
    # Gemelo simplificado de tipos_documentos (#621).
    'acceder_efectos_plazo':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_efectos_plazo': {'ADMIN', 'SUPERVISOR'},
    # Baja física (DELETE real) — solo ADMIN, mismo criterio de protección que
    # items_tecnicos (#594): solo si no está en uso por ninguna fila de catalogo_plazos.
    'eliminar_efectos_plazo':  {'ADMIN'},

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

    # CRUD admin de items_tecnicos (#594) — catálogo de apartados de contenido
    # técnico exigidos por RD 223/2008 / RD 337/2014. Gemelo de
    # requisitos_documentales con editor de condiciones anidado. Entra como
    # tarjeta del hub del supervisor (ADR-029 §1), sin metadata.json propio.
    'acceder_items_tecnicos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_items_tecnicos': {'ADMIN', 'SUPERVISOR'},
    # Baja física (DELETE real) — solo ADMIN, mismo criterio que requisitos_documentales.
    'eliminar_items_tecnicos':  {'ADMIN'},

    # CRUD admin de tipos_documentos (#621) — catálogo de tipos semánticos de
    # documento (código inmutable usado en motor de reglas y código, mismo
    # régimen que N019/tablas_maestras). Tabla plana, sin baja (ni lógica ni
    # física: el modelo no tiene columna `activo`). Entra como tarjeta del hub
    # del supervisor (ADR-029 §1), sin metadata.json propio.
    'acceder_tipos_documentos':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_tipos_documentos': {'ADMIN', 'SUPERVISOR'},

    # CRUD admin de normas/catalogo_variables (#637, N083) — catálogo de normas
    # legales y variables del motor. Norma: alta+edición, código inmutable
    # tras el alta (mismo régimen que N019/tipos_documentos). CatalogoVariable:
    # solo edición de filas existentes (etiqueta/tipo_dato/norma_id/activa) —
    # el alta de una variable nueva exige código (función en el Variable
    # Registry, `app/services/variables/`), no dato; sin ruta de creación.
    'acceder_normas_variables':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_normas_variables': {'ADMIN', 'SUPERVISOR'},

    # CRUD admin de organo_propio (#728, ADR-039 §1) — composición de la
    # Delegación Territorial propia + unidades por provincia. Solo edición
    # (sin alta/baja: filas estructuralmente fijas).
    'acceder_organo_propio':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_organo_propio': {'ADMIN', 'SUPERVISOR'},

    # CRUD admin de firmantes_portafirmas (#728, ADR-039 §2) — catálogo de
    # firmantes de escritos, desacoplado de usuarios. Baja lógica
    # (vigente/fecha_baja) vía gestionar_firmantes_portafirmas, sin permiso
    # de eliminación física aparte.
    'acceder_firmantes_portafirmas':   {'ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'},
    'gestionar_firmantes_portafirmas': {'ADMIN', 'SUPERVISOR'},

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
