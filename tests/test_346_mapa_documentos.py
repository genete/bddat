"""Tests issue #346 — tramites_tareas_documentos: mapa semántico de documentos.

Requieren BD con migraciones 337 y 346 aplicadas.
"""
import pytest


# ---------------------------------------------------------------------------
# Test 1 — Sin BD: estructura del modelo
# ---------------------------------------------------------------------------

def test_modelo_importable():
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    assert TramiteTareaDocumento.__tablename__ == 'tramites_tareas_documentos'


def test_modelo_en_all():
    import app.models as m
    assert 'TramiteTareaDocumento' in m.__all__


def test_pk_compuesta():
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    pk_cols = {c.name for c in TramiteTareaDocumento.__table__.primary_key.columns}
    assert pk_cols == {'tipo_tramite_id', 'orden_tarea', 'rol'}


def test_tipo_documento_id_nullable():
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    col = TramiteTareaDocumento.__table__.c['tipo_documento_id']
    assert col.nullable is True


# ---------------------------------------------------------------------------
# Test 2 — Con BD: ESPERAR_PLAZO con plazo>0 tiene ENTRADA mapeada
# ---------------------------------------------------------------------------

def test_esperar_plazo_con_plazo_tiene_entrada(app_ctx):
    """
    Todos los trámites con tarea ESPERAR_PLAZO y plazo > 0 deben tener al menos
    una fila ENTRADA en tramites_tareas_documentos para ese (tramite, orden).

    Los EP con plazo=0 se modelan con ENTRADA NULL y obligatorio=False, por lo
    que también tienen fila ENTRADA — este test verifica simplemente que no hay
    ningún par (tramite, orden_EP) sin fila ENTRADA en el mapa.
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    esperar_id = db.session.query(TipoTarea.id).filter_by(codigo='ESPERAR_PLAZO').scalar()
    assert esperar_id is not None

    pares_ep = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id == esperar_id)
        .all()
    )
    assert len(pares_ep) > 0, "No hay tareas ESPERAR_PLAZO en tramites_tareas"

    for tt_id, orden in pares_ep:
        entrada = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='ENTRADA')
            .first()
        )
        assert entrada is not None, (
            f"ESPERAR_PLAZO sin ENTRADA mapeada: tipo_tramite_id={tt_id} orden={orden}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Con BD: NOTIFICAR siempre tiene SALIDA mapeada
# ---------------------------------------------------------------------------

def test_notificar_tiene_salida(app_ctx):
    """
    Todos los pares (tramite, orden) con tarea NOTIFICAR tienen fila SALIDA
    en tramites_tareas_documentos (aunque sea NULL polimórfico).
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    notificar_id = db.session.query(TipoTarea.id).filter_by(codigo='NOTIFICAR').scalar()
    assert notificar_id is not None

    pares = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id == notificar_id)
        .all()
    )
    assert len(pares) > 0

    for tt_id, orden in pares:
        salida = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='SALIDA')
            .first()
        )
        assert salida is not None, (
            f"NOTIFICAR sin SALIDA mapeada: tipo_tramite_id={tt_id} orden={orden}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Con BD: no hay tipo_documento_id que no exista en tipos_documentos
# ---------------------------------------------------------------------------

def test_sin_tipo_documento_id_huerfano(app_ctx):
    """
    Todos los tipo_documento_id no nulos en tramites_tareas_documentos
    referencian un registro existente en tipos_documentos.
    """
    from app import db
    from sqlalchemy import text

    resultado = db.session.execute(text("""
        SELECT ttd.tipo_tramite_id, ttd.orden_tarea, ttd.rol, ttd.tipo_documento_id
        FROM public.tramites_tareas_documentos ttd
        LEFT JOIN public.tipos_documentos td ON td.id = ttd.tipo_documento_id
        WHERE ttd.tipo_documento_id IS NOT NULL
          AND td.id IS NULL
    """)).fetchall()

    assert resultado == [], (
        f"tipo_documento_id huérfanos encontrados: {resultado}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Con BD: auditoría de huecos en ELABORAR y ANALIZAR
# ---------------------------------------------------------------------------

def test_elaborar_analizar_tienen_salida(app_ctx):
    """
    Ningún par (tramite, orden_tarea) con tarea ELABORAR o ANALIZAR carece
    de fila SALIDA en tramites_tareas_documentos.
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    codigos = ['ELABORAR', 'ANALIZAR']
    ids = (
        db.session.query(TipoTarea.id)
        .filter(TipoTarea.codigo.in_(codigos))
        .all()
    )
    tarea_ids = [r[0] for r in ids]
    assert len(tarea_ids) == 2

    pares = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id.in_(tarea_ids))
        .all()
    )
    assert len(pares) > 0

    huecos = []
    for tt_id, orden in pares:
        salida = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='SALIDA')
            .first()
        )
        if salida is None:
            huecos.append((tt_id, orden))

    assert huecos == [], (
        f"ELABORAR/ANALIZAR sin SALIDA mapeada: {huecos}"
    )
