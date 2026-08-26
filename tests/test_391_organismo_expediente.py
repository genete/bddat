"""
Tests issue #391 — OrganismoExpediente.as_contexto_cb() y ContextoConsultaSeparata.
Tests issue #466 — direccion_notificacion_id en as_contexto_cb() con fallback.

Bloques:
  A) OrganismoExpediente.as_contexto_cb()  — stubs, sin BD ni app context.
  B) ContextoConsultaSeparata.get_contexto() — stubs + mock de query.
  C) #466 — as_contexto_cb() con direccion_notificacion_id y fallback.
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


def _org_exp(organismo=None, plazo_legal_dias=30, resultado=None,
             organismo_id=None, direccion_notificacion=None):
    """Stub de OrganismoExpediente con as_contexto_cb() delegando al método real."""
    from app.models.organismos_expediente import OrganismoExpediente
    oe = MagicMock()
    oe.organismo = organismo or _organismo()
    oe.plazo_legal_dias = plazo_legal_dias
    oe.resultado = resultado
    oe.organismo_id = organismo_id
    oe.direccion_notificacion = direccion_notificacion
    oe.as_contexto_cb = lambda: OrganismoExpediente.as_contexto_cb(oe)
    return oe


def _vinculo_stub(oe):
    """Stub de TramiteOrganismo apuntando a un OrganismoExpediente."""
    v = MagicMock()
    v.organismo_expediente = oe
    return v


def _tarea_stub(codigo, doc_producido=None, doc_usado=None, tramite_id=1):
    t = MagicMock()
    t.tramite_id = tramite_id
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documento_producido = doc_producido
    # Vínculos N:M (ADR-010): documento de entrada como lista de consumidos
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


# ───────────────────────────────────────────────────────────────────────────────
# A) OrganismoExpediente.as_contexto_cb()
# ───────────────────────────────────────────────────────────────────────────────

class TestAsContextoCb:

    def test_campos_basicos(self):
        oe = _org_exp(plazo_legal_dias=30, resultado=None)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'
        assert ctx['organismo_nif'] == 'A78003662'
        assert ctx['organismo_plazo_legal'] == 30
        assert ctx['organismo_resultado'] is None

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

    def test_resultado_pasa_directo(self):
        oe = _org_exp(resultado='cerrado_favorable')
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_resultado'] == 'cerrado_favorable'


# ───────────────────────────────────────────────────────────────────────────────
# B) ContextoConsultaSeparata.get_contexto()
# ───────────────────────────────────────────────────────────────────────────────

class TestContextoConsultaSeparata:

    def _cb(self, tarea=None, org_exp_found=None):
        """Construye el CB con mock de la query a OrganismoExpediente."""
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea)
        return cb, org_exp_found

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_organismo_expediente_devuelve_vacio(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        tarea = _tarea_stub('ELABORAR', tramite_id=99)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea)
        with patch('app.services.context_builders.contexto_consulta_separata.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = None
            result = cb.get_contexto()
        assert result == {}

    def test_elaborar_sin_notificar_ni_analizar_fechas_none(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.contexto_consulta_separata.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] is None
        assert ctx['organismo_fecha_respuesta'] is None
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'

    def test_con_notificar_ejecutado_fecha_envio(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        doc_notif = _doc(fecha=date(2026, 5, 15))
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=doc_notif, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif])

        oe = _org_exp(resultado=None)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.contexto_consulta_separata.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] == '15/05/2026'
        assert ctx['organismo_fecha_respuesta'] is None

    def test_con_analizar_ejecutado_fecha_respuesta(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        doc_notif = _doc(fecha=date(2026, 5, 15))
        doc_respuesta = _doc(fecha=date(2026, 6, 2))
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=doc_notif, tramite_id=1)
        tarea_anal = _tarea_stub('ANALIZAR', doc_usado=doc_respuesta, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif, tarea_anal])

        oe = _org_exp(resultado='cerrado_con_condicionados', plazo_legal_dias=30)
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.contexto_consulta_separata.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] == '15/05/2026'
        assert ctx['organismo_fecha_respuesta'] == '02/06/2026'
        assert ctx['organismo_resultado'] == 'cerrado_con_condicionados'
        assert ctx['organismo_plazo_legal'] == 30

    def test_notificar_sin_doc_producido_fecha_envio_none(self):
        from app.services.context_builders.contexto_consulta_separata import ContextoConsultaSeparata
        tarea_notif = _tarea_stub('NOTIFICAR', doc_producido=None, tramite_id=1)
        tarea_elab = _tarea_stub('ELABORAR', tramite_id=1)
        tarea_elab.tramite = _tramite_con_tareas([tarea_elab, tarea_notif])

        oe = _org_exp()
        cb = ContextoConsultaSeparata(MagicMock(), MagicMock(), tarea=tarea_elab)
        with patch('app.services.context_builders.contexto_consulta_separata.TramiteOrganismo') as mock_cls:
            mock_cls.query.filter_by.return_value.first.return_value = _vinculo_stub(oe)
            ctx = cb.get_contexto()

        assert ctx['organismo_fecha_envio'] is None


# ───────────────────────────────────────────────────────────────────────────────
# C) #466 — direccion_notificacion_id: campos de contacto y fallback
# ───────────────────────────────────────────────────────────────────────────────

def _dir_notif_stub(email=None, dir3=None, sir=None,
                    linea1='C/ Ejemplo 1', linea2='41001 Sevilla', provincia='SEVILLA'):
    """Stub de DireccionNotificacion."""
    d = MagicMock()
    d.email = email
    d.codigo_dir3 = dir3
    d.codigo_sir = sir
    d.direccion_formateada.return_value = {
        'linea1': linea1,
        'linea2': linea2,
        'provincia': provincia,
    }
    return d


class TestAsContextoCbDireccion:

    def test_sin_direccion_campos_son_none(self):
        """Sin direccion_notificacion ni organismo_id → campos de dirección None."""
        oe = _org_exp(organismo_id=None, direccion_notificacion=None)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_email'] is None
        assert ctx['organismo_dir3'] is None
        assert ctx['organismo_sir'] is None
        assert ctx['organismo_direccion_linea1'] is None
        assert ctx['organismo_direccion_linea2'] is None
        assert ctx['organismo_provincia'] is None

    def test_direccion_notificacion_guardada_se_usa_directamente(self):
        """Cuando hay direccion_notificacion en el registro, se usa sin fallback."""
        dir_stub = _dir_notif_stub(email='org@ejemplo.es', dir3='A12345678', linea1='Av. Test 5')
        oe = _org_exp(organismo_id=99, direccion_notificacion=dir_stub)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_email'] == 'org@ejemplo.es'
        assert ctx['organismo_dir3'] == 'A12345678'
        assert ctx['organismo_direccion_linea1'] == 'Av. Test 5'

    def test_fallback_a_obtener_direccion_cuando_fk_es_none(self):
        """Sin direccion_notificacion pero con organismo_id → se llama al fallback."""
        dir_stub = _dir_notif_stub(email='fallback@org.es', sir='SIR001')
        oe = _org_exp(organismo_id=42, direccion_notificacion=None)
        with patch('app.models.organismos_expediente.DireccionNotificacion') as mock_dn:
            mock_dn.obtener_direccion_notificacion.return_value = dir_stub
            ctx = oe.as_contexto_cb()
        mock_dn.obtener_direccion_notificacion.assert_called_once_with(42, es_consultado=True)
        assert ctx['organismo_email'] == 'fallback@org.es'
        assert ctx['organismo_sir'] == 'SIR001'

    def test_fallback_sin_resultado_campos_none(self):
        """Fallback devuelve None (organismo sin dirección en BD) → campos None."""
        oe = _org_exp(organismo_id=42, direccion_notificacion=None)
        with patch('app.models.organismos_expediente.DireccionNotificacion') as mock_dn:
            mock_dn.obtener_direccion_notificacion.return_value = None
            ctx = oe.as_contexto_cb()
        assert ctx['organismo_email'] is None
        assert ctx['organismo_provincia'] is None

    def test_campos_basicos_no_se_ven_afectados(self):
        """Los campos existentes (nombre, nif, plazo, resultado) siguen funcionando."""
        oe = _org_exp(plazo_legal_dias=15, resultado='cerrado_favorable',
                      organismo_id=None, direccion_notificacion=None)
        ctx = oe.as_contexto_cb()
        assert ctx['organismo_nombre'] == 'Red Eléctrica de España'
        assert ctx['organismo_nif'] == 'A78003662'
        assert ctx['organismo_plazo_legal'] == 15
        assert ctx['organismo_resultado'] == 'cerrado_favorable'
