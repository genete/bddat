"""
Tests #657/#658/#712 — hook de editar_tarea para la tarea NOTIFICAR (ADR-034 §6),
rehecho en #928 (ADR-049 §B; §6 del issue).

Al guardar una tarea NOTIFICAR, el hook deriva el canal del tipo de los
justificantes vinculados y hace upsert de Notificacion por tarea_id, con cotejo
no bloqueante del canal (#712) y de identificador_envio (#658). Desde #928:
crea la fila con cualquier canal (no solo el parseable) y **nunca escribe
`resultado`** (D2): lo fija el usuario; el parser solo lo propone. Los casos
propios de #928 (previos, sede, desvincular, rol incoherente) están en
test_928_hook_notificar.py.

Contra la BD de tests (app_ctx con rollback por SAVEPOINT) + fs_tmp (#674) para
que el movimiento físico real de mover_a_esftt no toque el servidor de ficheros.
El PDF es sintético (reportlab), misma receta que
test_655_parser_justificante_notifica.py — no se comitea ningún justificante
real de terceros. Los avisos del hook quedan en bitácora (D17), que necesita un
`current_user` real: fixture `con_usuario`.
"""
import io

import pytest
from reportlab.pdfgen import canvas

from app import db
from app.models.documentos import Documento
from app.models.notificaciones import Notificacion
from app.models.tipos_documentos import TipoDocumento
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


@pytest.fixture
def con_usuario(app_ctx):
    """Petición con usuario autenticado: la bitácora de los avisos del hook
    (D17) necesita `current_user` real."""
    from flask_login import login_user
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    with app_ctx.test_request_context():
        login_user(usuario)
        yield usuario


def _tarea_notificar():
    """Tarea NOTIFICAR sin vínculos ni fila en `notificaciones`, fabricada (#428)."""
    from tests.conftest import ArbolESFTT
    return ArbolESFTT(db).tarea_propia('NOTIFICAR', codigo_tramite='NOTIFICACION')


def _tipo_doc(codigo):
    t = TipoDocumento.query.filter_by(codigo=codigo).first()
    assert t is not None, f'la semilla debe traer el tipo de documento {codigo}'
    return t


def _documento_con_fichero(expediente_id, codigo_tipo, fs_tmp, contenido,
                           nombre='justificante.pdf'):
    from app.services.reloj_simulado import hoy
    (fs_tmp / nombre).write_bytes(contenido)
    doc = Documento(expediente_id=expediente_id, url=nombre,
                    tipo_doc_id=_tipo_doc(codigo_tipo).id,
                    asunto='#657 test', fecha_administrativa=hoy())
    db.session.add(doc)
    db.session.flush()
    return doc


def _fila_previa(tarea, canal, identificador_envio=None, resultado=None):
    notif = Notificacion(tarea_id=tarea.id, canal=canal,
                         identificador_envio=identificador_envio, resultado=resultado)
    db.session.add(notif)
    db.session.flush()
    return notif


def _producir(tarea, doc):
    return svc.editar_tarea(
        tarea, documentos_consumidos_ids=[], documento_producido_id=doc.id, notas=None)


class TestHookNotificarProducido:

    def test_justificante_notifica_reconocido_crea_fila_sin_resultado(self, con_usuario, fs_tmp):
        """El parseo solo aporta la remesa: el resultado lo fija el usuario (D2)."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert resultado.advertencia is None
        notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
        assert notif is not None
        assert notif.canal == 'NOTIFICA'
        assert notif.identificador_envio == '82541676'
        assert notif.resultado is None
        assert notif.documento_id == doc.id

    def test_pdf_no_reconocido_crea_fila_igualmente(self, con_usuario, fs_tmp):
        """Sin fechas NOT NULL, la fila ya no depende del parser: basta un
        justificante con canal (#928)."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico('Esto no es un justificante.'))

        assert _producir(tarea, doc).ok is True
        notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
        assert notif is not None
        assert notif.identificador_envio is None
        assert notif.resultado is None

    def test_sir_sin_fila_previa_crea_fila(self, con_usuario, fs_tmp):
        """Antes (#657) SIR no podía crear la fila: faltaba la fecha NOT NULL."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_SIR', fs_tmp, b'captura')

        assert _producir(tarea, doc).ok is True
        notif = Notificacion.query.filter_by(tarea_id=tarea.id).first()
        assert notif is not None
        assert notif.canal == 'SIR'
        assert notif.documento_id == doc.id

    def test_tipo_doc_sin_canal_no_crea_fila(self, con_usuario, fs_tmp):
        """Producido de un tipo ajeno a los justificantes con canal: el hook no
        crea nada, ni siquiera intenta parsear."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento_con_fichero(exp_id, 'RESOLUCION', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        assert _producir(tarea, doc).ok is True
        assert Notificacion.query.filter_by(tarea_id=tarea.id).first() is None

    def test_con_fila_previa_no_toca_resultado_ni_remesa(self, con_usuario, fs_tmp):
        """Con fila previa, el hook solo sigue al producido (documento_id)."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'SIR', identificador_envio='SIR-001', resultado='CORRECTA')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_SIR', fs_tmp, b'captura')

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.documento_id == doc.id
        assert notif.resultado == 'CORRECTA'
        assert notif.identificador_envio == 'SIR-001'


class TestHookNotificarCotejo:

    def test_remesa_coincide_sin_advertencia(self, con_usuario, fs_tmp):
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'NOTIFICA', identificador_envio='82541676')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.documento_id == doc.id
        assert notif.resultado is None  # el parseo ya no lo escribe (D2)

    def test_remesa_no_coincide_advierte_sin_bloquear(self, con_usuario, fs_tmp):
        """El riesgo real que motivó #658: justificante de otro expediente
        asociado a esta tarea. No bloquea — aviso, y la remesa no se pisa."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'NOTIFICA', identificador_envio='REMESA-DISTINTA')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert resultado.advertencia is not None
        assert '82541676' in resultado.advertencia['motivo']
        assert 'REMESA-DISTINTA' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.identificador_envio == 'REMESA-DISTINTA'

    def test_canal_no_coincide_con_parser_actualiza_canal_y_avisa(self, con_usuario, fs_tmp):
        """#712: registrado como SIR y luego se vincula un justificante NOTIFICA
        — el documento manda."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'SIR')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert 'NOTIFICA' in resultado.advertencia['motivo']
        assert 'SIR' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.canal == 'NOTIFICA'

    def test_canal_no_coincide_sin_parser_tambien_avisa(self, con_usuario, fs_tmp):
        """El cotejo de canal no depende de que haya parser — el canal se deriva
        del tipo de documento, siempre disponible."""
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'BANDEJA', identificador_envio='X-1')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_SIR', fs_tmp, b'captura')

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert 'SIR' in resultado.advertencia['motivo']
        assert 'BANDEJA' in resultado.advertencia['motivo']
        db.session.refresh(notif)
        assert notif.canal == 'SIR'
        assert notif.resultado is None

    def test_canal_coincide_no_avisa(self, con_usuario, fs_tmp):
        tarea = _tarea_notificar()
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        notif = _fila_previa(tarea, 'NOTIFICA', identificador_envio='82541676')
        doc = _documento_con_fichero(exp_id, 'JUSTIFICANTE_NOTIFICA', fs_tmp,
                                     _pdf_sintetico(TEXTO_JUSTIFICANTE))

        resultado = _producir(tarea, doc)

        assert resultado.ok is True
        assert resultado.advertencia is None
        db.session.refresh(notif)
        assert notif.canal == 'NOTIFICA'
