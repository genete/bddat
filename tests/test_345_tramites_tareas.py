"""Tests issue #345 — tramites_tareas: catálogo formal de secuencias de tareas.

Requieren BD con migraciones 345 aplicadas:
    345_tramites_tareas        (crea la tabla)
    345_seed_tramites_tareas   (pobla las 24 secuencias)

La sección F compara el catálogo con `docs/referencia/ESTRUCTURA_FTT.json` (#964).
"""
import json
from pathlib import Path

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
    """Todos los tipos de trámite del catálogo tienen al menos una tarea."""
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


# ---------------------------------------------------------------------------
# D) #368 — REDACTAR_ANUNCIO (ANUNCIO_BOJA, con los demás anuncios en F)
# ---------------------------------------------------------------------------

def test_redactar_anuncio_secuencia(app_ctx):
    """REDACTAR_ANUNCIO tiene exactamente una tarea ELABORAR."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite = db.session.query(TipoTramite).filter_by(codigo='REDACTAR_ANUNCIO').one()
    secuencia = (
        db.session.query(TramiteTarea)
        .filter_by(tipo_tramite_id=tramite.id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    codigos = [tt.tipo_tarea.codigo for tt in secuencia]
    assert codigos == ['ELABORAR']


# ---------------------------------------------------------------------------
# E) #369 — ANUNCIO_TITULAR
# ---------------------------------------------------------------------------

def test_anuncio_titular_secuencia(app_ctx):
    """ANUNCIO_TITULAR sigue el patrón B: ELABORAR→NOTIFICAR."""
    from app import db
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite = db.session.query(TipoTramite).filter_by(codigo='ANUNCIO_TITULAR').one()
    secuencia = (
        db.session.query(TramiteTarea)
        .filter_by(tipo_tramite_id=tramite.id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    codigos = [tt.tipo_tarea.codigo for tt in secuencia]
    assert codigos == ['ELABORAR', 'NOTIFICAR']


# ---------------------------------------------------------------------------
# F) #964 — anuncios de INFORMACION_PUBLICA y guarda contra ESTRUCTURA_FTT.json
# ---------------------------------------------------------------------------

def _secuencia(codigo_tramite):
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite = TipoTramite.query.filter_by(codigo=codigo_tramite).one()
    filas = (TramiteTarea.query.filter_by(tipo_tramite_id=tramite.id)
             .order_by(TramiteTarea.orden).all())
    return [f.tipo_tarea.codigo for f in filas]


# Secuencia exacta, no recuento: los tests anteriores solo contaban las dos
# ESPERAR_PLAZO de BOE y BOJA, y pasaban con el catálogo mal (#964).
SECUENCIAS_ANUNCIOS = {
    'ANUNCIO_BOE': ['ESPERAR_PLAZO', 'ESPERAR_PLAZO'],
    'ANUNCIO_PRENSA': ['ESPERAR_PLAZO', 'ESPERAR_PLAZO'],
    'ANUNCIO_BOJA': ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO'],
    'ANUNCIO_BOP': ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO'],
    'TABLON_AYUNTAMIENTOS': ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO'],
}


@pytest.mark.parametrize('codigo', sorted(SECUENCIAS_ANUNCIOS))
def test_secuencia_exacta_anuncios_ip(app_ctx, codigo):
    assert _secuencia(codigo) == SECUENCIAS_ANUNCIOS[codigo]


# Trámites del JSON sin poblar en BD a propósito: la consulta al operador del
# sistema (#450). Al poblarlos, quitarlos de aquí.
_SOLO_EN_JSON = {'SOLICITUD_INFORME_OPERADOR', 'RECEPCION_INFORME_OPERADOR'}


def _secuencias_json():
    """{codigo de trámite: {secuencia, …}} de `tareas_indicativas`, fase a fase."""
    ruta = Path(__file__).resolve().parents[1] / 'docs' / 'referencia' / 'ESTRUCTURA_FTT.json'
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    por_tramite = {}
    for fase in datos['FASES']:
        for tramite in fase.get('tramites', []):
            secuencia = tuple(tramite.get('tareas_indicativas') or ())
            por_tramite.setdefault(tramite['codigo'], set()).add(secuencia)
    return por_tramite


def test_json_da_una_sola_secuencia_por_tramite():
    """Un trámite que comparten varias fases (NOTIFICACION, RECEPCION_INFORME…)
    tiene una sola secuencia en `tramites_tareas`: el JSON no puede darle dos."""
    dobles = {c: s for c, s in _secuencias_json().items() if len(s) > 1}
    assert dobles == {}


def test_tramites_tareas_sigue_al_json(app_ctx):
    """Guarda de #964: la secuencia de cada trámite en el catálogo es la de
    `ESTRUCTURA_FTT.json`, la fuente de verdad. Es lo que habría cazado los
    anuncios de IP al cerrar #414, que corrigió el JSON sin migración."""
    from app.models.tipos_tramites import TipoTramite

    en_json = {c: list(next(iter(s))) for c, s in _secuencias_json().items()}
    en_bd = {t.codigo: _secuencia(t.codigo) for t in TipoTramite.query.all()}

    assert set(en_json) - set(en_bd) == _SOLO_EN_JSON
    assert set(en_bd) - set(en_json) == set()
    distintos = {c: {'json': en_json[c], 'bd': en_bd[c]}
                 for c in set(en_json) & set(en_bd) if en_json[c] != en_bd[c]}
    assert distintos == {}
