"""
Tests issue #391 — OrganismoExpediente.as_contexto_cb() y ContextoConsultaSeparata.

Bloques:
  A) OrganismoExpediente.as_contexto_cb()  — stubs, sin BD ni app context.
  B) ContextoConsultaSeparata.get_contexto() — stubs + mock de query.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def _organismo(nombre='Red Eléctrica de España', nif='A78003662'):
    org = MagicMock()
    org.nombre_completo = nombre
    org.nif = nif
    return org


def _org_exp(organismo=None, plazo_legal_dias=30, estado='pendiente', tramite_id=1):
    """Stub de OrganismoExpediente con as_contexto_cb() delegando al método real."""
    from app.models.organismos_expediente import OrganismoExpediente
    oe = MagicMock()
    oe.organismo = organismo or _organismo()
    oe.plazo_legal_dias = plazo_legal_dias
    oe.estado = estado
    oe.tramite_id = tramite_id
    oe.as_contexto_cb = lambda: OrganismoExpediente.as_contexto_cb(oe)
    return oe


def _tarea_stub(codigo, doc_producido=None, doc_usado=None, tramite_id=1):
    t = MagicMock()
    t.tramite_id = tramite_id
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documento_producido = doc_producido
    t.documento_usado = doc_usado
    return t


def _tramite_con_tareas(tareas):
    tr = MagicMock()
    tr.tareas = tareas
    return tr


def _doc(fecha=None):
    d = MagicMock()
    d.fecha_administrativa = fecha
    return d


# ───────────────────────────────────────────────────────────────────────────────
# A) OrganismoExpediente.as_contexto_cb()
# ───────────────────────────────────────────────────────────────────────────────

class TestAsContextoCb:

    def test_campos_basicos(self):
        oe = _org_exp(plazo_legal_dias=30, estado='separata_enviada')
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'
        assert ctx['organismo_nif'] == 'A78003662'
        assert ctx['organismo_plazo_legal'] == 30
        assert ctx['organismo_resultado'] == 'separata_enviada'

    def test_organismo_sin_nif(self):
        org = _organismo(nif=None)
        oe = _org_exp(organismo=org)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_nif'] is None

    def test_plazo_none(self):
        oe = _org_exp(plazo_legal_dias=None)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_plazo_legal'] is None

    def test_organismo_none_devuelve_none(self):
        oe = _org_exp()
        oe.organismo = None
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_nombre'] is None
        assert ctx['organismo_nif'] is None

    def test_estado_refleja_resultado(self):
        oe = _org_exp(estado='cerrado_favorable')
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_resultado'] == 'cerrado_favorable'


# ───────────────────────────────────────────────────────────────────────────────
# B) ContextoConsultaSeparata.get_contexto()
# ───────────────────────────────────────────────────────────────────────────────

class TestContextoConsultaSeparata:

    def _cb(self, tarea=None, org_exp_found=None):
        """Construye el CB con mock de la query a OrganismoExpediente."""
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea)
        return cb, org_exp_found

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_organismo_expediente_devuelve_vacio(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        tarea = _tarea_stub('ELABORAR', tramite_id=99)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea)
        with patch('app.services.context_builders.consulta_separata.OrganismoExpediente') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            result = cb.get_contexto()
        assert result == {}

    def test_elaborar_sin_notificar_ni_analizar_fechas_none(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(estado='pendiente')
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.consulta_separata.OrganismoExpediente') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = oe
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] is None
        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'

    def test_con_notificar_ejecutado_fecha_envio(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        doc_notif = _doc(fecha=date(2026, 5, 15))
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=doc_notif, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif])

        oe = _org_exp(estado='separata_enviada')
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.consulta_separata.OrganismoExpediente') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = oe
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] == '15/05/2026'
        assert ctx['organismo_fecha_respuesta'] is None

    def test_con_analizar_ejecutado_fecha_respuesta(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        doc_notif = _doc(fecha=date(2026, 5, 15))
        doc_respuesta = _doc(fecha=date(2026, 6, 2))
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=doc_notif, tramite_id=1)
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=doc_respuesta, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif, tarea_anal])

        oe = _org_exp(estado='cerrado_con_condicionados', plazo_legal_dias=30)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.consulta_separata.OrganismoExpediente') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = oe
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] == '15/05/2026'
        assert ctx['organismo_fecha_respuesta'] == '02/06/2026'
        assert ctx['organismo_resultado'] == 'cerrado_con_condicionados'
        assert ctx['organismo_plazo_legal'] == 30

    def test_notificar_sin_doc_producido_fecha_envio_none(self):
        from app.services.context_builders.consulta_separata import ContextoConsultaSeparata
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=None, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif])

        oe = _org_exp()
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.consulta_separata.OrganismoExpediente') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = oe
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] is None
