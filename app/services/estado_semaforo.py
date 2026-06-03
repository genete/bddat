"""
estado_semaforo.py — Estado-semáforo (color fino) por nodo del árbol del expediente.

FUENTE DE VERDAD: docs/referencia/MODELO_ESTADOS_SEMAFORO.md (§2 colores, §3 tareas,
§4 contenedores, §5 agregación/prioridad). Lo consume `services/arbol_expediente.py`
para decorar cada nodo con `semaforo {estado, color, propio}`.

Por qué un servicio NUEVO y no `seguimiento.py`:
  - `seguimiento.py` razona por PISTAS (grupos de fases por tipo), no por nodo del árbol.
  - Arrastra la deuda `PENDIENTE_ELABORAR` (un único 🟡); este modelo lo desdobla en
    `PENDIENTE_REDACTAR` 🔴 + `PENDIENTE_FIRMA` 🟡 mirando el tipo de doc BORRADOR_FIRMA.
  Se reutiliza el *algoritmo* (recorrido abajo-arriba + mayor prioridad), no su código.
  La unificación de ambos consumidores queda como deuda (MODELO §10).

CONTRATO de las funciones contenedor: devuelven `(estado, propio)`.
  - `estado`: código del estado-semáforo (agregado del subárbol si el nodo está en curso).
  - `propio`: True si el nodo "tiene algo que decir POR SÍ MISMO" (sin hijos → TRAMITAR;
    fase PDTE_CIERRE; solicitud todo-FIN-pero-EN_TRAMITE). El front rellena el círculo
    cuando `propio` (nodo expandido) o siempre con el color agregado si el nodo está
    colapsado (MODELO §5/§7). Las tareas (hojas) van siempre rellenas.
"""
from __future__ import annotations

from typing import Optional

# --- §2: nombre de color por estado (el front mapea nombre → paleta JdA) ---
COLOR: dict[str, str] = {
    'PENDIENTE_TRAMITAR':   'rojo',
    'PENDIENTE_ESTUDIO':    'rojo',
    'PENDIENTE_REDACTAR':   'rojo',
    'NOTIFICACION_AGOTADA': 'rojo',
    'PENDIENTE_FIRMA':      'amarillo',
    'PENDIENTE_NOTIFICAR':  'azul',
    'NOTIFICACION_FALLIDA': 'naranja',
    'PENDIENTE_CERRAR':     'naranja',
    'PENDIENTE_PLAZOS':     'gris',
    'PENDIENTE_SUBSANAR':   'gris',
    'FIN':                  'verde',
}

# --- §5: prioridad (1 = más urgente; se queda el de menor número al agregar) ---
PRIORIDAD: dict[str, int] = {
    'PENDIENTE_TRAMITAR':   1,
    'PENDIENTE_ESTUDIO':    2,
    'PENDIENTE_REDACTAR':   3,
    'NOTIFICACION_AGOTADA': 3,
    'PENDIENTE_FIRMA':      4,
    'PENDIENTE_NOTIFICAR':  5,
    'NOTIFICACION_FALLIDA': 6,
    'PENDIENTE_CERRAR':     6,
    'PENDIENTE_SUBSANAR':   7,
    'PENDIENTE_PLAZOS':     7,
    'FIN':                  8,
}

# Tipo de documento cuyo consumo distingue PENDIENTE_FIRMA de PENDIENTE_REDACTAR (§3 ELABORAR).
_TIPO_BORRADOR_FIRMA = 'BORRADOR_FIRMA'


def color(estado: str) -> str:
    """Nombre de color (§2) de un estado-semáforo; 'gris' si desconocido."""
    return COLOR.get(estado, 'gris')


def _mayor_prioridad(estados: list[str]) -> str:
    """Estado de mayor prioridad (menor número §5) de una lista no vacía.

    Si la lista llega vacía (no debería en un nodo en curso), degrada a FIN.
    """
    if not estados:
        return 'FIN'
    return min(estados, key=lambda e: PRIORIDAD.get(e, 99))


# ---------------------------------------------------------------------------
# Hojas: tareas (§3)
# ---------------------------------------------------------------------------

