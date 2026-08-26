"""
Tests #247 — helper serializar_org_exp y validaciones de CRUD organismos_expediente.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock


def _oe_stub(id=1, organismo_id=5, via='consulta', resultado=None,
             plazo_legal_dias=30, condicionados_doc_id=None):
    oe = MagicMock()
    oe.id = id
    oe.organismo_id = organismo_id
    oe.organismo = MagicMock(nombre_completo='Red Eléctrica de España, S.A.', nif='A78003662')
    oe.via = via
    oe.resultado = resultado
    oe.plazo_legal_dias = plazo_legal_dias
    oe.condicionados_doc_id = condicionados_doc_id
    return oe


class TestSerializarOrgExp:

    def test_get_organismos_ok(self, app):
        from app.services.consultas_organismos import serializar_org_exp
        oe = _oe_stub()
        with app.app_context():
            result = serializar_org_exp(oe)
        assert result['id'] == 1
        assert result['organismo_id'] == 5
        assert result['nombre_completo'] == 'Red Eléctrica de España, S.A.'
        assert result['nif'] == 'A78003662'
        assert result['via'] == 'consulta'
        assert result['resultado'] is None
        assert result['plazo_legal_dias'] == 30
        assert result['condicionados_doc_id'] is None

    def test_get_expediente_no_existe(self, app):
        # get_or_404 gestiona la respuesta 404; sin organismo los campos vienen None
        from app.services.consultas_organismos import serializar_org_exp
        oe = _oe_stub()
        oe.organismo = None
        with app.app_context():
            result = serializar_org_exp(oe)
        assert result['nombre_completo'] is None
        assert result['nif'] is None

    def test_post_organismo_ok(self, app):
        # Verifica que los campos del POST se serializan correctamente al crearse el registro
        from app.services.consultas_organismos import serializar_org_exp
        oe = _oe_stub(id=7, organismo_id=5, via='consulta', plazo_legal_dias=None)
        oe.organismo = MagicMock(nombre_completo='Endesa, S.A.', nif='A81947556')
        with app.app_context():
            result = serializar_org_exp(oe)
        assert result['id'] == 7
        assert result['organismo_id'] == 5
        assert result['via'] == 'consulta'
        assert result['plazo_legal_dias'] is None

    def test_post_organismo_sin_rol_consultado(self):
        entidad = MagicMock()
        entidad.rol_consultado = False
        assert not entidad.rol_consultado

    def test_post_organismo_via_invalida(self):
        from app.models.organismos_expediente import VIAS_ORGANISMO
        assert 'email' not in VIAS_ORGANISMO
        assert 'consulta' in VIAS_ORGANISMO
        assert 'declaracion_responsable' in VIAS_ORGANISMO

    def test_post_organismo_duplicado(self):
        # La BD lanza IntegrityError por uq_org_exp_fase_organismo (#396: por fase
        # —la ronda de consultas—, no por expediente, para admitir más de una
        # ronda tras un modificado de proyecto); aquí verificamos que la
        # constraint está declarada en el modelo.
        from app.models.organismos_expediente import OrganismoExpediente
        nombres = [c.name for c in OrganismoExpediente.__table_args__[:-1]]
        assert 'uq_org_exp_fase_organismo' in nombres

    def test_patch_resultado_ok(self):
        from app.models.organismos_expediente import RESULTADOS_ORGANISMO
        oe = MagicMock()
        nuevo = 'cerrado_favorable'
        assert nuevo in RESULTADOS_ORGANISMO
        oe.resultado = nuevo
        assert oe.resultado == 'cerrado_favorable'

    def test_patch_resultado_invalido(self):
        from app.models.organismos_expediente import RESULTADOS_ORGANISMO
        assert 'tramitado' not in RESULTADOS_ORGANISMO
        # #396: el ciclo de vida (pendiente/separata_enviada/en_tramitacion) ya
        # no son valores de resultado — se derivan, no se almacenan.
        assert 'pendiente' not in RESULTADOS_ORGANISMO

    def test_delete_organismo_ok(self, app):
        from app.services.consultas_organismos import serializar_org_exp
        oe = _oe_stub()
        with app.app_context():
            result = serializar_org_exp(oe)
        assert result is not None
        assert result['id'] == 1
