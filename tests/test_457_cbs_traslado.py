"""
Tests issue #457 — ContextoConsultaTrasladoTitular y ContextoConsultaTrasladoOrganismo.

Bloques:
  A) ContextoConsultaTrasladoTitular.get_contexto()
  B) ContextoConsultaTrasladoOrganismo.get_contexto()

Patrón: stubs + mock de queries, sin BD ni app context.
Los helpers de construcción se adaptan del patrón de test_391.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ───────────────────────────────────────────────────────────────────────────────
# Helpers compartidos
# ───────────────────────────────────────────────────────────────────────────────

def _organismo(nombre='Red Eléctrica de España', nif='A78003662'):
    org = MagicMock()
    org.nombre_completo = nombre
    org.nif = nif
    return org


def _org_exp(organismo=None, plazo_legal_dias=30, resultado=None):
    from app.models.organismos_expediente import OrganismoExpediente
    oe = MagicMock()
    oe.organismo = organismo or _organismo()
    oe.plazo_legal_dias = plazo_legal_dias
    oe.resultado = resultado
    oe.as_contexto_cb = lambda: OrganismoExpediente.as_contexto_cb(oe)
    return oe


def _vinculo(oe):
    v = MagicMock()
    v.organismo_expediente = oe
    return v


def _doc(fecha=None):
    d = MagicMock()
    d.fecha_administrativa = fecha
    return d


def _tarea_stub(codigo, doc_producido=None, consumidos=None, tramite_id=1):
    t = MagicMock()
    t.tramite_id = tramite_id
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documento_producido = doc_producido
    t.documentos_consumidos = consumidos if consumidos is not None else []
    return t


def _tramite_con_tareas(tareas):
    tr = MagicMock()
    tr.tareas = tareas
    return tr


def _vinculo_tramite(tareas):
    """Stub de TramiteOrganismo con tramite que tiene las tareas dadas."""
    vt = MagicMock()
    vt.tramite = _tramite_con_tareas(tareas)
    return vt


# ───────────────────────────────────────────────────────────────────────────────
# A) ContextoConsultaTrasladoTitular
# ───────────────────────────────────────────────────────────────────────────────

class TestContextoConsultaTrasladoTitular:

    _MODULE = 'app.services.context_builders.contexto_consulta_traslado_titular.TramiteOrganismo'

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_traslado_titular import (
            ContextoConsultaTrasladoTitular,
        )
        cb = ContextoConsultaTrasladoTitular(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_organismo_expediente_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_traslado_titular import (
            ContextoConsultaTrasladoTitular,
        )
        tarea = _tarea_stub('ELABORAR', tramite_id=5)
        tarea.tramite = _tramite_con_tareas([tarea])
        cb = ContextoConsultaTrasladoTitular(MagicMock(), MagicMock(), tarea=tarea)
        with patch(self._MODULE) as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            assert cb.get_contexto() == {}

    def test_elaborar_sin_documentos_fechas_none(self):
        from app.services.context_builders.contexto_consulta_traslado_titular import (
            ContextoConsultaTrasladoTitular,
        )
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaTrasladoTitular(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['titular_fecha_respuesta'] is None
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'

    def test_con_doc_elaborar_organismo_fecha(self):
        from app.services.context_builders.contexto_consulta_traslado_titular import (
            ContextoConsultaTrasladoTitular,
        )
        doc_respuesta = _doc(fecha=date(2026, 4, 10))
        tarea_elab = _tarea_stub('ELABORAR', consumidos=[doc_respuesta], tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaTrasladoTitular(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '10/04/2026'
        assert ctx['titular_fecha_respuesta'] is None

    def test_con_esperar_plazo_ejecutado_titular_fecha(self):
        from app.services.context_builders.contexto_consulta_traslado_titular import (
            ContextoConsultaTrasladoTitular,
        )
        doc_org = _doc(fecha=date(2026, 4, 10))
        doc_tit = _doc(fecha=date(2026, 5, 2))
        tarea_elab = _tarea_stub('ELABORAR', consumidos=[doc_org], tramite_id=1)
        tarea_notif = _tarea_stub('NOTIFICAR', tramite_id=1)
        tarea_esp = _tarea_stub('ESPERAR_PLAZO', doc_producido=doc_tit, tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif, tarea_esp])

        oe = _org_exp(resultado=None, plazo_legal_dias=15)
        cb = ContextoConsultaTrasladoTitular(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '10/04/2026'
        assert ctx['titular_fecha_respuesta'] == '02/05/2026'
        assert ctx['organismo_resultado'] is None
        assert ctx['organismo_plazo_legal'] == 15


# ───────────────────────────────────────────────────────────────────────────────
# B) ContextoConsultaTrasladoOrganismo
# ───────────────────────────────────────────────────────────────────────────────

class TestContextoConsultaTrasladoOrganismo:

    _MODULE = 'app.services.context_builders.contexto_consulta_traslado_organismo.TramiteOrganismo'

    def _mock_queries(self, mock_cls, vinculo_ppal, tramite_ant=None,
                      traslado_tit=None, num_iter=0):
        """Configura el mock de TramiteOrganismo para el CB de traslado organismo.

        Las tres queries de join se distinguen por la profundidad de la cadena
        filter: tramite_ant usa 3 filtros, las otras dos usan 2 filtros.
        """
        mock_cls.query.filter_by.return_value.first.return_value = vinculo_ppal
        q2 = (mock_cls.query.join.return_value.join.return_value
              .filter.return_value.filter.return_value)
        q3 = q2.filter.return_value
        q3.order_by.return_value.first.return_value = tramite_ant
        q2.order_by.return_value.first.return_value = traslado_tit
        q2.count.return_value = num_iter

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_organismo_expediente_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        tarea = _tarea_stub('ELABORAR', tramite_id=7)
        tarea.tramite = _tramite_con_tareas([tarea])
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=tarea)
        with patch(self._MODULE) as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            assert cb.get_contexto() == {}

    def test_primera_iteracion_sin_tramites_previos_fechas_none(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=10)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            self._mock_queries(mock_cls, _vinculo(oe),
                               tramite_ant=None, traslado_tit=None, num_iter=1)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['titular_fecha_respuesta'] is None
        assert ctx['organismo_num_iteraciones'] == 1
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'

    def test_con_tramite_anterior_organismo_fecha(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        doc_org = _doc(fecha=date(2026, 3, 15))
        tramite_ant = _vinculo_tramite([
            _tarea_stub('ESPERAR_PLAZO', doc_producido=doc_org),
        ])

        tarea_elab = _tarea_stub('ELABORAR', tramite_id=10)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            self._mock_queries(mock_cls, _vinculo(oe),
                               tramite_ant=tramite_ant, traslado_tit=None, num_iter=1)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '15/03/2026'
        assert ctx['titular_fecha_respuesta'] is None

    def test_con_traslado_titular_y_organismo_anterior_ambas_fechas(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        doc_org = _doc(fecha=date(2026, 3, 15))
        doc_tit = _doc(fecha=date(2026, 4, 20))
        tramite_ant = _vinculo_tramite([_tarea_stub('ESPERAR_PLAZO', doc_producido=doc_org)])
        traslado_tit = _vinculo_tramite([_tarea_stub('ESPERAR_PLAZO', doc_producido=doc_tit)])

        tarea_elab = _tarea_stub('ELABORAR', tramite_id=10)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None, plazo_legal_dias=15)
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            self._mock_queries(mock_cls, _vinculo(oe),
                               tramite_ant=tramite_ant, traslado_tit=traslado_tit, num_iter=2)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] == '15/03/2026'
        assert ctx['titular_fecha_respuesta'] == '20/04/2026'
        assert ctx['organismo_num_iteraciones'] == 2
        assert ctx['organismo_resultado'] is None
        assert ctx['organismo_plazo_legal'] == 15

    def test_esperar_plazo_sin_doc_producido_fecha_none(self):
        from app.services.context_builders.contexto_consulta_traslado_organismo import (
            ContextoConsultaTrasladoOrganismo,
        )
        tramite_ant = _vinculo_tramite([_tarea_stub('ESPERAR_PLAZO', doc_producido=None)])

        tarea_elab = _tarea_stub('ELABORAR', tramite_id=10)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp()
        cb = ContextoConsultaTrasladoOrganismo(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch(self._MODULE) as mock_cls:
            self._mock_queries(mock_cls, _vinculo(oe),
                               tramite_ant=tramite_ant, traslado_tit=None, num_iter=1)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_respuesta'] is None
