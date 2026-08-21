"""Tests issue #350 (revalidado en #558) — estado de tareas ESPERAR_PLAZO en seguimiento.

Tras #558 la regla de hoja vive en el núcleo (estado_dominio) y la proyección de
seguimiento (a) resuelve el plazo real vía services.plazos y (b) relabela la pista SOL
(la espera de plazo se muestra como subsanación). Aquí se prueba esa integración con el
cómputo de plazo real (catálogo seed de #350 + fechas hábiles).

Requieren:
  - BD con migraciones 350 aplicadas (350_variable_tipo_tramite, 350_seed_catalogo_plazos).
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) tipo_tramite sin entrada en catálogo → SIN_PLAZO → PENDIENTE_TRAMITAR
  B) tipo_tramite configurado, plazo activo → PENDIENTE_PLAZOS
  C) tipo_tramite configurado, plazo vencido → PENDIENTE_ESTUDIO
  D) tipo_tramite configurado, sin documento de inicio de cómputo → SIN_PLAZO →
     PENDIENTE_TRAMITAR  (cambio de #558: el núcleo unifica "sin cómputo" con el árbol;
     antes seguimiento lo trataba como espera/PLAZOS).
  E) plazo activo en la pista SOL → el relabel lo muestra como PENDIENTE_SUBSANAR.

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
    """Mock mínimo de Tarea ESPERAR_PLAZO no ejecutada para la regla de hoja.

    - ejecutada/planificada = False → el núcleo llega a la rama de plazo.
    - tipo_tarea.codigo = 'ESPERAR_PLAZO'
    - tramite.tipo_tramite.codigo  (para _variables_esperar_plazo)
    - documentos_consumidos[0].fecha_administrativa  (inicio de cómputo, ADR-010)
    """
    tarea = MagicMock()
    tarea.ejecutada = False
    tarea.planificada = False
    tarea.tipo_tarea = MagicMock(codigo='ESPERAR_PLAZO')
    # Sin documento producido, coherente con ejecutada=False (ADR-004). Explícito
    # desde #778: la entrada del catálogo declara con qué documento se cumple el
    # plazo, y un MagicMock ahí se leería como un cumplimiento con fecha falsa.
    tarea.documento_producido = None
    tarea.tramite = MagicMock()
    tarea.tramite.tipo_tramite = MagicMock(codigo=tipo_tramite_codigo)
    if doc_fecha is not None:
        doc = MagicMock()
        doc.fecha_administrativa = doc_fecha
        tarea.documentos_consumidos = [doc]
    else:
        tarea.documentos_consumidos = []
    return tarea


def _estado(tarea):
    with patch('app.services.plazos._hoy', return_value=HOY_EN_PLAZO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        from app.services.seguimiento import _estado_tarea
        return _estado_tarea(tarea)


# ---------------------------------------------------------------------------
# A) Sin entrada en catálogo → SIN_PLAZO → PENDIENTE_TRAMITAR
# ---------------------------------------------------------------------------

def test_sin_entrada_catalogo_devuelve_pendiente_tramitar(app_ctx):
    tarea = _mock_tarea('SOLICITUD_COMPATIBILIDAD', doc_fecha=DOC_FECHA)
    assert _estado(tarea) == 'PENDIENTE_TRAMITAR'


# ---------------------------------------------------------------------------
# B) Plazo activo → PENDIENTE_PLAZOS
# ---------------------------------------------------------------------------

def test_plazo_activo_devuelve_pendiente_plazos(app_ctx):
    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)
    assert _estado(tarea) == 'PENDIENTE_PLAZOS'


# ---------------------------------------------------------------------------
# C) Plazo vencido → PENDIENTE_ESTUDIO
# ---------------------------------------------------------------------------

def test_plazo_vencido_devuelve_pendiente_estudio(app_ctx):
    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)
    with patch('app.services.plazos._hoy', return_value=HOY_VENCIDO), \
         patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
        from app.services.seguimiento import _estado_tarea
        resultado = _estado_tarea(tarea)
    assert resultado == 'PENDIENTE_ESTUDIO'


# ---------------------------------------------------------------------------
# D) Sin documento de inicio de cómputo → SIN_PLAZO → PENDIENTE_TRAMITAR (#558)
# ---------------------------------------------------------------------------

def test_sin_documento_devuelve_pendiente_tramitar(app_ctx):
    """Configurado en catálogo pero sin documento que inicie el cómputo: el núcleo lo
    mapea a PENDIENTE_TRAMITAR (unificado con el árbol), no a una espera de plazo."""
    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=None)
    assert _estado(tarea) == 'PENDIENTE_TRAMITAR'


# ---------------------------------------------------------------------------
# E) Pista SOL → el relabel muestra la espera de plazo como subsanación
# ---------------------------------------------------------------------------

def test_relabel_sol_muestra_subsanar(app_ctx):
    from app.services.seguimiento import _relabel

    tarea = _mock_tarea('REQUERIMIENTO_SUBSANACION', doc_fecha=DOC_FECHA)
    estado = _estado(tarea)
    assert estado == 'PENDIENTE_PLAZOS'

    # En SOL se relabela; en el resto de pistas se mantiene PLAZOS.
    assert _relabel('SOL', estado) == 'PENDIENTE_SUBSANAR'
    assert _relabel('MA', estado) == 'PENDIENTE_PLAZOS'
