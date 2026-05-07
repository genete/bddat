"""test_348_instalacion_limpia — verifica datos de catálogo tras flask db upgrade heads

Requiere BD vacía con migraciones aplicadas desde cero.
No se puede ejecutar sobre la BD de desarrollo (ya tiene HEAD).
"""
import pytest


@pytest.mark.skip(reason="CI desactivado hasta limpiar migraciones — requiere BD limpia")
class TestCatalogoBaseTrasUpgrade:
    """Verifica que seed_catalogo_base puebla correctamente las tablas de catálogo."""

    def test_roles_count(self, db_session):
        from app.models import Rol
        assert db_session.query(Rol).count() == 4

    def test_tipos_fases_count(self, db_session):
        from app.models import TipoFase
        assert db_session.query(TipoFase).count() == 9

    def test_tipos_tramites_count(self, db_session):
        from app.models import TipoTramite
        assert db_session.query(TipoTramite).count() == 24

    def test_tipos_tareas_count(self, db_session):
        from app.models import TipoTarea
        assert db_session.query(TipoTarea).count() == 7

    def test_tipos_solicitudes_minimo(self, db_session):
        from app.models import TipoSolicitud
        # 17 base + 4 combinados = 21
        assert db_session.query(TipoSolicitud).count() == 21

    def test_tipos_ia_count(self, db_session):
        from app.models import TipoIA
        assert db_session.query(TipoIA).count() == 5

    def test_tipos_resultados_fases_count(self, db_session):
        from app.models import TipoResultadoFase
        assert db_session.query(TipoResultadoFase).count() == 6

    def test_tipos_expedientes_count(self, db_session):
        from app.models import TipoExpediente
        assert db_session.query(TipoExpediente).count() == 8

    def test_tarea_analizar_codigo_correcto(self, db_session):
        from app.models import TipoTarea
        tarea = db_session.query(TipoTarea).filter_by(id=1).one()
        assert tarea.codigo == 'ANALIZAR'

    def test_normas_seed(self, db_session):
        from app.models import Norma
        codigos = {n.codigo for n in db_session.query(Norma).filter(Norma.id.in_([3, 4])).all()}
        assert codigos == {'RD1955_2000', 'D9_2011'}

    def test_fases_tramites_count(self, db_session):
        from app.models import FaseTramite
        # 25 de seed_catalogo_base/a1b2c3d4e5f6 + 2 de 8deef1de808e = 27
        assert db_session.query(FaseTramite).count() == 27
