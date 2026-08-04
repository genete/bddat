"""
Tests #657/#658 — hook de editar_tarea para la tarea NOTIFICAR (ADR-034 §6).

Camino B (justificante definitivo): al fijar documento_producido_id en una
tarea NOTIFICAR, mapea tipo_doc→canal, parsea si es NOTIFICA (único canal con
parser, #655) y hace upsert de Notificacion por tarea_id, con cotejo no
bloqueante de identificador_envio (#658).

Contra la BD real de desarrollo (mismo patrón que test_667_mover_documento_
esftt.py — app_ctx con rollback por SAVEPOINT) + fs_tmp (#674) para que el
movimiento físico real de mover_a_esftt no toque el servidor de ficheros de
desarrollo. El PDF es sintético (reportlab), misma receta que
test_655_parser_justificante_notifica.py — no se comitea ningún justificante
real de terceros.
"""
import io
from datetime import date

import pytest
from reportlab.pdfgen import canvas

from app import db
from app.models.documentos import Documento
from app.models.notificaciones import Notificacion
from app.models.tareas import Tarea
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_tareas import TipoTarea
from app.services import mutaciones_arbol as svc

# Mismo texto de muestra que test_655 (datos ficticios, remesa 82541676, Leída).
TEXTO_JUSTIFICANTE = """\
Sistema de Notificaciones Electrónicas
Datos de la notificación
ID remesa: 82541676
ID notificación: 87718678
Destinatario: EMPRESA EJEMPLO, S.A.  Identificador: A00000000
Procedimiento: 9588 - Autorización administrativa previa para instalaciones de producción
Estados de la notificación
Puesta a disposición: 28/05/26 11:46
Estado: Leída
Fecha de lectura: 01/06/26 11:16
Generación del informe
Fecha y hora de generación: 02/06/26 07:50
"""


