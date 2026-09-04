"""
estado_dominio.py — Núcleo único de reglas de estado del árbol ESFTT.

FUENTE DE VERDAD: docs/referencia/MODELO_ESTADOS_SEMAFORO.md.
Una sola fuente para las dos proyecciones que deducen el estado del mismo árbol de
dominio (Solicitud → Fase → Trámite → Tarea):
  - `services/arbol_expediente.py` — proyección por NODO (vista de árbol): decora
    cada nodo 1:1 y usa el flag `propio`.
  - `services/seguimiento.py` — proyección por PISTAS (listado de seguimiento):
    agrega varias fases en una celda, con contador y nota.

De aquí salen, compartidos por ambas: el vocabulario canónico, la regla de hoja
`estado_tarea`, las reglas de contenedor (`estado_tramite/fase/solicitud/expediente`),
las tablas `COLOR`/`PRIORIDAD` y el helper `mayor_prioridad`. Lo que NO vive aquí es
el *alcance* de la agregación (qué nodos compiten) ni las decoraciones propias de
cada vista (contador/nota/relabel de seguimiento; serialización del árbol).

Unifica la deuda histórica `seguimiento.py`↔`estado_semaforo.py` (MODELO §10, #558):
vocabulario fino (REDACTAR/FIRMA), escalada de notificar (🔵→🟠→🔴, derivada de
`Notificacion`) y un único orden de prioridad canónico, coherente con el color
(🔴 > 🟠 > 🟡 > 🔵 > ⚪ > 🟢).

CONTRATO de las funciones contenedor: devuelven `(estado, propio)`.
  - `estado`: código de estado de dominio (agregado del subárbol si está en curso).
  - `propio`: True si el nodo "tiene algo que decir POR SÍ MISMO" (sin hijos →
    TRAMITAR; fase PDTE_CIERRE; solicitud todo-FIN-pero-EN_TRAMITE). El árbol rellena
    el círculo cuando `propio` (nodo expandido) o con el color agregado si está
    colapsado. Las tareas (hojas) van siempre rellenas.
"""
from __future__ import annotations

from typing import Optional

# --- Color por estado (MODELO §2; el front mapea nombre → paleta JdA) ---
# El orden refleja la prioridad: el color es coherente con la urgencia (#558).
COLOR: dict[str, str] = {
    'PENDIENTE_TRAMITAR':              'rojo',
    'PENDIENTE_ESTUDIO':               'rojo',
    'PENDIENTE_REDACTAR':              'rojo',
    'NOTIFICACION_AGOTADA':            'rojo',
    'PENDIENTE_CERRAR':                'naranja',
    'NOTIFICACION_FALLIDA':            'naranja',
    'PENDIENTE_FIRMA':                 'amarillo',
    'PENDIENTE_NOTIFICAR':             'azul',
    'PENDIENTE_RESULTADO_NOTIFICACION': 'azul',
    'PENDIENTE_PLAZOS':                'gris',
    'FIN':                             'verde',
}

# --- Prioridad canónica (1 = más urgente; al agregar se queda el de menor número) ---
# Orden ratificado #558: gradiente de "trabajo del tramitador". Monótono con el color,
# sin empates entre bandas distintas (el ganador de cada celda es determinista).
PRIORIDAD: dict[str, int] = {
    'PENDIENTE_TRAMITAR':               1,   # 🔴 trabajo del tramitador
    'PENDIENTE_ESTUDIO':                2,   # 🔴 (analizar · decidir resultado de fase finalizadora)
    'PENDIENTE_REDACTAR':               3,   # 🔴
    'NOTIFICACION_AGOTADA':             4,   # 🔴 procede publicación en boletín
    'PENDIENTE_CERRAR':                 5,   # 🟠 nuestra gestión (formalizar cierre de fase)
    'NOTIFICACION_FALLIDA':             6,   # 🟠 2º intento de notificación pendiente
    'PENDIENTE_FIRMA':                  7,   # 🟡 no depende del tramitador, pero paraliza si falta
    'PENDIENTE_NOTIFICAR':              8,   # 🔵 a la espera de que el destinatario reciba el envío
    'PENDIENTE_RESULTADO_NOTIFICACION': 9,   # 🔵 envío ya registrado, a la espera del justificante definitivo
    'PENDIENTE_PLAZOS':                 10,  # ⚪ espera pasiva
    'FIN':                              11,  # 🟢
}

