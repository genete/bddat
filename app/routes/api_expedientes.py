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
from app.routes.api_bc import _leer_bypass
from app.services.assembler import build
from app.services.requisitos import evaluar_requisitos
from app.services.items_tecnicos import evaluar_items_tecnicos
from app.services.consolidacion_defectos import consolidar_defectos
from app.services.diagnosticos import crear_diagnostico
from app.utils.permisos import verificar_acceso_expediente

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
    de tipos del inspector y el submenú 'Crear hijo' del menú contextual. Cada tipo
    llega marcado permitido/no-permitido (motor + modo global); los no-permitidos
    incluyen norma + motivo para el 'Mostrar todos…' atenuado.
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

def _resolver_nodo(expediente, tipo: str, nodo_id: int):
    """(tipo, nodo_id) → objeto del modelo validando pertenencia. ValueError si no."""
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
        return obj
    if tipo == 'tramite':
        obj = Tramite.query.get(nodo_id)
        if obj is None or obj.fase.solicitud.expediente_id != expediente.id:
            raise ValueError(f'Trámite {nodo_id} no encontrado en expediente {expediente.id}')
        return obj
    if tipo == 'tarea':
        obj = Tarea.query.get(nodo_id)
        if obj is None or obj.tramite.fase.solicitud.expediente_id != expediente.id:
            raise ValueError(f'Tarea {nodo_id} no encontrada en expediente {expediente.id}')
        return obj
    raise ValueError(f'Tipo de nodo desconocido: {tipo!r}')


def _bloqueo_422(res):
    """Respuesta uniforme árbol para bloqueo del motor o de un invariante ESFTT.

    El mensaje legible del bloqueo puede venir de DOS fuentes (ver EvaluacionResult):
      · motor de reglas    → `motivo` (descripción editorial de la regla)
      · invariantes ESFTT  → `norma_compilada` (su `_bloquear` deja `motivo=''`)
    Por eso se surfacea `motivo or norma_compilada` (mismo criterio que
    api_bc._res_error). Omitir el fallback dejaba los bloqueos de invariante con
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

    justificacion, err = _leer_bypass(data)
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
      solicitud: {observaciones}
      fase:      {resultado_fase_id, documento_resultado_id, observaciones}
      tramite:   {observaciones}
      tarea:     {documentos_consumidos_ids, documento_producido_id, notas}
    Respuesta éxito: {ok:true} 200. Bloqueo motor: {error, motivo, url_norma} 422.
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

    if tipo == 'solicitud':
        res = svc.editar_solicitud(nodo, observaciones=data.get('observaciones'))
    elif tipo == 'fase':
        res = svc.editar_fase(
            nodo,
            resultado_fase_id=data.get('resultado_fase_id'),
            documento_resultado_id=data.get('documento_resultado_id'),
            observaciones=data.get('observaciones'),
        )
    elif tipo == 'tramite':
        res = svc.editar_tramite(nodo, observaciones=data.get('observaciones'))
    elif tipo == 'tarea':
        res = svc.editar_tarea(
            nodo,
            documentos_consumidos_ids=data.get('documentos_consumidos_ids') or [],
            documento_producido_id=data.get('documento_producido_id'),
            notas=data.get('notas'),
        )
    else:
        return jsonify({'error': f'Tipo de nodo no editable: {tipo!r}'}), 422

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    return jsonify({'ok': True}), 200


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
    else:
        return jsonify({'error': f'Tipo de nodo no borrable: {tipo!r}'}), 422

    if res.bloqueo:
        return _bloqueo_422(res)
    if not res.ok:
        return jsonify({'error': res.error}), 422
    return jsonify({'ok': True}), 200


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

    Devuelve: {documentos: [{id, nombre, tipo_doc, fecha, enlace, externo,
    puede_abrir_carpeta}]}, orden id DESC. enlace/puede_abrir_carpeta permiten
    previsualizar cualquier documento del pool antes de decidir enlazarlo,
    no solo los ya consumidos/producidos de la tarea (#609).
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


def _tiene_secciones_extendidas(tarea) -> bool:
    """Trámite de la tarea ∈ _TRAMITES_CON_SECCIONES_ANALISIS (#442/#677)."""
    codigo_tramite = (
        tarea.tramite.tipo_tramite.codigo
        if tarea.tramite and tarea.tramite.tipo_tramite else None
    )
    return codigo_tramite in _TRAMITES_CON_SECCIONES_ANALISIS


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
     secciones_extendidas: bool, defectos_consolidado: [...], completo: bool,
     checklist_documental: [...], checklist_tecnico: [...], notas}

    `resultado_previsto` (ADR-033 §3): sentido que tendría el diagnóstico si se
    produjera ahora mismo, derivado del borrador agregado — informativo en
    ANALIZAR extendido (sin radio editable); no aplica a ANALIZAR simple, que
    sigue con resultado de elección libre.
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
        'defectos_consolidado': consolidado['items'],
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
    """DELETE .../requisitos-documentales/<requisito_id> — quita el vínculo documento↔requisito (#495)."""
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    solicitud = tarea.tramite.fase.solicitud
    vinculo = DocumentoRequisito.query.filter_by(
        requisito_id=requisito_id, solicitud_id=solicitud.id
    ).first()
    if vinculo is not None:
        db.session.delete(vinculo)
        db.session.commit()

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

    Body JSON: {texto, cubierto}. Upsert por (item_tecnico_id, solicitud_id).
    `cubierto` se fuerza a False si `texto` está vacío — evita el estado
    inválido de CoberturaItemTecnico (ver su docstring).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    ItemTecnico.query.get_or_404(item_tecnico_id)

    data = request.get_json(silent=True) or {}
    texto = (data.get('texto') or '').strip()
    cubierto = bool(data.get('cubierto')) and bool(texto)

    solicitud = tarea.tramite.fase.solicitud
    cobertura = CoberturaItemTecnico.query.filter_by(
        item_tecnico_id=item_tecnico_id, solicitud_id=solicitud.id
    ).first()
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

    return jsonify({'ok': True, 'checklist_tecnico': _checklist_tecnico_json(tarea)}), 200


