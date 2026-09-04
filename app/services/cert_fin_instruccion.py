"""
Consolidación del CERT_FIN_INSTRUCCION — la bisagra entre instrucción y resolución.

ADR-043. La fase finalizadora no se abre porque el sistema recuente fases: se
abre porque consta emitido el certificado de fin de instrucción de esa solicitud
(art. 82.1 LPACAP, «Instruidos los procedimientos, e inmediatamente antes de
redactar la propuesta de resolución…»). Este módulo es quien lo produce, y con él
deja de estar sin dueño el tipo documental que el catálogo declara ENTRADA
obligatoria del ELABORAR de ELABORACION.

NO ES UNA PUERTA, ES UNA REVISIÓN QUE A VECES SE CONSOLIDA (§E, reescrita)
=========================================================================

El técnico pregunta «¿cómo va esto?» en cualquier momento, desde el primer día de
la solicitud, y siempre obtiene un informe (`informe_instruccion.revisar`). Solo
cuando ese informe sale sin pendientes, ese mismo informe **se consolida** en el
certificado. Dos desenlaces y ningún error: con pendientes no se crea nada y se
puede volver a preguntar mañana.

La redacción anterior de §E hacía de esto una puerta que concedía o denegaba, y
dejaba que la emisión siguiera adelante aunque el motor bloqueara. El efecto se vio
al implementarlo: un certificado que declara bloqueada la resolución **ocupa el
ancla de §D** y, como deshacerlo es #838, impide emitir el bueno cuando se resuelve
lo que faltaba. Un certificado que dice «esto no está listo» no acredita nada: no
sirve como ENTRADA del ELABORAR que el catálogo le exige ser, ni de ancla para el
sello de #838.

EVALUAR PRIMERO, SIN CREAR NADA; CONSOLIDAR DESPUÉS (§E ter)
============================================================

El orden no es libre. Las dos reglas del art. 82.1 casan con el sujeto de la fase
finalizadora, así que mientras el certificado no conste, disparan. Antes se
resolvía anclando un `Documento` con url provisional para poder auditar con el
certificado ya puesto; ahora no hace falta ningún rodeo: se evalúa, y solo si el
informe sale limpio se crea algo. La regla del art. 82.1 se excluye del criterio de
«¿limpio?» **por definición** —es la única que este acto satisface, y esperar a que
deje de disparar sola sería esperar a nunca—, y el PDF la presenta como satisfecha
por el propio certificado en vez de como bloqueo.

GESTO EXPLÍCITO, NO AUTOMATISMO (decisión de #827)
==================================================

Lo pide el técnico desde el inspector de la solicitud; no se dispara solo al cerrar
la última fase. «Instruidos los procedimientos» es un hecho que alguien declara
(§B): automatizarlo lo convertiría en efecto colateral de cerrar una fase, «la
última fase de instrucción» no es determinable —nada impide que aparezca otra
después— y sería opaco justo donde importa. Mismo criterio que
`certificados.crear_cert` (CERT_PLAZO_CUMPLIDO); el contraejemplo automático es
`cert_fin_ip_consultas`, la deuda que ADR-043 §D pone a la vista.

DESHACER: EL ACTO QUE RETIRA EL SELLO (#838, ADR-043 §F)
========================================================

Emitido el certificado, la instrucción queda sellada: no se abre una fase de
instrucción nueva ni se reabre una cerrada (`invariantes_esftt`, las dos caras del
mismo acto). Cuando resulta que la instrucción no estaba terminada de verdad, la vía
no es contradecir el certificado sino retirarlo — y entonces vuelve a haber
instrucción abierta.

Es acto expreso y caro a propósito. Caro no por fricción artificial: `deshacer` no
cascadea nada, así que el técnico tiene que haber rebobinado antes la fase que
resuelve, paso a paso y pasando cada uno por su propio check. Y expreso porque exige
justificación, que queda en bitácora y la relata el informe del certificado
siguiente: quien redacte la resolución verá que hubo uno anterior y por qué se retiró.

Lo que borra es todo el rastro documental —la FK, el `CertificadoFase`, el `Documento`
y el PDF—, decisión de Carlos (2026-09-04) frente a desvincular o revocar. Un
certificado huérfano en el pool seguiría afirmando que la instrucción terminó, que es
el «documento que miente» que §E declaró inaceptable; y revocar exigiría un concepto
de anulación que no existe, para un documento interno autogenerado que nadie ha
notificado a nadie.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from flask_login import current_user

from app import db
from app.models.tipos_documentos import TipoDocumento
from app.services import bitacora as bitacora_svc
from app.services import informe_instruccion as informe_svc
from app.services.generador_cert import generar_certificado_fase
from app.services.invariantes_esftt import check_invariante

log = logging.getLogger(__name__)

CODIGO_CERT = 'CERT_FIN_INSTRUCCION'

# El mapa de fase finalizadora vive en `informe_instruccion`, que es quien
# pregunta al motor. Se reexporta aquí porque el nombre sigue leyéndose mejor
# desde el certificado, y para no romper a quien ya lo importaba de este módulo.
codigo_fase_finalizadora = informe_svc.codigo_fase_finalizadora


@dataclass
class Consolidacion:
    """Resultado del gesto: siempre hay informe; a veces, además, certificado.

    `error` y `bloqueo` son para fallos reales —ya estaba emitido, el PDF no se
    generó, la puerta cerrada dijo que no—, no para «faltan cosas»: eso no es un
    error, es el informe con pendientes, y viaja en `informe`.
    """
    informe: object
    consolidado: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None
    bloqueo: object = None

    def a_dict(self) -> dict:
        datos = self.informe.a_dict()
        datos.update({
            'consolidado': self.consolidado,
            'documento_id': self.documento_id,
            'certificado_id': self.certificado_id,
        })
        return datos


def revisar(solicitud):
    """Informe de la instrucción, sin efectos. Atajo del servicio del informe."""
    return informe_svc.revisar(solicitud)


def consolidar(solicitud) -> Consolidacion:
    """
    Revisa la instrucción de `solicitud` y, si no queda nada pendiente, consolida
    el informe en el CERT_FIN_INSTRUCCION anclado a ella (ADR-043 §D).

    Devuelve siempre `Consolidacion` con el informe dentro: con pendientes,
    `consolidado=False` y nada creado; sin pendientes, el certificado emitido.
    """
    if solicitud.documento_fin_instruccion_id is not None:
        return Consolidacion(
            informe=revisar(solicitud),
            documento_id=solicitud.documento_fin_instruccion_id,
            error='El certificado de fin de instrucción de esta solicitud ya está emitido.',
        )

    informe = revisar(solicitud)
    if not informe.limpio:
        return Consolidacion(informe=informe)

    # Puerta cerrada (ADR-043 §E). Sus dos supuestos —fases de instrucción sin
    # cerrar, o ninguna fase— ya los cubre el informe, que los recoge del árbol; se
    # comprueba igualmente porque es el invariante quien tiene la última palabra y
    # quien seguiría aplicando con el motor en modo global INACTIVO. Si alguna vez
    # discrepara del informe, manda él: certificar que la instrucción terminó cuando
    # no ha terminado no es un juicio de negocio discutible, es un documento que
    # miente (§B).
    res_inv = check_invariante('EMITIR', 'SOLICITUD', solicitud.id,
                               tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        log.warning('cert_fin_instruccion: el informe de la solicitud %s salió limpio '
                    'pero el invariante bloquea — %s', solicitud.id,
                    res_inv.motivo or res_inv.norma_compilada)
        return Consolidacion(informe=informe, bloqueo=res_inv)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_CERT).first()
    if tipo_doc is None:
        return Consolidacion(
            informe=informe,
            error=f'TipoDocumento {CODIGO_CERT!r} no encontrado en el catálogo.',
        )

    try:
        # `fase=None`: este certificado no es de una fase, certifica la instrucción
        # completa y se ancla a la solicitud (ADR-043 §D). El generador crea el
        # Documento con su url definitiva y cierra el vínculo por los dos lados.
        cert = generar_certificado_fase(
            solicitud.expediente, None, informe.auditoria, CODIGO_CERT,
            solicitud=solicitud, informe=informe,
        )
        if cert.ruta_pdf is None or cert.documento_id is None:
            # Sin PDF o sin documento, el ancla apuntaría a un certificado que no
            # existe como papel — peor que no tener certificado. `generar_certificado_fase`
            # ya dejó el error en el log.
            db.session.rollback()
            return Consolidacion(
                informe=informe,
                error='No se pudo generar el PDF del certificado. Revise el log del servidor.',
            )

        solicitud.documento_fin_instruccion_id = cert.documento_id
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'documentos', cert.documento_id,
            detalle={
                'tipo_documento': CODIGO_CERT,
                'solicitud_id': solicitud.id,
                'sujeto_auditado': informe.sujeto,
                'certificado_fase_id': cert.id,
                'actos_salvados': sum(len(b.salvado) for b in informe.salvados),
            },
        )

        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_fin_instruccion: fallo consolidando la solicitud %s: %s',
                  solicitud.id, exc)
        return Consolidacion(informe=informe, error=str(exc))

    log.info(
        'CERT_FIN_INSTRUCCION consolidado: doc=%s cert=%s solicitud=%s expediente=%s '
        '(sujeto %s, %s acto(s) salvado(s))',
        cert.documento_id, cert.id, solicitud.id, solicitud.expediente_id,
        informe.sujeto, sum(len(b.salvado) for b in informe.salvados),
    )
    return Consolidacion(
        informe=informe, consolidado=True,
        documento_id=cert.documento_id, certificado_id=cert.id,
    )


# ---------------------------------------------------------------------------
# Deshacer — el acto que retira el sello (#838, ADR-043 §F)
# ---------------------------------------------------------------------------

# Cómo consta el acto en bitácora. Se registra sobre `solicitudes` y no sobre
# `documentos` —al revés que la emisión, que anota el documento que nace— porque el
# documento deja de existir y lo que permanece es la solicitud: es ahí donde el
# informe del certificado SIGUIENTE lo encuentra para relatarlo.
#
# Y NO lleva `escape: True`, aunque también sea un acto excepcional con
# justificación. Ese marcador significa una cosa concreta en todo el sistema —se
# forzó un bloqueo del motor— y `informe_instruccion._relato_escapes` la da por
# supuesta al redactar («forzó el bloqueo del motor para…»). Aquí no se fuerza nada:
# la puerta se abre porque sus condiciones se cumplen. Marcarlo así produciría una
# frase falsa en el certificado y contaminaría el recuento de desviaciones.
ACCION_DESHACER = 'DESHACER_CERT_FIN_INSTRUCCION'


@dataclass
class Reversion:
    """Resultado de deshacer: qué se retiró, o por qué no pudo retirarse."""
    ok: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None
    bloqueo: object = None

    def a_dict(self) -> dict:
        return {
            'ok': self.ok,
            'documento_id': self.documento_id,
            'certificado_id': self.certificado_id,
        }


def deshacer(solicitud, *, justificacion: str) -> Reversion:
    """Retira el CERT_FIN_INSTRUCCION de `solicitud` y con él el sello de su
    instrucción (ADR-043 §F, vía 2: «la instrucción no estaba terminada de verdad»).

    Borra la FK, el `CertificadoFase`, el `Documento` y el PDF. `justificacion` es
    obligatoria —mismo criterio que `reabrir_fase`: no existe reversión silenciosa— y
    queda en bitácora, de donde la lee el informe del siguiente certificado.

    La puerta cerrada (`check_invariante('DESHACER', …)`) exige que no exista fase
    finalizadora: el rebobinado de la resolución es previo y lo hace el técnico paso a
    paso, porque un servicio que arrasara con ella para levantar el sello sería lo
    contrario de un acto caro.
    """
    if not justificacion or not justificacion.strip():
        return Reversion(
            error='Deshacer el certificado de fin de instrucción requiere justificación.')

    documento = solicitud.documento_fin_instruccion
    if documento is None:
        return Reversion(
            error='Esta solicitud no tiene certificado de fin de instrucción que deshacer.')

    res_inv = check_invariante('DESHACER', 'SOLICITUD', solicitud.id,
                               tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        return Reversion(bloqueo=res_inv)

    from app.models.certificados_fase import CertificadoFase

    documento_id = documento.id
    # Por el ancla, no por `CertificadoFase.documento_id`: esa vuelta se añadió en la
    # migración 827b y los certificados emitidos antes la tienen a NULL (el 901 de
    # AT-15, sin ir más lejos). El ancla, en cambio, existe desde el principio y es
    # la que define de quién es el certificado (§D). Sin fila que casar se borra solo
    # el documento: el sello lo levanta el ancla, no el certificado.
    cert = CertificadoFase.query.filter_by(documento_id=documento_id).first()
    certificado_id = cert.id if cert is not None else None
    # Se resuelven ANTES de borrar: después no hay objeto del que sacarlas.
    # `CertificadoFase.ruta_pdf` es absoluta y `Documento.url` relativa a
    # FILESYSTEM_BASE (ADR-032); las dos apuntan al mismo fichero, pero se recogen
    # las dos porque los certificados anteriores a 827b no tienen `CertificadoFase`
    # que casar y solo queda la del documento.
    rutas = _rutas_del_pdf(cert, documento)

    try:
        solicitud.documento_fin_instruccion_id = None
        db.session.flush()

        if cert is not None:
            db.session.delete(cert)
        db.session.delete(documento)
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'solicitudes', solicitud.id,
            detalle={
                'accion': ACCION_DESHACER,
                'justificacion': justificacion.strip(),
                'tipo_documento': CODIGO_CERT,
                'documento_id': documento_id,
                'certificado_fase_id': certificado_id,
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_fin_instruccion: fallo deshaciendo el de la solicitud %s: %s',
                  solicitud.id, exc)
        return Reversion(error=str(exc))

    _borrar_pdf(rutas)

    log.info('CERT_FIN_INSTRUCCION deshecho: doc=%s cert=%s solicitud=%s expediente=%s',
             documento_id, certificado_id, solicitud.id, solicitud.expediente_id)
    return Reversion(ok=True, documento_id=documento_id, certificado_id=certificado_id)


def _rutas_del_pdf(cert, documento) -> list:
    """Rutas absolutas candidatas del PDF, resueltas con los objetos todavía vivos.

    Defensivo por partida doble: `ruta_absoluta()` levanta si `FILESYSTEM_BASE` no
    está configurado o si la url no es del esquema local (los `bddat://` de las
    pruebas), y ninguno de esos casos debe impedir deshacer el certificado. Lo que
    manda son las filas; el fichero es consecuencia.
    """
    rutas = []
    ruta_cert = getattr(cert, 'ruta_pdf', None)
    if ruta_cert:
        rutas.append(ruta_cert)
    if documento.url and '://' not in documento.url:
        try:
            rutas.append(documento.ruta_absoluta())
        except (RuntimeError, ValueError) as exc:
            log.warning('cert_fin_instruccion: no se pudo resolver la ruta de %s — %s',
                        documento.url, exc)
    return rutas


def _borrar_pdf(rutas: list) -> None:
    """Borra el PDF del certificado, después del commit y sin poder revertirlo.

    Va detrás a propósito: si fallara antes, el rollback devolvería las filas pero no
    el fichero. Y su fallo no revierte nada —la BD ya dijo que el certificado no
    existe—, solo queda en el log: un PDF huérfano en disco no afirma nada que el
    sistema sostenga, mientras que una fila viva sí.

    Es el único sitio del proyecto que borra el fichero de un documento; el borrado
    del pool (`pool_borrar_documento`) deja el suyo. Aquí se borra porque el papel
    dice «la instrucción terminó» y acaba de dejar de ser cierto.
    """
    for ruta in rutas:
        try:
            if os.path.isfile(ruta):
                os.remove(ruta)
        except OSError as exc:
            log.warning('cert_fin_instruccion: no se pudo borrar el PDF %s — %s',
                        ruta, exc)
