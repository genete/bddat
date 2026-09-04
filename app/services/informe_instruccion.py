"""
informe_instruccion.py — «¿Cómo va esto?» sobre la instrucción de una solicitud.

ADR-043 §E/§E bis. El técnico puede preguntar en cualquier momento, desde el
primer día, y la respuesta es siempre un informe: qué falta y por qué, qué se
salvó bajo criterio propio, y el relato de lo instruido hasta ahora. Solo cuando
el informe sale sin pendientes ese mismo informe se consolida en el
CERT_FIN_INSTRUCCION (`app/services/cert_fin_instruccion.py`). Aquí no hay
efectos: este módulo mira y redacta, nunca escribe.

LO QUE SUBE AGUAS ARRIBA ES PROSA, NO DATO EN BRUTO (decisión de #827)
=====================================================================

Cada nodo entrega un `Bloque` **ya redactado por él**, y su padre recibe bloques
—no datos— y decide si los cita, los resume en una línea o los ignora. La tarea
sabe de tareas, el trámite sabe tratar sus tareas y la fase sus trámites; el
tronco no redacta nada del árbol, solo concatena.

El motivo no es de estilo. Si lo que subiera fuese dato en bruto, el tronco
tendría que **entenderlo** para redactarlo —saber que esta ronda de consultas se
hizo sobre el Anexo 1 y aquella sobre el proyecto original—, y eso devuelve la
especialización al tronco por la puerta de atrás: exactamente lo que §E bis
prohíbe («no lo produce un script que barre el árbol conociendo las
particularidades de cada tipo»). Con la prosa subiendo ya escrita, el punto de
extensión de #819 es una sola función —`bloque_fase`, por tipo de fase— y nada
más se entera.

Lo único que el tronco interpreta es `Bloque.categoria`, que es agnóstica:
cualquier fase sabe decir «esto impide cerrar» sin que el tronco sepa por qué.
Es el mismo reparto que `estado_dominio` hace con `(estado, propio)` — un dato
mínimo para decidir, todo lo demás decoración de quien lo muestra.

REDACTADO, NO MAQUETADO
=======================

`Bloque.relato` y `Bloque.pendiente` son párrafos de texto llano, sin markup. Sus
destinos son tres y ninguno comparte motor de render: el PDF del certificado
(reportlab), el modal del inspector (HTML) y —previsto desde ahora— el contexto
del escrito de resolución, que convertirá estos mismos párrafos en tokens de
plantilla en vez de recomponer el relato por su cuenta (#430, ADR-035). Si el
nodo maquetara, se ataría al primero de los tres.

LAS TRES CATEGORÍAS (§E)
========================

- `PENDIENTE` — algo no pasa y nada lo explica. Impide consolidar.
- `SALVADO`   — el acto se realizó por la vía de escape, con justificación en
                bitácora. Se relata en el certificado y **no impide**: el criterio
                motivado del tramitador es superior a la regla —para eso existe el
                escape— y por eso queda escrito y no escondido. Quien redacta la
                resolución tiene el certificado delante por catálogo, así que ve
                las desviaciones que debe motivar.
- `PASA`      — nada que objetar; solo aporta relato.

El escape lo relata **el nodo donde ocurrió**, no el tronco: la bitácora guarda
`(tabla, registro_id)` y esos ids son los del propio nodo. Las dos listas van
separadas y sin correlacionar escape↔regla — el registro no guarda qué regla se
esquivó y `evaluar()` cortocircuita en la primera, así que en el momento del
escape ni siquiera se conocen todas. Correlacionarlas es de #614.

LAS TRES FUENTES QUE NO SE REEMPLAZAN (§E)
==========================================

1. El árbol, consumiendo `estado_dominio` en vez de reimplementarlo: es el núcleo
   único de las reglas de estado y duplicarlo repetiría la divergencia que #558
   tuvo que unificar.
2. El motor, **una sola vez** sobre el acto que importa: crear la fase
   finalizadora. Sus reglas de precedencia ya son el veredicto normativo sobre si
   la instrucción está lista. No se pregunta nodo a nodo: las reglas son de un
   acto, no de un nodo, y re-evaluarlas sobre lo ya creado es arqueología.
3. El invariante estructural del emisor, que aquí no hace falta invocar porque
   sus dos supuestos ya los dice el árbol por sí mismo —una fase de instrucción
   sin cerrar levanta su propio `PENDIENTE`, y la solicitud sin ninguna fase habla
   de sí misma—. Sigue existiendo como puerta cerrada en `invariantes_esftt` y la
   consolidación lo comprueba igualmente antes de crear nada: es quien tiene la
   última palabra, y así no puede haber dos verdades que diverjan.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.services import estado_dominio as sem

log = logging.getLogger(__name__)


# --- Categorías (§E) -------------------------------------------------------
PENDIENTE = 'PENDIENTE'
SALVADO   = 'SALVADO'
PASA      = 'PASA'

# Qué fase finalizadora habilita el certificado en cada solicitud — es el sujeto
# contra el que se audita. Las dos finalizadoras nunca conviven en la misma
# solicitud (ADR-043 §C): RECONOCIMIENTO_INTERESADO es la de la solicitud
# INTERESADO, una solicitud paralela con vida propia; el resto resuelve por
# RESOLUCION. Este mapa y las dos filas de `reglas_motor` dicen lo mismo por
# duplicado a propósito —allí el sujeto documenta la regla para el supervisor,
# aquí se elige contra qué auditar—, y el aviso de arranque de
# `app/checks/catalogo_requerido.py` vigila que no diverjan si aparece una tercera.
_FASE_FINALIZADORA_POR_SIGLAS = {'INTERESADO': 'RECONOCIMIENTO_INTERESADO'}
_FASE_FINALIZADORA_DEFECTO = 'RESOLUCION'


# ---------------------------------------------------------------------------
# Contrato
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Bloque:
    """Lo que un nodo tiene que decir, ya redactado por quien sabe decirlo.

    `categoria` es lo único que el tronco interpreta. `relato` va al certificado
    (y al contexto de la resolución); `pendiente` va al modal del inspector: son
    dos registros distintos —el certificado narra lo instruido, el modal enumera
    lo que falta— y por eso el nodo escribe los dos, en vez de que el destino
    reescriba el que no le sirve.

    `ambito` es el hueco de #819: sobre qué conjunto documental se hizo esto
    (Proyecto, Proyecto + Anexo 1…). Hoy siempre None, que significa «el proyecto
    del expediente». Admitirlo desde ahora es barato; añadirlo después, no.
    """
    categoria: str
    titulo:    str
    relato:    tuple[str, ...] = ()
    pendiente: tuple[str, ...] = ()
    nodo:      Optional[tuple[str, int]] = None
    ambito:    Optional[str] = None

    def a_dict(self) -> dict:
        return {
            'categoria': self.categoria,
            'titulo': self.titulo,
            'relato': list(self.relato),
            'pendiente': list(self.pendiente),
            'nodo': {'tipo': self.nodo[0], 'id': self.nodo[1]} if self.nodo else None,
            'ambito': self.ambito,
        }


@dataclass
class Informe:
    """El informe completo de una solicitud: bloques + la auditoría que se congela.

    `auditoria` es el `AuditoriaResult` del motor sobre CREAR la fase finalizadora.
    Viaja aquí porque el certificado la congela tal cual (ADR-043 §E ter) y porque
    reevaluarla en el consolidador sería preguntar dos veces lo mismo.
    """
    solicitud_id: int
    bloques:      list = field(default_factory=list)
    auditoria:    object = None
    sujeto:       str = ''
    # Reglas que este acto satisface por definición (las del art. 82.1): no cuentan
    # como pendiente y el PDF las marca aparte en vez de listarlas como bloqueo.
    reglas_del_acto: tuple = ()

    @property
    def limpio(self) -> bool:
        """True si nada impide consolidar. Se decide sin leer una sola frase."""
        return not any(b.categoria == PENDIENTE for b in self.bloques)

    @property
    def pendientes(self) -> list:
        return [b for b in self.bloques if b.categoria == PENDIENTE]

    @property
    def salvados(self) -> list:
        return [b for b in self.bloques if b.categoria == SALVADO]

    def a_dict(self) -> dict:
        return {
            'limpio': self.limpio,
            'solicitud_id': self.solicitud_id,
            'sujeto': self.sujeto,
            'bloques': [b.a_dict() for b in self.bloques],
            'pendientes': [b.a_dict() for b in self.pendientes],
            'salvados': [b.a_dict() for b in self.salvados],
        }


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def codigo_fase_finalizadora(solicitud) -> str:
    """Código del `TipoFase` finalizador que esta solicitud abrirá."""
    tipo_sol = solicitud.tipo_solicitud
    siglas = tipo_sol.siglas if tipo_sol else None
    return _FASE_FINALIZADORA_POR_SIGLAS.get(siglas, _FASE_FINALIZADORA_DEFECTO)


def revisar(solicitud) -> Informe:
    """Informe de la instrucción de `solicitud`. Sin efectos: se puede repetir.

    Orden: primero la solicitud habla de sí misma, después cada fase de
    instrucción, y al final el motor. Las fases finalizadoras quedan fuera del
    barrido —«instruidos los procedimientos» no abarca la fase que resuelve, y
    contarla dejaría el certificado inemitible para siempre en cuanto alguien la
    abriera por la vía de escape que §A admite, que es justo el estado en que #814
    encontró AT-15—.
    """
    escapes = _escapes_del_arbol(solicitud)

    _precargar(solicitud)

    instruccion = [
        f for f in sorted(solicitud.fases, key=lambda f: f.id)
        if f.tipo_fase and not f.tipo_fase.es_finalizadora
    ]

    bloques_fases = []
    estados_fases = []
    for fase in instruccion:
        estado, bloque = _fase(fase, escapes)
        estados_fases.append(estado)
        if bloque is not None:
            bloques_fases.append(bloque)

    bloques = []
    propio = _solicitud(solicitud, instruccion, estados_fases, escapes)
    if propio is not None:
        bloques.append(propio)
    bloques.extend(bloques_fases)

    auditoria, sujeto, del_acto, bloques_motor = _veredicto_del_motor(solicitud)
    bloques.extend(bloques_motor)

    return Informe(
        solicitud_id=solicitud.id,
        bloques=bloques,
        auditoria=auditoria,
        sujeto=sujeto,
        reglas_del_acto=del_acto,
    )


def _precargar(solicitud) -> None:
    """Trae de una vez el árbol de la solicitud con sus documentos.

    El barrido toca todos los nodos y el documento producido de cada tarea, así
    que sin esto son cientos de consultas en una solicitud grande. Reutiliza el
    eager-loading del árbol (`arbol_expediente.opciones_solicitud`) — mismo grafo,
    un solo mapa que mantener— y devuelve la misma instancia por el identity map
    de la sesión, así que el llamador sigue trabajando con su objeto.

    Defensivo: si falla, el informe se calcula igual, solo que más despacio.
    """
    from app.models.solicitudes import Solicitud
    from app.services.arbol_expediente import opciones_solicitud
    try:
        Solicitud.query.options(*opciones_solicitud()).get(solicitud.id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('informe_instruccion: no se pudo precargar la solicitud %s — %s',
                    solicitud.id, exc)


def bloque_fase(fase, escapes: Optional[dict] = None) -> Optional[Bloque]:
    """Lo que una fase tiene que decir, redactado por ella.

    **Punto de extensión de #819.** Hoy toda fase se redacta igual: nombre, si
    está cerrada y cuándo, y lo que digan sus trámites. Cuando #819 defina el
    vínculo fase↔conjunto documental, aquí es donde una `CONSULTAS` con dos
    vueltas dirá sobre qué versión del proyecto se hizo cada una — y el registry
    por código de tipo sustituirá a esta única implementación genérica. El resto
    del módulo no se entera: recibe un `Bloque` igual que ahora.
    """
    _, bloque = _fase(fase, escapes if escapes is not None else {})
    return bloque


def bloque_tramite(tramite, escapes: Optional[dict] = None) -> Optional[Bloque]:
    """Lo que un trámite tiene que decir, con lo de sus tareas ya citado por él."""
    _, bloque = _tramite(tramite, escapes if escapes is not None else {})
    return bloque


def bloque_tarea(tarea, escapes: Optional[dict] = None) -> Optional[Bloque]:
    """Lo que una tarea tiene que decir. None = no tiene nada que decir."""
    _, bloque = _tarea(tarea, escapes if escapes is not None else {})
    return bloque


# ---------------------------------------------------------------------------
# Niveles del árbol — cada uno devuelve (estado_de_dominio, Bloque | None)
#
# El estado viaja aparte del bloque, y no dentro, porque es el ingrediente que el
# padre necesita para preguntar a `estado_dominio` por SU estado agregado. El
# bloque es prosa; el estado es dato de agregación. Mezclarlos obligaría al padre
# a leer el texto del hijo para saber cómo está.
# ---------------------------------------------------------------------------

def _tarea(tarea, escapes: dict) -> tuple[str, Optional[Bloque]]:
    codigo = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None
    nombre = tarea.tipo_tarea.nombre if tarea.tipo_tarea else f'Tarea #{tarea.id}'

    # El plazo sí se resuelve aquí, al revés que en `_check_completitud_cierre`
    # (#723), que lo omite a propósito: allí basta con «falta completar una tarea»
    # para un bloqueo que además se puede forzar; aquí el informe promete decir
    # qué falta y por qué, y «está a la espera de que venza un plazo» es una
    # respuesta muy distinta de «hay trabajo pendiente». El coste es una consulta
    # por espera, en un gesto puntual, no en una vista que se repinte.
    plazo = _plazo(tarea) if codigo == 'ESPERAR_PLAZO' else None
    estado = sem.estado_tarea(tarea, plazo=plazo)

    relato = _relato_escapes(escapes, 'tareas', tarea.id)

    if estado == 'FIN':
        if not relato:
            return estado, None            # nada que decir: su trámite ya la cuenta
        return estado, Bloque(SALVADO, nombre, relato=relato, nodo=('tarea', tarea.id))

    pendiente = (f'{nombre}: {sem.motivo(estado)}.',)
    if plazo and plazo.get('fecha_limite'):
        pendiente = (f'{nombre}: {sem.motivo(estado)} '
                     f'(vence el {_fecha(_iso_a_fecha(plazo["fecha_limite"]))}).',)
    return estado, Bloque(PENDIENTE, nombre, relato=relato,
                          pendiente=pendiente, nodo=('tarea', tarea.id))


def _tramite(tramite, escapes: dict) -> tuple[str, Optional[Bloque]]:
    nombre = tramite.tipo_tramite.nombre if tramite.tipo_tramite else f'Trámite #{tramite.id}'

    estados_tareas = []
    hijos = []
    for tarea in sorted(tramite.tareas, key=lambda t: t.id):
        estado_ta, bloque_ta = _tarea(tarea, escapes)
        estados_tareas.append(estado_ta)
        if bloque_ta is not None:
            hijos.append(bloque_ta)

    estado, _propio = sem.estado_tramite(tramite, estados_tareas)
    mios = _relato_escapes(escapes, 'tramites', tramite.id)

    if tramite.finalizado:
        fecha = _fecha_tramite(tramite)
        cuando = f' el {_fecha(fecha)}' if fecha else ''
        relato = (f'{nombre} — completado{cuando}.',) + mios + _de_hijos(hijos, 'relato')
        categoria = SALVADO if (mios or any(h.categoria == SALVADO for h in hijos)) else PASA
        return estado, Bloque(categoria, nombre, relato=relato, nodo=('tramite', tramite.id))

    if tramite.planificado:
        # Vacío no es hecho (#723): un trámite sin tareas no puede darse por completo.
        pendiente = (f'{nombre}: no tiene ninguna tarea. Complételo o bórrelo si no '
                     f'era necesario.',)
    else:
        pendiente = (f'{nombre}: {sem.motivo(estado)}.',) + _de_hijos(hijos, 'pendiente')

    return estado, Bloque(PENDIENTE, nombre, relato=mios + _de_hijos(hijos, 'relato'),
                          pendiente=pendiente, nodo=('tramite', tramite.id))


def _fase(fase, escapes: dict) -> tuple[str, Optional[Bloque]]:
    nombre = fase.tipo_fase.nombre if fase.tipo_fase else f'Fase #{fase.id}'

    estados_tramites = []
    hijos = []
    for tramite in sorted(fase.tramites, key=lambda t: t.id):
        estado_tr, bloque_tr = _tramite(tramite, escapes)
        estados_tramites.append(estado_tr)
        if bloque_tr is not None:
            hijos.append(bloque_tr)

    estado, _propio = sem.estado_fase(fase, estados_tramites)
    mios = _relato_escapes(escapes, 'fases', fase.id)

    if fase.finalizada:
        fecha = _fecha_cierre(fase)
        cuando = f' el {_fecha(fecha)}' if fecha else ''
        resultado = ''
        if fase.resultado_fase is not None:
            resultado = f' con resultado {fase.resultado_fase.nombre or fase.resultado_fase.codigo}'
        relato = ((f'Fase «{nombre}» — cerrada{cuando}{resultado}.',)
                  + mios + _de_hijos(hijos, 'relato'))
        categoria = SALVADO if (mios or any(h.categoria == SALVADO for h in hijos)) else PASA
        return estado, Bloque(categoria, nombre, relato=relato, nodo=('fase', fase.id))

    if fase.planificada:
        pendiente = (f'Fase «{nombre}»: no tiene ningún trámite. Tramítela o bórrela '
                     f'si no era necesaria.',)
    else:
        pendiente = ((f'Fase «{nombre}»: {sem.motivo(estado)}.',)
                     + _de_hijos(hijos, 'pendiente'))

    return estado, Bloque(PENDIENTE, nombre, relato=mios + _de_hijos(hijos, 'relato'),
                          pendiente=pendiente, nodo=('fase', fase.id))


def _solicitud(solicitud, instruccion: list, estados_fases: list,
               escapes: dict) -> Optional[Bloque]:
    """Lo que la solicitud dice de sí misma: su encabezado y, si no tiene fases de
    instrucción, que no las tiene.

    Ese segundo caso es el agujero de vacuidad que ningún bloque de fase puede
    cubrir —no hay nodos que hablen— y el mismo que #723 tapó en
    `Tramite.finalizado`: `all([])` es True y certificaría una instrucción que no
    existe. Se dice con el vocabulario del árbol: sin hijos, PLANIFICADA.
    """
    ts = solicitud.tipo_solicitud
    siglas = ts.siglas if ts else 'sin tipo'
    doc = getattr(solicitud, 'documento_solicitud', None)
    presentada = ''
    if doc is not None and doc.fecha_administrativa:
        presentada = f', presentada el {_fecha(doc.fecha_administrativa)}'
    encabezado = f'Solicitud #{solicitud.id} ({siglas}){presentada}.'

    mios = _relato_escapes(escapes, 'solicitudes', solicitud.id)

    if not instruccion:
        return Bloque(
            PENDIENTE, f'Solicitud #{solicitud.id}',
            relato=(encabezado,) + mios,
            pendiente=('Esta solicitud no tiene ninguna fase de instrucción: no hay '
                       'nada instruido que certificar. Cree y complete las fases que '
                       'el procedimiento requiera.',),
            nodo=('solicitud', solicitud.id),
        )

    _estado, _propio = sem.estado_solicitud(solicitud, estados_fases)
    cuantas = (f'Se instruyó en {len(instruccion)} fase' +
               ('s' if len(instruccion) > 1 else '') + '.')
    categoria = SALVADO if mios else PASA
    return Bloque(categoria, f'Solicitud #{solicitud.id}',
                  relato=(encabezado, cuantas) + mios,
                  nodo=('solicitud', solicitud.id))


# ---------------------------------------------------------------------------
# El motor — una sola pregunta, sobre el acto que importa
# ---------------------------------------------------------------------------

def _veredicto_del_motor(solicitud) -> tuple[object, str, tuple, list]:
    """Audita CREAR la fase finalizadora y traduce lo que bloquea a bloques.

    Las reglas de precedencia hacia esa fase *son* el veredicto normativo sobre si
    la instrucción está lista (requerimientos sin respuesta, organismos, IP, tasa).
    Se pregunta una vez, no nodo a nodo: las reglas del motor son de un acto, no de
    un nodo, y la única pregunta posible sobre lo ya creado sería «¿se permitiría
    crear esto hoy?», que es arqueología —las reglas cambian, y un nodo de junio
    dispararía hoy reglas que no existían—.

    Las del art. 82.1 se excluyen del criterio **por definición** (§E ter): son las
    únicas que este acto satisface, y esperar a que dejen de disparar solas sería
    esperar a nunca. Sus ids salen para que el PDF las presente como satisfechas
    en vez de como bloqueo.

    Defensivo (REGLAS_DESARROLLO §Servicios con catálogo): sin motor disponible el
    informe se queda con lo que dice el árbol, que no es poco, y lo deja en el log.
    """
    from app.models.tipos_fases import TipoFase
    from app.services.assembler import auditar_multi

    try:
        tipo_fase_fin = TipoFase.query.filter_by(
            codigo=codigo_fase_finalizadora(solicitud)).first()
        auditoria = auditar_multi(
            'CREAR', solicitud.expediente,
            objeto={'solicitud': solicitud, 'tipo_fase': tipo_fase_fin},
        )
        del_acto = _ids_reglas_del_acto()
    except (OperationalError, ProgrammingError) as exc:
        log.warning('informe_instruccion: motor no disponible para solicitud %s — %s',
                    solicitud.id, exc)
        return None, '', (), []

    bloques = []
    # Una fila por regla, aunque haya casado varias veces. `auditar_multi` audita
    # una vez por cada tipo simple de la solicitud (AAP y AAC en una AAP+AAC) y
    # acumula, así que toda regla de sujeto genérico —la tasa del art. 45.1, sin ir
    # más lejos— aparece repetida en `reglas_evaluadas`. Para el snapshot congelado
    # esa repetición es fiel y se queda; para el técnico es la misma frase dos veces.
    vistas = set()
    for regla in auditoria.reglas_evaluadas:
        if regla.regla_id in del_acto or regla.regla_id in vistas:
            continue
        if not regla.disparada or regla.neutralizada or regla.efecto != 'BLOQUEAR':
            continue
        vistas.add(regla.regla_id)
        norma = regla.norma_compilada or 'sin norma citada'
        bloques.append(Bloque(
            PENDIENTE,
            'Comprobación reglamentaria',
            pendiente=(f'{regla.descripcion or "Una regla del motor lo impide"} '
                       f'({norma}).',),
            nodo=('solicitud', solicitud.id),
        ))

    return auditoria, auditoria.sujeto, del_acto, bloques


def _ids_reglas_del_acto() -> tuple:
    """Ids de las reglas del art. 82.1 LPACAP — las que el certificado satisface.

    Por artículo y no por texto: la descripción es editorial y cambia (acaba de
    hacerlo, para que el bloqueo señale la salida), mientras que la cita normativa
    es lo que define a estas dos filas. Mismo criterio que usa el aviso de arranque
    de `catalogo_requerido._validar_finalizadoras_con_regla`.
    """
    from app.models.motor_reglas import ReglaMotor
    filas = ReglaMotor.query.filter_by(
        accion='CREAR', activa=True, articulo='82', apartado='1').all()
    return tuple(r.id for r in filas)


# ---------------------------------------------------------------------------
# Escapes de bitácora — se relatan donde ocurrieron
# ---------------------------------------------------------------------------

# Para qué se forzó el bloqueo, según la operación registrada. La bitácora guarda
# `{escape, justificacion, sujeto}` y a veces `motivo` (el texto del bloqueo que
# se forzó) o `accion` (REABRIR). No guarda qué regla se esquivó: correlacionarlo
# es de #614. En infinitivo para que la frase funcione igual con sujeto («CLG
# forzó… para cerrar») y sin él («se forzó… para cerrar»), que es lo que hay
# cuando el usuario ya no consta.
_FIN_DEL_ESCAPE = {
    ('CREAR', None):        'crear este elemento',
    ('BORRAR', None):       'borrar un elemento',
    ('ALTERAR', None):      'modificar este elemento',
    ('ALTERAR', 'REABRIR'): 'reabrir esta fase, que estaba cerrada',
}


def _escapes_del_arbol(solicitud) -> dict:
    """Todos los escapes del subárbol de la solicitud, indexados por nodo.

    Una sola consulta para todo el árbol: la alternativa —que cada nodo pregunte
    por los suyos— multiplicaría por el número de nodos un informe que ya recorre
    todo. Cada nivel toma después los suyos de este índice.

    **Carencia asumida, no olvidada** (ADR-043 §Consecuencias): la bitácora guarda
    `(tabla, registro_id)` y no la solicitud, así que reunir sus escapes solo puede
    hacerse desde los ids vivos de su árbol — y un escape sobre algo que después se
    borró es irrecuperable. Añadir `solicitud_id` al detalle lo resolvería donde ya
    se compone, y no depende del log completo de transacciones que #614 espera.
    """
    from sqlalchemy import and_, or_

    from app.models.bitacora import Bitacora

    ids: dict[str, list] = {'solicitudes': [solicitud.id], 'fases': [],
                            'tramites': [], 'tareas': []}
    for fase in solicitud.fases:
        ids['fases'].append(fase.id)
        for tramite in fase.tramites:
            ids['tramites'].append(tramite.id)
            for tarea in tramite.tareas:
                ids['tareas'].append(tarea.id)

    condiciones = [and_(Bitacora.tabla == tabla, Bitacora.registro_id.in_(valores))
                   for tabla, valores in ids.items() if valores]
    if not condiciones:
        return {}

    try:
        filas = (Bitacora.query
                 .filter(or_(*condiciones))
                 .order_by(Bitacora.id)
                 .all())
    except (OperationalError, ProgrammingError) as exc:
        log.warning('informe_instruccion: bitácora no disponible para solicitud %s — %s',
                    solicitud.id, exc)
        return {}

    indice: dict = {}
    for fila in filas:
        detalle = fila.detalle or {}
        # El filtro es en Python y no en SQL a propósito: `detalle` es JSON (no
        # JSONB) y el conjunto ya está acotado a los nodos de una solicitud.
        if not detalle.get('escape'):
            continue
        indice.setdefault((fila.tabla, fila.registro_id), []).append(fila)
    return indice


def _relato_escapes(escapes: dict, tabla: str, registro_id: int) -> tuple:
    """Los escapes de un nodo, ya redactados. Tupla vacía si no hubo ninguno."""
    filas = escapes.get((tabla, registro_id))
    if not filas:
        return ()

    frases = []
    for fila in filas:
        detalle = fila.detalle or {}
        para = _FIN_DEL_ESCAPE.get(
            (fila.operacion, detalle.get('accion')),
            _FIN_DEL_ESCAPE.get((fila.operacion, None), 'actuar sobre este elemento'),
        )
        cuando = f'El {_fecha(fila.created_at)}, ' if fila.created_at else ''
        quien = _quien(fila.usuario_id)
        # Con usuario, activa («CLG forzó…»); sin él, impersonal («se forzó…»).
        sujeto = f'{quien} forzó' if quien else 'se forzó'
        frase = f'{cuando}{sujeto} el bloqueo del motor para {para}'
        justificacion = _citable(detalle.get('justificacion'))
        if justificacion:
            frase += f', con esta justificación: «{justificacion}»'
        motivo = _citable(detalle.get('motivo'))
        if motivo:
            frase += f'. El sistema advertía: «{motivo}»'
        frases.append(frase + '.')
    return tuple(frases)


def _citable(texto) -> str:
    """Texto listo para ir entre comillas: sin el punto final que traiga.

    El punto de la frase que contiene la cita va fuera de las comillas, así que un
    texto que ya venga con el suyo —los motivos de bloqueo lo traen— produciría
    «…notificación.». con dos puntos seguidos."""
    return (texto or '').strip().rstrip('.').strip()


def _quien(usuario_id) -> str:
    """Siglas del usuario, o cadena vacía si no consta. El relato dice quién asumió
    la responsabilidad del escape; sin usuario, la frase sigue siendo correcta."""
    if not usuario_id:
        return ''
    try:
        from app.models.usuarios import Usuario
        usuario = Usuario.query.get(usuario_id)
    except (OperationalError, ProgrammingError):
        return ''
    if usuario is None:
        return ''
    return usuario.siglas or ''


# ---------------------------------------------------------------------------
# Fechas derivadas — ni fases ni trámites guardan fecha propia
# ---------------------------------------------------------------------------
# Decisión de diseño del modelo (§2.bis DISEÑO_FECHAS_PLAZOS.md, y los docstrings
# de Fase/Tramite/Tarea): la completitud se deduce de documentos, no de campos de
# fecha. Así que la fecha de lo instruido se deriva del documento que cierra cada
# cosa, que es además el que la acredita.

def _fecha_cierre(fase) -> Optional[date]:
    """La del documento que formaliza el resultado — el que hace `finalizada` True."""
    doc = fase.documento_resultado
    return doc.fecha_administrativa if doc is not None else None


def _fecha_tramite(tramite) -> Optional[date]:
    """La del último documento producido por sus tareas: un trámite está completo
    cuando lo están todas, así que su fecha es la de la última que produjo."""
    fechas = []
    for tarea in tramite.tareas:
        doc = tarea.documento_producido
        if doc is not None and doc.fecha_administrativa:
            fechas.append(doc.fecha_administrativa)
    return max(fechas) if fechas else None


def _fecha(valor) -> str:
    return valor.strftime('%d/%m/%Y') if valor else ''


def _iso_a_fecha(iso: str) -> Optional[date]:
    try:
        return date.fromisoformat(iso)
    except (TypeError, ValueError):
        return None


def _plazo(tarea) -> Optional[dict]:
    """Estado del plazo de una ESPERAR_PLAZO. Reutiliza el resolutor público del
    árbol (`arbol_expediente.plazo_tarea`), que ya es defensivo y lo comparte el
    inspector: recalcularlo aquí sería la tercera copia."""
    from app.services.arbol_expediente import plazo_tarea
    return plazo_tarea(tarea)


def _de_hijos(bloques: list, campo: str) -> tuple:
    """Concatena un campo de texto de los bloques hijos, en su orden."""
    salida = []
    for bloque in bloques:
        salida.extend(getattr(bloque, campo))
    return tuple(salida)