# Mismos valores que el CHECK ck_catalogo_requerimientos_categoria (#440, ver catalogo_requerimientos/routes.py)
_CATEGORIAS_REQUERIMIENTO_VALIDAS = {'documental', 'tecnica', 'administrativa', 'tasas'}


def _seleccionados_json(tarea) -> list:
    return [{
        'id': r.id,
        'texto': r.texto,
        'orden': r.orden,
        'desde_catalogo': r.desde_catalogo,
        'catalogo_requerimientos_id': r.catalogo_requerimientos_id,
    } for r in sorted(tarea.requerimientos, key=lambda r: r.orden)]


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos', methods=['GET'])
@login_required
def get_requerimientos(expediente_id, tarea_id):
    """
    GET .../requerimientos — estado inicial del panel shuttle: catálogo activo
    agrupado y selección actual de la tarea (#440).
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

    return jsonify({
        'catalogo': [{'id': c.id, 'texto': c.texto, 'categoria': c.categoria} for c in catalogo],
        'seleccionados': _seleccionados_json(tarea),
    }), 200


@api_bp.route('/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos', methods=['POST'])
@login_required
def post_requerimientos(expediente_id, tarea_id):
    """
    POST .../requerimientos — sustituye la lista completa de `requerimientos_tarea`
    en una sola llamada: crear, reordenar y borrar (#440).

    Body JSON: {items: [{catalogo_requerimientos_id: int|null, texto_libre: str|null}, ...]}
    Orden = posición en la lista (1-based). Exactamente uno de los dos campos
    de cada item debe tener valor (ck_requerimientos_tarea_exactamente_uno).
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

    try:
        tarea = _resolver_tarea_analizar(expediente, tarea_id)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

    data = request.get_json(silent=True) or {}
    items = data.get('items')
    if not isinstance(items, list):
        return jsonify({'error': 'items debe ser una lista'}), 422

    nuevas = []
    for i, it in enumerate(items, start=1):
        catalogo_id = it.get('catalogo_requerimientos_id')
        texto_libre = (it.get('texto_libre') or '').strip() or None
        if bool(catalogo_id) == bool(texto_libre):
            return jsonify({
                'error': f'Ítem {i}: exactamente uno de catalogo_requerimientos_id o texto_libre',
            }), 422
        nuevas.append(RequerimientoTarea(
            tarea_id=tarea.id, catalogo_requerimientos_id=catalogo_id,
            texto_libre=texto_libre, orden=i,
        ))

    RequerimientoTarea.query.filter_by(tarea_id=tarea.id).delete()
    db.session.add_all(nuevas)
    db.session.commit()

    return jsonify({'ok': True, 'seleccionados': _seleccionados_json(tarea)}), 200


@api_bp.route(
    '/expedientes/<int:expediente_id>/nodo/tarea/<int:tarea_id>/requerimientos/catalogo',
    methods=['POST'])
@login_required
def crear_requerimiento_catalogo(expediente_id, tarea_id):
    """
    POST .../requerimientos/catalogo — crea una entrada nueva en `catalogo_requerimientos`
    desde el shuttle ("Guardar en catálogo", #440). Gate por `gestionar_tarea` —
    distinto del CRUD de administración del catálogo (#593, solo Supervisor):
    aquí el técnico da de alta un texto reutilizable como subproducto de su
    trabajo en ANALIZAR, no está gestionando el catálogo.
    """
    expediente = Expediente.query.get_or_404(expediente_id)
    if verificar_acceso_expediente(expediente, 'gestionar_tarea'):
        return jsonify({'error': 'No tienes permiso para esta acción'}), 403

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