def _pdf_sintetico(texto: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    y = 800
    for linea in texto.splitlines():
        c.drawString(40, y, linea)
        y -= 14
    c.save()
    return buffer.getvalue()


def _tarea_notificar_real(app_ctx):
    """Tarea NOTIFICAR real sin vínculos documentales ni fila en notificaciones
    previos — evita pisar datos reales ajenos al test. Skip si no hay ninguna."""
    tarea = (
        Tarea.query
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .outerjoin(Notificacion, Notificacion.tarea_id == Tarea.id)
        .filter(
            TipoTarea.codigo == 'NOTIFICAR',
            ~Tarea.vinculos_documento.any(),
            Notificacion.id.is_(None),
        )
        .first()
    )
    if tarea is None:
        pytest.skip('No hay tareas NOTIFICAR sin vínculos/notificación en la BD de desarrollo')
    return tarea


def _tipo_doc(codigo):
    t = TipoDocumento.query.filter_by(codigo=codigo).first()
    if t is None:
        pytest.skip(f'Catálogo {codigo} no disponible en la BD de desarrollo')
    return t


def _documento_con_fichero(expediente_id, tipo_doc_id, fs_tmp, contenido_pdf, nombre='justificante.pdf'):
    (fs_tmp / nombre).write_bytes(contenido_pdf)
    doc = Documento(expediente_id=expediente_id, url=nombre, tipo_doc_id=tipo_doc_id,
                     asunto='#657 test')
    db.session.add(doc)
    db.session.flush()
    return doc


class TestHookNotificarCaminoBAutomatico:

    def test_justificante_notifica_reconocido_crea_fila(self, app_ctx, fs_tmp):
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')
        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is None
        notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
        assert notif is not None
        assert notif.canal == 'NOTIFICA'
        assert notif.identificador_envio == '82541676'
        assert notif.resultado == 'CORRECTA'
        assert notif.fecha_puesta_disposicion == date(2026, 5, 28)
        assert notif.fecha_resultado == date(2026, 6, 1)
        assert notif.documento_id == doc.id

    def test_pdf_no_reconocido_sin_fila_previa_no_crea_nada(self, app_ctx, fs_tmp):
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')
        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico('Esto no es un justificante.'))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert Notificacion.query.filter_by(tarea_id=tarea.id).first() is None

    def test_tipo_doc_sin_canal_reconocido_ignora_hook(self, app_ctx, fs_tmp):
        """Documento producido de un tipo ajeno a los 4 justificantes de notificación
        (p.ej. un tipo genérico) — el hook no hace nada, ni siquiera intenta parsear."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc_generico = TipoDocumento.query.filter(
            ~TipoDocumento.codigo.in_(
                ['JUSTIFICANTE_NOTIFICA', 'JUSTIFICANTE_BANDEJA', 'JUSTIFICANTE_SIR', 'JUSTIFICANTE_POSTAL']
            )
        ).first()
        if tipo_doc_generico is None:
            pytest.skip('No hay tipos de documento ajenos a NOTIFICAR en el catálogo')
        doc = _documento_con_fichero(
            expediente.id, tipo_doc_generico.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert Notificacion.query.filter_by(tarea_id=tarea.id).first() is None

    def test_canal_sin_parser_con_fila_previa_solo_actualiza_documento_id(self, app_ctx, fs_tmp):
        """SIR (sin parser, #655): con fila previa (camino A manual), el hook solo
        vincula documento_id — no toca resultado/fecha_resultado."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_SIR')

        notif = Notificacion(
            tarea_id=tarea.id, canal='SIR', identificador_envio='SIR-001',
            fecha_puesta_disposicion=date(2026, 5, 1),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(expediente.id, tipo_doc.id, fs_tmp, b'captura de pantalla (no PDF parseable)')

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.documento_id == doc.id
        assert notif.resultado is None
        assert notif.identificador_envio == 'SIR-001'

    def test_cotejo_coincide_actualiza_sin_advertencia(self, app_ctx, fs_tmp):
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')

        notif = Notificacion(
            tarea_id=tarea.id, canal='NOTIFICA', identificador_envio='82541676',
            fecha_puesta_disposicion=date(2026, 5, 28),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.resultado == 'CORRECTA'
        assert notif.documento_id == doc.id

    def test_cotejo_no_coincide_genera_advertencia_no_bloqueante(self, app_ctx, fs_tmp):
        """El riesgo real que motivó #658: justificante de otro expediente asociado
        a esta tarea. No bloquea — aviso, y el resultado se actualiza igualmente."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')

        notif = Notificacion(
            tarea_id=tarea.id, canal='NOTIFICA', identificador_envio='REMESA-DISTINTA',
            fecha_puesta_disposicion=date(2026, 5, 1),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is not None
        assert '82541676' in resultado.advertencia['motivo']
        assert 'REMESA-DISTINTA' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.identificador_envio == 'REMESA-DISTINTA'  # no se sobrescribe
        assert notif.resultado == 'CORRECTA'  # el resultado sí se actualiza

    def test_cotejo_canal_no_coincide_con_parser_actualiza_canal_y_avisa(self, app_ctx, fs_tmp):
        """#712 — bug real: notif.canal nunca se reasignaba. Registrado a mano como
        SIR y luego se vincula un justificante NOTIFICA — el documento manda."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')

        notif = Notificacion(
            tarea_id=tarea.id, canal='SIR', identificador_envio=None,
            fecha_puesta_disposicion=date(2026, 5, 1),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is not None
        assert 'NOTIFICA' in resultado.advertencia['motivo']
        assert 'SIR' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.canal == 'NOTIFICA'  # el documento manda, ya no se queda en SIR para siempre
        assert notif.resultado == 'CORRECTA'

    def test_cotejo_canal_no_coincide_sin_parser_tambien_avisa(self, app_ctx, fs_tmp):
        """El cotejo de canal no depende de que haya parser (a diferencia del cotejo
        de remesa) — el canal se deriva del tipo de documento, siempre disponible."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_SIR')

        notif = Notificacion(
            tarea_id=tarea.id, canal='BANDEJA', identificador_envio='X-1',
            fecha_puesta_disposicion=date(2026, 5, 1),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(expediente.id, tipo_doc.id, fs_tmp, b'captura de pantalla')

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is not None
        assert 'SIR' in resultado.advertencia['motivo']
        assert 'BANDEJA' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.canal == 'SIR'
        assert notif.resultado is None  # SIR no tiene parser — no se inventa un resultado

    def test_cotejo_canal_coincide_no_avisa(self, app_ctx, fs_tmp):
        """Caso base: canal ya registrado coincide con el del documento vinculado
        — sin aviso de canal (sigue sin aviso de remesa tampoco, #658)."""
        tarea = _tarea_notificar_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        tipo_doc = _tipo_doc('JUSTIFICANTE_NOTIFICA')

        notif = Notificacion(
            tarea_id=tarea.id, canal='NOTIFICA', identificador_envio='82541676',
            fecha_puesta_disposicion=date(2026, 5, 28),
        )
        db.session.add(notif)
        db.session.flush()

        doc = _documento_con_fichero(
            expediente.id, tipo_doc.id, fs_tmp, _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = svc.editar_tarea(
            tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.canal == 'NOTIFICA'
