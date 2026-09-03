"""
Emisión del CERT_FIN_INSTRUCCION — la bisagra entre instrucción y resolución.

ADR-043. La fase finalizadora no se abre porque el sistema recuente fases: se
abre porque consta emitido el certificado de fin de instrucción de esa solicitud
(art. 82.1 LPACAP, «Instruidos los procedimientos, e inmediatamente antes de
redactar la propuesta de resolución…»). Este módulo es quien lo emite, y con él
deja de estar sin dueño el tipo documental que el catálogo declara ENTRADA
obligatoria del ELABORAR de ELABORACION.

GESTO EXPLÍCITO, NO AUTOMATISMO (decisión de #827)
==================================================

La emisión la pide el técnico desde el inspector de la solicitud; no se dispara
sola al cerrar la última fase. «Instruidos los procedimientos» es un hecho que
alguien declara (ADR-043 §B): automatizarlo lo convertiría en efecto colateral de
cerrar una fase, «la última fase de instrucción» no es determinable —nada impide
que aparezca otra después— y sería opaco justo donde importa, cuando el invariante
impida la emisión. Mismo criterio que `certificados.crear_cert` (CERT_PLAZO_CUMPLIDO);
el contraejemplo automático es `cert_fin_ip_consultas`, la deuda que ADR-043 §D
pone a la vista.

POR QUÉ SE ANCLA ANTES DE AUDITAR
=================================

El orden de los pasos no es casual. El certificado congela un `AuditoriaResult`
—«el fundamento jurídico que habilita la resolución»— y la auditoría natural es la
de abrir la fase finalizadora. Pero las dos reglas del art. 82.1 casan justamente
con ese sujeto: mientras el certificado no conste, disparan. Auditar antes de
anclar produciría un certificado que declara bloqueada la resolución por falta del
certificado que se está emitiendo. Por eso se crea el `Documento`, se fija la FK y
solo entonces se audita: el snapshot refleja el estado en que la resolución queda
efectivamente habilitada.

Lo que este servicio NO hace: bloquear porque otra regla del motor siga disparando
(tasa impagada, organismos sin cerrar…). Esas son contenido normativo escapable
con justificación y bloquean donde les toca —al crear la fase—; aquí solo se
constata su estado, y el PDF lo hace constar tal cual. La única puerta cerrada es
el invariante de ADR-043 §E (`check_invariante('EMITIR', …)`).

Deshacer un certificado ya emitido es acto expreso y caro a propósito: va con el
sello de la instrucción (#838, ADR-043 §F), no aquí.
"""
from __future__ import annotations

import logging

from flask_login import current_user

from app import db
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_fases import TipoFase
from app.services import bitacora as bitacora_svc
from app.services.assembler import auditar_multi
from app.services.generador_cert import generar_certificado_fase
from app.services.invariantes_esftt import check_invariante
from app.services.mutaciones_arbol import ResultadoMutacion
from app.services.plazos import _hoy

log = logging.getLogger(__name__)

CODIGO_CERT = 'CERT_FIN_INSTRUCCION'

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


def codigo_fase_finalizadora(solicitud) -> str:
    """Código del `TipoFase` finalizador que esta solicitud abrirá."""
    tipo_sol = solicitud.tipo_solicitud
    siglas = tipo_sol.siglas if tipo_sol else None
    return _FASE_FINALIZADORA_POR_SIGLAS.get(siglas, _FASE_FINALIZADORA_DEFECTO)


