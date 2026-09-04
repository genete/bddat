"""API REST para expedientes.

ENDPOINTS:
    1. GET /api/expedientes - Listado paginado con cursor (scroll infinito)

VERSIÓN: 2.3
FECHA: 2026-06-11
CAMBIOS v2.3: Añadidos campos titulo_proyecto, ia, municipios_resumen (#543).
              Nuevos filtros ia_id y municipio_id (#543).
CAMBIOS v2.2: Eliminado endpoint /jerarquia (solo consumido por vistas BC obsoletas, issue #500).
              url_tramitacion apunta a expedientes.arbol.
CAMBIOS v2.1: Añadido campo 'codigo' ("AT-{numero_at}") a serialización del listado
              para compatibilidad con ScrollInfinito genérico (Opción B, Issue #61).
"""

from datetime import date
from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from app import db
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.tipos_expedientes import TipoExpediente
from app.models.municipios_proyecto import MunicipioProyecto
from app.models import (
    Solicitud, Fase, TipoSolicitud, TipoFase,
    Proyecto, TipoIA, Usuario,
    Tramite, Tarea, TipoTramite, TipoTarea, Documento,
    OrganismoExpediente,
)
from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
from app.models.items_tecnicos import ItemTecnico, CoberturaItemTecnico
from app.models.catalogo_requerimientos import CatalogoRequerimiento
from app.models.requerimientos_tarea import RequerimientoTarea
from app.services.arbol_expediente import construir_arbol
from app.services.tipos_creables import tipos_creables_de_nodo
from app.services.detalle_nodo import detalle_de_nodo, info_apertura_documento
from app.services.esquema_editable import esquema_de_nodo
from app.services import mutaciones_arbol as svc
from app.services import consultas_organismos as svc_consultas
from app.utils.api_respuestas import leer_bypass
from app.utils.formularios import leer_json
from app.services.assembler import build
from app.services.requisitos import evaluar_requisitos
from app.services.items_tecnicos import evaluar_items_tecnicos
from app.services.consolidacion_defectos import consolidar_defectos
from app.services.diagnosticos import (
    crear_diagnostico, revertir_diagnostico, motivo_bloqueo_reversion,
    DiagnosticoConsumidoError, DiagnosticoSuperadoError, FaseCerradaError,
    motivo_check_ya_exigido, motivo_check_ya_exigido_lote,
    diagnostico_donde_se_exigio_item, diagnostico_donde_se_exigio_requerimiento,
)
from app.services.invariantes_esftt import check_invariante
from app.services import bitacora as bitacora_svc
from app.services import mensajes_internos as servicio_mensajes
from app.models.notificaciones import Notificacion
from app.services.parser_justificante_notifica import (
    parsear_justificante_notifica, parsear_justificante_notifica_zip,
)
from app.utils.permisos import verificar_acceso_expediente, tiene_permiso

# Trámites cuya tarea ANALIZAR lleva las secciones extendidas del contenedor
# (#442: check documental #495, check técnico #581, requerimientos #440).
# El resto de trámites cuya tarea ANALIZAR produce un DIAGNOSTICO (CONSULTA_SEPARATA,
# AUDIENCIA...) solo necesita el núcleo común (resultado + producir documento).
_TRAMITES_CON_SECCIONES_ANALISIS = {'ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION'}

# Blueprint para API
api_bp = Blueprint('api', __name__, url_prefix='/api')


# =============================================================================
# ENDPOINT 1: Listado paginado (scroll infinito)
# =============================================================================

@api_bp.route('/expedientes', methods=['GET'])
@login_required
def listar_expedientes():
    """
    Endpoint GET /api/expedientes - Listado paginado con cursor.

    PAGINACIÓN POR CURSOR:
        Ventajas vs OFFSET:
        - Rendimiento constante O(1) incluso con millones de registros
        - No sufre "page drift" si se insertan/borran registros durante navegación
        - Utiliza índice PRIMARY KEY (id) para búsqueda eficiente

        Funcionamiento:
        - cursor: ID del último expediente recibido en llamada anterior
        - limit: Número de registros a devolver (máx 100, default 50)
        - Query: WHERE id > cursor ORDER BY id ASC LIMIT limit
        - Si cursor=0 o ausente: primera página (sin filtro WHERE)

    FILTROS:
        - search: Búsqueda parcial en numero_at o nombre_completo del titular (ILIKE)
        - estado: Filtro por estado del expediente (futuro: tabla estados)

    RESPUESTA JSON:
        {
            "data": [expediente1, expediente2, ...],
            "next_cursor": 156,  # ID del último expediente devuelto
            "has_more": true,    # ¿Existen más registros?
            "total": 523         # Total de expedientes (con filtros aplicados)
        }

    Cada expediente incluye el campo 'codigo' ("AT-{numero_at}") para
    compatibilidad con ScrollInfinito genérico (Issue #61, Opción B).

    Query Parameters:
        cursor (int, opcional): ID del último expediente recibido. Default: 0 (primera página)
        limit (int, opcional): Registros por página. Min 1, max 100. Default: 50
        search (str, opcional): Búsqueda parcial. Mínimo 2 caracteres.
        estado (str, opcional): Filtro por estado (mock por ahora).

    Returns:
        JSON con data, next_cursor, has_more, total (opcional)
        HTTP Status: 200 OK, 400 Bad Request, 401 Unauthorized
    """

    # ==========================================================================
    # PASO 1: Parsear y validar parámetros
    # ==========================================================================

    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'Cursor debe ser >= 0'}), 400

        limit = int(request.args.get('limit', 50))
        if limit < 1:
            return jsonify({'error': 'Limit debe ser >= 1'}), 400
        if limit > 100:
            limit = 100

        search_query = request.args.get('search', '').strip()
        if search_query and len(search_query) < 2:
            return jsonify({'error': 'Search debe tener al menos 2 caracteres'}), 400

        estado_filter = request.args.get('estado', '').strip()
        responsable_filter = request.args.get('responsable', '').strip()
        ia_id_filter = request.args.get('ia_id', '').strip()
        municipio_id_filter = request.args.get('municipio_id', '').strip()
        tipo_exp_filter = request.args.get('tipo_expediente_id', '').strip()

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # ==========================================================================
    # PASO 2: Construir query base con eager loading
    # ==========================================================================

    query = db.session.query(Expediente).options(
        joinedload(Expediente.titular),
        joinedload(Expediente.tipo_expediente),
        joinedload(Expediente.responsable),
        joinedload(Expediente.proyecto).joinedload(Proyecto.ia),
    )

    # ==========================================================================
    # PASO 3: Aplicar cursor (paginación)
    # ==========================================================================

    if cursor > 0:
        query = query.filter(Expediente.id > cursor)

    # ==========================================================================
    # PASO 4: Aplicar filtros opcionales
    # ==========================================================================

    search_numero = None

    if search_query:
        try:
            search_numero = int(search_query)
        except ValueError:
            pass

        filtros_busqueda = []

        if search_numero is not None:
            filtros_busqueda.append(Expediente.numero_at == search_numero)

        filtros_busqueda.append(
            Expediente.titular.has(
                func.lower(Entidad.nombre_completo).contains(func.lower(search_query))
            )
        )

        query = query.filter(or_(*filtros_busqueda))

    if responsable_filter == 'yo':
        query = query.filter(Expediente.responsable_id == current_user.id)
    elif responsable_filter == 'sin_asignar':
        query = query.filter(Expediente.responsable_id.is_(None))

    if tipo_exp_filter:
        try:
            query = query.filter(Expediente.tipo_expediente_id == int(tipo_exp_filter))
        except ValueError:
            return jsonify({'error': 'tipo_expediente_id debe ser entero'}), 400

    if ia_id_filter:
        try:
            ia_pids = db.session.query(Proyecto.id).filter(
                Proyecto.ia_id == int(ia_id_filter)
            ).subquery()
            query = query.filter(Expediente.proyecto_id.in_(ia_pids))
        except ValueError:
            return jsonify({'error': 'ia_id debe ser entero'}), 400

    if municipio_id_filter:
        try:
            muni_pids = db.session.query(MunicipioProyecto.proyecto_id).filter(
                MunicipioProyecto.municipio_id == int(municipio_id_filter)
            ).subquery()
            query = query.filter(Expediente.proyecto_id.in_(muni_pids))
        except ValueError:
            return jsonify({'error': 'municipio_id debe ser entero'}), 400

    if estado_filter:
        estados_validos = ['borrador', 'tramitacion', 'finalizado', 'archivado']
        if estado_filter.lower() not in estados_validos:
            return jsonify({'error': f'Estado inválido. Válidos: {", ".join(estados_validos)}'}), 400

        # Subquery: IDs de expedientes con alguna solicitud
        ids_con_solicitudes = db.session.query(Solicitud.expediente_id).subquery()

        if estado_filter in ('tramitacion', 'finalizado', 'archivado'):
            # Sin campo estado en Solicitud, estos filtros equivalen a "con solicitudes"
            query = query.filter(Expediente.id.in_(ids_con_solicitudes))
        elif estado_filter == 'borrador':
            query = query.filter(Expediente.id.notin_(ids_con_solicitudes))

    # ==========================================================================
    # PASO 5: Ejecutar query con limit + 1
    # ==========================================================================

    query = query.order_by(Expediente.id.asc())
    expedientes = query.limit(limit + 1).all()

    has_more = len(expedientes) > limit
    if has_more:
        expedientes = expedientes[:limit]

    next_cursor = expedientes[-1].id if expedientes else cursor

    # ==========================================================================
    # PASO 5b: Obtener estadísticas de solicitudes para los IDs de esta página
    # Una sola query adicional evita N+1 y no modifica el query principal
    # ==========================================================================

    ids_pagina = [e.id for e in expedientes]
    sol_stats = {}
    if ids_pagina:
        rows = db.session.query(
            Solicitud.expediente_id,
            func.count(Solicitud.id).label('total'),
            func.count(Solicitud.id).label('activas')
        ).filter(
            Solicitud.expediente_id.in_(ids_pagina)
        ).group_by(Solicitud.expediente_id).all()
        sol_stats = {row.expediente_id: row for row in rows}

    # Conteo de municipios por proyecto (batch, evita N+1)
    proyecto_ids = [e.proyecto_id for e in expedientes if e.proyecto_id]
    muni_counts = {}
    if proyecto_ids:
        muni_rows = db.session.query(
            MunicipioProyecto.proyecto_id,
            func.count(MunicipioProyecto.municipio_id).label('cnt')
        ).filter(
            MunicipioProyecto.proyecto_id.in_(proyecto_ids)
        ).group_by(MunicipioProyecto.proyecto_id).all()
        muni_counts = {row.proyecto_id: row.cnt for row in muni_rows}

    # ==========================================================================
    # PASO 6: Calcular total (solo si hay filtros)
    # ==========================================================================

    total = None
    if search_query or estado_filter:
        count_query = db.session.query(func.count(Expediente.id))

        if cursor > 0:
            count_query = count_query.filter(Expediente.id > cursor)

        if search_query:
            filtros_busqueda = []
            if search_numero is not None:
                filtros_busqueda.append(Expediente.numero_at == search_numero)

            filtros_busqueda.append(
                db.session.query(Expediente).join(Entidad, Expediente.titular_id == Entidad.id).filter(
                    func.lower(Entidad.nombre_completo).contains(func.lower(search_query))
                ).exists()
            )
            count_query = count_query.filter(or_(*filtros_busqueda))

        total = count_query.scalar()

    # ==========================================================================
    # PASO 7: Serializar a JSON
    # ==========================================================================

    data = []
    for exp in expedientes:
        if exp.responsable:
            nombre_responsable = f"{exp.responsable.apellido1 or ''} {exp.responsable.apellido2 or ''}, {exp.responsable.nombre or ''}".strip()
            nombre_responsable = ' '.join(nombre_responsable.split())
            if nombre_responsable.startswith(','):
                nombre_responsable = nombre_responsable[1:].strip()
        else:
            nombre_responsable = 'Sin asignar'

        # Datos de solicitudes de esta página
        stats = sol_stats.get(exp.id)
        num_solicitudes = stats.total if stats else 0
        num_activas = stats.activas if stats else 0
        if num_solicitudes == 0:
            estado_tramitacion = 'SIN_SOLICITUDES'
        elif num_activas > 0:
            estado_tramitacion = 'EN_TRAMITE'
        else:
            estado_tramitacion = 'RESUELTO'

        muni_cnt = muni_counts.get(exp.proyecto_id, 0)
        titulo_proyecto = exp.proyecto.titulo if exp.proyecto else '—'
        ia_siglas = (exp.proyecto.ia.siglas if exp.proyecto and exp.proyecto.ia else '—')
        municipios_resumen = (
            f'{muni_cnt} municipio{"s" if muni_cnt != 1 else ""}' if muni_cnt else '—'
        )

        expediente_dict = {
            'id':                  exp.id,
            'codigo':              f'AT-{exp.numero_at}',   # Opción B Issue #61
            'numero_at':           exp.numero_at,
            'titular':             exp.titular.nombre_completo if exp.titular else 'Sin titular',
            'tipo_expediente':     exp.tipo_expediente.tipo if exp.tipo_expediente else 'Sin tipo',
            'titulo_proyecto':     titulo_proyecto,
            'ia':                  ia_siglas,
            'municipios_resumen':  municipios_resumen,
            'responsable':         nombre_responsable,
            'heredado':            exp.heredado if exp.heredado is not None else False,
            # Campos SFTT (#70)
            'num_solicitudes':     num_solicitudes,
            'num_activas':         num_activas,
            'estado_tramitacion':  estado_tramitacion,
            'url_tramitacion':     url_for('expedientes.arbol', id=exp.id)
        }
        data.append(expediente_dict)

    # ==========================================================================
    # PASO 8: Respuesta JSON
    # ==========================================================================

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more
    }

    if total is not None:
        response['total'] = total

    return jsonify(response), 200



