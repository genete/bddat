"""
CERT_CIERRE_SOLICITUD — el certificado de cierre de la solicitud (#996, N6).

ADR-049 §F. Una solicitud puede pedir varios actos a la vez (`AAP+AAC+DUP` son
tres), cada uno con su plazo para resolver y su fase de resolución; desde #956
cada una de esas fases se cierra con su certificado. Faltaba el documento que
cuenta cómo terminó la solicitud entera. Es este, y ocupa
`Solicitud.documento_cierre_id`, que existía desde #778 sin que nadie lo llenara.

QUÉ CONSTATA (D2)
=================
Tres partes, en este orden:

1. **El plazo de resolver, acto por acto** —lo único con contenido propio—: la
   fase que lo resolvió y su resultado, el plazo legal y su norma, la fecha
   límite con los días de suspensión, la notificación al solicitante (el
   documento que cita su `CERT_CUMPLIMIENTO_FASE`) y si fue en plazo o fuera; si
   fuera, el efecto del vencimiento que dice el catálogo, sin interpretarlo. Sale
   de `plazos.plazos_de_la_solicitud`. Emitir fuera de plazo no está prohibido: el
   certificado lo hace constar.
2. **La instrucción**: número y emisión del `CERT_FIN_INSTRUCCION`, con un enlace
   a su PDF. Su relato solo existe en el PDF (vive en `certificados_fase`, sin
   `datos`), así que no se copia. Si no consta, se dice y no impide emitir.
3. **Copia literal** de la foto fija de cada `CERT_CIERRE_FASE`, con su número y
   emisión: ya cuenta la fase, sus trámites, la notificación y los escapes.

GESTO MANUAL, COMO LOS DEMÁS CERTIFICADOS (D1)
==============================================
El botón del inspector de la solicitud responde siempre: con algo pendiente es un
informe y no se crea nada; si no falta nada, se emite; si ya estaba, se muestra.
Se emite cuando cada acto tiene su fase de resolución creada, cerrada y con su
`CERT_CIERRE_FASE`, y no queda ninguna fase abierta. La comprobación «¿queda algún
acto sin resolver?» es la de `Solicitud.estado` (D6,
`actos_solicitud.actos_sin_resolver`); el certificado exige además los sellos.

FOTO FIJA (D3)
==============
Al emitir, `certificados.datos` guarda el resumen del plazo ya redactado y las
copias de los certificados de fase tal cual. La vista del emitido lo pinta sin
recalcular: el plazo vivo (#922) se sigue calculando, y el certificado es la
constancia de lo que constaba al emitirse (no contradice «el resultado del plazo
nunca se guarda», ADR-049 §E). Las copias no pueden quedar viejas: solo se emite
con la solicitud resuelta y notificada, y entonces ninguna fase se reabre ni se
crea (`invariantes_esftt._check_reabrir` y su otro extremo, #996).

SE RETIRA CON JUSTIFICACIÓN (D4)
================================
`retirar` borra la fila y su documento y vacía `documento_cierre_id`, con la
justificación en bitácora; el certificado siguiente lo relata. Bloqueado si
alguna tarea lo tiene vinculado (otra solicitud lo usa como entrada, #997). Lo
único que puede estar mal es el resumen del plazo —fecha de presentación,
catálogo de plazos o calendario de inhábiles erróneos al emitir—: retirar,
corregir y volver a emitir.

SIN `solicitud_id` NI `fase_id`
===============================
La fila de `certificados` va con los dos nulos: el índice único por
`solicitud_id` (#901) no lleva `tipo` y chocaría con el `CERT_FIN_IP_CONSULTAS` de
la misma solicitud. Se llega al certificado por `documento_cierre_id`
(`sellos.certificado_cierre_solicitud`), que ya garantiza uno por solicitud.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Optional

from flask_login import current_user
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services import bitacora as bitacora_svc
from app.services import cert_cierre_fase
from app.services import informe_instruccion as informe_svc
from app.services import sellos
from app.services.actos_solicitud import (
    FASES_RESOLUTORAS, actos_de, actos_sin_resolver, fase_de, fase_resolutora,
)
from app.services.assembler import build_sujeto
from app.services.invariantes_esftt import (
    advertir_documentos_criticos_huerfanos, check_invariante,
)
from app.services.plazos import plazos_de_la_solicitud

log = logging.getLogger(__name__)

CODIGO_CERT = sellos.CERT_CIERRE_SOLICITUD

# Cómo consta la retirada en bitácora: sobre `solicitudes`, porque el certificado y
# su documento desaparecen y lo que permanece es la solicitud —ahí la encuentra el
# certificado siguiente (`informe_instruccion.relato_retiradas`)—. Sin `escape`:
# no se fuerza ningún bloqueo (mismo criterio que `cert_fin_instruccion.ACCION_DESHACER`).
ACCION_RETIRAR = 'RETIRAR_CERT_CIERRE_SOLICITUD'

# Versión de la forma de `datos` (foto fija). Si cambia la plantilla, la del
# emitido tiene que seguir sabiendo leer lo que se congeló con la anterior.
VERSION_DATOS = 1

# Cómo está la fase que resuelve cada acto.
SIN_CREAR = 'SIN_CREAR'
ABIERTA = 'ABIERTA'
SIN_CERTIFICADO = 'SIN_CERTIFICADO'   # cerrada sin CERT_CIERRE_FASE (antes de #956)
LISTA = 'LISTA'

# Veredicto del plazo de un acto, tal como lo dice el certificado.
EN_PLAZO = 'EN_PLAZO'
FUERA_DE_PLAZO = 'FUERA_DE_PLAZO'
SIN_PLAZO = 'SIN_PLAZO'
SIN_NOTIFICACION = 'SIN_NOTIFICACION'

_UNIDADES = {
    'DIAS_HABILES': ('día hábil', 'días hábiles'),
    'DIAS_NATURALES': ('día natural', 'días naturales'),
    'MESES': ('mes', 'meses'),
    'ANOS': ('año', 'años'),
}


# ---------------------------------------------------------------------------
# Revisión — el informe, sin efectos
# ---------------------------------------------------------------------------

@dataclass
class Acto:
    """Lo que el certificado necesita de un acto: su fase, cómo está y su plazo."""
    siglas: str
    fase_codigo: str
    fase_nombre: str
    situacion: str
    fase: object = None                    # la Fase, o None si no se ha creado
    certificado_cierre: object = None      # su CERT_CIERRE_FASE, si lo tiene
    documento_cumplimiento: object = None  # el que cita su CERT_CUMPLIMIENTO_FASE
    plazo: object = None                   # plazos.EstadoPlazoActo


@dataclass
class Informe:
    """El informe de cierre de una solicitud: lo que diría el certificado y lo que
    falta para poder emitirlo. Se calcula siempre; solo se guarda al emitir."""
    solicitud: object
    actos: list = field(default_factory=list)            # [Acto], en su orden
    fases_abiertas: list = field(default_factory=list)   # otras fases sin cerrar
    instruccion: Optional[dict] = None
    retiradas: tuple = ()
    advertencia: Optional[dict] = None

    @property
    def pendientes(self) -> list:
        """Frases de lo que impide emitir, una por fase (AAP y AAC comparten la suya)."""
        if not self.actos:
            return ['La solicitud no tiene tipo: no hay actos que certificar.']
        frases = []
        for actos in _por_fase([a for a in self.actos if a.situacion != LISTA]):
            primero = actos[0]
            nombre = f'«{primero.fase_nombre}»'
            que = _enumerar([a.siglas for a in actos])
            if primero.situacion == SIN_CREAR:
                frases.append(f'Falta crear la fase {nombre}, que resuelve {que}.')
            elif primero.situacion == ABIERTA:
                frases.append(f'La fase {nombre}, que resuelve {que}, sigue abierta: '
                              f'ciérrela con su certificado de cierre.')
            else:
                frases.append(f'La fase {nombre}, que resuelve {que}, se cerró sin '
                              f'certificado de cierre (antes de que existiera, #956): '
                              f'reábrala y ciérrela con el suyo. Si la resolución ya es '
                              f'firme, no podrá reabrirse.')
        for fase in self.fases_abiertas:
            frases.append(f'La fase «{_nombre_fase(fase)}» sigue abierta: el cierre de la '
                          f'solicitud no se certifica con fases sin cerrar.')
        return frases

    @property
    def limpio(self) -> bool:
        return not self.pendientes

    def a_dict(self) -> dict:
        return {'limpio': self.limpio, 'pendientes': self.pendientes}


def revisar(solicitud) -> Informe:
    """El informe de cierre de `solicitud`, sin crear nada. Se puede repetir."""
    nombres = _nombres_fases_resolutoras()
    sin_resolver = actos_sin_resolver(solicitud)
    actos = []
    resolutoras = set()
    # `plazos_de_la_solicitud` devuelve un plazo por acto, en el orden de `actos_de`.
    for acto, plazo in zip(actos_de(solicitud), plazos_de_la_solicitud(solicitud)):
        fase = fase_de(acto)
        codigo = fase_resolutora(solicitud, acto.siglas)
        certificado = None
        if acto in sin_resolver:
            situacion = SIN_CREAR if fase is None else ABIERTA
        else:
            certificado = sellos.certificado_cierre(fase)
            situacion = LISTA if certificado is not None else SIN_CERTIFICADO
        if fase is not None:
            resolutoras.add(fase.id)
        actos.append(Acto(
            siglas=acto.siglas,
            fase_codigo=codigo,
            fase_nombre=_nombre_fase(fase) if fase is not None else nombres.get(codigo, codigo),
            situacion=situacion,
            fase=fase,
            certificado_cierre=certificado,
            documento_cumplimiento=(sellos.documento_cumplimiento_sellado(fase)
                                    if fase is not None else None),
            plazo=plazo,
        ))

    return Informe(
        solicitud=solicitud,
        actos=actos,
        fases_abiertas=[f for f in sorted(solicitud.fases, key=lambda f: f.id)
                        if not f.finalizada and f.id not in resolutoras],
        instruccion=_instruccion(solicitud),
        retiradas=informe_svc.relato_retiradas(
            solicitud, accion=ACCION_RETIRAR,
            que='un certificado de cierre anterior de esta solicitud'),
        advertencia=advertir_documentos_criticos_huerfanos(solicitud.expediente_id),
    )


def _instruccion(solicitud) -> Optional[dict]:
    """El `CERT_FIN_INSTRUCCION` de la solicitud: su documento, su número (la fila
    de `certificados_fase`) y su emisión; None si no consta.

    Los emitidos antes de #827 no tienen `CertificadoFase.documento_id` que casar:
    entonces van sin número y con la fecha del documento.
    """
    documento = solicitud.documento_fin_instruccion
    if documento is None:
        return None
    from app.models.certificados_fase import CertificadoFase
    try:
        certificado = CertificadoFase.query.filter_by(documento_id=documento.id).first()
    except (OperationalError, ProgrammingError) as exc:
        log.warning('cert_cierre_solicitud: certificados_fase no disponible para la '
                    'solicitud %s — %s', solicitud.id, exc)
        certificado = None
    if certificado is not None and certificado.fecha_generacion is not None:
        emitido = _local(certificado.fecha_generacion).strftime('%d/%m/%Y %H:%M')
    else:
        emitido = _fecha(documento.fecha_administrativa) or None
    return {
        'documento_id': documento.id,
        'certificado_id': certificado.id if certificado is not None else None,
        'emitido': emitido,
    }


# ---------------------------------------------------------------------------
# Emitir — el gesto
# ---------------------------------------------------------------------------

@dataclass
class Emision:
    """Resultado del gesto: siempre hay informe; a veces, además, certificado.

    `error` y `bloqueo` son para fallos de verdad —catálogo sin el tipo, la puerta
    cerrada dijo que no—, no para «faltan cosas»: eso es el informe con
    pendientes, y no se ha creado nada.
    """
    informe: Informe
    emitido: bool = False
    ya_emitido: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None
    bloqueo: object = None

    def a_dict(self) -> dict:
        datos = self.informe.a_dict()
        datos.update({
            'emitido': self.emitido,
            'ya_emitido': self.ya_emitido,
            'documento_id': self.documento_id,
            'certificado_id': self.certificado_id,
        })
        return datos


def emitir(solicitud) -> Emision:
    """Emite el `CERT_CIERRE_SOLICITUD` de `solicitud` si no falta nada.

    - ya emitido → el existente, sin tocar nada;
    - informe con pendientes → el informe, y nada creado;
    - limpio → `Documento` (`fecha_administrativa` NULL, url
      `bddat://certificados/{id}`) + `Certificado(tipo, datos=<foto fija>)` sin
      `solicitud_id` ni `fase_id` + `solicitud.documento_cierre_id` + bitácora
      `CREAR documentos`.
    """
    existente = sellos.certificado_cierre_solicitud(solicitud)
    if existente is not None:
        return Emision(informe=revisar(solicitud), emitido=True, ya_emitido=True,
                       documento_id=existente.documento_id, certificado_id=existente.id)

    informe = revisar(solicitud)
    if not informe.limpio:
        return Emision(informe=informe)

    # Puerta cerrada: sus supuestos ya los cubre el informe; se comprueba igualmente
    # porque el invariante tiene la última palabra (mismo criterio que los otros
    # certificados).
    res_inv = check_invariante('EMITIR', 'SOLICITUD', solicitud.id, tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        log.warning('cert_cierre_solicitud: el informe de la solicitud %s salió limpio '
                    'pero el invariante bloquea — %s', solicitud.id,
                    res_inv.motivo or res_inv.norma_compilada)
        return Emision(informe=informe, bloqueo=res_inv)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_CERT).first()
    if tipo_doc is None:
        return Emision(informe=informe,
                       error=f'TipoDocumento {CODIGO_CERT!r} no encontrado en el catálogo.')

    expediente = solicitud.expediente
    datos = foto_fija(informe)
    try:
        documento = Documento(
            expediente_id=expediente.id,
            tipo_doc_id=tipo_doc.id,
            url='bddat://certificados/0',   # provisional hasta tener cert.id
            fecha_administrativa=None,
            asunto=f'Cierre de la solicitud — {datos["solicitud"]} (#{solicitud.id})',
        )
        db.session.add(documento)
        db.session.flush()

        # Sin `solicitud` ni `fase`: ver el docstring del módulo.
        certificado = Certificado(
            documento=documento, tipo=CODIGO_CERT, datos=datos,
            generado_en=datetime.now(UTC).replace(tzinfo=None),
        )
        db.session.add(certificado)
        db.session.flush()
        documento.url = f'bddat://certificados/{certificado.id}'

        # Por la relación, para que `documento.anclado_en_cierre` lo vea ya.
        solicitud.documento_cierre = documento
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'documentos', documento.id,
            detalle={
                'tipo_documento': CODIGO_CERT,
                'solicitud_id': solicitud.id,
                'certificado_id': certificado.id,
                'actos': [a['acto'] for a in datos['actos']],
                'certificados_de_fase': [c['certificado_id'] for c in datos['fases']],
                'sujeto': build_sujeto(expediente, solicitud),
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cierre_solicitud: fallo emitiendo el de la solicitud %s: %s',
                  solicitud.id, exc)
        return Emision(informe=informe, error=str(exc))

    log.info('CERT_CIERRE_SOLICITUD emitido: doc=%s cert=%s solicitud=%s expediente=%s',
             documento.id, certificado.id, solicitud.id, expediente.id)
    return Emision(informe=informe, emitido=True,
                   documento_id=documento.id, certificado_id=certificado.id)


def foto_fija(informe: Informe) -> dict:
    """Lo que se guarda en `certificados.datos` al emitir (D3).

    Texto ya redactado, no ids que haya que volver a resolver —salvo el del
    documento del fin de instrucción, para enlazar su PDF—: la vista del emitido lo
    pinta tal cual aunque después cambie la fecha del escrito de solicitud, el
    catálogo de plazos o el calendario. Las copias de los certificados de fase
    llevan su `datos` sin tocar y su huella. La del propio certificado no va aquí:
    es de su fila.
    """
    solicitud = informe.solicitud
    expediente = solicitud.expediente
    tipo = solicitud.tipo_solicitud
    escrito = solicitud.documento_solicitud
    return {
        'version': VERSION_DATOS,
        'expediente': f'AT-{expediente.numero_at}',
        'solicitud_id': solicitud.id,
        'solicitud': tipo.siglas if tipo else f'Solicitud #{solicitud.id}',
        'solicitante': _solicitante(solicitud),
        'presentada': _fecha(escrito.fecha_administrativa) if escrito is not None else '',
        'actos': [_acto_en_datos(a) for a in informe.actos],
        'instruccion': informe.instruccion,
        'fases': _copias(informe),
        'retiradas': list(informe.retiradas),
    }


def _acto_en_datos(acto: Acto) -> dict:
    """El resumen del plazo de un acto (D2.1), ya redactado."""
    fase = acto.fase
    plazo = acto.plazo
    con_plazo = plazo is not None and plazo.estado != 'SIN_PLAZO'
    if not con_plazo:
        veredicto = SIN_PLAZO
    elif plazo.estado == 'CUMPLIDO':
        veredicto = FUERA_DE_PLAZO if plazo.cumplido_fuera_de_plazo else EN_PLAZO
    else:
        veredicto = SIN_NOTIFICACION
    vencido = veredicto == FUERA_DE_PLAZO or (con_plazo and plazo.estado == 'VENCIDO')
    documento = acto.documento_cumplimiento
    return {
        'acto': acto.siglas,
        'fase': acto.fase_nombre,
        'fase_id': fase.id if fase is not None else None,
        'situacion': acto.situacion,
        'resultado': (fase.resultado_fase.nombre or fase.resultado_fase.codigo
                      if fase is not None and fase.finalizada and fase.resultado_fase
                      else None),
        'plazo': {
            'duracion': _duracion(plazo.plazo_valor, plazo.plazo_unidad),
            'norma': plazo.norma_origen,
            'fecha_limite': _fecha(plazo.fecha_limite),
            'dias_suspendidos': plazo.dias_suspendidos,
            'fecha_limite_sin_suspender': _fecha(plazo.fecha_limite_sin_suspender),
        } if con_plazo else None,
        'notificacion': {
            'fecha': _fecha(documento.fecha_administrativa),
            'documento_id': documento.id,
            'documento': (documento.tipo_doc.nombre if documento.tipo_doc
                          else f'Documento {documento.id}'),
        } if documento is not None else None,
        'veredicto': veredicto,
        'efecto': (plazo.efecto_nombre or plazo.efecto) if vencido else None,
    }


def _copias(informe: Informe) -> list:
    """Copia literal de cada `CERT_CIERRE_FASE` de las fases que resuelven, una por
    fase (AAP y AAC en una RESOLUCION comparten la suya), con su huella."""
    copias = []
    for actos in _por_fase([a for a in informe.actos if a.certificado_cierre is not None]):
        certificado = actos[0].certificado_cierre
        momento = sellos.momento_emision(certificado)
        copias.append({
            'fase_id': actos[0].fase.id,
            'fase': actos[0].fase_nombre,
            'actos': [a.siglas for a in actos],
            'certificado_id': certificado.id,
            'documento_id': certificado.documento_id,
            'emitido': momento.strftime('%d/%m/%Y %H:%M') if momento else None,
            'datos': copy.deepcopy(certificado.datos or {}),
        })
    return copias


# ---------------------------------------------------------------------------
# Retirar (D4)
# ---------------------------------------------------------------------------

@dataclass
class Retirada:
    """Resultado de retirar: qué se borró, o por qué no pudo borrarse."""
    ok: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None

    def a_dict(self) -> dict:
        return {'ok': self.ok, 'documento_id': self.documento_id,
                'certificado_id': self.certificado_id}


def retirar(solicitud, *, justificacion: str) -> Retirada:
    """Retira el certificado de cierre de `solicitud`, con justificación (D4).

    Borra la fila de `certificados` y su `Documento`, vacía `documento_cierre_id` y
    deja en bitácora `ALTERAR solicitudes` la justificación y los ids retirados; el
    certificado siguiente lo relata. Bloqueado si alguna tarea tiene vinculado el
    documento: otra solicitud lo usa como entrada (#997), y borrarlo con el vínculo
    vivo moriría además en IntegrityError.
    """
    if not justificacion or not justificacion.strip():
        return Retirada(error='Retirar el certificado de cierre de la solicitud requiere '
                              'justificación.')
    documento = solicitud.documento_cierre
    if documento is None:
        return Retirada(error='Esta solicitud no tiene certificado de cierre que retirar.')
    if documento.vinculos_tarea:
        tarea = documento.vinculos_tarea[0].tarea
        return Retirada(error=(
            f'El certificado de cierre está vinculado a la tarea «{_nombre_tarea(tarea)}» '
            f'de la solicitud #{tarea.tramite.fase.solicitud_id}: desvincúlelo de ella '
            f'antes de retirarlo.'
        ))

    certificado = documento.certificado
    documento_id = documento.id
    certificado_id = certificado.id if certificado is not None else None
    expediente = solicitud.expediente
    try:
        solicitud.documento_cierre = None
        db.session.flush()
        if certificado is not None:
            db.session.delete(certificado)
            db.session.flush()
        db.session.delete(documento)
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'solicitudes', solicitud.id,
            detalle={
                'accion': ACCION_RETIRAR,
                'justificacion': justificacion.strip(),
                'tipo_documento': CODIGO_CERT,
                'documento_id': documento_id,
                'certificado_id': certificado_id,
                'sujeto': build_sujeto(expediente, solicitud),
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cierre_solicitud: fallo retirando el de la solicitud %s: %s',
                  solicitud.id, exc)
        return Retirada(error=str(exc))

    log.info('CERT_CIERRE_SOLICITUD retirado: doc=%s cert=%s solicitud=%s',
             documento_id, certificado_id, solicitud.id)
    return Retirada(ok=True, documento_id=documento_id, certificado_id=certificado_id)


# ---------------------------------------------------------------------------
# Vista — lo que pinta la plantilla, emitido o calculado
# ---------------------------------------------------------------------------

@dataclass
class Vista:
    """Datos de la plantilla única. `datos` tiene siempre la forma de la foto fija:
    emitido, la guardada; sin emitir, la misma calculada ahora, sin guardar nada."""
    datos: dict
    emitido: bool
    limpio: bool
    pendientes: list                      # [str], solo en el borrador
    copias: list                          # [cert_cierre_fase.Vista], una por fase
    enlace_instruccion: Optional[str] = None
    advertencia: Optional[str] = None
    certificado_id: Optional[int] = None
    documento_certificado_id: Optional[int] = None
    emitido_en: Optional[str] = None
    calculado_en: Optional[str] = None


def vista(solicitud) -> Vista:
    """La vista del certificado de cierre de `solicitud`: el emitido, leído de su
    foto fija; o, si no lo hay, el informe calculado al vuelo."""
    certificado = sellos.certificado_cierre_solicitud(solicitud)
    if certificado is not None:
        datos = certificado.datos or {}
        momento = sellos.momento_emision(certificado)
        return Vista(
            datos=datos, emitido=True, limpio=True, pendientes=[],
            copias=_vistas_de_copias(datos),
            enlace_instruccion=_enlace_instruccion(solicitud.expediente_id, datos),
            certificado_id=certificado.id,
            documento_certificado_id=certificado.documento_id,
            emitido_en=momento.strftime('%d/%m/%Y %H:%M') if momento else None,
        )

    informe = revisar(solicitud)
    datos = foto_fija(informe)
    return Vista(
        datos=datos, emitido=False, limpio=informe.limpio, pendientes=informe.pendientes,
        copias=_vistas_de_copias(datos),
        enlace_instruccion=_enlace_instruccion(solicitud.expediente_id, datos),
        advertencia=(informe.advertencia or {}).get('motivo'),
        calculado_en=datetime.now().strftime('%d/%m/%Y %H:%M'),
    )


def _vistas_de_copias(datos: dict) -> list:
    """Cada copia, como la vista emitida de su certificado de fase: misma plantilla."""
    return [
        cert_cierre_fase.vista_emitida(
            c.get('datos') or {}, fase_id=c.get('fase_id'),
            certificado_id=c.get('certificado_id'),
            documento_certificado_id=c.get('documento_id'),
            emitido_en=c.get('emitido'), fase_nombre=c.get('fase') or '',
        )
        for c in datos.get('fases') or []
    ]


def _enlace_instruccion(expediente_id: int, datos: dict) -> Optional[str]:
    """El enlace al PDF del fin de instrucción, el mismo que da el inspector para
    ese documento (`detalle_nodo.info_apertura_documento`). Se calcula al pintar:
    el documento no puede desaparecer mientras exista la fase que resuelve
    (`_check_deshacer_cert_fin_instruccion`)."""
    instruccion = datos.get('instruccion') or {}
    documento_id = instruccion.get('documento_id')
    if documento_id is None:
        return None
    documento = db.session.get(Documento, documento_id)
    if documento is None:
        return None
    from app.services.detalle_nodo import info_apertura_documento
    return info_apertura_documento(expediente_id, documento, estricto=False).get('enlace')


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def _por_fase(actos: list) -> list:
    """Agrupa los actos por la fase que los resuelve (o la que les tocaría, si no
    existe), en el orden en que aparecen."""
    grupos: dict = {}
    for acto in actos:
        clave = acto.fase.id if acto.fase is not None else acto.fase_codigo
        grupos.setdefault(clave, []).append(acto)
    return list(grupos.values())


def _nombres_fases_resolutoras() -> dict:
    """Nombre de cada tipo de fase que resuelve actos, para nombrar las que aún no
    se han creado. Una consulta; sin catálogo, el código."""
    from app.models.tipos_fases import TipoFase
    try:
        filas = TipoFase.query.filter(TipoFase.codigo.in_(FASES_RESOLUTORAS)).all()
    except (OperationalError, ProgrammingError) as exc:
        log.warning('cert_cierre_solicitud: catálogo de tipos de fase no disponible — %s', exc)
        return {}
    return {tf.codigo: (tf.nombre or tf.codigo) for tf in filas}


def _solicitante(solicitud) -> str:
    entidad = solicitud.entidad
    if entidad is None:
        return ''
    return f'{entidad.nombre_completo} ({entidad.nif})' if entidad.nif else entidad.nombre_completo


def _duracion(valor, unidad) -> str:
    if valor is None:
        return ''
    singular, plural = _UNIDADES.get(unidad, (unidad, unidad))
    return f'{valor} {singular if valor == 1 else plural}'


def _enumerar(elementos: list) -> str:
    """«AAP», «AAP y AAC», «AAP, AAC y DUP»."""
    if len(elementos) <= 1:
        return ''.join(elementos)
    return f'{", ".join(elementos[:-1])} y {elementos[-1]}'


def _nombre_fase(fase) -> str:
    tf = fase.tipo_fase
    return (tf.nombre or tf.codigo) if tf else f'Fase #{fase.id}'


def _nombre_tarea(tarea) -> str:
    """«Trámite › Tarea (#id)»: lo que el técnico busca en el árbol."""
    tt = tarea.tipo_tarea
    tr = tarea.tramite.tipo_tramite
    nombre_tarea = (tt.nombre if tt else None) or 'Tarea'
    nombre_tramite = (tr.nombre if tr else None) or 'Trámite'
    return f'{nombre_tramite} › {nombre_tarea} (#{tarea.id})'


def _fecha(valor) -> str:
    return valor.strftime('%d/%m/%Y') if valor else ''


def _local(momento: datetime) -> datetime:
    """Un `DateTime` sin zona guardado en UTC, en la hora del servidor (mismo
    criterio que `sellos.momento_emision`)."""
    return momento.replace(tzinfo=timezone.utc).astimezone()
