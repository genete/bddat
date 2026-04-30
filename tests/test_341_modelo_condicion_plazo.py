"""Tests issue #341 sesión 2 — modelo CondicionPlazo y extensiones de CatalogoPlazo."""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# A) Sin BD — importación y estructura del modelo
# ---------------------------------------------------------------------------

def test_condicion_plazo_importable():
    from app.models.condiciones_plazo import CondicionPlazo
    assert CondicionPlazo.__tablename__ == 'condiciones_plazo'


def test_condicion_plazo_en_all():
    import app.models as m
    assert 'CondicionPlazo' in m.__all__


def test_catalogo_plazo_tiene_orden():
    from app.models.catalogo_plazos import CatalogoPlazo
    assert hasattr(CatalogoPlazo, 'orden')


def test_catalogo_plazo_tiene_condiciones():
    from app.models.catalogo_plazos import CatalogoPlazo
    assert hasattr(CatalogoPlazo, 'condiciones')


# ---------------------------------------------------------------------------
# B) Con BD — integridad referencial y cascade (requiere app_ctx)
# ---------------------------------------------------------------------------

@pytest.fixture()
def plazo_base(app_ctx):
    """Crea una entrada mínima en catalogo_plazos y la devuelve."""
    from app import db
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.efectos_plazo import EfectoPlazo

    efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
    assert efecto is not None, 'Seed de efectos_plazo no encontrado — ¿migración aplicada?'

    # tipo_elemento_id=9999 no existe en tipos_fases pero la FK es polimórfica (sin constraint)
    plazo = CatalogoPlazo(
        tipo_elemento='FASE',
        tipo_elemento_id=9999,
        plazo_valor=30,
        plazo_unidad='DIAS_NATURALES',
        efecto_vencimiento_id=efecto.id,
        orden=10,
    )
    db.session.add(plazo)
    db.session.flush()
    return plazo


def test_condicion_plazo_creacion(app_ctx, plazo_base):
    """Crea CondicionPlazo vinculada a CatalogoPlazo y verifica atributos."""
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    assert var is not None, 'Variable estado_plazo no encontrada — ¿migración bc4a9f1d8e02 aplicada?'

    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='EQ',
        valor='EN_PLAZO',
        orden=1,
    )
    db.session.add(cond)
    db.session.flush()

    assert cond.id is not None
    assert cond.variable.nombre == 'estado_plazo'
    assert cond.catalogo_plazo.id == plazo_base.id


def test_condicion_plazo_cascade_delete(app_ctx, plazo_base):
    """Al borrar CatalogoPlazo, sus CondicionPlazo se eliminan en cascada."""
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='EQ',
        valor='VENCIDO',
        orden=1,
    )
    db.session.add(cond)
    db.session.flush()
    cond_id = cond.id

    db.session.delete(plazo_base)
    db.session.flush()

    assert CondicionPlazo.query.get(cond_id) is None


def test_condicion_plazo_check_operador_invalido(app_ctx, plazo_base):
    """CheckConstraint rechaza operadores no reconocidos."""
    import sqlalchemy.exc
    from app import db
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable

    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    cond = CondicionPlazo(
        catalogo_plazo_id=plazo_base.id,
        variable_id=var.id,
        operador='LIKE',   # inválido — no está en el CheckConstraint
        valor='algo',
        orden=1,
    )
    db.session.add(cond)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db.session.flush()


def test_catalogo_plazo_orden_default(app_ctx):
    """Entradas existentes tienen orden=100 tras la migración."""
    from app.models.catalogo_plazos import CatalogoPlazo
    plazos = CatalogoPlazo.query.all()
    if not plazos:
        pytest.skip('BD sin seed en catalogo_plazos — server_default verificado vía ciclo upgrade/downgrade')
    assert all(p.orden == 100 for p in plazos), (
        'Alguna entrada existente tiene orden != 100; el server_default no se aplicó'
    )


def test_catalogo_plazo_relationship_condiciones_vacia(app_ctx, plazo_base):
    """Una entrada nueva sin condiciones tiene lista vacía (no None)."""
    assert plazo_base.condiciones == []
