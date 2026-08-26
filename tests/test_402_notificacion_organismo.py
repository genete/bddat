"""
Tests issue #402 — ContextoNotificacionOrganismo.

Bloque único: get_contexto() con stubs, sin BD ni app context.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _organismo(nombre='Confederación Hidrográfica del Guadalquivir', nif='Q4150013E'):
    org = MagicMock()
    org.nombre_completo = nombre
    org.nif = nif
    return org


def _org_exp(organismo=None, plazo_legal_dias=30, resultado=None):
    """Stub de OrganismoExpediente con as_contexto_cb() delegando al método real."""
    from app.models.organismos_expediente import OrganismoExpediente
    oe = MagicMock()
    oe.organismo = organismo or _organismo()
    oe.plazo_legal_dias = plazo_legal_dias
    oe.resultado = resultado
    oe.as_contexto_cb = lambda: OrganismoExpediente.as_contexto_cb(oe)
    return oe


def _vinculo_stub(oe):
    """Stub de TramiteOrganismo apuntando a un OrganismoExpediente."""
    v = MagicMock()
    v.organismo_expediente = oe
    return v


def _tarea_stub(codigo, doc_usado=None, tramite_id=1):
    t = MagicMock()
    t.tramite_id = tramite_id
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documentos_consumidos = [doc_usado] if doc_usado is not None else []
    return t


def _tramite_con_tareas(tareas):
    tr = MagicMock()
    tr.tareas = tareas
    return tr


def _doc(fecha=None):
    d = MagicMock()
    d.fecha_administrativa = fecha
    return d


def _cb(tarea):
    from app.services.context_builders.contexto_notificacion_organismo import ContextoNotificacionOrganismo
    return ContextoNotificacionOrganismo(MagicMock(), MagicMock(), tarea=tarea)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoNotificacionOrganismo:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_notificacion_organismo import ContextoNotificacionOrganismo
        cb = ContextoNotificacionOrganismo(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_organismo_expediente_devuelve_vacio(self):
        tarea = _tarea_stub('ELABORAR', tramite_id=99)
        cb = _cb(tarea)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            result = cb.get_contexto()
        assert result == {}

    def test_sin_analizar_fechas_none(self):
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None, plazo_legal_dias=30)
        cb = _cb(tarea_elab)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['organismo_fecha_limite'] is None
        assert ctx['organismo_nombre'] == 'Confederación Hidrográfica del Guadalquivir'

    def test_con_analizar_ejecutado_fechas_calculadas(self):
        doc_resp = _doc(fecha=date(2026, 4, 10))
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=doc_resp, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])

        oe = _org_exp(resultado='cerrado_con_condicionados', plazo_legal_dias=30)
        cb = _cb(tarea_elab)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '10/04/2026'
        assert ctx['organismo_fecha_limite'] == '10/05/2026'  # +30 días
        assert ctx['organismo_resultado'] == 'cerrado_con_condicionados'
        assert ctx['organismo_plazo_legal'] == 30

    def test_plazo_15_dias(self):
        doc_resp = _doc(fecha=date(2026, 5, 1))
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=doc_resp, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])

        oe = _org_exp(plazo_legal_dias=15)
        cb = _cb(tarea_elab)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_limite'] == '16/05/2026'  # +15 días

    def test_plazo_none_fecha_limite_none(self):
        doc_resp = _doc(fecha=date(2026, 5, 1))
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=doc_resp, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])

        oe = _org_exp(plazo_legal_dias=None)
        cb = _cb(tarea_elab)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '01/05/2026'
        assert ctx['organismo_fecha_limite'] is None

    def test_analizar_sin_doc_consumido_fechas_none(self):
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=None, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_anal])

        oe = _org_exp(plazo_legal_dias=30)
        cb = _cb(tarea_elab)
        with patch('app.services.context_builders.contexto_notificacion_organismo.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['organismo_fecha_limite'] is None