# Tipo de documento cuyo consumo distingue PENDIENTE_FIRMA de PENDIENTE_REDACTAR (§3 ELABORAR).
_TIPO_BORRADOR_FIRMA = 'BORRADOR_FIRMA'

# Frase humana de por qué un estado sigue pendiente (#723): fuente única para no
# inventar redacciones nuevas en cada consumidor que necesite explicar un bloqueo
# (hoy: invariantes_esftt._check_completitud_cierre; candidato futuro: el tooltip
# de seguimiento.py, #743).
MOTIVO: dict[str, str] = {
    'PENDIENTE_TRAMITAR':               'falta iniciar o completar una tarea',
    'PENDIENTE_ESTUDIO':                'falta analizar o decidir el resultado',
    # Faltaba hasta #827: su primer consumidor (_check_completitud_cierre) solo
    # explica trámites, y una fase PDTE_CIERRE es precisamente la que sí puede
    # cerrarse. El informe de fin de instrucción sí necesita nombrarla —ahí una
    # fase sin formalizar es lo que impide certificar—, y la redacción vive aquí
    # para que no se invente otra distinta en cada consumidor.
    'PENDIENTE_CERRAR':                 'falta formalizar su cierre con el documento de resultado',
    'PENDIENTE_REDACTAR':               'falta redactar el documento',
    'PENDIENTE_FIRMA':                  'el documento está pendiente de firma',
    'PENDIENTE_NOTIFICAR':              'falta registrar el envío de la notificación',
    'PENDIENTE_RESULTADO_NOTIFICACION': 'falta el justificante definitivo de la notificación',
    'NOTIFICACION_FALLIDA':             'la notificación falló y queda un intento pendiente',
    'NOTIFICACION_AGOTADA':             'la notificación se agotó sin éxito',
    'PENDIENTE_PLAZOS':                 'está a la espera de que venza un plazo',
}


def color(estado: str) -> str:
    """Nombre de color (MODELO §2) de un estado; 'gris' si desconocido."""
    return COLOR.get(estado, 'gris')


def motivo(estado: str) -> str:
    """Frase humana de por qué `estado` sigue pendiente; genérica si es desconocido."""
    return MOTIVO.get(estado, 'hay trabajo pendiente')


