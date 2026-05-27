"""Tests issue #1 — Cuaderno de bitácora agnóstico.

Bloques:
  A) registrar() — escritura correcta en BD.
  B) CHECK constraint — operación inválida rechazada por BD.
  C) detalle libre — JSON arbitrario admitido y recuperado íntegro.
  D) entradas independientes — cada operación produce su propia fila.
  E) columna nullable — solo obligatoria semánticamente en ALTERAR.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.bitacora import Bitacora
from app.services.bitacora import registrar

# ID de usuario existente en el seed de desarrollo
_UID = 1


# ---------------------------------------------------------------------------
# A) Escritura correcta
# ---------------------------------------------------------------------------

def test_registrar_persiste_campos_basicos(app_ctx):
    entrada = registrar(_UID, 'CREAR', 'expedientes', 42)
    db.session.flush()

    assert entrada.id is not None
    assert entrada.usuario_id == _UID
    assert entrada.operacion == 'CREAR'
    assert entrada.tabla == 'expedientes'
    assert entrada.registro_id == 42
    assert entrada.columna is None
    assert entrada.detalle is None
    assert entrada.created_at is not None


# ---------------------------------------------------------------------------
# B) CHECK constraint — operación inválida
# ---------------------------------------------------------------------------

def test_operacion_invalida_viola_constraint(app_ctx):
    registrar(_UID, 'LEER', 'expedientes', 1)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


# ---------------------------------------------------------------------------
# C) Detalle libre
# ---------------------------------------------------------------------------

def test_detalle_libre_json_arbitrario(app_ctx):
    payload = {'escape': True, 'regla_id': 5, 'justificacion': 'texto libre', 'ids': [3, 7]}
    entrada = registrar(_UID, 'ALTERAR', 'tramites', 10, columna='estado', detalle=payload)
    db.session.flush()

    recuperado = Bitacora.query.get(entrada.id)
    assert recuperado.detalle == payload


# ---------------------------------------------------------------------------
# D) Entradas independientes por operación
# ---------------------------------------------------------------------------

def test_tres_operaciones_generan_tres_entradas(app_ctx):
    registrar(_UID, 'CREAR',  'fases', 1)
    registrar(_UID, 'ALTERAR', 'fases', 1, columna='resultado')
    registrar(_UID, 'BORRAR', 'fases', 1, detalle={'nombre': 'INSTRUCCION'})
    db.session.flush()

    filas = Bitacora.query.filter_by(tabla='fases', registro_id=1).all()
    assert len(filas) == 3
    operaciones = {f.operacion for f in filas}
    assert operaciones == {'CREAR', 'ALTERAR', 'BORRAR'}


# ---------------------------------------------------------------------------
# E) columna nullable fuera de ALTERAR
# ---------------------------------------------------------------------------

def test_columna_nullable_en_crear_y_borrar(app_ctx):
    e1 = registrar(_UID, 'CREAR',  'tareas', 99)
    e2 = registrar(_UID, 'BORRAR', 'tareas', 99)
    db.session.flush()

    assert e1.columna is None
    assert e2.columna is None
