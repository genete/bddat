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

Deshacer un certificado ya emitido es acto expreso y caro a propósito: va con el
sello de la instrucción (#838, ADR-043 §F), no aquí.
"""
from __future__ import annotations

import logging
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
