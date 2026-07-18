"""
Tests issue #591 — activo_red, envolvente, activos_expediente + variables
aplica_rd223_2008 / aplica_rd337_2014.

Los tests de integración (clase TestIntegracionBD) requieren la migración
fd603abba8af aplicada en la BD de desarrollo — se skippean si las tablas
no existen todavía.
"""
from datetime import date

import pytest


@pytest.fixture(autouse=True)
def _fs_tmp(fs_tmp):
    """FILESYSTEM_BASE redirigido a tmp_path (#674) — precaución, mismo patrón
    que los demás tests que crean Expediente con numero_at de prueba."""
    pass


# ---------------------------------------------------------------------------
# A) Modelos — repr / properties, sin BD
# ---------------------------------------------------------------------------

class TestModelos:

    def test_envolvente_es_fisica(self):
        from app.models.activo_red import Envolvente
        env = Envolvente(tipo='subestacion')
        assert env.es_fisica is True
        assert env.es_logica is False

    def test_envolvente_es_logica(self):
        from app.models.activo_red import Envolvente
        env = Envolvente(tipo='linea')
        assert env.es_logica is True
        assert env.es_fisica is False

    def test_repr_activo_red(self):
        from app.models.activo_red import ActivoRed
        a = ActivoRed(nombre='LA JANDA')
        assert 'LA JANDA' in repr(a)


# ---------------------------------------------------------------------------
# B) Variables aplica_rd223_2008 / aplica_rd337_2014 — stubs duck-typing
# ---------------------------------------------------------------------------

class _StubEnvolvente:
    _FISICAS = {'centro_transformacion', 'subestacion', 'posicion',
                'armario_seccionamiento', 'celda_prefabricada',
                'planta_fotovoltaica', 'parque_eolico',
                'planta_almacenamiento', 'planta_hibrida'}
    _LOGICAS = {'linea', 'circuito'}

    def __init__(self, tipo):
        self.tipo = tipo

    @property
    def es_fisica(self):
        return self.tipo in self._FISICAS

    @property
    def es_logica(self):
        return self.tipo in self._LOGICAS


class _StubActivo:
    def __init__(self, envolvente=None):
        self.envolvente = envolvente


class _StubVinculo:
    def __init__(self, activo):
        self.activo = activo


class _StubExpediente:
    def __init__(self, vinculos=None):
        self.activos_expediente = vinculos or []


class _StubCtx:
    def __init__(self, expediente):
        self.expediente = expediente


def _get_variable(nombre):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no registrada'
    return fn


class TestVariableRD223:

    def test_registrada(self):
        _get_variable('aplica_rd223_2008')

    def test_sin_expediente(self):
        fn = _get_variable('aplica_rd223_2008')
        assert fn(_StubCtx(None)) is False

    def test_sin_activos(self):
        fn = _get_variable('aplica_rd223_2008')
        assert fn(_StubCtx(_StubExpediente([]))) is False

    def test_con_envolvente_logica(self):
        fn = _get_variable('aplica_rd223_2008')
        vinculo = _StubVinculo(_StubActivo(_StubEnvolvente('linea')))
        assert fn(_StubCtx(_StubExpediente([vinculo]))) is True

    def test_solo_envolvente_fisica_no_activa(self):
        fn = _get_variable('aplica_rd223_2008')
        vinculo = _StubVinculo(_StubActivo(_StubEnvolvente('subestacion')))
        assert fn(_StubCtx(_StubExpediente([vinculo]))) is False

    def test_activo_sin_envolvente_no_activa(self):
        fn = _get_variable('aplica_rd223_2008')
        vinculo = _StubVinculo(_StubActivo(envolvente=None))
        assert fn(_StubCtx(_StubExpediente([vinculo]))) is False


class TestVariableRD337:

    def test_registrada(self):
        _get_variable('aplica_rd337_2014')

    def test_sin_expediente(self):
        fn = _get_variable('aplica_rd337_2014')
        assert fn(_StubCtx(None)) is False

    def test_con_envolvente_fisica(self):
        fn = _get_variable('aplica_rd337_2014')
        vinculo = _StubVinculo(_StubActivo(_StubEnvolvente('centro_transformacion')))
        assert fn(_StubCtx(_StubExpediente([vinculo]))) is True

    def test_solo_envolvente_logica_no_activa(self):
        fn = _get_variable('aplica_rd337_2014')
        vinculo = _StubVinculo(_StubActivo(_StubEnvolvente('circuito')))
        assert fn(_StubCtx(_StubExpediente([vinculo]))) is False


