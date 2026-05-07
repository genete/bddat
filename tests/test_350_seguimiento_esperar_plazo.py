"""Tests issue #350 — _estado_esperar_plazo consulta catalogo_plazos.

Requieren:
  - BD con migraciones 350 aplicadas:
      350_variable_tipo_tramite  (tipo_tramite en catalogo_variables)
      350_seed_catalogo_plazos   (6 entradas ESPERAR_PLAZO en catalogo_plazos)
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) tipo_tramite sin entrada en catálogo → PENDIENTE_TRAMITAR
  B) tipo_tramite configurado, plazo activo, pista no SOL → PENDIENTE_PLAZOS
  C) tipo_tramite configurado, plazo vencido → PENDIENTE_ESTUDIO
  D) tipo_tramite configurado, sin documento (inicio cómputo no disponible) → PENDIENTE_PLAZOS
  E) tipo_tramite configurado, plazo activo, pista SOL → PENDIENTE_SUBSANAR

Fechas de referencia (REQUERIMIENTO_SUBSANACION, 10 días hábiles, sin festivos):
  doc_fecha      = 2026-01-05 (lun)
  fecha_limite   = 2026-01-19 (lun)  — 10.º día hábil
  HOY_EN_PLAZO   = 2026-01-12 (lun)  — 6 hábiles restantes → EN_PLAZO
  HOY_VENCIDO    = 2026-01-20 (mar)  — 1 día tras vencimiento → VENCIDO
"""
from datetime import date
from unittest.mock import MagicMock, patch


DOC_FECHA    = date(2026, 1, 5)
HOY_EN_PLAZO = date(2026, 1, 12)
HOY_VENCIDO  = date(2026, 1, 20)


def _mock_tarea(tipo_tramite_codigo, doc_fecha=None):
    """Mock mínimo de Tarea para _estado_esperar_plazo.

    - tipo_tarea.codigo = 'ESPERAR_PLAZO'  (requerido por _get_tipo_elemento_codigo)
    - tramite.tipo_tramite.codigo          (requerido por _variables_esperar_plazo)
    - documento_usado.fecha_administrativa (requerido por _resolver_campo_fecha)
    """
    tarea = MagicMock()
    tarea.tipo_tarea = MagicMock(codigo='ESPERAR_PLAZO')
    tarea.tramite = MagicMock()
    tarea.tramite.tipo_tramite = MagicMock(codigo=tipo_tramite_codigo)
    if doc_fecha is not None:
        doc = MagicMock()
        doc.fecha_administrativa = doc_fecha
        tarea.documento_usado = doc
    else:
        tarea.documento_usado = None
    return tarea


# ---------------------------------------------------------------------------
# A) Sin entrada en catálogo → PENDIENTE_TRAMITAR
# ---------------------------------------------------------------------------

def test_sin_entrada_catalogo_devuelve_pendiente_tramitar(app_ctx):
    """SOLICITUD_COMPATIBILIDAD no tiene plazo configurado en el seed de #350.
    Debe devolver PENDIENTE_TRAMITAR independientemente de fechas.
    """
    from app.services.seguimiento import _estado_esperar_plazo

    tarea = _mock_tarea('SOLICITUD_COMPATIBILIDAD', doc_fecha=DOC_FECHA)

    with patch('app.services.plazos._hoy', return_value=HOY_EN_PLAZO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = _estado_esperar_plazo(tarea, 'MA')

    assert resultado == 'PENDIENTE_TRAMITAR'


# ---------------------------------------------------------------------------
# B) Plazo activo, pista no SOL → PENDIENTE_PLAZOS
# ---------------------------------------------------------------------------

def test_plazo_activo_pista_ma_devuelve_pendiente_plazos(app_ctx):
    """REQUERIMIENTO_SUBSANACION con 6 días hábiles restantes.
    Pista 'MA' (no SOL) → PENDIENTE_PLAZOS.
    """
    from app.services.seguimiento import _estado_esperar_plazo

    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)

    with patch('app.services.plazos._hoy', return_value=HOY_EN_PLAZO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = _estado_esperar_plazo(tarea, 'MA')

    assert resultado == 'PENDIENTE_PLAZOS'


# ---------------------------------------------------------------------------
# C) Plazo vencido → PENDIENTE_ESTUDIO
# ---------------------------------------------------------------------------

def test_plazo_vencido_devuelve_pendiente_estudio(app_ctx):
    """REQUERIMIENTO_SUBSANACION con plazo vencido (hoy > fecha_limite).
    El técnico debe actuar → PENDIENTE_ESTUDIO.
    """
    from app.services.seguimiento import _estado_esperar_plazo

    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)

    with patch('app.services.plazos._hoy', return_value=HOY_VENCIDO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = _estado_esperar_plazo(tarea, 'MA')

    assert resultado == 'PENDIENTE_ESTUDIO'


# ---------------------------------------------------------------------------
# D) Sin documento de inicio de cómputo → estado_espera (SIN_PLAZO)
# ---------------------------------------------------------------------------

def test_sin_documento_devuelve_pendiente_plazos(app_ctx):
    """REQUERIMIENTO_SUBSANACION con entrada en catálogo pero sin documento_usado.
    obtener_estado_plazo devuelve SIN_PLAZO → estado_espera → PENDIENTE_PLAZOS.
    """
    from app.services.seguimiento import _estado_esperar_plazo

    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=None)

    with patch('app.services.plazos._hoy', return_value=HOY_EN_PLAZO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = _estado_esperar_plazo(tarea, 'MA')

    assert resultado == 'PENDIENTE_PLAZOS'


# ---------------------------------------------------------------------------
# E) Plazo activo, pista SOL → PENDIENTE_SUBSANAR
# ---------------------------------------------------------------------------

def test_plazo_activo_pista_sol_devuelve_pendiente_subsanar(app_ctx):
    """REQUERIMIENTO_SUBSANACION en pista SOL (solicitud del interesado).
    Plazo activo → PENDIENTE_SUBSANAR en lugar de PENDIENTE_PLAZOS.
    """
    from app.services.seguimiento import _estado_esperar_plazo

    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)

    with patch('app.services.plazos._hoy', return_value=HOY_EN_PLAZO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        resultado = _estado_esperar_plazo(tarea, 'SOL')

    assert resultado == 'PENDIENTE_SUBSANAR'
