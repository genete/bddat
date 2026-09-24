"""
CERT_CUMPLIMIENTO_FASE — el sello del cumplimiento del plazo de resolver (#947, N4).

ADR-049 §E/§F. Desde #930 (N2) el plazo de resolver de cada acto se da por
cumplido **calculándolo en cada lectura**: se busca en la fase que resuelve el
acto la notificación al titular y se toma el documento más antiguo que la
acredita. Funciona, pero nada lo fija: meses después, cambiar la fecha de ese
justificante, su tipo, desvincularlo o subir otro con fecha anterior cambia el
cumplimiento en silencio.

Este certificado es el momento en que la Administración dice «esto consta y no se
mueve». Deja escrito **qué documento** acredita la notificación al titular
(`datos = {"documento_id": N}`, y nada más). Desde entonces:

- el plazo lee el certificado en vez de recalcular (`sellos`,
  `notificaciones.documento_cumplimiento_fase`);
- el documento citado queda protegido: fecha, tipo, fichero, desvinculación y
  borrado (`sellos.motivo_sellado`, que consultan el pool y `editar_tarea`);
- la única forma de corregirlo es **deshacerlo**, con justificación y rastro en
  bitácora, y volver a emitirlo.

GESTO MANUAL, TRES DESENLACES Y NINGÚN ERROR (patrón `cert_fin_instruccion`)
==========================================================================
El botón de la fase siempre responde con la misma vista: si falta algo, la vista
dice qué y no se crea nada; si está todo, se emite y se muestra; si ya estaba
emitido, se muestra. «Falta la notificación» no es un error: es el borrador
calculado, que no se guarda (§F: «el borrador no se guarda, se calcula y se
muestra»).

Emitir con la fase ya cerrada **se permite**: no muta su interior —sella lo que
ADR-036 ya sella— y cubre las fases cerradas antes de que existiera este
certificado. Deshacer, en cambio, solo con la fase abierta.

SIN PDF: UNA VISTA HTML ÚNICA (#947, D2)
=======================================
El borrador calculado y el certificado emitido se pintan con la misma plantilla;
solo cambia de dónde salen los datos (`vista`). Un PDF generado al vuelo no es
una foto fija de nada, es otra forma de ver los datos; pasarlo a PDF es posterior
(issue futuro). Ser certificado se lee de la fila de `certificados`, nunca de la
url (ver `sellos`).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from flask_login import current_user

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services import bitacora as bitacora_svc
from app.services import notificaciones as notif_svc
from app.services import sellos
from app.services.actos_solicitud import actos_de, fase_de
from app.services.assembler import build_sujeto
from app.services.invariantes_esftt import check_invariante

log = logging.getLogger(__name__)

CODIGO_CERT = sellos.CERT_CUMPLIMIENTO_FASE

# Cómo consta el deshacer en bitácora: sobre `fases`, como `reabrir_fase`, porque
# el certificado y su documento desaparecen y lo que permanece es la fase. Sin
# `escape: True`, por el mismo motivo que `cert_fin_instruccion.ACCION_DESHACER`:
# ese marcador significa «se forzó un bloqueo del motor», y aquí no se fuerza nada.
ACCION_DESHACER = 'DESHACER_CERT_CUMPLIMIENTO_FASE'

# Lo que el técnico lee del canal de cada justificante de cumplimiento. El canal
# es implícito en el tipo (`notificaciones.CANAL_POR_TIPO_DOC`); el anuncio del
# edicto no tiene canal propio (#568).
_CANAL_LEGIBLE = {
    'NOTIFICA': 'Notifica (electrónica)',
    'POSTAL': 'Correo postal',
}


# ---------------------------------------------------------------------------
# Revisión — la vista calculada, sin efectos
# ---------------------------------------------------------------------------

@dataclass
class Revision:
    """Lo que el certificado citaría si se emitiera ahora, o qué falta."""
    fase: object
    finalizadora: bool
    documento: Optional[Documento] = None          # el que se citaría (cálculo)
    tareas_notificar: list = field(default_factory=list)  # NOTIFICAR del titular

    @property
    def falta(self) -> Optional[str]:
        if not self.finalizadora:
            return ('Solo las fases finalizadoras tienen certificado de cumplimiento: '
                    'esta fase no resuelve ningún acto.')
        if self.documento is not None:
            return None
        if not self.tareas_notificar:
            return ('No consta la notificación al titular: la fase todavía no tiene la '
                    'tarea «Notificar» del trámite «Notificación».')
        return ('No consta la notificación al titular: la tarea «Notificar» del '
                'trámite «Notificación» no tiene vinculado ningún justificante que la '
                'acredite (puesta a disposición en Notifica, acuse postal —del primer '
                'intento o definitivo— o anuncio publicado).')


def revisar(fase) -> Revision:
    """El cálculo, sin crear nada y sin mirar el sello: qué documento citaría el
    certificado (`notificaciones.calcular_documento_cumplimiento_fase`) o qué
    falta. Es el borrador de la vista y el paso previo de `emitir`."""
    finalizadora = bool(fase.tipo_fase and fase.tipo_fase.es_finalizadora)
    if not finalizadora:
        return Revision(fase=fase, finalizadora=False)
    return Revision(
        fase=fase,
        finalizadora=True,
        documento=notif_svc.calcular_documento_cumplimiento_fase(fase),
        tareas_notificar=[
            tarea
            for tramite in fase.tramites
            for tarea in tramite.tareas
            if notif_svc.es_notificar_del_titular(tarea)
        ],
    )


# ---------------------------------------------------------------------------
# Emitir — el gesto manual
# ---------------------------------------------------------------------------

@dataclass
class Emision:
    """Resultado del gesto: siempre hay revisión; a veces, además, certificado.

    `error` y `bloqueo` son para fallos reales (fase no finalizadora, catálogo
    sin el tipo, la puerta cerrada dijo que no), no para «falta la notificación»:
    eso es la revisión con `falta`, y no se ha creado nada.
    """
    revision: Revision
    emitido: bool = False       # hay certificado: recién emitido o ya estaba
    ya_emitido: bool = False    # ya estaba antes de este gesto
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None
    bloqueo: object = None

    def a_dict(self) -> dict:
        return {
            'emitido': self.emitido,
            'ya_emitido': self.ya_emitido,
            'documento_id': self.documento_id,
            'certificado_id': self.certificado_id,
            'falta': None if self.emitido else self.revision.falta,
        }


def emitir(fase) -> Emision:
    """Emite el `CERT_CUMPLIMIENTO_FASE` de `fase` si consta la notificación al
    titular; si no, devuelve la revisión con lo que falta y no crea nada.

    El certificado es un `Documento` (`fecha_administrativa` NULL —no tiene fecha
    propia, §F—, url `bddat://certificados/{id}`, sin vínculo a tarea: excepción
    aceptada por ADR-049 §B) más su fila de `certificados` con `tipo`, `fase_id`
    y `datos = {"documento_id": <citado>}`. Bitácora `CREAR documentos` con el
    documento citado.
    """
    existente = sellos.certificado_cumplimiento(fase)
    if existente is not None:
        # No es un error: el botón «si ya existe, lo muestra».
        return Emision(
            revision=revisar(fase), emitido=True, ya_emitido=True,
            documento_id=existente.documento_id, certificado_id=existente.id,
        )

    revision = revisar(fase)
    if not revision.finalizadora:
        return Emision(revision=revision, error=revision.falta)
    if revision.documento is None:
        return Emision(revision=revision)

    # Puerta cerrada: sus dos supuestos ya los cubre la revisión; se comprueba
    # igualmente porque el invariante tiene la última palabra (mismo criterio que
    # `cert_fin_instruccion.consolidar`).
    res_inv = check_invariante('EMITIR', 'FASE', fase.id, tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        log.warning('cert_cumplimiento_fase: la revisión de la fase %s salió completa '
                    'pero el invariante bloquea — %s', fase.id,
                    res_inv.motivo or res_inv.norma_compilada)
        return Emision(revision=revision, bloqueo=res_inv)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_CERT).first()
    if tipo_doc is None:
        return Emision(revision=revision,
                       error=f'TipoDocumento {CODIGO_CERT!r} no encontrado en el catálogo.')

    citado = revision.documento
    expediente = fase.solicitud.expediente
    try:
        documento = Documento(
            expediente_id=expediente.id,
            tipo_doc_id=tipo_doc.id,
            url='bddat://certificados/0',   # provisional hasta tener cert.id
            fecha_administrativa=None,
            asunto=f'Cumplimiento del plazo de resolver — {_nombre_fase(fase)}',
        )
        db.session.add(documento)
        db.session.flush()

        # Por las relaciones y no por los id a pelo: así `fase.certificados_cumplimiento`
        # y `documento.certificado`, si ya estaban cargados, ven el certificado nuevo.
        certificado = Certificado(
            documento=documento, tipo=CODIGO_CERT, fase=fase,
            datos={'documento_id': citado.id},
            # Explícito y no por el default del modelo (`utcnow`, obsoleto): la
            # misma hora UTC sin zona que ya guarda la columna.
            generado_en=datetime.now(UTC).replace(tzinfo=None),
        )
        db.session.add(certificado)
        db.session.flush()
        documento.url = f'bddat://certificados/{certificado.id}'

        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'documentos', documento.id,
            detalle={
                'tipo_documento': CODIGO_CERT,
                'fase_id': fase.id,
                'certificado_id': certificado.id,
                'documento_citado_id': citado.id,
                'sujeto': build_sujeto(expediente, fase),
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cumplimiento_fase: fallo emitiendo el de la fase %s: %s', fase.id, exc)
        return Emision(revision=revision, error=str(exc))

    log.info('CERT_CUMPLIMIENTO_FASE emitido: doc=%s cert=%s fase=%s cita=%s expediente=%s',
             documento.id, certificado.id, fase.id, citado.id, expediente.id)
    return Emision(revision=revision, emitido=True,
                   documento_id=documento.id, certificado_id=certificado.id)


# ---------------------------------------------------------------------------
# Deshacer — el acto que retira el sello
# ---------------------------------------------------------------------------

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


def deshacer(fase, *, justificacion: str) -> Reversion:
    """Retira el `CERT_CUMPLIMIENTO_FASE` de `fase` y con él el sello: el plazo
    vuelve a calcularse y el documento que citaba deja de estar protegido.

    - `justificacion` obligatoria (mismo criterio que `reabrir_fase` y
      `cert_fin_instruccion.deshacer`: no hay reversión silenciosa).
    - Solo con la fase abierta (`check_invariante('DESHACER', …)`): si está
      cerrada, reabrirla antes; si la resolución es firme, `_check_reabrir` ya
      cierra esa puerta.
    - Borra la fila de `certificados` y su `Documento`; no hay fichero que borrar.
    - Bitácora `ALTERAR fases` con la justificación **y el documento que citaba**:
      queda rastro aunque la fila desaparezca.
    """
    if not justificacion or not justificacion.strip():
        return Reversion(
            error='Deshacer el certificado de cumplimiento requiere justificación.')

    certificado = sellos.certificado_cumplimiento(fase)
    if certificado is None:
        return Reversion(error='Esta fase no tiene certificado de cumplimiento que deshacer.')

    res_inv = check_invariante('DESHACER', 'FASE', fase.id, tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        return Reversion(bloqueo=res_inv)

    documento = certificado.documento
    # Nada lo consume por catálogo, pero la Despensa deja vincular cualquier
    # documento del pool. Borrarlo con el vínculo vivo moriría en IntegrityError
    # (el ORM intentaría dejar `documentos_tarea.documento_id` a NULL): se dice
    # quién lo usa, igual que el pool con los documentos referenciados.
    if documento.vinculos_tarea:
        tarea = documento.vinculos_tarea[0].tarea
        return Reversion(error=(
            f'El certificado está vinculado a la tarea «{_nombre_tarea(tarea)}»: '
            f'desvincúlelo de ella antes de deshacerlo.'
        ))

    documento_id = documento.id
    certificado_id = certificado.id
    citado_id = (certificado.datos or {}).get('documento_id')
    expediente = fase.solicitud.expediente

    try:
        db.session.delete(certificado)
        db.session.flush()
        db.session.delete(documento)
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'fases', fase.id,
            detalle={
                'accion': ACCION_DESHACER,
                'justificacion': justificacion.strip(),
                'tipo_documento': CODIGO_CERT,
                'documento_id': documento_id,
                'certificado_id': certificado_id,
                'documento_citado_id': citado_id,
                'sujeto': build_sujeto(expediente, fase),
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cumplimiento_fase: fallo deshaciendo el de la fase %s: %s', fase.id, exc)
        return Reversion(error=str(exc))

    log.info('CERT_CUMPLIMIENTO_FASE deshecho: doc=%s cert=%s fase=%s citaba=%s',
             documento_id, certificado_id, fase.id, citado_id)
    return Reversion(ok=True, documento_id=documento_id, certificado_id=certificado_id)


# ---------------------------------------------------------------------------
# Vista — lo que pinta la plantilla, emitido o calculado
# ---------------------------------------------------------------------------

@dataclass
class VistaDocumento:
    id: int
    tipo: str
    fecha: Optional[str]
    canal: str
    tarea: Optional[str]


@dataclass
class Vista:
    """Datos de la plantilla única. Solo lo que no se mueve: la fase, los actos
    que resuelve, el documento citado y, si está emitido, la huella. **Sin
    veredicto de plazo** (cumplido o vencido): ese resultado «nunca se guarda: se
    pinta siempre» (§E), y ya lo pintan las barras del plazo (#922)."""
    expediente: str
    solicitud: str
    fase_id: int
    fase: str
    actos: list
    emitido: bool
    documento: Optional[VistaDocumento]
    falta: Optional[str]
    certificado_id: Optional[int] = None
    documento_certificado_id: Optional[int] = None
    emitido_en: Optional[str] = None
    calculado_en: Optional[str] = None


def vista(fase) -> Vista:
    """La vista del certificado de `fase`: el emitido, leído de lo sellado; o, si
    no lo hay, el borrador calculado al vuelo, sin guardar nada."""
    expediente = fase.solicitud.expediente
    tipo_sol = fase.solicitud.tipo_solicitud
    comun = dict(
        expediente=f'AT-{expediente.numero_at}',
        solicitud=tipo_sol.siglas if tipo_sol else f'Solicitud #{fase.solicitud_id}',
        fase_id=fase.id,
        fase=_nombre_fase(fase),
        actos=[acto.siglas for acto in actos_de(fase.solicitud) if fase_de(acto) is fase],
    )

    certificado = sellos.certificado_cumplimiento(fase)
    if certificado is not None:
        citado = sellos.documento_citado(certificado)
        momento = sellos.momento_emision(certificado)
        return Vista(
            **comun, emitido=True,
            documento=_vista_documento(fase, citado) if citado is not None else None,
            falta=None,
            certificado_id=certificado.id,
            documento_certificado_id=certificado.documento_id,
            emitido_en=momento.strftime('%d/%m/%Y %H:%M') if momento else None,
        )

    revision = revisar(fase)
    return Vista(
        **comun, emitido=False,
        documento=(_vista_documento(fase, revision.documento)
                   if revision.documento is not None else None),
        falta=revision.falta,
        calculado_en=datetime.now().strftime('%d/%m/%Y %H:%M'),
    )


def _vista_documento(fase, documento) -> VistaDocumento:
    codigo = documento.tipo_doc.codigo if documento.tipo_doc else None
    canal = notif_svc.canal_de_tipo(codigo) if codigo else None
    if canal is not None:
        canal_legible = _CANAL_LEGIBLE.get(canal, canal)
    elif codigo == 'ANUNCIO_PUBLICADO':
        canal_legible = 'Edicto (art. 44 LPACAP)'
    else:
        canal_legible = '—'
    tarea = next(
        (v.tarea for v in documento.vinculos_tarea if v.tarea.tramite.fase_id == fase.id),
        None,
    )
    return VistaDocumento(
        id=documento.id,
        tipo=documento.tipo_doc.nombre if documento.tipo_doc else f'Documento {documento.id}',
        fecha=(documento.fecha_administrativa.strftime('%d/%m/%Y')
               if documento.fecha_administrativa else None),
        canal=canal_legible,
        tarea=_nombre_tarea(tarea) if tarea is not None else None,
    )


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
