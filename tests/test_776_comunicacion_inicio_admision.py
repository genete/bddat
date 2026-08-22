"""
Tests issue #776 — ContextoComunicacionInicioAdmision.

Bloque único: get_contexto() con stubs (MagicMock), sin BD ni app context.
obtener_estado_plazo_solicitud se mockea para no depender de catalogo_plazos real.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _documento_solicitud(fecha_administrativa=None):
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    return doc


def _solicitud(id=1, documento_solicitud=None):
    s = MagicMock()
    s.id = id
    s.documento_solicitud = documento_solicitud
    return s


def _fase(solicitud=None):
    f = MagicMock()
    f.solicitud = solicitud
    return f


def _tramite(fase=None):
    t = MagicMock()
    t.fase = fase
    return t


def _tarea(tramite=None):
    t = MagicMock()
    t.tramite = tramite
    return t


def _cb(tarea):
    from app.services.context_builders.contexto_comunicacion_inicio_admision import (
        ContextoComunicacionInicioAdmision,
    )
    return ContextoComunicacionInicioAdmision(MagicMock(), MagicMock(), tarea=tarea)


def _estado_plazo(estado='EN_PLAZO', plazo_valor=3, plazo_unidad='MESES',
                   norma_origen='Art. 21.3 LPACAP', efecto_nombre='Silencio administrativo desestimatorio'):
    e = MagicMock()
    e.estado = estado
    e.plazo_valor = plazo_valor
    e.plazo_unidad = plazo_unidad
    e.norma_origen = norma_origen
    e.efecto_nombre = efecto_nombre
    return e


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoComunicacionInicioAdmision:

    def test_sin_tarea_devuelve_vacio(self):
        cb = _cb(tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_fase_devuelve_vacio(self):
        tarea = _tarea(_tramite(fase=None))
        assert _cb(tarea).get_contexto() == {}

    def test_sin_solicitud_devuelve_vacio(self):
        tarea = _tarea(_tramite(_fase(solicitud=None)))
        assert _cb(tarea).get_contexto() == {}

    def test_con_plazo_y_fecha_resueltos(self):
        doc = _documento_solicitud(fecha_administrativa=date(2026, 1, 15))
        solicitud = _solicitud(documento_solicitud=doc)
        tarea = _tarea(_tramite(_fase(solicitud)))

        with patch(
            'app.services.plazos.obtener_estado_plazo_solicitud',
            return_value=_estado_plazo(),
        ):
            ctx = _cb(tarea).get_contexto()

        assert ctx['plazo_maximo_resolucion'] == 3
        assert ctx['unidad_plazo'] == 'meses'
        assert ctx['norma_plazo'] == 'Art. 21.3 LPACAP'
        assert ctx['efecto_silencio'] == 'Silencio administrativo desestimatorio'
        assert ctx['fecha_recepcion_solicitud'] == '15/01/2026'

    def test_unidad_dias_habiles_legible(self):
        doc = _documento_solicitud(fecha_administrativa=date(2026, 1, 15))
        solicitud = _solicitud(documento_solicitud=doc)
        tarea = _tarea(_tramite(_fase(solicitud)))

        with patch(
            'app.services.plazos.obtener_estado_plazo_solicitud',
            return_value=_estado_plazo(plazo_valor=10, plazo_unidad='DIAS_HABILES'),
        ):
            ctx = _cb(tarea).get_contexto()

        assert ctx['plazo_maximo_resolucion'] == 10
        assert ctx['unidad_plazo'] == 'días hábiles'

    def test_degradado_sin_entrada_catalogo(self):
        """#347: SIN_PLAZO -> campos de plazo a None, sin excepción."""
        doc = _documento_solicitud(fecha_administrativa=date(2026, 1, 15))
        solicitud = _solicitud(documento_solicitud=doc)
        tarea = _tarea(_tramite(_fase(solicitud)))

        with patch(
            'app.services.plazos.obtener_estado_plazo_solicitud',
            return_value=_estado_plazo(estado='SIN_PLAZO'),
        ):
            ctx = _cb(tarea).get_contexto()

        assert ctx['plazo_maximo_resolucion'] is None
        assert ctx['unidad_plazo'] is None
        assert ctx['norma_plazo'] is None
        assert ctx['efecto_silencio'] is None
        # La fecha de recepción no depende del plazo: sigue resuelta.
        assert ctx['fecha_recepcion_solicitud'] == '15/01/2026'

    def test_degradado_sin_documento_solicitud(self):
        """#347: sin documento_solicitud -> fecha None, sin excepción."""
        solicitud = _solicitud(documento_solicitud=None)
        tarea = _tarea(_tramite(_fase(solicitud)))

        with patch(
            'app.services.plazos.obtener_estado_plazo_solicitud',
            return_value=_estado_plazo(),
        ):
            ctx = _cb(tarea).get_contexto()

        assert ctx['fecha_recepcion_solicitud'] is None
        # El plazo no depende del documento de solicitud: sigue resuelto.
        assert ctx['plazo_maximo_resolucion'] == 3

    def test_degradado_documento_solicitud_sin_fecha_administrativa(self):
        doc = _documento_solicitud(fecha_administrativa=None)
        solicitud = _solicitud(documento_solicitud=doc)
        tarea = _tarea(_tramite(_fase(solicitud)))

        with patch(
            'app.services.plazos.obtener_estado_plazo_solicitud',
            return_value=_estado_plazo(),
        ):
            ctx = _cb(tarea).get_contexto()

        assert ctx['fecha_recepcion_solicitud'] is None