def puede_emitirse(solicitud) -> tuple[bool, str]:
    """(emisible, motivo) sin efectos secundarios — para que la UI sepa si ofrecer
    el gesto y, si no, por qué. Misma respuesta que daría `emitir_…`, obtenida de
    las mismas dos comprobaciones para que no puedan divergir."""
    if solicitud.documento_fin_instruccion_id is not None:
        return False, 'El certificado de fin de instrucción de esta solicitud ya está emitido.'
    res_inv = check_invariante('EMITIR', 'SOLICITUD', solicitud.id,
                               tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        return False, res_inv.motivo or res_inv.norma_compilada
    return True, ''


def emitir_cert_fin_instruccion(solicitud) -> ResultadoMutacion:
    """
    Emite el certificado de fin de instrucción de `solicitud` y lo ancla a ella.

    Devuelve `ResultadoMutacion` con `ids=[documento_id]`, o con `bloqueo` si el
    invariante de ADR-043 §E lo impide (puerta cerrada, sin justificación posible).
    """
    if solicitud.documento_fin_instruccion_id is not None:
        return ResultadoMutacion(
            ok=False,
            error='El certificado de fin de instrucción de esta solicitud ya está emitido.',
        )

    # Puerta cerrada (ADR-043 §E): fases de instrucción sin cerrar, o ninguna fase.
    # Antes que nada — no se crea ni un Documento si la instrucción no ha terminado.
    res_inv = check_invariante('EMITIR', 'SOLICITUD', solicitud.id,
                               tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_CERT).first()
    if tipo_doc is None:
        return ResultadoMutacion(
            ok=False,
            error=f'TipoDocumento {CODIGO_CERT!r} no encontrado en el catálogo.',
        )

    expediente = solicitud.expediente
    tipo_fase_fin = TipoFase.query.filter_by(
        codigo=codigo_fase_finalizadora(solicitud)).first()

    try:
        # 1. Documento con url provisional y ancla a la solicitud. El destino real
        #    depende del id del certificado, que aún no existe; lo completa
        #    `generar_certificado_fase` (mismo patrón de url provisional que
        #    `certificados.crear_cert` y `cert_fin_ip_consultas`).
        doc = Documento(
            expediente_id=expediente.id,
            tipo_doc_id=tipo_doc.id,
            url=f'bddat://certificados/pendiente-{CODIGO_CERT}',
            tipo_contenido='application/pdf',
            fecha_administrativa=_hoy(),
            asunto=f'Certificado de fin de instrucción — solicitud #{solicitud.id}',
        )
        db.session.add(doc)
        db.session.flush()

        solicitud.documento_fin_instruccion_id = doc.id
        db.session.flush()

        # 2. Auditoría CON el certificado ya anclado (ver encabezado del módulo).
        auditoria = auditar_multi(
            'CREAR', expediente,
            objeto={'solicitud': solicitud, 'tipo_fase': tipo_fase_fin},
        )

        # 3. Snapshot inmutable + PDF. `fase=None`: este certificado no es de una
        #    fase, certifica la instrucción completa (ADR-043 §D).
        cert = generar_certificado_fase(
            expediente, None, auditoria, CODIGO_CERT,
            documento=doc, solicitud=solicitud,
        )
        if cert.ruta_pdf is None:
            # El PDF no se generó: el ancla apuntaría a un documento sin fichero,
            # que es peor que no tener certificado. `generar_certificado_fase`
            # ya dejó el error en el log.
            db.session.rollback()
            return ResultadoMutacion(
                ok=False,
                error='No se pudo generar el PDF del certificado. Revise el log del servidor.',
            )

        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'documentos', doc.id,
            detalle={
                'tipo_documento': CODIGO_CERT,
                'solicitud_id': solicitud.id,
                'sujeto_auditado': auditoria.sujeto,
                'auditoria_permitida': auditoria.permitido,
                'certificado_fase_id': cert.id,
            },
        )

        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('emitir_cert_fin_instruccion: fallo en solicitud %s: %s',
                  solicitud.id, exc)
        return ResultadoMutacion(ok=False, error=str(exc))

    log.info(
        'CERT_FIN_INSTRUCCION emitido: doc=%s cert=%s solicitud=%s expediente=%s '
        '(auditoría %s sobre %s)',
        doc.id, cert.id, solicitud.id, expediente.id,
        'permitida' if auditoria.permitido else 'con bloqueos', auditoria.sujeto,
    )
    return ResultadoMutacion(ok=True, ids=[doc.id])
