"""A quién se notifica en cada trámite (#968, N5a-2; ADR-051 §C, §D, §E, §H, §L, §M).

Reúne en un solo sitio lo que BDDAT sabe del destinatario de una notificación:

- **Qué fuentes** notifica cada (tipo de fase, tipo de trámite): catálogo
  `notificacion_fuentes` (`fuentes_del_tramite`, `resolver_fuente`).
- **A quién**, fuente por fuente, leyendo solo tablas que rellenó el usuario
  (§H): la solicitud y su representante (regla de §K), `tramites_organismos`,
  `organismos_expediente` de la solicitud (también los de declaración
  responsable), `interesados_expediente` y `tramites_destinatario` (§L). Nada se
  adivina: si el dato no está, sale un **hueco** («falta elegir…»).
- **¿A quién falta notificar?** y **qué sobra**: solo lee (`estado_del_tramite`).
  De ahí cuelgan el invariante de `Tramite.finalizado` (§E), el rojo propio del
  trámite en el semáforo (`estado_dominio.estado_tramite`) y el relato de
  `informe_instruccion`.
- **El destinatario de un trámite de un solo destinatario** para el escrito del
  ELABORAR (`destinatario_del_tramite`) y el destinatario de cada `NOTIFICAR`
  (`siguiente_destinatario`, `destinatario_de`).

No escribe. Rellenar la `NOTIFICAR`, el botón «añadir las notificaciones que
faltan» y registrar la elección del usuario en `tramites_destinatario` son de
`mutaciones_arbol` (`crear_tarea`, `anadir_notificaciones_que_faltan`,
`fijar_destinatario`, `registrar_destinatario_tramite`), que lo llaman.

**Clave de idempotencia (§D): (trámite, fuente, titular).** El *titular* de una
notificación es a quién se notifica en derecho: el representado cuando se envía
a un representante (`en_nombre_de_entidad_id`), o la propia entidad. Así una
notificación ya hecha al solicitante sigue contando aunque después se le asigne
un representante, y la fila sin justificante se refresca al nuevo receptor.

**Cálculo por solicitud (§M).** `Tramite.finalizado` se evalúa muchas veces al
pintar el árbol. El estado de todos los trámites de una solicitud se calcula de
una vez, cargando cada tabla con una sola consulta, y se guarda en `session.info`
hasta el siguiente `flush`, `commit` o `rollback` de la sesión: nunca se
persiste, y cualquier escritura lo invalida.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import event
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.notificaciones import FUENTES
from app.services import notificaciones as notif_svc

log = logging.getLogger(__name__)

# Fases cuya existencia hace que la resolución notifique al órgano ambiental
# (ADR-051 §C): si la fase existe es porque las reglas del motor la exigieron.
FASES_AMBIENTALES = ('COMPATIBILIDAD_AMBIENTAL', 'FIGURA_AMBIENTAL_EXTERNA',
                     'AAU_AAUS_INTEGRADA')

# Fuentes cuyo destinatario lo elige el usuario en el propio trámite
# (`tramites_destinatario`, §L). `ORGANO_AMBIENTAL` lo es solo en su fase: en la
# resolución sale de la fase ambiental de la solicitud.
_ELEGIDAS_EN_TRAMITE = ('BOLETIN', 'AYUNTAMIENTO', 'MINISTERIO', 'ORGANO_SUPERIOR')

# Rol de la entidad entre las que se elige (§C, tabla de fuentes).
ROL_ELEGIBLE = {
    'BOLETIN': 'publicador',
    'AYUNTAMIENTO': 'publicador',
    'MINISTERIO': 'consultado',
    'ORGANO_SUPERIOR': 'consultado',
    'ORGANO_AMBIENTAL': 'consultado',
}

# Cómo se nombra cada fuente en prosa (relato, mensajes de bloqueo).
ETIQUETA_FUENTE = {
    'SOLICITANTE': 'solicitante',
    'ORGANISMO_DEL_TRAMITE': 'organismo del trámite',
    'ORGANISMOS_CONSULTADOS': 'organismo consultado',
    'ORGANO_AMBIENTAL': 'órgano ambiental',
    'PROPIETARIOS_DUP': 'titular de bienes y derechos',
    'INTERESADOS_RECONOCIDOS': 'interesado reconocido',
    'BOLETIN': 'boletín oficial',
    'AYUNTAMIENTO': 'ayuntamiento',
    'MINISTERIO': 'ministerio',
    'ORGANO_SUPERIOR': 'órgano superior',
}

_TIPO_ORIGEN_INTERESADO = {
    'PROPIETARIOS_DUP': 'DUP',
    'INTERESADOS_RECONOCIDOS': 'INTERESADO_RECONOCIDO',
}

_CLAVE_CACHE = 'bddat_destinatarios_notificacion'


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Esperado:
    """Alguien a quien hay que notificar en el trámite, por una fuente.

    `titular_id` es a quién se notifica en derecho (clave de idempotencia);
    `receptor_id`, a quién se envía (su representante, o él mismo).
    `direccion_id` es la dirección que fijó el dato del usuario
    (`organismos_expediente.direccion_notificacion_id`); sin ella se usa la del
    rol de la fuente."""
    fuente: str
    titular_id: int
    receptor_id: int
    direccion_id: Optional[int] = None


@dataclass(frozen=True)
class Falta:
    """Una notificación que falta. Sin `titular_id` es un **hueco**: la fuente
    exige a alguien que aún no se ha elegido; `motivo` dice dónde elegirlo."""
    fuente: str
    titular_id: Optional[int] = None
    nombre: Optional[str] = None
    motivo: Optional[str] = None

    @property
    def texto(self) -> str:
        etiqueta = ETIQUETA_FUENTE.get(self.fuente, self.fuente)
        if self.titular_id is None:
            return f'Falta elegir a quién notificar como {etiqueta}: {self.motivo}.'
        return f'Falta notificar a {self.nombre or f"la entidad #{self.titular_id}"} ({etiqueta}).'


@dataclass
class EstadoDestinatarios:
    """Lo que un trámite con fuentes dice de sus notificaciones (§D, §E)."""
    fuentes: tuple
    esperados: list = field(default_factory=list)    # [Esperado]
    faltan: list = field(default_factory=list)       # [Falta]
    sobran: list = field(default_factory=list)       # [Tarea]
    huecos: dict = field(default_factory=dict)       # fuente → motivo

    @property
    def completo(self) -> bool:
        return not self.faltan and not self.sobran

    def textos(self) -> list[str]:
        """Por qué el trámite no está terminado, en prosa: «falta notificar a
        X», «sobra la notificación a Y»."""
        lineas = [f.texto for f in self.faltan]
        for tarea in self.sobran:
            notif = tarea.notificacion
            nombre = (notif.dest_nombre if notif is not None and notif.dest_nombre
                      else 'un destinatario sin fijar')
            etiqueta = ETIQUETA_FUENTE.get(notif.fuente, notif.fuente) if notif else '?'
            lineas.append(
                f'Sobra la notificación a {nombre} ({etiqueta}): ya no sale de su origen. '
                f'Corrija el origen y borre la tarea.')
        return lineas


# ---------------------------------------------------------------------------
# Caché de la sesión (§M)
# ---------------------------------------------------------------------------

@event.listens_for(Session, 'after_flush')
@event.listens_for(Session, 'after_commit')
@event.listens_for(Session, 'after_rollback')
@event.listens_for(Session, 'after_soft_rollback')
def _invalidar(session, *_args):
    session.info.pop(_CLAVE_CACHE, None)


def _cache() -> dict:
    from app import db
    return db.session.info.setdefault(_CLAVE_CACHE, {})


# ---------------------------------------------------------------------------
# Catálogo de fuentes
# ---------------------------------------------------------------------------

def _catalogo() -> dict:
    """{(tipo_fase_id, tipo_tramite_id): (fuente, …)} en su orden. Una sola
    consulta por sesión y escritura. Sin la tabla, vacío y aviso (#347)."""
    cache = _cache()
    if 'catalogo' in cache:
        return cache['catalogo']
    from app import db
    from app.models.notificacion_fuentes import NotificacionFuente
    try:
        filas = (NotificacionFuente.query
                 .order_by(NotificacionFuente.tipo_fase_id, NotificacionFuente.tipo_tramite_id,
                           NotificacionFuente.orden)
                 .with_entities(NotificacionFuente.tipo_fase_id,
                                NotificacionFuente.tipo_tramite_id,
                                NotificacionFuente.fuente)
                 .all())
    except (OperationalError, ProgrammingError):
        log.warning('notificacion_fuentes no disponible: ningún trámite tiene fuentes')
        db.session.rollback()
        return {}
    catalogo: dict = {}
    for tf_id, tt_id, fuente in filas:
        catalogo.setdefault((tf_id, tt_id), []).append(fuente)
    catalogo = {k: tuple(v) for k, v in catalogo.items()}
    _cache()['catalogo'] = catalogo
    return catalogo


def fuentes_del_tramite(tramite) -> Optional[tuple]:
    """Fuentes de `tramite` según `notificacion_fuentes`, o `None` si su (fase,
    trámite) no tiene ninguna: una `NOTIFICAR` ahí está fuera de la secuencia
    del catálogo y su fuente se indica a mano."""
    return _catalogo().get((tramite.fase.tipo_fase_id, tramite.tipo_tramite_id))


def resolver_fuente(tramite, fuente: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """(fuente, error) de una `NOTIFICAR` nueva en `tramite` (ADR-051 §B): con
    una sola fuente la toma sola; con varias, o sin declarar, hay que indicarla.
    Una fuente indicada tiene que ser de las del trámite."""
    admitidas = fuentes_del_tramite(tramite)
    if fuente is not None:
        if fuente not in (admitidas or FUENTES):
            opciones = ', '.join(admitidas or FUENTES)
            return None, f'Fuente «{fuente}» no válida para este trámite. Opciones: {opciones}.'
        return fuente, None
    if admitidas is not None and len(admitidas) == 1:
        return admitidas[0], None
    opciones = ', '.join(admitidas or FUENTES)
    return None, (f'Indica la fuente de la notificación (a quién y por qué se notifica). '
                  f'Opciones: {opciones}.')


def es_elegida_en_tramite(tramite, fuente: str) -> bool:
    """El destinatario de esta fuente lo elige el usuario en el propio trámite
    (`tramites_destinatario`, §L)."""
    if fuente in _ELEGIDAS_EN_TRAMITE:
        return True
    return fuente == 'ORGANO_AMBIENTAL' and _codigo_fase(tramite.fase) in FASES_AMBIENTALES


def tiene_elaborar(tramite) -> bool:
    """La secuencia del tipo de trámite (`tramites_tareas`) lleva ELABORAR: el
    destinatario se decide al elaborar, no en la `NOTIFICAR` (§H)."""
    from app.models.tipos_tareas import TipoTarea
    from app.models.tramites_tareas import TramiteTarea
    try:
        return (TramiteTarea.query
                .join(TipoTarea, TipoTarea.id == TramiteTarea.tipo_tarea_id)
                .filter(TramiteTarea.tipo_tramite_id == tramite.tipo_tramite_id,
                        TipoTarea.codigo == 'ELABORAR')
                .first()) is not None
    except (OperationalError, ProgrammingError):
        log.warning('tramites_tareas no disponible: se supone trámite sin ELABORAR')
        return False


def entidades_elegibles(fuente: str) -> list:
    """Entidades activas entre las que el usuario elige para `fuente` (§C):
    las de rol publicador para boletines y ayuntamientos; las de rol consultado
    para ministerio, órgano superior y órgano ambiental."""
    from app.models.entidad import Entidad
    rol = ROL_ELEGIBLE.get(fuente)
    if rol is None:
        return []
    columna = Entidad.rol_publicador if rol == 'publicador' else Entidad.rol_consultado
    return (Entidad.query.filter(columna.is_(True), Entidad.activo.is_(True))
            .order_by(Entidad.nombre_completo).all())


# ---------------------------------------------------------------------------
# Precarga por solicitud (§M)
# ---------------------------------------------------------------------------

def _codigo_fase(fase) -> Optional[str]:
    return fase.tipo_fase.codigo if fase.tipo_fase is not None else None


def _es_notificar(tarea) -> bool:
    return tarea.tipo_tarea is not None and tarea.tipo_tarea.codigo == 'NOTIFICAR'


def _titular(notif) -> Optional[int]:
    return notif.en_nombre_de_entidad_id or notif.entidad_id


class _Precarga:
    """Las tablas de una solicitud, cada una con una sola consulta y solo si
    alguna fuente la necesita."""

    def __init__(self, solicitud, catalogo: dict):
        self.solicitud = solicitud
        self.catalogo = catalogo
        self.fases = list(solicitud.fases)
        self.tramites = [t for f in self.fases for t in f.tramites]
        self._ids_tramites = [t.id for t in self.tramites]
        self._elegidos = None
        self._organismo_del_tramite = None
        self._consultados = None
        self._interesados = None
        self._escapes = None

    @property
    def elegidos(self) -> dict:
        """{tramite_id: TramiteDestinatario}"""
        if self._elegidos is None:
            from app.models.tramites_destinatario import TramiteDestinatario
            self._elegidos = {
                r.tramite_id: r for r in TramiteDestinatario.query.filter(
                    TramiteDestinatario.tramite_id.in_(self._ids_tramites)).all()
            } if self._ids_tramites else {}
        return self._elegidos

    @property
    def organismo_del_tramite(self) -> dict:
        """{tramite_id: (organismo_id, direccion_notificacion_id)}"""
        if self._organismo_del_tramite is None:
            from app import db
            from app.models.organismos_expediente import OrganismoExpediente
            from app.models.tramites_organismos import TramiteOrganismo
            filas = (db.session.query(TramiteOrganismo.tramite_id,
                                      OrganismoExpediente.organismo_id,
                                      OrganismoExpediente.direccion_notificacion_id)
                     .join(OrganismoExpediente,
                           OrganismoExpediente.id == TramiteOrganismo.organismo_expediente_id)
                     .filter(TramiteOrganismo.tramite_id.in_(self._ids_tramites))
                     .all()) if self._ids_tramites else []
            self._organismo_del_tramite = {t: (o, d) for t, o, d in filas}
        return self._organismo_del_tramite

    @property
    def consultados(self) -> list:
        """[(organismo_id, direccion_notificacion_id)] de las consultas de la
        solicitud, sin repetir organismo (la fila más reciente manda)."""
        if self._consultados is None:
            from app.models.organismos_expediente import OrganismoExpediente
            ids_fases = [f.id for f in self.fases]
            filas = (OrganismoExpediente.query
                     .filter(OrganismoExpediente.fase_id.in_(ids_fases))
                     .order_by(OrganismoExpediente.id)
                     .all()) if ids_fases else []
            por_organismo = {}
            for oe in filas:
                por_organismo[oe.organismo_id] = oe.direccion_notificacion_id
            self._consultados = list(por_organismo.items())
        return self._consultados

    @property
    def interesados(self) -> list:
        """[(tipo_origen, entidad_id)] activos con entidad, del expediente."""
        if self._interesados is None:
            from app.models.interesados_expediente import InteresadoExpediente
            filas = (InteresadoExpediente.query
                     .filter(InteresadoExpediente.expediente_id == self.solicitud.expediente_id,
                             InteresadoExpediente.activo.is_(True),
                             InteresadoExpediente.entidad_id.isnot(None),
                             InteresadoExpediente.tipo_origen.in_(
                                 tuple(_TIPO_ORIGEN_INTERESADO.values())))
                     .order_by(InteresadoExpediente.id)
                     .all())
            self._interesados = [(i.tipo_origen, i.entidad_id) for i in filas]
        return self._interesados

    def escapes(self) -> set:
        """Ids de las `NOTIFICAR` de la solicitud que avanzaron sin destinatario
        por escape (§B). Una consulta, solo entre las que no tienen entidad."""
        if self._escapes is None:
            from app.models.bitacora import Bitacora
            ids = [ta.id for tr in self.tramites
                   if (tr.fase.tipo_fase_id, tr.tipo_tramite_id) in self.catalogo
                   for ta in tr.tareas
                   if _es_notificar(ta) and not (ta.notificacion and ta.notificacion.entidad_id)]
            self._escapes = set()
            if ids:
                for e in Bitacora.query.filter(Bitacora.tabla == 'tareas',
                                               Bitacora.registro_id.in_(ids)).all():
                    if (e.detalle or {}).get('accion') == notif_svc.ACCION_SIN_DESTINATARIO:
                        self._escapes.add(e.registro_id)
        return self._escapes


# ---------------------------------------------------------------------------
# De dónde sale cada fuente (§C)
# ---------------------------------------------------------------------------

def _elegido_como_esperado(fuente, elegido) -> Esperado:
    if elegido.representante_entidad_id:
        return Esperado(fuente, elegido.entidad_id, elegido.representante_entidad_id)
    return Esperado(fuente, elegido.entidad_id, elegido.entidad_id)


def _resolver(fuente: str, tramite, p: _Precarga) -> tuple[list, Optional[str]]:
    """(esperados, hueco) de una fuente en un trámite. `hueco` es el motivo si
    la fuente exige a alguien que aún no se ha elegido."""
    solicitud = p.solicitud

    if fuente == 'SOLICITANTE':
        if solicitud.entidad_id is None:
            return [], 'la solicitud no tiene solicitante'
        receptor = solicitud.representante_entidad_id or solicitud.entidad_id
        return [Esperado(fuente, solicitud.entidad_id, receptor)], None

    if fuente == 'ORGANISMO_DEL_TRAMITE':
        ligado = p.organismo_del_tramite.get(tramite.id)
        if ligado is None:
            return [], 'el trámite no está ligado a ningún organismo consultado'
        organismo_id, direccion_id = ligado
        return [Esperado(fuente, organismo_id, organismo_id, direccion_id)], None

    if fuente == 'ORGANISMOS_CONSULTADOS':
        return [Esperado(fuente, o, o, d) for o, d in p.consultados], None

    if fuente in _TIPO_ORIGEN_INTERESADO:
        origen = _TIPO_ORIGEN_INTERESADO[fuente]
        vistos, esperados = set(), []
        for tipo, entidad_id in p.interesados:
            if tipo == origen and entidad_id not in vistos:
                vistos.add(entidad_id)
                esperados.append(Esperado(fuente, entidad_id, entidad_id))
        return esperados, None

    if es_elegida_en_tramite(tramite, fuente):
        elegido = p.elegidos.get(tramite.id)
        if elegido is None:
            donde = ('elíjalo al elaborar el escrito del trámite' if tiene_elaborar(tramite)
                     else 'elíjalo en la tarea de notificar')
            return [], f'no se ha elegido el destinatario del trámite; {donde}'
        return [_elegido_como_esperado(fuente, elegido)], None

    if fuente == 'ORGANO_AMBIENTAL':
        return _organo_ambiental_de_la_solicitud(p)

    log.warning('Fuente %r sin regla de resolución', fuente)
    return [], f'la fuente {fuente} no sabe calcularse'


def _organo_ambiental_de_la_solicitud(p: _Precarga) -> tuple[list, Optional[str]]:
    """En la resolución, el órgano ambiental de la fase ambiental de la
    solicitud, si la tiene (§C): el elegido en sus trámites
    (`tramites_destinatario`) o, si alguno no lo guardó, al que se le notificó."""
    fases = [f for f in p.fases if _codigo_fase(f) in FASES_AMBIENTALES]
    if not fases:
        return [], None
    catalogo = _catalogo()
    vistos, esperados = set(), []
    for fase in fases:
        for tramite in sorted(fase.tramites, key=lambda t: t.id):
            if 'ORGANO_AMBIENTAL' not in catalogo.get((fase.tipo_fase_id,
                                                       tramite.tipo_tramite_id), ()):
                continue
            candidatos = []
            elegido = p.elegidos.get(tramite.id)
            if elegido is not None:
                candidatos.append(_elegido_como_esperado('ORGANO_AMBIENTAL', elegido))
            for ta in tramite.tareas:
                notif = ta.notificacion if _es_notificar(ta) else None
                if notif is not None and notif.fuente == 'ORGANO_AMBIENTAL' and notif.entidad_id:
                    candidatos.append(Esperado('ORGANO_AMBIENTAL', _titular(notif),
                                               notif.entidad_id))
            for e in candidatos:
                if e.titular_id not in vistos:
                    vistos.add(e.titular_id)
                    esperados.append(e)
    if not esperados:
        return [], ('la solicitud tiene fase ambiental y en ella no consta a qué órgano '
                    'ambiental se dirigió')
    return esperados, None


# ---------------------------------------------------------------------------
# «¿A quién falta notificar?» y sobrantes (§D)
# ---------------------------------------------------------------------------

def _estado(tramite, fuentes: tuple, p: _Precarga) -> EstadoDestinatarios:
    estado = EstadoDestinatarios(fuentes=fuentes)
    for fuente in fuentes:
        esperados, hueco = _resolver(fuente, tramite, p)
        estado.esperados.extend(esperados)
        if hueco is not None:
            estado.huecos[fuente] = hueco

    claves = {(e.fuente, e.titular_id) for e in estado.esperados}
    cubiertos = set()
    vacias = []           # NOTIFICAR con fuente y sin entidad, en orden
    for ta in sorted(tramite.tareas, key=lambda t: t.id):
        if not _es_notificar(ta) or ta.notificacion is None:
            continue
        notif = ta.notificacion
        if notif.fuente not in fuentes:
            estado.sobran.append(ta)
            continue
        if notif.entidad_id is None:
            vacias.append(ta)
            continue
        clave = (notif.fuente, _titular(notif))
        if clave in claves and clave not in cubiertos:
            cubiertos.add(clave)
        else:
            estado.sobran.append(ta)

    pendientes = [e for e in estado.esperados if (e.fuente, e.titular_id) not in cubiertos]
    huecos = dict(estado.huecos)
    escapes = p.escapes() if vacias else set()
    for ta in vacias:
        fuente = ta.notificacion.fuente
        # Una NOTIFICAR sin entidad ocupa el sitio de alguien de su fuente: si
        # avanzó por escape, lo cubre (se relata como salvada, §B); si no, está
        # por rellenar y ese alguien sigue faltando. Sin nadie a quien ocupar,
        # sobra.
        i = next((i for i, e in enumerate(pendientes) if e.fuente == fuente), None)
        if i is not None:
            if ta.id in escapes:
                pendientes.pop(i)
            continue
        if fuente in huecos:
            if ta.id in escapes:
                huecos.pop(fuente)
            continue
        if ta.id not in escapes:
            estado.sobran.append(ta)

    estado.faltan = ([Falta(e.fuente, e.titular_id) for e in pendientes]
                     + [Falta(f, motivo=m) for f, m in huecos.items()])
    return estado


def _poner_nombres(estados: dict) -> None:
    faltan = [f for e in estados.values() if e is not None for f in e.faltan
              if f.titular_id is not None]
    if not faltan:
        return
    from app.models.entidad import Entidad
    nombres = dict(Entidad.query.filter(Entidad.id.in_({f.titular_id for f in faltan}))
                   .with_entities(Entidad.id, Entidad.nombre_completo).all())
    for estado in estados.values():
        if estado is None:
            continue
        estado.faltan = [Falta(f.fuente, f.titular_id, nombres.get(f.titular_id), f.motivo)
                         if f.titular_id is not None else f
                         for f in estado.faltan]


def estado_de_la_solicitud(solicitud) -> dict:
    """{tramite_id: EstadoDestinatarios | None} de todos los trámites de la
    solicitud, calculado de una vez (§M). `None` = trámite sin fuentes: el
    invariante no le aplica."""
    cache = _cache().setdefault('solicitudes', {})
    if solicitud.id in cache:
        return cache[solicitud.id]
    catalogo = _catalogo()
    p = _Precarga(solicitud, catalogo)
    estados = {}
    for tramite in p.tramites:
        fuentes = catalogo.get((tramite.fase.tipo_fase_id, tramite.tipo_tramite_id))
        estados[tramite.id] = _estado(tramite, fuentes, p) if fuentes else None
    _poner_nombres(estados)
    # El cálculo puede haber lanzado consultas con autoflush: se guarda al final.
    _cache().setdefault('solicitudes', {})[solicitud.id] = estados
    return estados


def estado_del_tramite(tramite) -> Optional[EstadoDestinatarios]:
    """«¿A quién falta notificar?» y sobrantes de un trámite, o `None` si no
    tiene fuentes. Solo lee."""
    # Un trámite sin persistir (o un stub de test unitario) no tiene solicitud
    # que cargar: no hay nada que vigilar todavía.
    if getattr(tramite, 'id', None) is None or not fuentes_del_tramite(tramite):
        return None
    return estado_de_la_solicitud(tramite.fase.solicitud).get(tramite.id)


def completo(tramite) -> bool:
    """Nadie falta ni sobra (§E): lo que añade este issue a `Tramite.finalizado`."""
    estado = estado_del_tramite(tramite)
    return estado is None or estado.completo


def motivos(tramite) -> list[str]:
    """Por qué el trámite no está completo en cuanto a sus notificaciones."""
    estado = estado_del_tramite(tramite)
    return estado.textos() if estado is not None else []


# ---------------------------------------------------------------------------
# El destinatario concreto: para rellenar una NOTIFICAR y para el escrito
# ---------------------------------------------------------------------------

def como_destinatario(esperado: Esperado) -> notif_svc.Destinatario:
    """El `Destinatario` que se copia en la fila (§B): receptor, en nombre de
    quién y dirección — la del dato del usuario si la hay y sigue activa, o la
    del rol de la fuente, o la principal."""
    from app import db
    from app.models.direccion_notificacion import DireccionNotificacion
    from app.models.entidad import Entidad
    receptor = db.session.get(Entidad, esperado.receptor_id)
    en_nombre_de = (db.session.get(Entidad, esperado.titular_id)
                    if esperado.titular_id != esperado.receptor_id else None)
    direccion = None
    if esperado.direccion_id is not None:
        direccion = db.session.get(DireccionNotificacion, esperado.direccion_id)
        if direccion is not None and not direccion.activo:
            direccion = None
    if direccion is None:
        direccion = notif_svc.direccion_de_rol(esperado.receptor_id, esperado.fuente)
    return notif_svc.Destinatario(entidad=receptor, en_nombre_de=en_nombre_de,
                                  direccion=direccion)


def esperado_de(tarea) -> Optional[Esperado]:
    """El esperado que corresponde a una `NOTIFICAR` que ya tiene destinatario
    (misma fuente y titular), o `None` si sobra o el trámite no tiene fuentes."""
    notif = tarea.notificacion
    estado = estado_del_tramite(tarea.tramite)
    if estado is None or notif is None or notif.entidad_id is None:
        return None
    titular = _titular(notif)
    return next((e for e in estado.esperados
                 if e.fuente == notif.fuente and e.titular_id == titular), None)


def siguiente_esperado(tramite, fuente: str) -> Optional[Esperado]:
    """El primero de `fuente` a quien aún falta notificar en el trámite."""
    estado = estado_del_tramite(tramite)
    if estado is None:
        return None
    falta = next((f for f in estado.faltan if f.fuente == fuente and f.titular_id is not None),
                 None)
    if falta is None:
        return None
    return next(e for e in estado.esperados
                if e.fuente == fuente and e.titular_id == falta.titular_id)


@dataclass(frozen=True)
class DestinatarioTramite:
    """El destinatario de un trámite de un solo destinatario (§H): el que
    imprime el escrito del ELABORAR y con el que nace su `NOTIFICAR`.

    - `destinatario` resuelto, o `None`.
    - Sin él, `motivo` dice por qué y, si lo elige el usuario, `elegibles` son
      las entidades del rol entre las que elegir (`fuente` dice cuál)."""
    fuente: Optional[str]
    destinatario: Optional[notif_svc.Destinatario] = None
    motivo: Optional[str] = None
    elegibles: tuple = ()

    @property
    def aplica(self) -> bool:
        return self.fuente is not None


def destinatario_del_tramite(tramite) -> DestinatarioTramite:
    """A quién va el escrito del trámite (§H). Solo en trámites con una sola
    fuente y un solo destinatario: la ELABORACION de las finalizadoras no tiene
    fuentes (no imprime destinatario) y la NOTIFICACION de la resolución, con
    varias, no tiene ELABORAR."""
    fuentes = fuentes_del_tramite(tramite)
    if not fuentes or len(fuentes) != 1:
        return DestinatarioTramite(fuente=None)
    fuente = fuentes[0]
    estado = estado_del_tramite(tramite)
    esperados = [e for e in estado.esperados if e.fuente == fuente] if estado else []
    if len(esperados) == 1:
        return DestinatarioTramite(fuente=fuente, destinatario=como_destinatario(esperados[0]))
    if len(esperados) > 1:
        return DestinatarioTramite(
            fuente=fuente, motivo='el trámite tiene más de un destinatario y el escrito es '
                                  'para uno solo')
    motivo = (estado.huecos.get(fuente) if estado else None) or 'no hay a quién dirigirlo'
    elegibles = tuple(entidades_elegibles(fuente)) if es_elegida_en_tramite(tramite, fuente) else ()
    return DestinatarioTramite(fuente=fuente, motivo=motivo, elegibles=elegibles)