# =============================================================================
# ENDPOINT 3: Árbol completo del expediente (Vista de árbol, ADR-016)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/arbol', methods=['GET'])
@login_required
def get_arbol_expediente(expediente_id):
    """
    GET /api/expedientes/<id>/arbol — árbol completo para la vista de árbol (ADR-016).

    Payload: ADR-016 §16 — JSON anidado de dominio (expediente → solicitudes →
    fases → trámites → tareas) con decoradores por nodo, estado SEMÁNTICO (el color
    lo pone el front en el tematizado de xyflow), plazos resueltos en backend y
    agregadores de subárbol (§11) en cada nodo no-hoja.

    El detalle fino de cada nodo NO viaja aquí: va en el endpoint lazy
    /nodo/<tipo>/<id> consultado al seleccionar (§16).
    """
    expediente = Expediente.query.get_or_404(expediente_id)

    # Control de acceso sobre expediente concreto (REGLAS_DESARROLLO §Control de acceso).
    # Devuelve None si hay acceso, o un redirect si no. De paso habilita el
    # indicador de bombilla del header para TRAMITADOR.
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    arbol = construir_arbol(expediente_id)
    if arbol is None:
        return jsonify({'error': 'Expediente no encontrado'}), 404
    return jsonify(arbol), 200


# =============================================================================
# ENDPOINT 4: Tipos de hijo creables bajo un nodo (despensa + menú, ADR-016 §16/§8)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<tipo>/<int:nodo_id>/tipos-creables', methods=['GET'])
@login_required
def get_tipos_creables(expediente_id, tipo, nodo_id):
    """
    GET .../nodo/<tipo>/<nodo_id>/tipos-creables — tipos de hijo creables (ADR-016 §16, §8).

    <tipo> ∈ {expediente, solicitud, fase, tramite}. Fuente única para la despensa
    de tipos del inspector y el submenú 'Crear hijo' del menú contextual. Listado
    puramente didáctico (ADR-037 §D): 'canonicos' (vocabulario) y 'resto' (el resto
    del catálogo, tras un 'ver todos'). No evalúa el motor — el veredicto de permiso
    llega como respuesta al POST real de creación, no en este GET.
    """
    expediente = Expediente.query.get_or_404(expediente_id)

    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        data = tipos_creables_de_nodo(expediente, tipo, nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    return jsonify(data), 200


# =============================================================================
# ENDPOINT 5: Detalle lazy de un nodo para el inspector (ADR-016 §5/§16)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<tipo>/<int:nodo_id>', methods=['GET'])
@login_required
def get_detalle_nodo(expediente_id, tipo, nodo_id):
    """
    GET .../nodo/<tipo>/<nodo_id> — detalle read-only del nodo (ADR-016 §5/§16).

    <tipo> ∈ {expediente, solicitud, fase, tramite, tarea}. El árbol solo lleva
    decoradores; el detalle fino del nodo seleccionado se pide aquí bajo demanda.
    Payload: campos adaptativos por nivel + documentos clicables + plazo (si
    ESPERAR_PLAZO) + referencia de ancestros. La cabecera y los agregados los toma
    el front del árbol ya cargado.
    """
    expediente = Expediente.query.get_or_404(expediente_id)

    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        data = detalle_de_nodo(expediente, tipo, nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    return jsonify(data), 200


# =============================================================================
# Helper privado de resolución de nodo
# =============================================================================

class FaseSelladaError(Exception):
    """Nodo bajo una fase cerrada, resuelto en un verbo de escritura (#720,
    ADR-036 §6, capa 1 — resolver de nodo).

    Red temprana, redundante a propósito con `check_invariante('MUTAR', ...)`
    del servicio de dominio (capa 2): corta antes de invocar el servicio, con
    el mismo mensaje. No se captura ruta a ruta — el `errorhandler` del
    blueprint más abajo la traduce a 422 para cualquier vista que la deje
    propagar, así que una ruta nueva que use `_resolver_nodo` queda cubierta
    sin tener que acordarse de nada.
    """
    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(motivo)


_VERBOS_MUTACION = {'POST', 'PUT', 'PATCH', 'DELETE'}


def _verificar_no_sellado(sujeto: str, entidad_id: int, permitir_fase_cerrada: bool) -> None:
    """Lanza FaseSelladaError si `sujeto`/`entidad_id` cuelga de una fase
    cerrada y la request actual es de escritura. No hace nada en GET, ni
    cuando `permitir_fase_cerrada=True` (la usa el propio endpoint de
    reapertura, que necesita resolver una fase cerrada para reabrirla)."""
    if permitir_fase_cerrada or request.method not in _VERBOS_MUTACION:
        return
    res = check_invariante('MUTAR', sujeto, entidad_id)
    if res is not None:
        raise FaseSelladaError(res.motivo or res.norma_compilada)


def _resolver_nodo(expediente, tipo: str, nodo_id: int, *, permitir_fase_cerrada: bool = False):
    """(tipo, nodo_id) → objeto del modelo validando pertenencia. ValueError si no.

    `permitir_fase_cerrada`: ver `_verificar_no_sellado` — excepción explícita
    para el endpoint de reapertura de fase.
    """
    if tipo == 'expediente':
        if nodo_id != expediente.id:
            raise ValueError(
                f'Nodo expediente {nodo_id} no coincide con el expediente {expediente.id}')
        return expediente
    if tipo == 'solicitud':
        obj = Solicitud.query.get(nodo_id)
        if obj is None or obj.expediente_id != expediente.id:
            raise ValueError(f'Solicitud {nodo_id} no encontrada en expediente {expediente.id}')
        return obj
    if tipo == 'fase':
        obj = Fase.query.get(nodo_id)
        if obj is None or obj.solicitud.expediente_id != expediente.id:
            raise ValueError(f'Fase {nodo_id} no encontrada en expediente {expediente.id}')
        _verificar_no_sellado('FASE', obj.id, permitir_fase_cerrada)
        return obj
    if tipo == 'tramite':
        obj = Tramite.query.get(nodo_id)
        if obj is None or obj.fase.solicitud.expediente_id != expediente.id:
            raise ValueError(f'Trámite {nodo_id} no encontrado en expediente {expediente.id}')
        _verificar_no_sellado('TRAMITE', obj.id, permitir_fase_cerrada)
        return obj
    if tipo == 'tarea':
        obj = Tarea.query.get(nodo_id)
        if obj is None or obj.tramite.fase.solicitud.expediente_id != expediente.id:
            raise ValueError(f'Tarea {nodo_id} no encontrada en expediente {expediente.id}')
        _verificar_no_sellado('TAREA', obj.id, permitir_fase_cerrada)
        return obj
    if tipo == 'organismo':
        obj = OrganismoExpediente.query.get(nodo_id)
        if obj is None or obj.expediente_id != expediente.id:
            raise ValueError(f'Organismo {nodo_id} no encontrado en expediente {expediente.id}')
        _verificar_no_sellado('ORGANISMO', obj.id, permitir_fase_cerrada)
        return obj
    raise ValueError(f'Tipo de nodo desconocido: {tipo!r}')


@api_bp.errorhandler(FaseSelladaError)
def _manejar_fase_sellada(e: FaseSelladaError):
    """#720 — traduce el corte temprano de `_resolver_nodo` al mismo shape que
    un bloqueo de invariante. `puede_escapar=False`: no bypasseable, la única
    vía es reabrir la fase antes (`POST .../nodo/fase/<id>/reabrir`)."""
    return jsonify({'error': 'Fase cerrada', 'motivo': e.motivo, 'puede_escapar': False}), 422


def _bloqueo_422(res):
    """Respuesta uniforme árbol para bloqueo del motor o de un invariante ESFTT.

    El mensaje legible del bloqueo puede venir de DOS fuentes (ver EvaluacionResult):
      · motor de reglas    → `motivo` (descripción editorial de la regla)
      · invariantes ESFTT  → `norma_compilada` (su `_bloquear` deja `motivo=''`)
    Por eso se surfacea `motivo or norma_compilada`. Omitir el fallback dejaba
    los bloqueos de invariante con
    `motivo` vacío y el front solo mostraba el genérico "Bloqueado por el motor".
    """
    b = res.bloqueo
    return jsonify({
        'error': 'Bloqueado por el motor',
        'motivo': b.motivo or b.norma_compilada,
        'url_norma': b.url_norma,
        'puede_escapar': b.puede_escapar,
    }), 422


# =============================================================================
# ENDPOINT 6: Crear hijo bajo un nodo (ADR-016 S3b)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<padre_tipo>/<int:padre_id>/hijos',
              methods=['POST'])
@login_required
def crear_hijo_nodo(expediente_id, padre_tipo, padre_id):
    """
    POST .../nodo/<padre_tipo>/<padre_id>/hijos — crear hijo bajo un nodo (ADR-016 §S3b).

    Body JSON: {tipo_id} o {tipo_ids:[...]} cuando padre_tipo=='expediente'.
    Bypass del motor (#324/#616): {..., bypass:true, justificacion:'...'} salta la
    evaluación y registra la creación en bitácora con detalle {escape:true, justificacion}.
    bypass=true sin justificacion → 400.
    Respuesta éxito: {ok:true, ids:[...]} 201.
    Bloqueo motor: {error, motivo, url_norma, puede_escapar} 422.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    # Hoja vs estructura (ADR-017 §6): bajo trámite se crean tareas (gestionar_tareas,
    # incluye ADMINISTRATIVO); el resto crea estructura (gestionar_estructura_expediente).
    accion = 'gestionar_tarea' if padre_tipo == 'tramite' else 'gestionar_estructura'
    if verificar_acceso_expediente(expediente, accion):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        padre = _resolver_nodo(expediente, padre_tipo, padre_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}

    justificacion, err = leer_bypass(data)
    if err:
        return err

    if padre_tipo == 'expediente':
        tipo_ids = data.get('tipo_ids') or (
            [data['tipo_id']] if 'tipo_id' in data else None)
        if not tipo_ids:
            return jsonify({'error': 'Se requiere tipo_id o tipo_ids'}), 422
        tipos = []
        for tid in tipo_ids:
            t = TipoSolicitud.query.get(tid)
            if not t:
                return jsonify({'error': f'TipoSolicitud {tid} no encontrado'}), 404
            tipos.append(t)
        res = svc.crear_solicitud(expediente, tipos, expediente.titular_id,
                                   justificacion=justificacion)

    elif padre_tipo == 'solicitud':
        tipo_id = data.get('tipo_id')
        if not tipo_id:
            return jsonify({'error': 'Se requiere tipo_id'}), 422
        tipo = TipoFase.query.get(tipo_id)
        if not tipo:
            return jsonify({'error': f'TipoFase {tipo_id} no encontrado'}), 404
        res = svc.crear_fase(padre, tipo, justificacion=justificacion)

    elif padre_tipo == 'fase':
        tipo_id = data.get('tipo_id')
        if not tipo_id:
            return jsonify({'error': 'Se requiere tipo_id'}), 422
        tipo = TipoTramite.query.get(tipo_id)
        if not tipo:
            return jsonify({'error': f'TipoTramite {tipo_id} no encontrado'}), 404
        res = svc.crear_tramite(padre, tipo, justificacion=justificacion)

    elif padre_tipo == 'tramite':
        tipo_id = data.get('tipo_id')
        if not tipo_id:
            return jsonify({'error': 'Se requiere tipo_id'}), 422
        tipo = TipoTarea.query.get(tipo_id)
        if not tipo:
            return jsonify({'error': f'TipoTarea {tipo_id} no encontrado'}), 404
        res = svc.crear_tarea(padre, tipo, justificacion=justificacion)

    else:
        return jsonify({'error': f'Tipo de nodo no admite hijos: {padre_tipo!r}'}), 422

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422

    payload = {'ok': True, 'ids': res.ids}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 201


# =============================================================================
# ENDPOINT 7: Editar un nodo (ADR-016 S3b)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<tipo>/<int:nodo_id>',
              methods=['PATCH'])
@login_required
def editar_nodo(expediente_id, tipo, nodo_id):
    """
    PATCH .../nodo/<tipo>/<nodo_id> — editar campos de un nodo (ADR-016 §S3b).

    Body JSON varía por nivel:
      solicitud:  {observaciones}
      fase:       {resultado_fase_id, documento_resultado_id, observaciones}
      tramite:    {observaciones}
      tarea:      {documentos_consumidos_ids, documento_producido_id, notas}
      organismo:  {via, resultado, direccion_notificacion_id, documento_id} (ADR-042 §C)
    Respuesta éxito: {ok:true} 200. Bloqueo motor: {error, motivo, url_norma} 422.

    Contrato del cuerpo (#832): edición PARCIAL — una clave ausente conserva el
    valor que ya tiene el nodo; enviarla con `null` (o `[]`) sí lo vacía.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    # Hoja (tarea → gestionar_tareas, incluye ADMINISTRATIVO) vs estructura
    # (solicitud/fase/trámite → gestionar_estructura_expediente). ADR-017 §6.
    accion = 'gestionar_tarea' if tipo == 'tarea' else 'gestionar_estructura'
    if verificar_acceso_expediente(expediente, accion):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        nodo = _resolver_nodo(expediente, tipo, nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}

    # Clave AUSENTE ≠ clave con null (#832). El contrato de `mutaciones_arbol.editar_*`
    # es "esto es el estado completo deseado" —`editar_tarea` diffea los vínculos y
    # libera lo que sobre—, así que un cuerpo parcial borraba lo que no nombraba:
    # las observaciones de varias solicitudes, y en #825 los CONSUMIDO que disparan
    # el plazo (el script tuvo que releerlos y reponerlos a mano para no perderlos).
    # `leer_json` rellena con el valor actual del nodo lo que el cliente no envía,
    # convirtiendo la petición parcial en su equivalente completa sin tocar el
    # servicio. Enviar la clave con null sigue significando vaciar.
    if tipo == 'solicitud':
        res = svc.editar_solicitud(
            nodo, observaciones=leer_json(data, 'observaciones', nodo.observaciones))
    elif tipo == 'fase':
        justificacion, err = leer_bypass(data)
        if err:
            return err
        res = svc.editar_fase(
            nodo,
            resultado_fase_id=leer_json(data, 'resultado_fase_id', nodo.resultado_fase_id),
            documento_resultado_id=leer_json(data, 'documento_resultado_id',
                                             nodo.documento_resultado_id),
            observaciones=leer_json(data, 'observaciones', nodo.observaciones),
            justificacion=justificacion,
        )
    elif tipo == 'tramite':
        res = svc.editar_tramite(
            nodo, observaciones=leer_json(data, 'observaciones', nodo.observaciones))
    elif tipo == 'tarea':
        producido = nodo.documento_producido
        res = svc.editar_tarea(
            nodo,
            documentos_consumidos_ids=leer_json(
                data, 'documentos_consumidos_ids',
                [d.id for d in nodo.documentos_consumidos]) or [],
            documento_producido_id=leer_json(data, 'documento_producido_id',
                                             producido.id if producido else None),
            notas=leer_json(data, 'notas', nodo.notas),
        )
    elif tipo == 'organismo':
        res = svc.editar_organismo(
            nodo,
            via=leer_json(data, 'via', nodo.via),
            resultado=leer_json(data, 'resultado', nodo.resultado) or None,
            direccion_notificacion_id=leer_json(data, 'direccion_notificacion_id',
                                                nodo.direccion_notificacion_id),
            documento_id=leer_json(data, 'documento_id', nodo.documento_id),
        )
    else:
        return jsonify({'error': f'Tipo de nodo no editable: {tipo!r}'}), 422

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    payload = {'ok': True}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 200


# =============================================================================
# ENDPOINT 7bis: Vincular un huérfano a una tarea — vía rápida del radar (#630)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/vincular_huerfano',
              methods=['POST'])
@login_required
def vincular_huerfano(expediente_id, tarea_id):
    """
    POST .../nodo/tarea/<tarea_id>/vincular_huerfano — vía rápida del radar de
    huérfanos (#630, ADR-038 §5), alternativa a "Ir a la tarea" para candidatas
    de alta confianza. Body JSON: {documento_id, rol}, rol ∈ {CONSUMIDO, PRODUCIDO}.

    Llama a svc.editar_tarea — el mismo mutador que usa el guardado del árbol,
    sin lógica de vinculación duplicada. Repite server-side las reglas de
    exclusión de la lista de candidatas (app/services/huerfanos.py, ADR-038
    §4): defensa en profundidad ante una lista desactualizada en cliente.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_nodo(expediente, 'tarea', tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    rol = data.get('rol')
    documento_id = data.get('documento_id')
    if rol not in ('CONSUMIDO', 'PRODUCIDO') or not documento_id:
        return jsonify({'error': 'rol (CONSUMIDO|PRODUCIDO) y documento_id son obligatorios'}), 400

    doc = Documento.query.get(documento_id)
    if not doc or doc.expediente_id != expediente_id:
        return jsonify({'error': 'Documento no válido para este expediente'}), 422
    if (doc.url or '').startswith('bddat://') or doc.vinculos_tarea:
        return jsonify({'error': 'El documento ya no es huérfano'}), 409

    if rol == 'PRODUCIDO' and tarea.documento_producido is not None:
        return jsonify({'error': 'La tarea ya tiene un documento producido — sustituirlo requiere revertirlo primero desde el árbol'}), 422
    if rol == 'CONSUMIDO' and tarea.ejecutada:
        return jsonify({'error': 'La tarea ya está ejecutada — no se añaden consumidos sin revertir primero'}), 422

    consumidos_ids = [v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']
    producido_id = tarea.documento_producido.id if tarea.documento_producido else None
    if rol == 'CONSUMIDO':
        consumidos_ids.append(documento_id)
    else:
        producido_id = documento_id

    res = svc.editar_tarea(
        tarea,
        documentos_consumidos_ids=consumidos_ids,
        documento_producido_id=producido_id,
        notas=tarea.notas,
    )
    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    payload = {'ok': True}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 200


# =============================================================================
# ENDPOINT 7ter: Sugerencia de tipo de documento y asunto para subida inline
# desde la Despensa (#367)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/sugerencia_documento',
              methods=['GET'])
@login_required
def sugerencia_documento_tarea(expediente_id, tarea_id):
    """
    GET .../nodo/tarea/<tarea_id>/sugerencia_documento — sugerencia de
    tipo_doc_id + asunto para subir un documento nuevo desde la Despensa de
    esta tarea (#367). Solo lectura: no crea ni vincula nada.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    try:
        tarea = _resolver_nodo(expediente, 'tarea', tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    from app.services.sugerencia_documento import sugerencia_subida
    return jsonify(sugerencia_subida(tarea)), 200


# =============================================================================
# ENDPOINT 8: Borrar un nodo (ADR-016 S3b)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<tipo>/<int:nodo_id>',
              methods=['DELETE'])
@login_required
def borrar_nodo(expediente_id, tipo, nodo_id):
    """
    DELETE .../nodo/<tipo>/<nodo_id> — borrar un nodo (ADR-016 §S3b).

    Sin body. Respuesta éxito: {ok:true} 200. Bloqueo motor: {error, motivo, url_norma} 422.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    # Mismo criterio hoja/estructura que editar_nodo (ADR-017 §6).
    accion = 'gestionar_tarea' if tipo == 'tarea' else 'gestionar_estructura'
    if verificar_acceso_expediente(expediente, accion):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        nodo = _resolver_nodo(expediente, tipo, nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    if tipo == 'solicitud':
        res = svc.borrar_solicitud(nodo)
    elif tipo == 'fase':
        res = svc.borrar_fase(nodo)
    elif tipo == 'tramite':
        res = svc.borrar_tramite(nodo)
    elif tipo == 'tarea':
        res = svc.borrar_tarea(nodo)
    elif tipo == 'organismo':
        res = svc.borrar_organismo(nodo)
    else:
        return jsonify({'error': f'Tipo de nodo no borrable: {tipo!r}'}), 422

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    return jsonify({'ok': True}), 200


# =============================================================================
# ENDPOINT 8bis: Reabrir una fase cerrada (#720, ADR-036)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/fase/<int:nodo_id>/reabrir',
              methods=['POST'])
@login_required
def reabrir_fase_nodo(expediente_id, nodo_id):
    """
    POST .../nodo/fase/<fase_id>/reabrir — reabre una fase cerrada (#720, ADR-036).

    Único camino para tocar el interior de una fase FINALIZADA: retira su
    resultado/documento de cierre y queda en bitácora. Body JSON:
    {justificacion} — obligatoria siempre, no hay reapertura silenciosa.

    Bloqueo (422, `puede_escapar: false`): la solicitud ya está resuelta y
    notificada — puerta cerrada, ADR-036 §4.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    # Mismo permiso que cerrar la fase (editar_nodo) y crear/borrar estructura.
    if verificar_acceso_expediente(expediente, 'gestionar_estructura'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        fase = _resolver_nodo(expediente, 'fase', nodo_id, permitir_fase_cerrada=True)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    justificacion = (data.get('justificacion') or '').strip()

    res = svc.reabrir_fase(fase, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    return jsonify({'ok': True}), 200


# =============================================================================
# ENDPOINT 8quater: Certificar el fin de instrucción (#827, ADR-043 §E)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/solicitud/<int:nodo_id>'
              '/certificado-fin-instruccion', methods=['POST'])
@login_required
def emitir_cert_fin_instruccion_nodo(expediente_id, nodo_id):
    """
    POST .../nodo/solicitud/<solicitud_id>/certificado-fin-instruccion — revisa la
    instrucción y, si no queda nada pendiente, consolida el certificado (#827,
    ADR-043 §E).

    Gesto explícito del técnico, repetible desde el primer día de la solicitud. Sin
    body: no hay nada que elegir. **Falta algo no es un error** — se responde 200
    con el informe y `consolidado: false`, y no se ha creado nada; el técnico ve qué
    falta y puede volver a preguntar mañana.

    Respuesta 200: el informe (`informe_instruccion.Informe.a_dict` + `consolidado`,
    `documento_id`, `certificado_id`).

    422 se reserva para errores de verdad: ya estaba emitido, el catálogo no tiene
    el tipo documental, o el PDF no se pudo generar. El 422 de bloqueo
    (`puede_escapar: false`) solo aparecería si la puerta cerrada del invariante
    discrepara del informe, que sería una divergencia a investigar.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    # Mismo permiso que cerrar una fase o reabrirla: es un acto sobre la estructura
    # de la tramitación, no sobre el contenido de una tarea.
    if verificar_acceso_expediente(expediente, 'gestionar_estructura'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        solicitud = _resolver_nodo(expediente, 'solicitud', nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    from app.services.cert_fin_instruccion import consolidar

    res = consolidar(solicitud)
    if res.bloqueo:
        return _bloqueo_422(res)
    if res.error:
        payload = res.a_dict()
        payload['error'] = res.error
        return jsonify(payload), 422
    return jsonify(res.a_dict()), 200


# =============================================================================
# ENDPOINT 8ter: Alta de organismo consultado en una fase CONSULTAS (ADR-042 §C)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/fase/<int:nodo_id>/organismos',
              methods=['POST'])
@login_required
def crear_organismo_nodo(expediente_id, nodo_id):
    """
    POST .../nodo/fase/<fase_id>/organismos — alta de un organismo consultado
    (ADR-042 §C). No es "crear hijo" por despensa: `OrganismoExpediente` no es
    un tipo de catálogo (ver docstring de `mutaciones_arbol.crear_organismo`),
    así que tiene endpoint propio en vez de reutilizar ENDPOINT 6.

    Body JSON: {organismo_id, via, documento_id?}. `organismo_id` es el id de
    la Entidad consultada (rol_consultado=True). `documento_id` obligatorio si
    via='declaracion_responsable', ausente si via='consulta'.
    Bypass (#324/#616): {..., bypass:true, justificacion:'...'}.
    Respuesta éxito: {ok:true, ids:[...]} 201. Bloqueo motor: {error, motivo,
    url_norma, puede_escapar} 422.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_estructura'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        fase = _resolver_nodo(expediente, 'fase', nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}

    justificacion, err = leer_bypass(data)
    if err:
        return err

    organismo_id = data.get('organismo_id')
    if not organismo_id:
        return jsonify({'error': 'Se requiere organismo_id'}), 422
    entidad = Entidad.query.get(organismo_id)
    if not entidad:
        return jsonify({'error': f'Entidad {organismo_id} no encontrada'}), 404

    via = data.get('via', '')
    res = svc.crear_organismo(
        fase, entidad, via=via, documento_id=data.get('documento_id'),
        justificacion=justificacion,
    )

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422

    payload = {'ok': True, 'ids': res.ids}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 201


# =============================================================================
# ENDPOINT 8quater: Enviar consultas en bloque (ADR-042 §C, #396 bloque 5)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/fase/<int:nodo_id>/organismos/enviar-consultas',
              methods=['POST'])
@login_required
def enviar_consultas_nodo(expediente_id, nodo_id):
    """
    POST .../nodo/fase/<fase_id>/organismos/enviar-consultas — crea una
    CONSULTA_SEPARATA por cada organismo vía consulta que aún no tenga una
    (ADR-042 §C). Acción de fase, incremental e idempotente por construcción:
    repetir la llamada no duplica separatas ya creadas, solo recoge organismos
    dados de alta después (segunda ronda incluida).

    Sin body obligatorio. Bypass (#324/#616): {bypass:true, justificacion:'...'}.
    Respuesta éxito: {ok:true, ids:[...]} 201 (`ids` puede venir vacío si no
    había ningún organismo pendiente). Bloqueo motor: {error, motivo, url_norma,
    puede_escapar} 422.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_estructura'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        fase = _resolver_nodo(expediente, 'fase', nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    res = svc_consultas.enviar_consultas(fase, data)

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422

    payload = {'ok': True, 'ids': res.ids}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 201


# =============================================================================
# ENDPOINT 8quinquies: Crear traslado a organismo/titular (ADR-042 §D, la mitad
# de titular es obra de #396 bloque 5 — el traslado a organismo vía despensa
# del nodo queda para #652, ver ADR-042 §D)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/organismo/<int:nodo_id>/traslados',
              methods=['POST'])
@login_required
def crear_traslado_nodo(expediente_id, nodo_id):
    """
    POST .../nodo/organismo/<oe_id>/traslados — crea un trámite
    CONSULTA_TRASLADO_ORGANISMO o CONSULTA_TRASLADO_TITULAR vinculado a este
    organismo.

    Body JSON: {tipo: 'ORGANISMO'|'TITULAR'}. Bypass (#324/#616).
    Respuesta éxito: {ok:true, ids:[...]} 201. Bloqueo motor: 422.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_estructura'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    oe = OrganismoExpediente.query.get(nodo_id)
    if oe is None or oe.expediente_id != expediente.id:
        return jsonify({'error': f'Organismo {nodo_id} no encontrado en el expediente'}), 404

    data = request.get_json(silent=True) or {}
    data = dict(data)
    data['organismo_expediente_id'] = oe.id
    res = svc_consultas.crear_traslado(oe.fase, data)

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422

    payload = {'ok': True, 'ids': res.ids}
    if res.advertencia:
        payload['advertencia'] = res.advertencia
    return jsonify(payload), 201


# =============================================================================
# ENDPOINT 9: Esquema editable de un nodo (ADR-016 S3b)
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/nodo/<tipo>/<int:nodo_id>/editable',
              methods=['GET'])
@login_required
def get_esquema_editable(expediente_id, tipo, nodo_id):
    """
    GET .../nodo/<tipo>/<nodo_id>/editable — esquema de campos editables (ADR-016 §S3b).

    Devuelve el contrato genérico que el inspector usa para pintar el formulario editor:
    {nodo:{tipo,id}, campos:[{campo, etiqueta, control, valor, opciones?}]}.
    El expediente devuelve campos:[] (no editable en v1).
    """
    expediente = Expediente.query.get_or_404(expediente_id)

    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        data = esquema_de_nodo(expediente, tipo, nodo_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    return jsonify(data), 200


# =============================================================================
# ENDPOINT 10: Pool de documentos del expediente (despensa de tarea, ADR-016 §S3b-3)
# =============================================================================

def _nombre_documento(doc) -> str:
    """Nombre de presentación de un Documento: tipo (interno bddat://) o filename (real)."""
    url = doc.url or ''
    if url.startswith('bddat://'):
        # Sin fichero real — el "segmento final" sería solo el id numérico.
        return doc.tipo_doc.nombre if doc.tipo_doc else f'Documento {doc.id}'
    filename = url.replace('\\', '/').rsplit('/', 1)[-1]
    filename = filename.split('?')[0].split('#')[0]
    return filename or f'Documento {doc.id}'


@api_bp.route('/expedientes/<int:expediente_id>/pool', methods=['GET'])
@login_required
def pool_documentos(expediente_id):
    """
    GET /api/expedientes/<id>/pool — pool estructurado para la despensa de tareas (S3b-3).

    Devuelve: {documentos: [{id, nombre, tipo_doc, tipo_doc_codigo, fecha, enlace,
    externo, puede_abrir_carpeta}]}, orden id DESC. enlace/puede_abrir_carpeta
    permiten previsualizar cualquier documento del pool antes de decidir
    enlazarlo, no solo los ya consumidos/producidos de la tarea (#609).
    `tipo_doc_codigo` (#712): permite filtrar client-side (p.ej. los 4
    JUSTIFICANTE_* en el desplegable de NotificarEditor) sin endpoint aparte,
    reutilizando el pool que la Despensa ya carga una vez por sesión de la isla.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    docs = Documento.query.filter_by(
        expediente_id=expediente_id
    ).order_by(Documento.id.desc()).all()

    result = [{
        'id': doc.id,
        'nombre': _nombre_documento(doc),
        'tipo_doc': doc.tipo_doc.nombre if doc.tipo_doc else None,
        'tipo_doc_codigo': doc.tipo_doc.codigo if doc.tipo_doc else None,
        'fecha': doc.fecha_administrativa.strftime('%d/%m/%Y') if doc.fecha_administrativa else None,
        **info_apertura_documento(expediente_id, doc),
    } for doc in docs]
    return jsonify({'documentos': result}), 200


# =============================================================================
# ENDPOINT 11: Contenedor de la tarea ANALIZAR (#442)
# =============================================================================

def _resolver_tarea_analizar(expediente, tarea_id):
    """(expediente, tarea_id) → Tarea de tipo ANALIZAR. ValueError si no."""
    tarea = _resolver_nodo(expediente, 'tarea', tarea_id)
    codigo = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None
    if codigo != 'ANALIZAR':
        raise ValueError(f'La tarea {tarea_id} no es de tipo ANALIZAR (es {codigo!r})')
    return tarea


def _candado_diagnostico_producido(tarea):
    """422 si la tarea ya tiene diagnóstico producido, o None si puede mutar.

    ADR-033 §5: los tres puntos de persistencia de bloque (Vincular/Desvincular
    documental, Guardar ítem técnico, Guardar cambios del shuttle) deben pasar
    por el flujo controlado de reversión — nunca mutar directamente con el
    diagnóstico ya producido. El cliente revierte primero (DELETE .../analizar,
    con su propia confirmación destructiva o puerta cerrada) y solo entonces
    repite la mutación.

    Motivo veraz (#723, caso 3): consulta la misma vigencia que
    `revertir_diagnostico` antes de redactar el mensaje — si la reversión
    también está bloqueada (consumido, superado o ya notificado), lo dice, en
    vez de prometer siempre "revierte antes" cuando esa salida no existe. El
    candado en sí sigue sin ser forzable (`puede_escapar` propio, fijo en
    False): la vía de escape, si la hay, es revertir con justificación, no
    saltarse este candado.
    """
    if tarea.documento_producido is None:
        return None
    bloqueo = motivo_bloqueo_reversion(tarea)
    motivo = bloqueo.motivo if bloqueo else (
        'El diagnóstico de esta tarea ya se ha producido. Revierte el '
        'diagnóstico antes de modificar este bloque.'
    )
    return jsonify({
        'error': 'Diagnóstico ya producido',
        'motivo': motivo,
        'puede_escapar': False,
    }), 422


def _codigo_tramite(tarea) -> str | None:
    return (
        tarea.tramite.tipo_tramite.codigo
        if tarea.tramite and tarea.tramite.tipo_tramite else None
    )


def _tiene_secciones_extendidas(tarea) -> bool:
    """Trámite de la tarea ∈ _TRAMITES_CON_SECCIONES_ANALISIS (#442/#677)."""
    return _codigo_tramite(tarea) in _TRAMITES_CON_SECCIONES_ANALISIS


def _es_ronda_subsanacion(tarea) -> bool:
    """
    True si la tarea es de REQUERIMIENTO_SUBSANACIÓN (#695): en ese trámite se
    coteja lo heredado de una vuelta ya producida (ADR-033 §7) — el shuttle de
    requerimientos ofrece "Marcar como resuelto" y bloquea editar/quitar.
    En ANALISIS_DOCUMENTAL se está redactando el defecto por primera vez, así
    que ahí solo caben editar/quitar, nunca "resuelto".
    """
    return _codigo_tramite(tarea) == 'REQUERIMIENTO_SUBSANACION'


def _resultado_derivado(consolidado: dict) -> str:
    """Resultado derivado del borrador agregado (ADR-033 §3): vacío → favorable,
    con defectos → desfavorable. No es una elección libre en ANALIZAR extendido."""
    return 'favorable' if not consolidado['items'] else 'desfavorable'


def _checklist_documental_json(tarea) -> list:
    """Checklist documental completo —cubiertos y pendientes— para la sección inline (#495)."""
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_requisitos(solicitud, variables)

    items = []
    for it in resultado['items']:
        req = it['requisito']
        doc = it['documento']
        items.append({
            'requisito_id': req.id,
            'tipo_documento': req.tipo_documento.nombre if req.tipo_documento else None,
            'descripcion_legal': req.descripcion_legal,
            'norma': req.norma.titulo if req.norma else None,
            'articulo': req.articulo,
            'cubierto': it['cubierto'],
            'documento': {'id': doc.id, 'nombre': _nombre_documento(doc)} if doc else None,
        })
    return items


def _checklist_tecnico_json(tarea) -> list:
    """Checklist técnico completo —favorable/desfavorable/no revisado— (#581)."""
    solicitud = tarea.tramite.fase.solicitud
    _, variables = build(solicitud.expediente, objeto=tarea)
    resultado = evaluar_items_tecnicos(solicitud, variables)

    items = []
    for it in resultado['items']:
        item = it['item']
        cobertura = it['cobertura']
        items.append({
            'item_tecnico_id': item.id,
            'descripcion': item.descripcion,
            'norma': item.norma.titulo if item.norma else None,
            'articulo': item.articulo,
            'texto': cobertura.texto if cobertura else '',
            'cubierto': cobertura.cubierto if cobertura else False,
        })
    return items


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/analizar',
              methods=['GET'])
@login_required
def get_analizar(expediente_id, tarea_id):
    """
    GET .../nodo/tarea/<tarea_id>/analizar — payload del contenedor de #442/#677.

    {resultado, resultado_previsto, documento_producido: {...}|null,
     secciones_extendidas: bool, es_ronda_subsanacion: bool, defectos_consolidado: [...],
     defectos_resueltos: [...], completo: bool, checklist_documental: [...],
     checklist_tecnico: [...], notas}

    `resultado_previsto` (ADR-033 §3): sentido que tendría el diagnóstico si se
    produjera ahora mismo, derivado del borrador agregado — informativo en
    ANALIZAR extendido (sin radio editable); no aplica a ANALIZAR simple, que
    sigue con resultado de elección libre.

    `defectos_resueltos` (ADR-033 §7): requerimientos libres ya marcados
    resueltos por el técnico — no cuentan como defecto activo, se exponen
    aparte solo para que el borrador muestre progreso entre vueltas de
    subsanación.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    secciones_extendidas = _tiene_secciones_extendidas(tarea)
    consolidado = consolidar_defectos(tarea)

    documento_producido = None
    resultado = None
    doc = tarea.documento_producido
    if doc is not None and doc.diagnostico is not None:
        diag = doc.diagnostico
        resultado = diag.resultado
        documento_producido = {
            'id': doc.id,
            'diagnostico_id': diag.id,
            'resultado': diag.resultado,
            'defectos': diag.defectos or [],
            'nombre': doc.tipo_doc.nombre if doc.tipo_doc else 'Diagnóstico',
        }

    return jsonify({
        'resultado': resultado,
        'resultado_previsto': _resultado_derivado(consolidado),
        'documento_producido': documento_producido,
        'secciones_extendidas': secciones_extendidas,
        'es_ronda_subsanacion': _es_ronda_subsanacion(tarea),
        'defectos_consolidado': consolidado['items'],
        'defectos_resueltos': consolidado['items_resueltos'],
        'completo': consolidado['completo'],
        'checklist_documental': _checklist_documental_json(tarea) if secciones_extendidas else [],
        'checklist_tecnico': _checklist_tecnico_json(tarea) if secciones_extendidas else [],
        'notas': tarea.notas,
    }), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/analizar',
              methods=['POST'])
@login_required
def post_analizar(expediente_id, tarea_id):
    """
    POST .../nodo/tarea/<tarea_id>/analizar — produce el documento de diagnóstico.

    Body JSON: {resultado?, justificacion?}. En ANALIZAR extendido (ADR-033 §3)
    `resultado` no es una elección libre: se deriva del borrador agregado
    (favorable si vacío, desfavorable si hay defectos) e ignora lo que mande el
    cliente — "condicionado" deja de ser representable por construcción. En
    ANALIZAR simple se mantiene la elección libre de hoy (favorable|condicionado|
    desfavorable).

    Si el consolidado no está completo y no se aporta `justificacion`, se
    bloquea (422, mismo shape que un bloqueo de motor) — con `justificacion` se
    salta el gate y se registra en bitácora (ver crear_diagnostico). Bloqueo
    también si la tarea ya tiene documento producido.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    justificacion = (data.get('justificacion') or '').strip() or None

    consolidado = consolidar_defectos(tarea)

    if _tiene_secciones_extendidas(tarea):
        resultado = _resultado_derivado(consolidado)
    else:
        resultado = data.get('resultado')
        if resultado not in ('favorable', 'condicionado', 'desfavorable'):
            return jsonify({'error': 'resultado debe ser favorable, condicionado o desfavorable'}), 422

    if not consolidado['completo'] and not justificacion:
        return jsonify({
            'error': 'Quedan ítems sin revisar',
            'motivo': 'El checklist no está completo. Aporta una justificación para producir '
                      'el documento igualmente, o termina de revisarlo primero.',
            'defectos_consolidado': consolidado['items'],
        }), 422

    try:
        doc = crear_diagnostico(tarea, resultado, consolidado['items'], justificacion=justificacion)
    except FaseCerradaError as e:
        return jsonify({'error': 'Fase cerrada', 'motivo': str(e), 'puede_escapar': False}), 422
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    return jsonify({
        'ok': True,
        'documento': {
            'id': doc.id,
            'nombre': doc.tipo_doc.nombre if doc.tipo_doc else 'Diagnóstico',
            'tipo_doc': doc.tipo_doc.nombre if doc.tipo_doc else None,
            'fecha': None,
        },
    }), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/analizar',
              methods=['DELETE'])
@login_required
def delete_analizar(expediente_id, tarea_id):
    """
    DELETE .../nodo/tarea/<tarea_id>/analizar — revierte el diagnóstico producido
    (ADR-033 §5, enmienda ADR-005). Vuelve la tarea a "Borrador defectos".

    Body opcional: {justificacion} — fuerza los bloqueos que lo admiten (#714).

    Bloqueo (422): tarea sin documento producido, documento consumido por otra
    tarea, o diagnóstico ya superado dentro de la cadena de subsanación (#714).
    Mismo shape que un bloqueo de motor; `puede_escapar` distingue la puerta
    cerrada (consumido, o requerimiento ya notificado al titular: el acto salió
    fuera y no se deshace) del bloqueo forzable con justificación (superado por
    una vuelta posterior, con todo aún en casa).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    justificacion = (data.get('justificacion') or '').strip() or None

    try:
        revertir_diagnostico(tarea, justificacion=justificacion)
    except FaseCerradaError as e:
        return jsonify({'error': 'Fase cerrada', 'motivo': str(e), 'puede_escapar': False}), 422
    except DiagnosticoConsumidoError as e:
        return jsonify({
            'error': 'Diagnóstico consumido',
            'motivo': str(e),
            'puede_escapar': False,
        }), 422
    except DiagnosticoSuperadoError as e:
        return jsonify({
            'error': 'Diagnóstico superado',
            'motivo': str(e),
            'puede_escapar': e.puede_escapar,
        }), 422
    except ValueError as e:
        return jsonify({'error': str(e)}), 422

    return jsonify({'ok': True}), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notas', methods=['PATCH'])
@login_required
def patch_notas_tarea(expediente_id, tarea_id):
    """
    PATCH .../nodo/tarea/<tarea_id>/notas — guarda solo `notas` (#677, ADR-033 §7).

    Bloque aparte del contenedor de ANALIZAR con guardado inline propio, fuera
    del ciclo borrador/Guardar general de `editar_tarea`: ese ciclo también
    diffea `documentos_tarea` contra un `documentos_consumidos_ids` que en
    ANALIZAR extendido queda obsoleto durante la sesión (el check documental
    deriva vínculos CONSUMIDO en directo, ver sincronizar_consumido_documental) —
    reutilizarlo aquí podría deshacer esos vínculos recién derivados. Un
    endpoint que solo toca `ta.notas` evita el problema por construcción.

    Body JSON: {notas}. No requiere que la tarea sea de tipo ANALIZAR — es
    el mismo campo genérico de `_esquema_tarea`, válido para cualquier tarea.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    tarea = _resolver_nodo(expediente, 'tarea', tarea_id)

    data = request.get_json(silent=True) or {}
    tarea.notas = (data.get('notas') or '').strip() or None
    db.session.commit()

    return jsonify({'ok': True, 'notas': tarea.notas}), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requisitos-documentales/<int:requisito_id>',
    methods=['POST'])
@login_required
def vincular_requisito_documental(expediente_id, tarea_id, requisito_id):
    """
    POST .../requisitos-documentales/<requisito_id> — vincula un documento del pool
    al requisito documental para la solicitud de la tarea (#495).

    Body JSON: {documento_id}. Upsert por (requisito_id, solicitud_id) — reasigna
    el documento si ya había un vínculo (ver DocumentoRequisito, #192).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    candado = _candado_diagnostico_producido(tarea)
    if candado:
        return candado

    requisito = RequisitoDocumental.query.get_or_404(requisito_id)

    data = request.get_json(silent=True) or {}
    documento = Documento.query.filter_by(
        id=data.get('documento_id'), expediente_id=expediente_id
    ).first()
    if documento is None:
        return jsonify({'error': 'Documento no encontrado en este expediente'}), 422

    solicitud = tarea.tramite.fase.solicitud
    vinculo = DocumentoRequisito.query.filter_by(
        requisito_id=requisito.id, solicitud_id=solicitud.id
    ).first()
    if vinculo is None:
        vinculo = DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id, documento_id=documento.id
        )
        db.session.add(vinculo)
    else:
        vinculo.documento_id = documento.id
    db.session.commit()

    svc.sincronizar_consumido_documental(tarea)

    return jsonify({'ok': True, 'checklist_documental': _checklist_documental_json(tarea)}), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requisitos-documentales/<int:requisito_id>',
    methods=['DELETE'])
@login_required
def desvincular_requisito_documental(expediente_id, tarea_id, requisito_id):
    """DELETE .../requisitos-documentales/<requisito_id> — quita el vínculo documento↔requisito (#495).

    Body JSON opcional: {justificacion}. Desvincular es la única mutación
    documental que puede crear un defecto nuevo (vincular siempre resuelve, nunca
    lo contrario) — si el requisito ya figuraba en un diagnóstico notificado de una
    vuelta anterior, el técnico se está desdiciendo de algo ya exigido y necesita
    justificarlo (#724, 422 forzable, auditado en bitácora). Sin vínculo previo no
    hay transición hacia el defecto: no aplica.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    candado = _candado_diagnostico_producido(tarea)
    if candado:
        return candado

    solicitud = tarea.tramite.fase.solicitud
    vinculo = DocumentoRequisito.query.filter_by(
        requisito_id=requisito_id, solicitud_id=solicitud.id
    ).first()

    data = request.get_json(silent=True) or {}
    justificacion = (data.get('justificacion') or '').strip() or None

    defecto_exigido = None
    if vinculo is not None:
        defecto_exigido = diagnostico_donde_se_exigio_item(tarea, 'documental', requisito_id)
        if defecto_exigido is not None and not justificacion:
            return jsonify({
                'error': 'Requisito ya exigido en una vuelta anterior notificada',
                'motivo': motivo_check_ya_exigido('documental', defecto_exigido.get('texto', '')),
                'puede_escapar': True,
            }), 422

        db.session.delete(vinculo)
        db.session.commit()

        if defecto_exigido is not None:
            bitacora_svc.registrar(
                current_user.id, 'ALTERAR', 'tareas', tarea.id,
                detalle={
                    'escape': True, 'justificacion': justificacion,
                    'origen': 'documental', 'requisito_id': requisito_id,
                },
            )

    svc.sincronizar_consumido_documental(tarea)

    return jsonify({'ok': True, 'checklist_documental': _checklist_documental_json(tarea)}), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/coberturas-tecnicas/<int:item_tecnico_id>',
    methods=['POST'])
@login_required
def guardar_cobertura_tecnica(expediente_id, tarea_id, item_tecnico_id):
    """
    POST .../coberturas-tecnicas/<item_tecnico_id> — registra el veredicto del
    tramitador sobre un ítem técnico para la solicitud de la tarea (#581).

    Body JSON: {texto, cubierto, justificacion?}. Upsert por (item_tecnico_id,
    solicitud_id). `cubierto` se fuerza a False si `texto` está vacío — evita el
    estado inválido de CoberturaItemTecnico (ver su docstring).

    Si el guardado hace que el ítem pase a "no cumple" (transición hacia el
    defecto: antes no lo era —no revisado o favorable—, ahora sí) y ese ítem ya
    figuraba en un diagnóstico notificado de una vuelta anterior, el técnico se
    está desdiciendo de algo ya exigido y necesita justificarlo (#724, 422
    forzable, auditado en bitácora). Guardar sin cambiar el sentido de "no
    cumple" (o resolverlo) no pasa por aquí.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    candado = _candado_diagnostico_producido(tarea)
    if candado:
        return candado

    ItemTecnico.query.get_or_404(item_tecnico_id)

    data = request.get_json(silent=True) or {}
    texto = (data.get('texto') or '').strip()
    cubierto = bool(data.get('cubierto')) and bool(texto)
    justificacion = (data.get('justificacion') or '').strip() or None

    solicitud = tarea.tramite.fase.solicitud
    cobertura = CoberturaItemTecnico.query.filter_by(
        item_tecnico_id=item_tecnico_id, solicitud_id=solicitud.id
    ).first()

    era_defecto_antes = cobertura is not None and bool((cobertura.texto or '').strip()) and not cobertura.cubierto
    es_defecto_despues = bool(texto) and not cubierto

    defecto_exigido = None
    if es_defecto_despues and not era_defecto_antes:
        defecto_exigido = diagnostico_donde_se_exigio_item(tarea, 'tecnico', item_tecnico_id)
        if defecto_exigido is not None and not justificacion:
            return jsonify({
                'error': 'Ítem técnico ya exigido en una vuelta anterior notificada',
                'motivo': motivo_check_ya_exigido('tecnico', defecto_exigido.get('texto', '')),
                'puede_escapar': True,
            }), 422

    if cobertura is None:
        cobertura = CoberturaItemTecnico(
            item_tecnico_id=item_tecnico_id, solicitud_id=solicitud.id,
            texto=texto, cubierto=cubierto,
        )
        db.session.add(cobertura)
    else:
        cobertura.texto = texto
        cobertura.cubierto = cubierto
    db.session.commit()

    if defecto_exigido is not None:
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'tareas', tarea.id,
            detalle={
                'escape': True, 'justificacion': justificacion,
                'origen': 'tecnico', 'item_tecnico_id': item_tecnico_id,
            },
        )

    return jsonify({'ok': True, 'checklist_tecnico': _checklist_tecnico_json(tarea)}), 200


# Mismos valores que el CHECK ck_catalogo_requerimientos_categoria (#440, ver catalogo_requerimientos/routes.py)
_CATEGORIAS_REQUERIMIENTO_VALIDAS = {'documental', 'tecnica', 'administrativa', 'tasas'}


def _seleccionados_json(solicitud) -> list:
    return [{
        'id': r.id,
        'texto': r.texto,
        'orden': r.orden,
        'desde_catalogo': r.desde_catalogo,
        'catalogo_requerimientos_id': r.catalogo_requerimientos_id,
        'texto_libre': r.texto_libre,
        'resuelto': r.resuelto,
    } for r in sorted(solicitud.requerimientos, key=lambda r: r.orden)]


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos', methods=['GET'])
@login_required
def get_requerimientos(expediente_id, tarea_id):
    """
    GET .../requerimientos — estado inicial del panel shuttle: catálogo activo
    agrupado y selección actual de la solicitud (#440, elevado a `solicitud_id`
    en #679, ADR-033 §7 — continuo entre vueltas de subsanación).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    catalogo = (
        CatalogoRequerimiento.query
        .filter_by(activo=True)
        .order_by(CatalogoRequerimiento.categoria, CatalogoRequerimiento.id)
        .all()
    )

    solicitud = tarea.tramite.fase.solicitud
    return jsonify({
        'catalogo': [{'id': c.id, 'texto': c.texto, 'categoria': c.categoria} for c in catalogo],
        'seleccionados': _seleccionados_json(solicitud),
    }), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos', methods=['POST'])
@login_required
def post_requerimientos(expediente_id, tarea_id):
    """
    POST .../requerimientos — sustituye la lista completa de `requerimientos_tarea`
    de la solicitud en una sola llamada: crear, reordenar, borrar y marcar
    resuelto (#440, elevado a `solicitud_id` en #679, ADR-033 §7).

    Body JSON: {items: [{catalogo_requerimientos_id: int|null, texto_libre: str|null,
    resuelto: bool}, ...], justificacion?}. Orden = posición en la lista (1-based).
    Exactamente uno de catalogo_requerimientos_id/texto_libre debe tener valor
    (ck_requerimientos_tarea_exactamente_uno).

    El frontend no debe permitir quitar de la lista un ítem ya persistido
    (con `id`) de una vuelta anterior — solo marcarlo `resuelto` — para no
    perder el juicio del técnico sin dejar rastro. El backend no lo impone
    (upsert por reemplazo total, igual que hoy): confía en esa restricción de UI.

    Único endpoint que puede mutar varios ítems a la vez (reemplaza la lista
    completa) — si alguno de los que YA estaban resueltos deja de estarlo (o
    desaparece del payload) y ya figuraba en un diagnóstico notificado de una
    vuelta anterior, es una transición hacia el defecto: el técnico se desdice
    de algo ya exigido y cerrado, y necesita justificarlo en lote (#724, 422
    forzable con la lista completa de textos afectados, auditado en bitácora).
    Un ítem que sigue pendiente sin cambiar de sentido no pasa por aquí.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    candado = _candado_diagnostico_producido(tarea)
    if candado:
        return candado

    data = request.get_json(silent=True) or {}
    items = data.get('items')
    if not isinstance(items, list):
        return jsonify({'error': 'items debe ser una lista'}), 422
    justificacion = (data.get('justificacion') or '').strip() or None

    solicitud = tarea.tramite.fase.solicitud

    nuevas = []
    claves_despues = {}
    for i, it in enumerate(items, start=1):
        catalogo_id = it.get('catalogo_requerimientos_id')
        texto_libre = (it.get('texto_libre') or '').strip() or None
        if bool(catalogo_id) == bool(texto_libre):
            return jsonify({
                'error': f'Ítem {i}: exactamente uno de catalogo_requerimientos_id o texto_libre',
            }), 422
        resuelto = bool(it.get('resuelto'))
        nuevas.append(RequerimientoTarea(
            solicitud_id=solicitud.id, catalogo_requerimientos_id=catalogo_id,
            texto_libre=texto_libre, orden=i, resuelto=resuelto,
        ))
        clave = ('cat', catalogo_id) if catalogo_id else ('libre', texto_libre)
        claves_despues[clave] = resuelto

    # #724: la fila se borra y recrea entera (`id` no estable entre guardados),
    # así que el emparejamiento antes/después va por (catalogo_id) o (texto_libre)
    # — no por `id`. Solo mira lo YA resuelto (antes) que deja de estarlo o
    # desaparece: un ítem que sigue pendiente sin cambiar de sentido no es una
    # transición, aunque también estuviera en un diagnóstico notificado.
    textos_ya_exigidos = []
    for previo in solicitud.requerimientos:
        if not previo.resuelto:
            continue
        clave = ('cat', previo.catalogo_requerimientos_id) if previo.catalogo_requerimientos_id \
            else ('libre', previo.texto_libre)
        if claves_despues.get(clave) is True:
            continue  # sigue resuelto, sin cambio de sentido
        defecto = diagnostico_donde_se_exigio_requerimiento(
            tarea, catalogo_requerimientos_id=previo.catalogo_requerimientos_id, texto=previo.texto,
        )
        if defecto is not None:
            textos_ya_exigidos.append(defecto.get('texto', previo.texto))

    if textos_ya_exigidos and not justificacion:
        return jsonify({
            'error': 'Hay requerimientos ya exigidos en una vuelta anterior notificada',
            'motivo': motivo_check_ya_exigido_lote(textos_ya_exigidos),
            'puede_escapar': True,
        }), 422

    RequerimientoTarea.query.filter_by(solicitud_id=solicitud.id).delete()
    db.session.add_all(nuevas)
    db.session.commit()

    if textos_ya_exigidos:
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'tareas', tarea.id,
            detalle={
                'escape': True, 'justificacion': justificacion,
                'origen': 'requerimiento', 'items': textos_ya_exigidos,
            },
        )

    return jsonify({'ok': True, 'seleccionados': _seleccionados_json(solicitud)}), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos/catalogo',
    methods=['POST'])
@login_required
def crear_requerimiento_catalogo(expediente_id, tarea_id):
    """
    POST .../requerimientos/catalogo — crea una entrada nueva en `catalogo_requerimientos`
    desde el shuttle ("Guardar en catálogo", #440).

    Doble gate (#684): `gestionar_tarea` sobre el expediente —es una acción hecha
    mientras se trabaja una tarea ANALIZAR concreta— **y además**
    `gestionar_catalogo_requerimientos`, el mismo permiso que exige el CRUD de
    administración del catálogo (#593, `{ADMIN, SUPERVISOR}`). Antes solo pedía el
    primero, así que cualquier TRAMITADOR/ADMINISTRATIVO insertaba filas en el
    catálogo maestro desde el shuttle, eludiendo el control de #593: el catálogo se
    diseñó curado (imagen homogénea de la administración) y esto era una puerta
    trasera a texto basura, duplicados o categorización errónea.

    Para quien NO tiene el permiso, la UI ofrece "Solicitar guardado en
    catálogo", que desde #28 manda un mensaje al SUPERVISOR por
    `solicitar_alta_catalogo` (abajo) y NO pasa por aquí — este endpoint sigue
    siendo escritura directa y por tanto exclusivo de quien puede curar el
    catálogo.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403
    if not tiene_permiso('gestionar_catalogo_requerimientos'):
        return jsonify({
            'error': 'Solo Supervisor o Administrador pueden dar de alta requerimientos '
                     'en el catálogo',
        }), 403

    try:
        _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    texto = (data.get('texto') or '').strip()
    categoria = data.get('categoria')
    if not texto:
        return jsonify({'error': 'texto es obligatorio'}), 422
    if categoria not in _CATEGORIAS_REQUERIMIENTO_VALIDAS:
        return jsonify({'error': 'categoria no es válida'}), 422

    requerimiento = CatalogoRequerimiento(texto=texto, categoria=categoria)
    db.session.add(requerimiento)
    db.session.commit()

    return jsonify({
        'ok': True,
        'requerimiento': {'id': requerimiento.id, 'texto': requerimiento.texto, 'categoria': requerimiento.categoria},
    }), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos/catalogo/solicitar',
    methods=['POST'])
@login_required
def solicitar_alta_catalogo(expediente_id, tarea_id):
    """
    POST .../requerimientos/catalogo/solicitar — propone al Supervisor un alta en
    `catalogo_requerimientos` (#28, contrato heredado de #684).

    El envés de `crear_requerimiento_catalogo`: mismo sitio de la interfaz, misma
    intención del usuario, efecto distinto. Aquí NO se escribe en el catálogo —
    se crea un mensaje ALTA_CATALOGO_REQUERIMIENTO en la bandeja del Supervisor,
    que decidirá y, si procede, dará el alta desde el CRUD de #593.

    Por eso no se reutiliza el endpoint de #440 con un flag: aquel es escritura
    directa en el catálogo maestro y debe seguir siendo exclusivo de quien puede
    curarlo. El aviso es un mensaje, no un alta.

    Gate: `gestionar_tarea` sobre el expediente, el mismo que ya hace falta para
    trabajar la tarea ANALIZAR desde la que se propone. NO se exige
    `gestionar_catalogo_requerimientos` — precisamente quien no lo tiene es el
    destinatario de esta vía.

    El requerimiento se añade igualmente como texto libre en la tarea; eso lo
    hace el front por su cuenta, y es plenamente funcional en el diagnóstico.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    try:
        servicio_mensajes.crear(
            'ALTA_CATALOGO_REQUERIMIENTO',
            current_user.id,
            texto=data.get('texto'),
            categoria=data.get('categoria'),
        )
        db.session.commit()
    except servicio_mensajes.PayloadInvalido as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 422

    return jsonify({
        'ok': True,
        'mensaje': 'Propuesta enviada al Supervisor. El requerimiento se añade '
                   'como texto libre mientras la decide.',
    }), 200


# =============================================================================
# ENDPOINT 12: Contenedor de la tarea NOTIFICAR (#657/#658/#712, ADR-034)
# =============================================================================

_CANALES_VALIDOS = {'NOTIFICA', 'BANDEJA', 'SIR', 'POSTAL'}
_RESULTADOS_VALIDOS = {'CORRECTA', 'INCORRECTA'}


def _resolver_tarea_notificar(expediente, tarea_id):
    """(expediente, tarea_id) → Tarea de tipo NOTIFICAR. ValueError si no."""
    tarea = _resolver_nodo(expediente, 'tarea', tarea_id)
    codigo = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None
    if codigo != 'NOTIFICAR':
        raise ValueError(f'La tarea {tarea_id} no es de tipo NOTIFICAR (es {codigo!r})')
    return tarea


def _notificacion_json(notif: Notificacion) -> dict:
    return {
        'id': notif.id,
        'canal': notif.canal,
        'identificador_envio': notif.identificador_envio,
        'fecha_puesta_disposicion': notif.fecha_puesta_disposicion.isoformat()
            if notif.fecha_puesta_disposicion else None,
        'resultado': notif.resultado,
        'fecha_resultado': notif.fecha_resultado.isoformat() if notif.fecha_resultado else None,
        'numero_intento': notif.numero_intento,
        'observaciones': notif.observaciones,
        'documento_id': notif.documento_id,
    }


def _parsear_fecha_iso(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notificar',
              methods=['GET'])
@login_required
def get_notificar(expediente_id, tarea_id):
    """
    GET .../nodo/tarea/<tarea_id>/notificar — payload del contenedor de #657.

    {notificacion: {canal, identificador_envio, fecha_puesta_disposicion,
     resultado, fecha_resultado, numero_intento, observaciones, documento_id}|null,
     documento_producido: {id, nombre}|null}
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        tarea = _resolver_tarea_notificar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    doc = tarea.documento_producido
    return jsonify({
        'notificacion': _notificacion_json(tarea.notificacion) if tarea.notificacion else None,
        'documento_producido': {'id': doc.id, 'nombre': _nombre_documento(doc)} if doc else None,
    }), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notificar',
              methods=['POST'])
@login_required
def post_notificar(expediente_id, tarea_id):
    """
    POST .../nodo/tarea/<tarea_id>/notificar — "Registrar puesta a disposición"
    (camino A, ADR-034 §6).

    Body JSON: {canal, identificador_envio?, fecha_puesta_disposicion}. Upsert
    por tarea_id: si ya existe fila (p.ej. creada por el hook de editar_tarea,
    #657/#658), actualiza estos tres campos sin tocar resultado/fecha_resultado/
    numero_intento/observaciones — "Registrar notificación" (PATCH) es la acción
    que los gestiona.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_notificar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    canal = data.get('canal')
    if canal not in _CANALES_VALIDOS:
        return jsonify({'error': 'canal debe ser NOTIFICA, BANDEJA, SIR o POSTAL'}), 422

    fecha_puesta = _parsear_fecha_iso(data.get('fecha_puesta_disposicion'))
    if fecha_puesta is None:
        return jsonify({'error': 'fecha_puesta_disposicion es obligatoria (AAAA-MM-DD)'}), 422

    identificador_envio = (data.get('identificador_envio') or '').strip() or None

    notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
    if notif is None:
        notif = Notificacion(tarea_id=tarea.id)
        db.session.add(notif)
    notif.canal = canal
    notif.identificador_envio = identificador_envio
    notif.fecha_puesta_disposicion = fecha_puesta
    db.session.commit()

    return jsonify({'ok': True, 'notificacion': _notificacion_json(notif)}), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notificar',
              methods=['PATCH'])
@login_required
def patch_notificar(expediente_id, tarea_id):
    """
    PATCH .../nodo/tarea/<tarea_id>/notificar — "Registrar notificación" (camino B
    manual, ADR-034 §6/SIR). Body JSON: {resultado, fecha_resultado, numero_intento,
    observaciones?, documento_id?}.

    `documento_id` (#712, acto 3 del flujo de dos actos, opcional): vincula ese
    documento del pool como Producido de la tarea ANTES de persistir los campos
    de resultado — reutiliza `svc.editar_tarea` (mismo mecanismo de movimiento
    físico y del hook de cotejo que usa la Despensa, sin duplicarlo), sustituyendo
    el producido anterior si lo había. El hook puede auto-rellenar resultado/
    fecha_resultado al vincular (si el documento es parseable) pero los valores
    del body de esta misma llamada se persisten justo después y ganan siempre —
    son los que el usuario ya revisó/corrigió en el formulario, no un re-parseo.

    Sin `documento_id`, requiere fila previa (creada por "Registrar puesta a
    disposición" o por el hook automático al vincular un justificante parseable)
    — 422 si no existe: fecha_puesta_disposicion es NOT NULL y este endpoint no
    la conoce, así que no puede crear la fila desde cero.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_notificar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}

    advertencia_vinculo = None
    documento_id = data.get('documento_id')
    if documento_id is not None:
        doc = Documento.query.get(documento_id)
        if not doc or doc.expediente_id != expediente.id:
            return jsonify({'error': 'Documento no válido para este expediente'}), 422
        tipo_codigo = doc.tipo_doc.codigo if doc.tipo_doc else None
        if tipo_codigo not in svc.MAPA_CANAL_POR_TIPO_DOC:
            return jsonify({'error': 'El documento no es un justificante de notificación (JUSTIFICANTE_*)'}), 422

        consumidos_ids = [v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']
        res_vinculo = svc.editar_tarea(
            tarea, documentos_consumidos_ids=consumidos_ids,
            documento_producido_id=documento_id, notas=tarea.notas,
        )
        if res_vinculo.bloqueo:
            return _bloqueo_422(res_vinculo)
        if not res_vinculo.ok:
            return jsonify({'error': res_vinculo.error}), 422
        advertencia_vinculo = res_vinculo.advertencia

    notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
    if notif is None:
        return jsonify({
            'error': 'Sin envío registrado',
            'motivo': 'Registra la puesta a disposición antes de registrar la notificación.',
        }), 422

    resultado = data.get('resultado')
    if resultado not in _RESULTADOS_VALIDOS:
        return jsonify({'error': 'resultado debe ser CORRECTA o INCORRECTA'}), 422

    fecha_resultado = _parsear_fecha_iso(data.get('fecha_resultado'))
    if fecha_resultado is None:
        return jsonify({'error': 'fecha_resultado es obligatoria (AAAA-MM-DD)'}), 422

    numero_intento = data.get('numero_intento')
    if numero_intento not in (1, 2):
        return jsonify({'error': 'numero_intento debe ser 1 o 2'}), 422

    notif.resultado = resultado
    notif.fecha_resultado = fecha_resultado
    notif.numero_intento = numero_intento
    notif.observaciones = (data.get('observaciones') or '').strip() or None
    db.session.commit()

    payload = {'ok': True, 'notificacion': _notificacion_json(notif)}
    if advertencia_vinculo:
        payload['advertencia'] = advertencia_vinculo
    return jsonify(payload), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notificar/parsear',
              methods=['POST'])
@login_required
def post_notificar_parsear(expediente_id, tarea_id):
    """
    POST .../notificar/parsear — parseo transitorio del justificante de puesta a
    disposición (camino A, ADR-034 §1): recibe el PDF/ZIP en memoria, lo parsea
    y devuelve los datos extraídos SIN persistir nada ni guardar el fichero — el
    usuario verifica/corrige en el formulario antes de confirmar con POST
    .../notificar. Solo NOTIFICA tiene parser hoy (#655).

    Multipart: 'fichero'. Respuesta: el `.to_dict()` del parser (incluye
    `reconocido`); `{reconocido: false}` si no es un justificante NOTIFICA
    reconocible (nunca 422 — es un intento especulativo).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        _resolver_tarea_notificar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    fichero = request.files.get('fichero')
    if not fichero or not fichero.filename:
        return jsonify({'error': 'Ningún fichero recibido'}), 400

    nombre = fichero.filename.lower()
    if nombre.endswith('.zip'):
        resultado = parsear_justificante_notifica_zip(fichero.stream)
    else:
        resultado = parsear_justificante_notifica(fichero.stream)

    return jsonify(resultado.to_dict()), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/notificar/parsear_documento',
              methods=['POST'])
@login_required
def post_notificar_parsear_documento(expediente_id, tarea_id):
    """
    POST .../notificar/parsear_documento — preview del justificante DEFINITIVO
    (#712, acto 1 del flujo de dos actos): a diferencia de .../notificar/parsear
    (fichero transitorio sin subir), aquí el documento YA está en el pool del
    expediente — se lee de disco por `documento_id`, se parsea con la misma
    lógica que usa el hook de vinculación (`parsear_documento_notifica`), y NO
    se persiste nada ni se vincula como Producido — eso lo hace el PATCH
    .../notificar (acto 3) cuando el usuario confirma.

    Body JSON: {documento_id}. Solo NOTIFICA tiene parser (#655): para el
    resto de canales responde `{reconocido: false, canal}` sin intentar nada
    — el usuario rellena a mano (mismo criterio que ADR-034 §"SIR").
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        _resolver_tarea_notificar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    documento_id = data.get('documento_id')
    doc = Documento.query.get(documento_id) if documento_id else None
    if not doc or doc.expediente_id != expediente.id:
        return jsonify({'error': 'Documento no válido para este expediente'}), 422

    tipo_codigo = doc.tipo_doc.codigo if doc.tipo_doc else None
    canal = svc.MAPA_CANAL_POR_TIPO_DOC.get(tipo_codigo)
    if canal is None:
        return jsonify({'error': 'El documento no es un justificante de notificación (JUSTIFICANTE_*)'}), 422

    if canal != 'NOTIFICA':
        return jsonify({'reconocido': False, 'canal': canal}), 200

    resultado = svc.parsear_documento_notifica(doc)
    if resultado is None:
        return jsonify({'reconocido': False, 'canal': canal}), 200

    payload = resultado.to_dict()
    payload['canal'] = canal
    return jsonify(payload), 200
