"""Tests issue #345 — tramites_tareas: catálogo formal de secuencias de tareas.

Requieren BD con migraciones 345 aplicadas:
    345_tramites_tareas        (crea la tabla)
    345_seed_tramites_tareas   (pobla las 24 secuencias)
"""
import pytest


# ---------------------------------------------------------------------------
# A) Sin BD — estructura del modelo
# ---------------------------------------------------------------------------

def test_modelo_importable():
    from app.models.tramites_tareas import TramiteTarea
    assert TramiteTarea.__tablename__ == 'tramites_tareas'


def test_modelo_en_all():
    import app.models as m
    assert 'TramiteTarea' in m.__all__


def test_pk_compuesta():
    from app.models.tramites_tareas import TramiteTarea
    pk_cols = {c.name for c in TramiteTarea.__table__.primary_key.columns}
    assert pk_cols == {'tipo_tramite_id', 'orden'}


def test_fk_tipo_tramite():
    from app.models.tramites_tareas import TramiteTarea
    col = TramiteTarea.__table__.c['tipo_tramite_id']
    assert col.foreign_keys


def test_fk_tipo_tarea():
    from app.models.tramites_tareas import TramiteTarea
    col = TramiteTarea.__table__.c['tipo_tarea_id']
    assert col.foreign_keys


# ---------------------------------------------------------------------------
# B) Con BD — integridad del seed
# ---------------------------------------------------------------------------

def test_todos_tramites_tienen_tarea(app_ctx):
    """Los 24 tipos de trámite del catálogo tienen al menos una tarea."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    total_tramites = db.session.query(TipoTramite).count()
    tramites_con_tarea = (
        db.session.query(TramiteTarea.tipo_tramite_id)
        .distinct()
        .count()
    )
    assert tramites_con_tarea == total_tramites


def test_anuncio_boe_doble_esperar_plazo(app_ctx):
    """ANUNCIO_BOE tiene exactamente 2 tareas ESPERAR_PLAZO en órdenes distintos."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    boe = db.session.query(TipoTramite).filter_by(codigo='ANUNCIO_BOE').one()
    esperar = db.session.query(TipoTarea).filter_by(codigo='ESPERAR_PLAZO').one()

    filas = (
        db.session.query(TramiteTarea)
        .filter_by(tipo_tramite_id=boe.id, tipo_tarea_id=esperar.id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    assert len(filas) == 2
    assert filas[0].orden != filas[1].orden


def test_consulta_orm_secuencia_ordenada(app_ctx):
    """Dado un TipoTramite, la secuencia de tareas devuelta está ordenada por orden."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite = db.session.query(TipoTramite).filter_by(codigo='REQUERIMIENTO_SUBSANACION').one()
    secuencia = (
        db.session.query(TramiteTarea)
        .filter_by(tipo_tramite_id=tramite.id)
        .order_by(TramiteTarea.orden)
        .all()
    )

    codigos = [tt.tipo_tarea.codigo for tt in secuencia]
    assert codigos == ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']


def test_consulta_orm_relaciones_cargadas(app_ctx):
    """TramiteTarea carga las relaciones tipo_tramite y tipo_tarea correctamente."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea

    primera = db.session.query(TramiteTarea).first()
    assert primera is not None
    assert primera.tipo_tramite is not None
    assert primera.tipo_tarea is not None


@pytest.mark.skip(reason="#345 — expedientes_solicitudes: seed pendiente de sesión de análisis normativo")
def test_expedientes_solicitudes_no_vacia(app_ctx):
    from app import db
    from app.models.expedientes_solicitudes import ExpedienteSolicitud
    assert db.session.query(ExpedienteSolicitud).count() > 0


# ---------------------------------------------------------------------------
# C) Catálogo v6.0 — ADR-003/004/005, #361, #363, #371
# ---------------------------------------------------------------------------

def test_elaborar_en_catalogo(app_ctx):
    """ELABORAR existe como tipo de tarea tras la migración 370."""
    from app import db
    from app.models.tipos_tareas import TipoTarea
    elaborar = db.session.query(TipoTarea).filter_by(codigo='ELABORAR').first()
    assert elaborar is not None


@pytest.mark.parametrize('codigo', ['REDACTAR', 'FIRMAR', 'INCORPORAR', 'PUBLICAR'])
def test_tipos_obsoletos_eliminados(app_ctx, codigo):
    """Los tipos de tarea eliminados en v6.0 no deben existir en el catálogo."""
    from app import db
    from app.models.tipos_tareas import TipoTarea
    tipo = db.session.query(TipoTarea).filter_by(codigo=codigo).first()
    assert tipo is None, f"TipoTarea '{codigo}' debería haber sido eliminado (ADR-003/004, #371)"


def test_requerimiento_subsanacion_usa_elaborar(app_ctx):
    """REQUERIMIENTO_SUBSANACION sigue el patrón C+A: ELABORAR→NOTIFICAR→ESPERAR_PLAZO→ANALIZAR."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite = db.session.query(TipoTramite).filter_by(codigo='REQUERIMIENTO_SUBSANACION').one()
    secuencia = (
        db.session.query(TramiteTarea)
        .filter_by(tipo_tramite_id=tramite.id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    codigos = [tt.tipo_tarea.codigo for tt in secuencia]
    assert codigos == ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']
