"""
cola_administrativo.py — Agregador de la cola de "Mi trabajo" del administrativo (#501, ADR-017 §2).

Listado transversal (atraviesa todos los expedientes EN_TRAMITE) de las tareas que
son trabajo administrativo típico: NOTIFICAR, ELABORAR y ESPERAR_PLAZO no finalizadas.
NO incluye ANALIZAR (trabajo del técnico); la "puerta abierta" del permiso permite al
admin actuar sobre cualquier tarea desde el árbol, pero la cola solo OFRECE su
subconjunto (es una guía, no un límite de acceso — ADR-017 §6).

El estado de cada tarea sale del núcleo único `estado_dominio` (#558) — la misma verdad
que el árbol y el seguimiento. El plazo de ESPERAR_PLAZO se resuelve en el backend
(calendario hábil) vía `arbol_expediente.plazo_tarea`. La cola NO añade columnas nuevas
respecto al diseño: amplía qué tareas selecciona y el texto de "Pendiente" (directiva #2).

"Tocado por" queda DIFERIDO (placeholder en el front); aquí viaja como None (#501 §3).

Salida: {'data': [fila...], 'next_cursor': int, 'has_more': bool}.
"""
from __future__ import annotations

import logging

from sqlalchemy import or_, cast, String
from sqlalchemy.orm import joinedload

from app import db
from app.models.tareas import Tarea
from app.models.tramites import Tramite
from app.models.fases import Fase
from app.models.solicitudes import Solicitud
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.tipos_tareas import TipoTarea

import app.services.estado_dominio as ed
from app.services.arbol_expediente import plazo_tarea

log = logging.getLogger(__name__)

# Tipos de tarea que la cola ofrece como trabajo administrativo (ADR-017 §2).
TIPOS_COLA = ('NOTIFICAR', 'ELABORAR', 'ESPERAR_PLAZO')


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def construir_cola(*, cursor: int = 0, limit: int = 50, filtros: dict | None = None) -> dict:
    """
    Construye una página de la cola administrativa.

    Cursor por `Tarea.id`. Como el descarte de tareas FIN / de solicitudes resueltas
    ocurre en Python (depende de documentos y plazo, no es SQL puro), se lee una
    ventana mayor que `limit` y se emite hasta `limit` filas pendientes. Una página
    puede salir corta: el front sigue paginando mientras `has_more` sea True.
    """
    filtros = filtros or {}
    limit = min(max(limit, 1), 100)
    ventana = limit * 4

    tareas = _query_base(cursor, filtros).limit(ventana + 1).all()
    hay_mas_db = len(tareas) > ventana
    tareas = tareas[:ventana]

    data: list[dict] = []
    ultimo_id = cursor
    corte = False
    for tarea in tareas:
        ultimo_id = tarea.id
        fila = _fila_si_pendiente(tarea, filtros)
        if fila is not None:
            data.append(fila)
            if len(data) >= limit:
                corte = True
                break

    return {
        'data': data,
        'next_cursor': ultimo_id,
        'has_more': corte or hay_mas_db,
    }


# ---------------------------------------------------------------------------
# Query base (filtros SQL: tipo de tarea, cursor, búsqueda, tipo de expediente)
# ---------------------------------------------------------------------------

def _query_base(cursor: int, filtros: dict):
    q = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(Fase, Tramite.fase_id == Fase.id)
        .join(Solicitud, Fase.solicitud_id == Solicitud.id)
        .join(Expediente, Solicitud.expediente_id == Expediente.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .outerjoin(Entidad, Expediente.titular_id == Entidad.id)
        .options(
            joinedload(Tarea.tipo_tarea),
            joinedload(Tarea.vinculos_documento)
                .joinedload(DocumentoTarea.documento).joinedload(Documento.tipo_doc),
            joinedload(Tarea.vinculos_documento)
                .joinedload(DocumentoTarea.documento).joinedload(Documento.notificacion),
            joinedload(Tarea.tramite).joinedload(Tramite.tipo_tramite),
            joinedload(Tarea.tramite).joinedload(Tramite.fase).joinedload(Fase.tipo_fase),
            joinedload(Tarea.tramite).joinedload(Tramite.fase)
                .joinedload(Fase.solicitud).joinedload(Solicitud.tipo_solicitud),
            joinedload(Tarea.tramite).joinedload(Tramite.fase)
                .joinedload(Fase.solicitud).joinedload(Solicitud.expediente)
                .joinedload(Expediente.titular),
        )
        .filter(TipoTarea.codigo.in_(TIPOS_COLA))
    )

    if cursor > 0:
        q = q.filter(Tarea.id > cursor)

    search = (filtros.get('search') or '').strip()
    if search:
        num_at = search.upper().removeprefix('AT-').removeprefix('AT')
        q = q.filter(or_(
            cast(Expediente.numero_at, String).ilike(f'%{num_at}%'),
            Entidad.nombre_completo.ilike(f'%{search}%'),
        ))

    tipo_expediente_id = filtros.get('tipo_expediente_id')
    if tipo_expediente_id:
        q = q.filter(Expediente.tipo_expediente_id == tipo_expediente_id)

    return q.order_by(Tarea.id.asc())


# ---------------------------------------------------------------------------
# Selección y serialización de filas (filtros computados: estado y plazo)
# ---------------------------------------------------------------------------