def mayor_prioridad(estados: list[str]) -> str:
    """Estado de mayor prioridad (menor número) de una lista no vacía.

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
    Estado de dominio de una tarea según su tipo (MODELO §3).

    `plazo` es el dict ya resuelto por la proyección para ESPERAR_PLAZO
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
    """NOTIFICAR (§3): usa el modelo Notificacion (resultado + numero_intento), anclado
    a la tarea (ADR-034) — se lee vía `tarea.notificacion`, no por el documento
    producido: la fila puede existir (camino A, "Registrar envío") antes de que
    haya ningún documento vinculado.
    """
    if not tarea.documentos_consumidos:
        return 'PENDIENTE_TRAMITAR'        # falta el documento firmado que notificar
    notif = getattr(tarea, 'notificacion', None)
    if notif is None:
        return 'PENDIENTE_NOTIFICAR'       # 🔵 a la espera de que se registre el envío
    if notif.resultado is None:
        return 'PENDIENTE_RESULTADO_NOTIFICACION'  # 🔵 envío registrado, falta el definitivo
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
    if estado_plazo == 'CUMPLIDO':
        # En la práctica no se alcanza: el documento de cumplimiento de toda
        # entrada poblada es el PRODUCIDO, y una tarea con producido está
        # ejecutada — la función ya devolvió FIN antes de llegar aquí. Explícito
        # y no en el `else` porque sí es alcanzable si una entrada declarase el
        # cumplimiento con rol CONSUMIDO: llegó el documento que se esperaba pero
        # la tarea aún no lo ha producido, que es trabajo pendiente, no espera.
        return 'PENDIENTE_TRAMITAR'
    return 'PENDIENTE_PLAZOS'              # ⚪ EN_PLAZO / PROXIMO_VENCER / INDEFINIDO


def _tiene_borrador_firma(tarea) -> bool:
    """True si entre los documentos consumidos hay un PDF de tipo BORRADOR_FIRMA."""
    for doc in tarea.documentos_consumidos:
        td = getattr(doc, 'tipo_doc', None)
        if td and td.codigo == _TIPO_BORRADOR_FIRMA:
            return True
    return False


# ---------------------------------------------------------------------------
# Contenedores (§4) — reciben los estados ya computados de sus hijos
# ---------------------------------------------------------------------------

def estado_tramite(tramite, estados_tareas: list[str]) -> tuple[str, bool]:
    if not tramite.tareas:                 # planificado: sin tareas aún
        return ('PENDIENTE_TRAMITAR', True)
    return (mayor_prioridad(estados_tareas), False)


# ---------------------------------------------------------------------------
# Nivel sintético: organismo (ADR-042) — no es un nivel ESFTT, es un nodo de
# agrupación entre Fase y Trámite derivado de TramiteOrganismo. Mismo patrón de
# hoja/contenedor que el resto: estructura derivada de sus trámites, nunca de
# un campo `resultado` almacenado (ese campo es semántico, no estructural —
# ver docstring de OrganismoExpediente.resultado, DISEÑO_CONSULTAS_ORGANISMOS.md §7).
# ---------------------------------------------------------------------------

def estado_organismo(oe, estados_tramites: list[str]) -> tuple[str, bool]:
    if oe.via == 'declaracion_responsable':  # sin trámites por naturaleza: resuelto de origen
        return ('FIN', True)
    if not estados_tramites:                 # vía consulta, aún sin separata
        return ('PENDIENTE_TRAMITAR', True)
    return (mayor_prioridad(estados_tramites), False)


def estado_fase(fase, estados_tramites: list[str]) -> tuple[str, bool]:
    if fase.planificada:                   # sin trámites aún
        return ('PENDIENTE_TRAMITAR', True)
    if fase.pdte_cierre:                   # todos los trámites cerrados, falta formalizar
        # Solo las finalizadoras requieren resultado_fase_id explícito (el técnico
        # tiene la última palabra). Las intermedias cierran por documento_resultado_id
        # (un certificado de fase); su resultado_fase_id debe quedar NULL → van a CERRAR.
        es_finalizadora = getattr(fase.tipo_fase, 'es_finalizadora', False)
        if es_finalizadora and fase.resultado_fase_id is None:
            return ('PENDIENTE_ESTUDIO', True)   # 🔴 falta decidir resultado
        return ('PENDIENTE_CERRAR', True)        # 🟠 falta documento formalizador
    return (mayor_prioridad(estados_tramites), False)


def estado_solicitud(solicitud, estados_fases: list[str]) -> tuple[str, bool]:
    if not solicitud.fases:                # sin fases aún
        return ('PENDIENTE_TRAMITAR', True)
    if solicitud.estado != 'EN_TRAMITE':   # finalizada / archivada
        return ('FIN', False)
    agregado = mayor_prioridad(estados_fases)
    if agregado == 'FIN':                  # todas las fases en FIN pero sigue EN_TRAMITE
        return ('PENDIENTE_CERRAR', True)  # 🟠 lista para cerrar
    return (agregado, False)


def estado_expediente(expediente, estados_solicitudes: list[str]) -> tuple[str, bool]:
    if not estados_solicitudes:            # expediente sin solicitudes
        return ('PENDIENTE_TRAMITAR', True)
    return (mayor_prioridad(estados_solicitudes), False)
