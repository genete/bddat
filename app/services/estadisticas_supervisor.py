"""
estadisticas_supervisor.py — Agregados del panel de estadísticas del supervisor.

Bloque CONTROL de la vista del supervisor (#579, ADR-028 §2). Produce los tres
agregados que consume la isla React `estadisticas`:

    {kpis, por_estado, por_tecnico}

CONTRATO DE REUSO DEL NÚCLEO (no se reimplementa ninguna regla de estado):
El estado agregado de CADA expediente lo da `arbol_expediente.construir_arbol`,
que a su vez deriva del núcleo `estado_dominio` (#558):
  - estado del expediente  → arbol['expediente']['semaforo']['estado'] (uno de los
    10 estados canónicos; es exactamente sem.estado_expediente()).
  - plazos vencidos        → suma de sol['agregados']['plazos_vencidos'] (ya los
    cuenta el walk del árbol vía obtener_estado_plazo).
Así el panel enseña EXACTAMENTE el mismo estado que el árbol y el seguimiento, sin
"tercera verdad".

COSTE (v1 síncrono, ADR-028 §2): se llama construir_arbol una vez por expediente —
el mismo walk de árbol que ya hace hoy el listado de seguimiento por fila y el árbol
por nodo. Si con datos reales resulta lento, el paso siguiente es denormalizar el
`estado` agregado por expediente (columna o agregado materializado invalidado en
mutación) → carga instantánea con GROUP BY. NO se optimiza a ciegas: medir primero.

Defensivo ante catálogo/BD no disponible (REGLAS_DESARROLLO §Servicios con catálogo,
#347): captura OperationalError/ProgrammingError y degrada a agregados vacíos sin
propagar la excepción.
"""
from __future__ import annotations

import logging

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import joinedload

from app.models.expedientes import Expediente
from app.services import estado_dominio as sem
from app.services.arbol_expediente import construir_arbol

log = logging.getLogger(__name__)

# Etiqueta del cubo de expedientes sin técnico asignado (responsable_id NULL).
_SIN_ASIGNAR = 'Sin asignar'


def _kpis_vacios() -> dict:
    return {'total': 0, 'en_tramite': 0, 'plazos_vencidos': 0, 'finalizados': 0}


def calcular_estadisticas() -> dict:
    """
    Agregados del panel de estadísticas del supervisor.

    Returns:
        {
          'kpis':       {'total', 'en_tramite', 'plazos_vencidos', 'finalizados'},
          'por_estado': [ {'estado', 'color', 'n'} ],   # 10 estados canónicos
          'por_tecnico':[ {'tecnico', 'completados', 'en_tramite'} ],
        }

    Si la BD no está disponible devuelve la estructura con agregados vacíos (KPIs a
    cero, listas vacías) — el panel renderiza sin romper.
    """
    try:
        expedientes = (
            Expediente.query
            .options(joinedload(Expediente.responsable))
            .order_by(Expediente.id)
            .all()
        )
    except (OperationalError, ProgrammingError) as exc:
        log.warning('estadisticas_supervisor: BD no disponible — %s', exc)
        return {'kpis': _kpis_vacios(), 'por_estado': [], 'por_tecnico': []}

    kpis = _kpis_vacios()
    # Conteo por estado canónico (clave = código de estado de dominio).
    conteo_estado: dict[str, int] = {}
    # Conteo por técnico: {siglas: {'completados': n, 'en_tramite': n}}.
    conteo_tecnico: dict[str, dict[str, int]] = {}

    for exp in expedientes:
        estado, vencidos = _estado_y_vencidos(exp.id)

        kpis['total'] += 1
        kpis['plazos_vencidos'] += vencidos
        finalizado = estado == 'FIN'
        if finalizado:
            kpis['finalizados'] += 1
        else:
            kpis['en_tramite'] += 1

        conteo_estado[estado] = conteo_estado.get(estado, 0) + 1

        tecnico = exp.responsable.siglas if exp.responsable else _SIN_ASIGNAR
        cubo = conteo_tecnico.setdefault(tecnico, {'completados': 0, 'en_tramite': 0})
        cubo['completados' if finalizado else 'en_tramite'] += 1

    return {
        'kpis': kpis,
        'por_estado': _serializar_por_estado(conteo_estado),
        'por_tecnico': _serializar_por_tecnico(conteo_tecnico),
    }


def _estado_y_vencidos(expediente_id: int) -> tuple[str, int]:
    """
    Estado agregado del expediente y nº de plazos vencidos, vía el núcleo.

    Devuelve ('PENDIENTE_TRAMITAR', 0) degradado si el árbol no se pudo construir
    (BD caída / expediente sin árbol) — un expediente sin solicitudes ya cuenta como
    PENDIENTE_TRAMITAR en el propio núcleo (estado_expediente).
    """
    arbol = construir_arbol(expediente_id)
    if arbol is None:
        return ('PENDIENTE_TRAMITAR', 0)

    estado = arbol['expediente']['semaforo']['estado']
    vencidos = sum(
        sol['agregados'].get('plazos_vencidos', 0) for sol in arbol['solicitudes']
    )
    return (estado, vencidos)


def _serializar_por_estado(conteo: dict[str, int]) -> list[dict]:
    """
    Lista para la tarta, en el orden canónico de prioridad del núcleo (COLOR).

    Recorre los 10 estados de sem.COLOR (orden = prioridad #558) e incluye solo los
    que tienen expedientes, adjuntando el nombre de banda de color para que el front
    los tematice a la paleta JdA. La agrupación visual por banda la hace el front.
    """
    return [
        {'estado': estado, 'color': sem.COLOR[estado], 'n': conteo[estado]}
        for estado in sem.COLOR
        if conteo.get(estado, 0) > 0
    ]


def _serializar_por_tecnico(conteo: dict[str, dict[str, int]]) -> list[dict]:
    """
    Lista para las barras de carga por técnico, ordenada por carga total descendente.

    'Sin asignar' (expedientes huérfanos) se incluye como un cubo más: es información
    de supervisión relevante, no ruido.
    """
    filas = [
        {'tecnico': tecnico, 'completados': c['completados'], 'en_tramite': c['en_tramite']}
        for tecnico, c in conteo.items()
    ]
    filas.sort(key=lambda f: f['completados'] + f['en_tramite'], reverse=True)
    return filas