def _fila_si_pendiente(tarea, filtros: dict) -> dict | None:
    """Devuelve la fila si la tarea es trabajo pendiente y pasa los filtros; si no, None."""
    sol = tarea.tramite.fase.solicitud
    if not sol.activa:                       # solo solicitudes EN_TRAMITE
        return None

    estado, plazo = _estado_y_plazo(tarea)
    if estado == 'FIN':                       # ya hecha: no es trabajo pendiente
        return None

    f_pendiente = filtros.get('pendiente')
    if f_pendiente and estado != f_pendiente:
        return None

    f_plazo = filtros.get('plazo')
    if f_plazo and _bucket_plazo(plazo) != f_plazo:
        return None

    return _fila(tarea, estado, plazo)


def _estado_y_plazo(tarea) -> tuple[str, dict | None]:
    """Estado de dominio de la tarea (+ plazo resuelto si es ESPERAR_PLAZO).

    Réplica de la lógica de seguimiento._estado_tarea, defensiva: un fallo de plazo
    degrada a None (el núcleo lo mapea a PENDIENTE_TRAMITAR) sin tumbar la fila.
    """
    tt = getattr(tarea, 'tipo_tarea', None)
    codigo = tt.codigo if tt else None
    plazo = None
    if codigo == 'ESPERAR_PLAZO':
        try:
            plazo = plazo_tarea(tarea, tarea.tramite)
        except Exception as exc:  # noqa: BLE001 — un plazo no debe tumbar la cola
            log.warning('cola: plazo no disponible para tarea %s — %s', tarea.id, exc)
    return ed.estado_tarea(tarea, plazo=plazo), plazo


def _fila(tarea, estado: str, plazo: dict | None) -> dict:
    tramite = tarea.tramite
    fase = tramite.fase
    sol = fase.solicitud
    exp = sol.expediente
    titular = exp.titular if exp else None
    return {
        'tarea_id':      tarea.id,
        'expediente_id': exp.id if exp else None,
        'num_at':        exp.numero_at if exp else None,
        'titular':       titular.nombre_completo if titular else '—',
        'solicitud':     sol.tipo_solicitud.siglas if sol.tipo_solicitud else '—',
        'fase':          _nombre_tipo(fase.tipo_fase),
        'tramite':       _nombre_tipo(tramite.tipo_tramite),
        'tarea':         tarea.tipo_tarea.codigo if tarea.tipo_tarea else '—',
        'pendiente':         _mensaje_pendiente(tarea, estado),
        'pendiente_codigo':  estado,
        'plazo':         plazo,
        'tocado_por':    None,   # diferido (#501 §3): el front pinta '—'
    }


# ---------------------------------------------------------------------------
# Texto de "Pendiente" por tipo de tarea + estado de dominio (ADR-017 §2)
# ---------------------------------------------------------------------------

def _mensaje_pendiente(tarea, estado: str) -> str:
    codigo = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None

    if codigo == 'NOTIFICAR':
        if estado == 'PENDIENTE_TRAMITAR':
            return 'falta doc firmado'
        if estado == 'NOTIFICACION_FALLIDA':
            return 'notificación fallida — 2º intento'
        if estado == 'NOTIFICACION_AGOTADA':
            return 'notificación agotada — procede edicto'
        # PENDIENTE_NOTIFICAR: distingue por presencia de justificante (producido)
        if tarea.documento_producido is None:
            return 'esperando justificante'
        return 'esperando registro de resultado'

    if codigo == 'ELABORAR':
        if estado == 'PENDIENTE_FIRMA':
            return 'pendiente de firma'
        return 'pendiente elaborar'

    if codigo == 'ESPERAR_PLAZO':
        if estado == 'PENDIENTE_ESTUDIO':       # plazo vencido → hay que actuar
            return 'plazo vencido — incorporar'
        if estado == 'PENDIENTE_TRAMITAR':
            return 'pendiente iniciar plazo'
        return _texto_espera(tarea)             # PENDIENTE_PLAZOS

    return 'pendiente'


def _texto_espera(tarea) -> str:
    """Afina "esperando recepción" por el tipo de trámite/fase (ADR-017 §2, ilustrativo)."""
    tramite = tarea.tramite
    cod_tramite = _codigo(tramite.tipo_tramite if tramite else None)
    cod_fase = _codigo(tramite.fase.tipo_fase if tramite and tramite.fase else None)

    if 'PUBLICACION' in cod_tramite:
        return 'esperando publicación efectiva'
    if 'INFORMACION_PUBLICA' in cod_fase:
        return 'esperando alegaciones'
    if 'CONSULTA' in cod_tramite:
        return 'esperando informe del organismo'
    if 'REQUERIMIENTO' in cod_tramite or 'SUBSAN' in cod_tramite:
        return 'esperando subsanación'
    return 'esperando recepción'


# ---------------------------------------------------------------------------
# Plazo → bucket para el filtro (hoy / semana / vencido / sin_plazo)
# ---------------------------------------------------------------------------

def _bucket_plazo(plazo: dict | None) -> str:
    if not plazo:
        return 'sin_plazo'
    if plazo.get('estado') == 'VENCIDO':
        return 'vencido'
    dias = plazo.get('dias_restantes')
    if dias is None:
        return 'sin_plazo'
    if dias < 0:
        return 'vencido'
    if dias == 0:
        return 'hoy'
    if dias <= 7:
        return 'semana'
    return 'futuro'


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _nombre_tipo(tipo) -> str:
    """Nombre legible de un tipo de catálogo (nombre → código → '—')."""
    if tipo is None:
        return '—'
    return getattr(tipo, 'nombre', None) or getattr(tipo, 'codigo', None) or '—'


def _codigo(tipo) -> str:
    return (getattr(tipo, 'codigo', None) or '') if tipo is not None else ''