def estado_tarea(tarea, plazo: Optional[dict] = None) -> str:
    """
    Estado-semáforo de una tarea según su tipo (MODELO §3).

    `plazo` es el dict ya resuelto por arbol_expediente para ESPERAR_PLAZO
    ({estado, fecha_limite, dias_restantes} o None) — no se recalcula aquí.
    Regla general §3: verde = tarea ejecutada (salvo NOTIFICAR, que depende del
    resultado de la notificación).
    """
    tt = getattr(tarea, 'tipo_tarea', None)
    codigo = tt.codigo if tt else None

    # NOTIFICAR no sigue el "ejecutada → FIN": su color lo fija el resultado.
    if codigo == 'NOTIFICAR':
        return _estado_notificar(tarea)

    if tarea.ejecutada:
        return 'FIN'
    if tarea.planificada:                 # sin ningún documento vinculado
        return 'PENDIENTE_TRAMITAR'

    if codigo == 'ANALIZAR':
        # No planificada (tiene consumido) y sin producido → falta el informe.
        return 'PENDIENTE_ESTUDIO'

    if codigo == 'ELABORAR':
        if not tarea.documentos_consumidos:
            return 'PENDIENTE_TRAMITAR'
        if _tiene_borrador_firma(tarea):
            return 'PENDIENTE_FIRMA'       # PDF listo para firma presente
        return 'PENDIENTE_REDACTAR'

    if codigo == 'ESPERAR_PLAZO':
        return _estado_esperar_plazo(plazo)

    return 'PENDIENTE_TRAMITAR'            # tipo desconocido — seguro por defecto


def _estado_notificar(tarea) -> str:
    """NOTIFICAR (§3): usa el modelo Notificacion (resultado + numero_intento)."""
    if not tarea.documentos_consumidos:
        return 'PENDIENTE_TRAMITAR'        # falta el documento firmado que notificar
    doc = tarea.documento_producido
    notif = getattr(doc, 'notificacion', None) if doc else None
    if notif is None:
        return 'PENDIENTE_NOTIFICAR'       # 🔵 a la espera del destinatario
    if notif.resultado == 'CORRECTA':
        return 'FIN'
    # INCORRECTA: 1 → queda 2º intento (🟠); 2 → agotada, procede edicto (🔴)
    return 'NOTIFICACION_AGOTADA' if notif.numero_intento == 2 else 'NOTIFICACION_FALLIDA'


def _estado_esperar_plazo(plazo: Optional[dict]) -> str:
    """ESPERAR_PLAZO no ejecutada (§3): mapea el estado de plazo ya computado."""
    estado_plazo = (plazo or {}).get('estado')
    if estado_plazo in (None, 'SIN_PLAZO'):
        return 'PENDIENTE_TRAMITAR'        # plazo no configurado / sin cómputo
    if estado_plazo == 'VENCIDO':
        return 'PENDIENTE_ESTUDIO'         # 🔴 hay que actuar
    return 'PENDIENTE_PLAZOS'              # ⚪ EN_PLAZO / PROXIMO_VENCER / INDEFINIDO


def _tiene_borrador_firma(tarea) -> bool:
    """True si entre los documentos consumidos hay un PDF de tipo BORRADOR_FIRMA."""
    for doc in tarea.documentos_consumidos:
        td = getattr(doc, 'tipo_doc', None)
        if td and td.codigo == _TIPO_BORRADOR_FIRMA:
            return True
    return False


# ---------------------------------------------------------------------------
# Contenedores (§4) — reciben los estados-semáforo ya computados de sus hijos
# ---------------------------------------------------------------------------

def estado_tramite(tramite, estados_tareas: list[str]) -> tuple[str, bool]:
    if not tramite.tareas:                 # planificado: sin tareas aún
        return ('PENDIENTE_TRAMITAR', True)
    return (_mayor_prioridad(estados_tareas), False)


def estado_fase(fase, estados_tramites: list[str]) -> tuple[str, bool]:
    if fase.planificada:                   # sin trámites aún
        return ('PENDIENTE_TRAMITAR', True)
    if fase.pdte_cierre:                   # todos los trámites cerrados, falta formalizar
        # Solo las finalizadoras requieren resultado_fase_id explícito (el técnico
        # tiene la última palabra). Las intermedias cierran por documento_resultado_id;
        # su resultado_fase_id debe quedar NULL.
        es_finalizadora = getattr(fase.tipo_fase, 'es_finalizadora', False)
        if es_finalizadora and fase.resultado_fase_id is None:
            return ('PENDIENTE_ESTUDIO', True)   # 🔴 falta decidir resultado
        return ('PENDIENTE_CERRAR', True)        # 🟠 falta documento formalizador
    return (_mayor_prioridad(estados_tramites), False)


def estado_solicitud(solicitud, estados_fases: list[str]) -> tuple[str, bool]:
    if not solicitud.fases:                # sin fases aún
        return ('PENDIENTE_TRAMITAR', True)
    if solicitud.estado != 'EN_TRAMITE':   # finalizada / archivada
        return ('FIN', False)
    agregado = _mayor_prioridad(estados_fases)
    if agregado == 'FIN':                  # todas las fases en FIN pero sigue EN_TRAMITE
        return ('PENDIENTE_CERRAR', True)  # 🟠 lista para cerrar
    return (agregado, False)


def estado_expediente(expediente, estados_solicitudes: list[str]) -> tuple[str, bool]:
    if not estados_solicitudes:            # expediente sin solicitudes
        return ('PENDIENTE_TRAMITAR', True)
    return (_mayor_prioridad(estados_solicitudes), False)
