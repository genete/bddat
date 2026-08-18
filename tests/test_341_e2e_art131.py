"""Tests E2E issue #341 sesión 5 — art. 131.1 párr. 2 RD 1955/2000.

Reanclados a nivel TAREA en #788. Los 15/30 días no son de la fase CONSULTAS
sino de cada organismo consultado, y corren desde la notificación de SU separata:
el plazo vive en la tarea ESPERAR_PLAZO del trámite CONSULTA_SEPARATA, cuyo
documento consumido es el justificante de esa notificación. Las dos filas de
nivel fase que lo contaban en días naturales desde la fecha de solicitud eran un
duplicado mal anclado del seed #341, anterior al #463 que puso el mismo plazo en
el nivel del acto; se retiraron en la migración 788b.

Lo que estos tests siguen verificando es lo mismo: que las DOS CONDICIONES del
art. 131.1 párr. 2 (`es_solicitud_aac_pura` + `tiene_solicitud_aap_favorable`)
seleccionan la entrada de 15 en vez de la de 30, sobre grafo ORM real y contexto
completo.

Requieren:
  - BD con migraciones S1-S5 y 788 aplicadas.
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) AAC con AAP previa favorable → 15 días hábiles
  B) AAC sin AAP previa → 30 días hábiles
  C) AAC con DUP (no es_solicitud_aac_pura) → 30 días hábiles
"""
import pytest
from datetime import date
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _fs_tmp(fs_tmp):
    """FILESYSTEM_BASE redirigido a tmp_path (#674) — precaución, mismo patrón
    que los demás tests que crean Expediente con numero_at de prueba."""
    pass


# ---------------------------------------------------------------------------
# Helpers de construcción del grafo ORM
# ---------------------------------------------------------------------------

def _get_tipo(model_class, **filtros):
    obj = model_class.query.filter_by(**filtros).first()
    assert obj is not None, (
        f'{model_class.__name__} con {filtros} no encontrado — '
        f'¿migración S5 aplicada?'
    )
    return obj


def _crear_solicitud(db, expediente, tipo_solicitud):
    from app.models import Solicitud, Entidad
    entidad = Entidad.query.first()
    assert entidad is not None, 'Tabla entidades vacía — seed necesario'
    sol = Solicitud(
        expediente=expediente,
        tipo_solicitud=tipo_solicitud,
        entidad=entidad,
    )
    db.session.add(sol)
    db.session.flush()
    return sol


def _crear_fase_finalizadora_favorable(db, solicitud, tipo_fase_resolucion, resultado_favorable):
    from app.models import Fase, Documento
    doc = Documento(
        expediente=solicitud.expediente,
        url='https://test.local/resolucion-aap',
        fecha_administrativa=date(2025, 1, 15),
    )
    db.session.add(doc)
    db.session.flush()

    fase = Fase(
        solicitud=solicitud,
        tipo_fase=tipo_fase_resolucion,
        resultado_fase=resultado_favorable,
        documento_resultado=doc,
    )
    db.session.add(fase)
    db.session.flush()
    return fase


def _crear_espera_separata(db, solicitud, tipos, fecha_notificacion):
    """Fase CONSULTAS → trámite CONSULTA_SEPARATA → tarea ESPERAR_PLAZO.

    La tarea consume el justificante de la notificación de la separata: es ese
    documento el que porta la fecha de inicio del cómputo
    (campo_fecha={'rol':'CONSUMIDO'}). Devuelve la tarea, que es el elemento con
    plazo desde #788.
    """
    from app.models import Fase, Tramite, Tarea, Documento
    from app.models.documentos_tarea import DocumentoTarea

    fase = Fase(solicitud=solicitud, tipo_fase=tipos['tf_consultas'])
    db.session.add(fase)
    db.session.flush()

    tramite = Tramite(fase=fase, tipo_tramite=tipos['tt_separata'])
    db.session.add(tramite)
    db.session.flush()

    tarea = Tarea(tramite=tramite, tipo_tarea=tipos['tta_esperar'])
    db.session.add(tarea)
    db.session.flush()

    justificante = Documento(
        expediente=solicitud.expediente,
        url='https://test.local/justificante-separata',
        fecha_administrativa=fecha_notificacion,
    )
    db.session.add(justificante)
    db.session.flush()

    db.session.add(DocumentoTarea(
        tarea_id=tarea.id, documento_id=justificante.id, rol='CONSUMIDO',
    ))
    db.session.flush()
    return tarea


# ---------------------------------------------------------------------------
# Fixture compartida — tipos maestros
# ---------------------------------------------------------------------------

