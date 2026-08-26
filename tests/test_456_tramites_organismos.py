"""
Tests issue #456 — TramiteOrganismo y OrganismoExpediente.consulta_completa.

Bloques:
  A) Modelo TramiteOrganismo — atributos y constraints declarados.
  B) OrganismoExpediente.consulta_completa — casos ADR-011 §6.
  C) OrganismoExpediente — campo condicionados_doc_id presente.

Patrón: objetos Python puros y reflexión de modelo, sin BD real.
"""
from unittest.mock import MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# A) Modelo TramiteOrganismo
# ─────────────────────────────────────────────────────────────────────────────

class TestModeloTramiteOrganismo:

    def test_tabla_correcta(self):
        from app.models.tramites_organismos import TramiteOrganismo
        assert TramiteOrganismo.__tablename__ == 'tramites_organismos'

    def test_columnas_requeridas(self):
        from app.models.tramites_organismos import TramiteOrganismo
        cols = {c.name for c in TramiteOrganismo.__table__.columns}
        assert 'id' in cols
        assert 'tramite_id' in cols
        assert 'organismo_expediente_id' in cols

    def test_tramite_id_unique(self):
        from app.models.tramites_organismos import TramiteOrganismo
        col = TramiteOrganismo.__table__.c['tramite_id']
        assert col.unique or any(
            'tramite_id' in [c.name for c in uc.columns]
            for uc in TramiteOrganismo.__table__.constraints
            if hasattr(uc, 'columns')
        )

    def test_uq_tramorg_tramite_constraint(self):
        from app.models.tramites_organismos import TramiteOrganismo
        nombres = [c.name for c in TramiteOrganismo.__table__.constraints]
        assert 'uq_tramorg_tramite' in nombres


# ─────────────────────────────────────────────────────────────────────────────
# B) OrganismoExpediente.consulta_completa
# ─────────────────────────────────────────────────────────────────────────────

def _oe_stub(via='consulta', resultado=None):
    from app.models.organismos_expediente import OrganismoExpediente
    oe = MagicMock()
    oe.via = via
    oe.resultado = resultado
    oe.consulta_completa = property(lambda s: OrganismoExpediente.consulta_completa.fget(s))
    # Instanciar delegando al método real
    oe.consulta_completa = OrganismoExpediente.consulta_completa.fget(oe)
    return oe


class TestConsultaCompleta:

    def _eval(self, via, resultado):
        from app.models.organismos_expediente import OrganismoExpediente
        oe = MagicMock()
        oe.via = via
        oe.resultado = resultado
        return OrganismoExpediente.consulta_completa.fget(oe)

    def test_resultado_none_incompleta(self):
        """Ciclo en curso (#396: 'pendiente'/'separata_enviada'/'en_tramitacion'
        ya no son valores de resultado — el único representante de "aún no
        cerrado" es NULL)."""
        assert not self._eval('consulta', None)

    def test_cerrado_favorable_completa(self):
        assert self._eval('consulta', 'cerrado_favorable')

    def test_cerrado_con_condicionados_completa(self):
        assert self._eval('consulta', 'cerrado_con_condicionados')

    def test_audiencia_previa_incompleta(self):
        assert not self._eval('consulta', 'audiencia_previa')

    def test_declaracion_responsable_exonerado_completa(self):
        assert self._eval('declaracion_responsable', 'exonerado')

    def test_declaracion_responsable_none_incompleta(self):
        assert not self._eval('declaracion_responsable', None)


# ─────────────────────────────────────────────────────────────────────────────
# C) condicionados_doc_id en OrganismoExpediente
# ─────────────────────────────────────────────────────────────────────────────

class TestCondicionadosDocId:

    def test_columna_presente(self):
        from app.models.organismos_expediente import OrganismoExpediente
        cols = {c.name for c in OrganismoExpediente.__table__.columns}
        assert 'condicionados_doc_id' in cols

    def test_columna_nullable(self):
        from app.models.organismos_expediente import OrganismoExpediente
        col = OrganismoExpediente.__table__.c['condicionados_doc_id']
        assert col.nullable

    def test_tramite_id_eliminado(self):
        from app.models.organismos_expediente import OrganismoExpediente
        cols = {c.name for c in OrganismoExpediente.__table__.columns}
        assert 'tramite_id' not in cols

    def test_num_iteraciones_eliminado(self):
        from app.models.organismos_expediente import OrganismoExpediente
        cols = {c.name for c in OrganismoExpediente.__table__.columns}
        assert 'num_iteraciones_organismo' not in cols
