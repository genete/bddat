"""Tests issue #328 — integración e2e: evaluar_multi entrega estado_plazo al motor.

Verifica la cadena completa:
  evaluar_multi(accion, exp, fase)
    → _compilar_variables(ctx)            # calcula estado_plazo real vía plazos.py
    → evaluar(accion, sujeto, variables)  # motor evalúa ReglaMotor condicionada en estado_plazo
    → EvaluacionResult bloqueado/permitido

Requiere:
  - BD con migraciones y seed de catalogo_plazos para CONSULTAS/AAC (30 días naturales).
  - catalogo_variables con estado_plazo activa (id=2).
  - Fixture app_ctx (rollback automático por test).
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
# Helpers ORM (misma estructura que test_341_e2e_art131)
# ---------------------------------------------------------------------------

def _get_tipo(model_class, **filtros):
    obj = model_class.query.filter_by(**filtros).first()
    assert obj is not None, (
        f'{model_class.__name__} con {filtros} no encontrado — ¿migración aplicada?'
    )
    return obj


def _crear_solicitud(db, expediente, tipo_solicitud):
    from app.models import Solicitud, Entidad
    entidad = Entidad.query.first()
    assert entidad is not None, 'Tabla entidades vacía — seed necesario'
    sol = Solicitud(expediente=expediente, tipo_solicitud=tipo_solicitud, entidad=entidad)
    db.session.add(sol)
    db.session.flush()
    return sol


def _crear_fase_consultas(db, solicitud, tipo_fase_consultas, fecha_admin):
    """Crea fase CONSULTAS con documento_solicitud (campo_fecha para cómputo de plazo)."""
    from app.models import Fase, Documento
    doc_sol = Documento(
        expediente=solicitud.expediente,
        url='https://docs.test/doc-328',
        fecha_administrativa=fecha_admin,
    )
    db.session.add(doc_sol)
    db.session.flush()
    solicitud.documento_solicitud = doc_sol
    db.session.flush()
    fase = Fase(solicitud=solicitud, tipo_fase=tipo_fase_consultas)
    db.session.add(fase)
    db.session.flush()
    return fase


def _insertar_regla_estado_plazo(db, sujeto_patron, valor_bloqueo):
    """Inserta ReglaMotor + CondicionRegla: BORRAR bloqueado si estado_plazo == valor_bloqueo."""
    from app.models.motor_reglas import ReglaMotor, CondicionRegla, CatalogoVariable
    var = CatalogoVariable.query.filter_by(nombre='estado_plazo').first()
    assert var is not None, 'catalogo_variables sin estado_plazo — seed pendiente'

    regla = ReglaMotor(
        accion='BORRAR',
        sujeto=sujeto_patron,
        efecto='BLOQUEAR',
        descripcion=f'Test #328: bloquear BORRAR cuando estado_plazo={valor_bloqueo}',
    )
    db.session.add(regla)
    db.session.flush()

    condicion = CondicionRegla(
        regla_id=regla.id,
        variable_id=var.id,
        operador='EQ',
        valor=valor_bloqueo,
        orden=1,
    )
    db.session.add(condicion)
    db.session.flush()
    return regla


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tipos_328(app_ctx):
    from app.models import TipoFase, TipoSolicitud, TipoExpediente
    return {
        'tf_consultas': _get_tipo(TipoFase, codigo='CONSULTAS'),
        'ts_aac':       _get_tipo(TipoSolicitud, siglas='AAC'),
        'tipo_exp':     TipoExpediente.query.first(),
    }


@pytest.fixture()
def expediente_328(app_ctx, tipos_328):
    from app import db
    from app.models import Expediente, Proyecto
    import time
    proyecto = Proyecto(
        titulo='Proyecto test #328',
        descripcion='Test',
        fecha=date(2025, 1, 1),
        finalidad='Test',
        emplazamiento='Test',
    )
    db.session.add(proyecto)
    db.session.flush()
    exp = Expediente(
        numero_at=int(time.time() * 1000) % 10_000_000,
        proyecto=proyecto,
        tipo_expediente=tipos_328['tipo_exp'],
    )
    db.session.add(exp)
    db.session.flush()
    return exp


# ---------------------------------------------------------------------------
# A) Plazo vencido → BLOQUEAR
# ---------------------------------------------------------------------------

def test_evaluar_multi_bloquea_cuando_estado_plazo_vencido(app_ctx, tipos_328, expediente_328):
    """
    evaluar_multi('BORRAR', exp, fase) devuelve BLOQUEAR cuando:
      - Existe ReglaMotor: BORRAR/estado_plazo==VENCIDO → BLOQUEAR
      - fecha_admin=2024-01-01 + _hoy=2025-05-01 → VENCIDO (>30 días naturales)
    """
    from app import db
    from app.services.assembler import evaluar_multi

    sol = _crear_solicitud(db, expediente_328, tipos_328['ts_aac'])
    fase = _crear_fase_consultas(db, sol, tipos_328['tf_consultas'], date(2024, 1, 1))

    sujeto_patron = f'ANY/{tipos_328["ts_aac"].siglas}/CONSULTAS'
    _insertar_regla_estado_plazo(db, sujeto_patron, 'VENCIDO')

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 1)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = evaluar_multi('BORRAR', expediente_328, fase)

    assert not resultado.permitido, (
        'Se esperaba BLOQUEAR (estado_plazo=VENCIDO); obtenido permitido=True'
    )


# ---------------------------------------------------------------------------
# B) Plazo en vigor → PERMITIR (la condición VENCIDO no se cumple)
# ---------------------------------------------------------------------------

def test_evaluar_multi_permite_cuando_estado_plazo_en_plazo(app_ctx, tipos_328, expediente_328):
    """
    Con la misma regla activa, si el plazo no ha vencido el motor no bloquea:
      - fecha_admin=2025-04-28 + _hoy=2025-05-01 → EN_PLAZO (3 de 30 días transcurridos)
      - La condición estado_plazo==VENCIDO no se cumple → PERMITIR
    """
    from app import db
    from app.services.assembler import evaluar_multi

    sol = _crear_solicitud(db, expediente_328, tipos_328['ts_aac'])
    fase = _crear_fase_consultas(db, sol, tipos_328['tf_consultas'], date(2025, 4, 28))

    sujeto_patron = f'ANY/{tipos_328["ts_aac"].siglas}/CONSULTAS'
    _insertar_regla_estado_plazo(db, sujeto_patron, 'VENCIDO')

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 1)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = evaluar_multi('BORRAR', expediente_328, fase)

    assert resultado.permitido, (
        'Se esperaba PERMITIR (estado_plazo=EN_PLAZO); obtenido permitido=False'
    )