class TestAmbosRDSimultaneos:

    def test_linea_y_subestacion_activan_ambas(self):
        """Un expediente con una línea (RD223) que llega a una subestación
        nueva (RD337) debe activar ambas variables a la vez."""
        fn_223 = _get_variable('aplica_rd223_2008')
        fn_337 = _get_variable('aplica_rd337_2014')
        vinculos = [
            _StubVinculo(_StubActivo(_StubEnvolvente('linea'))),
            _StubVinculo(_StubActivo(_StubEnvolvente('subestacion'))),
        ]
        ctx = _StubCtx(_StubExpediente(vinculos))
        assert fn_223(ctx) is True
        assert fn_337(ctx) is True


# ---------------------------------------------------------------------------
# C) Integración con BD real — requiere migración fd603abba8af aplicada
# ---------------------------------------------------------------------------

def _tablas_existen():
    from app import db
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    return inspector.has_table('activo_red', schema='public')


def _crear_expediente(db, tipo_exp):
    from app.models import Expediente, Proyecto
    import time
    proyecto = Proyecto(
        titulo='Test activo_red #591',
        descripcion='Test',
        fecha=date(2026, 1, 1),
        finalidad='Test',
        emplazamiento='Test',
    )
    db.session.add(proyecto)
    db.session.flush()
    numero_at = int(time.time() * 1000) % 10_000_000
    exp = Expediente(numero_at=numero_at, proyecto=proyecto, tipo_expediente=tipo_exp)
    db.session.add(exp)
    db.session.flush()
    return exp


class TestIntegracionBD:
    """
    Requiere la migración fd603abba8af aplicada — se skippea con
    ProgrammingError (tabla inexistente) si aún no se ha corrido
    `flask db upgrade` en la BD de desarrollo.
    """

    def test_vinculo_activo_expediente_activa_variable(self, app_ctx):
        from app import db
        from app.models import TipoExpediente
        from app.models.activo_red import ActivoRed, Envolvente
        from app.models.activos_expediente import ActivoExpediente
        from app.services.assembler import ExpedienteContext

        if not _tablas_existen():
            pytest.skip('Migración fd603abba8af no aplicada todavía (tabla activo_red ausente)')

        tipo_exp = TipoExpediente.query.first()
        assert tipo_exp is not None, 'Sin tipos_expedientes en BD de test'
        exp = _crear_expediente(db, tipo_exp)

        activo = ActivoRed(nombre='Línea test #591')
        db.session.add(activo)
        db.session.flush()

        envolvente = Envolvente(activo_id=activo.id, tipo='linea')
        db.session.add(envolvente)

        vinculo = ActivoExpediente(
            activo_id=activo.id,
            expediente_id=exp.id,
            estado_administrativo='en_tramitacion',
        )
        db.session.add(vinculo)
        db.session.flush()

        import app.services.variables.calculado  # noqa: F401 — registra las funciones
        from app.services.variables import _REGISTRY

        ctx = ExpedienteContext(exp)
        assert _REGISTRY['aplica_rd223_2008'](ctx) is True
        assert _REGISTRY['aplica_rd337_2014'](ctx) is False

    def test_expediente_con_ambos_tipos_de_envolvente(self, app_ctx):
        from app import db
        from app.models import TipoExpediente
        from app.models.activo_red import ActivoRed, Envolvente
        from app.models.activos_expediente import ActivoExpediente
        from app.services.assembler import ExpedienteContext
        from app.services.variables import _REGISTRY

        if not _tablas_existen():
            pytest.skip('Migración fd603abba8af no aplicada todavía (tabla activo_red ausente)')

        tipo_exp = TipoExpediente.query.first()
        exp = _crear_expediente(db, tipo_exp)

        linea = ActivoRed(nombre='Línea test #591')
        subestacion = ActivoRed(nombre='Subestación test #591')
        db.session.add_all([linea, subestacion])
        db.session.flush()

        db.session.add(Envolvente(activo_id=linea.id, tipo='linea'))
        db.session.add(Envolvente(activo_id=subestacion.id, tipo='subestacion'))

        db.session.add(ActivoExpediente(
            activo_id=linea.id, expediente_id=exp.id, estado_administrativo='en_tramitacion',
        ))
        db.session.add(ActivoExpediente(
            activo_id=subestacion.id, expediente_id=exp.id, estado_administrativo='en_tramitacion',
        ))
        db.session.flush()

        ctx = ExpedienteContext(exp)
        assert _REGISTRY['aplica_rd223_2008'](ctx) is True
        assert _REGISTRY['aplica_rd337_2014'](ctx) is True
