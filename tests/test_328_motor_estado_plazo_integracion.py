"""Tests issue #328 — integración e2e: evaluar_multi entrega estado_plazo al motor.

Verifica la cadena completa:
  evaluar_multi(accion, exp, tarea)
    → _compilar_variables(ctx)            # calcula estado_plazo real vía plazos.py
    → evaluar(accion, sujeto, variables)  # motor evalúa ReglaMotor condicionada en estado_plazo
    → EvaluacionResult bloqueado/permitido

El elemento con plazo es la tarea ESPERAR_PLAZO de la separata desde #788: la
fase no porta fecha administrativa y por tanto no puede tener plazo. Lo que se
prueba aquí no cambia — que el estado calculado llega al motor y condiciona el
efecto—, solo el nivel al que se calcula.

Nota sobre el sujeto: `_compilar_sujeto` para en el trámite (4 segmentos), así
que la regla de una tarea se escribe contra `.../<fase>/<tramite>`. Es
deliberado: alargarlo rompería el matching de todas las reglas del motor (ver
`plazos.compilar_camino`).

Requiere:
  - BD con migraciones y seed de catalogo_plazos para CONSULTA_SEPARATA (30 días hábiles).
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


def _crear_espera_separata(db, solicitud, tipos, fecha_notificacion):
    """Fase CONSULTAS → trámite CONSULTA_SEPARATA → tarea ESPERAR_PLAZO.

    El justificante que consume la tarea porta la fecha de inicio del cómputo
    (campo_fecha={'rol':'CONSUMIDO'}).
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
        url='https://docs.test/justificante-328',
        fecha_administrativa=fecha_notificacion,
    )
    db.session.add(justificante)
    db.session.flush()

    db.session.add(DocumentoTarea(
        tarea_id=tarea.id, documento_id=justificante.id, rol='CONSUMIDO',
    ))
    db.session.flush()
    return tarea


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
    from app.models import (TipoFase, TipoSolicitud, TipoExpediente,
                            TipoTramite, TipoTarea)
    return {
        'tf_consultas': _get_tipo(TipoFase, codigo='CONSULTAS'),
        'tt_separata':  _get_tipo(TipoTramite, codigo='CONSULTA_SEPARATA'),
        'tta_esperar':  _get_tipo(TipoTarea, codigo='ESPERAR_PLAZO'),
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
    evaluar_multi('BORRAR', exp, tarea) devuelve BLOQUEAR cuando:
      - Existe ReglaMotor: BORRAR/estado_plazo==VENCIDO → BLOQUEAR
      - notificación=2024-01-01 + _hoy=2025-05-01 → VENCIDO (>30 días hábiles)
    """
    from app import db
    from app.services.assembler import evaluar_multi

    sol = _crear_solicitud(db, expediente_328, tipos_328['ts_aac'])
    espera = _crear_espera_separata(db, sol, tipos_328, date(2024, 1, 1))

    sujeto_patron = f'ANY/{tipos_328["ts_aac"].siglas}/CONSULTAS/CONSULTA_SEPARATA'
    _insertar_regla_estado_plazo(db, sujeto_patron, 'VENCIDO')

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 1)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = evaluar_multi('BORRAR', expediente_328, espera)

    assert not resultado.permitido, (
        'Se esperaba BLOQUEAR (estado_plazo=VENCIDO); obtenido permitido=True'
    )


# ---------------------------------------------------------------------------
# B) Plazo en vigor → PERMITIR (la condición VENCIDO no se cumple)
# ---------------------------------------------------------------------------

def test_evaluar_multi_permite_cuando_estado_plazo_en_plazo(app_ctx, tipos_328, expediente_328):
    """
    Con la misma regla activa, si el plazo no ha vencido el motor no bloquea:
      - notificación=2025-04-28 + _hoy=2025-05-01 → EN_PLAZO (3 de 30 días hábiles)
      - La condición estado_plazo==VENCIDO no se cumple → PERMITIR
    """
    from app import db
    from app.services.assembler import evaluar_multi

    sol = _crear_solicitud(db, expediente_328, tipos_328['ts_aac'])
    espera = _crear_espera_separata(db, sol, tipos_328, date(2025, 4, 28))

    sujeto_patron = f'ANY/{tipos_328["ts_aac"].siglas}/CONSULTAS/CONSULTA_SEPARATA'
    _insertar_regla_estado_plazo(db, sujeto_patron, 'VENCIDO')

    with patch('app.services.plazos._hoy', return_value=date(2025, 5, 1)), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = evaluar_multi('BORRAR', expediente_328, espera)

    assert resultado.permitido, (
        'Se esperaba PERMITIR (estado_plazo=EN_PLAZO); obtenido permitido=False'
    )