@pytest.fixture()
def tipos(app_ctx):
    from app.models import (TipoFase, TipoSolicitud, TipoResultadoFase, TipoExpediente,
                            TipoTramite, TipoTarea)

    return {
        # RESOLUCION es la fase finalizadora genérica (es_finalizadora=True)
        'tf_resolucion':  _get_tipo(TipoFase, codigo='RESOLUCION'),
        'tf_consultas':   _get_tipo(TipoFase, codigo='CONSULTAS'),
        'tt_separata':    _get_tipo(TipoTramite, codigo='CONSULTA_SEPARATA'),
        'tta_esperar':    _get_tipo(TipoTarea, codigo='ESPERAR_PLAZO'),
        'ts_aap':         _get_tipo(TipoSolicitud, siglas='AAP'),
        'ts_aac':         _get_tipo(TipoSolicitud, siglas='AAC'),
        'resultado_fav':  _get_tipo(TipoResultadoFase, codigo='FAVORABLE'),
        'tipo_exp':       TipoExpediente.query.first(),
    }


@pytest.fixture()
def expediente_base(app_ctx, tipos):
    from app import db
    from app.models import Expediente, Proyecto
    import time

    proyecto = Proyecto(
        titulo='Proyecto test E2E art.131',
        descripcion='Test',
        fecha=date(2025, 1, 1),
        finalidad='Test',
        emplazamiento='Test',
    )
    db.session.add(proyecto)
    db.session.flush()

    numero_at = int(time.time() * 1000) % 10_000_000
    exp = Expediente(
        numero_at=numero_at,
        proyecto=proyecto,
        tipo_expediente=tipos['tipo_exp'],
    )
    db.session.add(exp)
    db.session.flush()
    return exp


# ---------------------------------------------------------------------------
# A) AAC con AAP previa favorable → 15 días
# ---------------------------------------------------------------------------

def test_e2e_aac_con_aap_previa_usa_plazo_15_dias(app_ctx, tipos, expediente_base):
    """
    Expediente con S1 AAP resuelta favorablemente + S2 AAC pura.
    Espera de la separata de S2 → selecciona entrada orden=10 → 15 días hábiles.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    # S1: AAP con resolución favorable
    sol_aap = _crear_solicitud(db, exp, tipos['ts_aap'])
    _crear_fase_finalizadora_favorable(
        db, sol_aap, tipos['tf_resolucion'], tipos['resultado_fav']
    )

    # S2: AAC pura
    sol_aac = _crear_solicitud(db, exp, tipos['ts_aac'])
    espera = _crear_espera_separata(db, sol_aac, tipos, date(2025, 5, 5))

    ctx = ExpedienteContext(expediente=exp, objeto=espera)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(espera, 'TAREA', ctx=ctx)

    # lun 5 may + 15 días hábiles = lun 26 may
    assert estado.fecha_limite == date(2025, 5, 26), (
        f'Se esperaba 2025-05-26 (15 días hábiles); obtenido {estado.fecha_limite}'
    )
    assert estado.estado != 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# B) AAC sin AAP previa → 30 días
# ---------------------------------------------------------------------------

def test_e2e_aac_sin_aap_previa_usa_plazo_30_dias(app_ctx, tipos, expediente_base):
    """
    Expediente solo con S2 AAC (sin ninguna AAP previa).
    Espera de la separata → condición falla → fallback orden=20 → 30 días.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    sol_aac = _crear_solicitud(db, exp, tipos['ts_aac'])
    espera = _crear_espera_separata(db, sol_aac, tipos, date(2025, 5, 5))

    ctx = ExpedienteContext(expediente=exp, objeto=espera)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(espera, 'TAREA', ctx=ctx)

    # lun 5 may + 30 días hábiles = lun 16 jun
    assert estado.fecha_limite == date(2025, 6, 16), (
        f'Se esperaba 2025-06-16 (30 días hábiles); obtenido {estado.fecha_limite}'
    )
    assert estado.estado != 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# C) AAC con DUP → no es_solicitud_aac_pura → 30 días
# ---------------------------------------------------------------------------

def test_e2e_aac_con_dup_no_es_pura_usa_plazo_30_dias(app_ctx, tipos, expediente_base):
    """
    S2 = solicitud AAC+DUP.
    es_solicitud_aac_pura → False (contiene DUP).
    Aunque haya AAP previa favorable, la condición AND no se cumple → 30 días.
    """
    from app import db
    from app.models import TipoSolicitud
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    ts_aac_dup = TipoSolicitud.query.filter_by(siglas='AAC+DUP').first()
    if ts_aac_dup is None:
        pytest.skip('No existe tipo_solicitud AAC+DUP en BD')

    exp = expediente_base

    # S1: AAP favorable
    sol_aap = _crear_solicitud(db, exp, tipos['ts_aap'])
    _crear_fase_finalizadora_favorable(
        db, sol_aap, tipos['tf_resolucion'], tipos['resultado_fav']
    )

    # S2: AAC+DUP → es_solicitud_aac_pura = False
    sol_aac_dup = _crear_solicitud(db, exp, ts_aac_dup)
    espera = _crear_espera_separata(db, sol_aac_dup, tipos, date(2025, 5, 5))

    ctx = ExpedienteContext(expediente=exp, objeto=espera)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(espera, 'TAREA', ctx=ctx)

    assert estado.fecha_limite == date(2025, 6, 16), (
        f'Se esperaba 2025-06-16 (30 días hábiles); obtenido {estado.fecha_limite}'
    )
    assert estado.estado != 'SIN_PLAZO'
