"""Tests E2E issue #341 sesión 5 — art. 131.1 párr. 2 RD 1955/2000.

Requieren:
  - BD con migraciones S1-S5 aplicadas.
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) AAC con AAP previa favorable → 15 días naturales
  B) AAC sin AAP previa → 30 días naturales
  C) AAC con DUP (no es_solicitud_aac_pura) → 30 días naturales
"""
import pytest
from datetime import date
from unittest.mock import patch


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
        url='test://resolucion-aap',
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


def _crear_fase_consultas(db, solicitud, tipo_fase_consultas, fecha_admin):
    """
    Crea la fase CONSULTAS vinculando documento_solicitud en la solicitud.
    campo_fecha={'fk':'documento_solicitud_id'} → navega fase.solicitud.documento_solicitud.
    """
    from app.models import Fase, Documento
    doc_sol = Documento(
        expediente=solicitud.expediente,
        url='test://doc-solicitud-aac',
        fecha_administrativa=fecha_admin,
    )
    db.session.add(doc_sol)
    db.session.flush()

    solicitud.documento_solicitud = doc_sol
    db.session.flush()

    fase = Fase(
        solicitud=solicitud,
        tipo_fase=tipo_fase_consultas,
    )
    db.session.add(fase)
    db.session.flush()
    return fase


# ---------------------------------------------------------------------------
# Fixture compartida — tipos maestros
# ---------------------------------------------------------------------------

@pytest.fixture()
def tipos(app_ctx):
    from app.models import TipoFase, TipoSolicitud, TipoResultadoFase, TipoExpediente

    return {
        # RESOLUCION es la fase finalizadora genérica (es_finalizadora=True)
        'tf_resolucion':  _get_tipo(TipoFase, codigo='RESOLUCION'),
        'tf_consultas':   _get_tipo(TipoFase, codigo='CONSULTAS'),
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
    CONSULTAS de S2 → selecciona entrada orden=10 → 15 días naturales.
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
    fecha_admin = date(2025, 5, 5)
    fase_consultas = _crear_fase_consultas(
        db, sol_aac, tipos['tf_consultas'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_consultas)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_consultas, 'FASE', ctx=ctx)

    # 5 may + 15 días naturales = 20 may (martes, hábil)
    assert estado.fecha_limite == date(2025, 5, 20), (
        f'Se esperaba 2025-05-20 (15 días); obtenido {estado.fecha_limite}'
    )
    assert estado.estado != 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# B) AAC sin AAP previa → 30 días
# ---------------------------------------------------------------------------

def test_e2e_aac_sin_aap_previa_usa_plazo_30_dias(app_ctx, tipos, expediente_base):
    """
    Expediente solo con S2 AAC (sin ninguna AAP previa).
    CONSULTAS de S2 → condición falla → fallback orden=100 → 30 días.
    """
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.plazos import obtener_estado_plazo

    exp = expediente_base

    sol_aac = _crear_solicitud(db, exp, tipos['ts_aac'])
    fecha_admin = date(2025, 5, 5)
    fase_consultas = _crear_fase_consultas(
        db, sol_aac, tipos['tf_consultas'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_consultas)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_consultas, 'FASE', ctx=ctx)

    # 5 may + 30 días naturales = 4 jun (miércoles, hábil)
    assert estado.fecha_limite == date(2025, 6, 4), (
        f'Se esperaba 2025-06-04 (30 días); obtenido {estado.fecha_limite}'
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
    fecha_admin = date(2025, 5, 5)
    fase_consultas = _crear_fase_consultas(
        db, sol_aac_dup, tipos['tf_consultas'], fecha_admin
    )

    ctx = ExpedienteContext(expediente=exp, objeto=fase_consultas)

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 6)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        estado = obtener_estado_plazo(fase_consultas, 'FASE', ctx=ctx)

    assert estado.fecha_limite == date(2025, 6, 4), (
        f'Se esperaba 2025-06-04 (30 días); obtenido {estado.fecha_limite}'
    )
    assert estado.estado != 'SIN_PLAZO'
