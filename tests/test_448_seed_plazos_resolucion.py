"""Tests issue #448 — seed catalogo_plazos para fase RESOLUCION.

Reescrito en #785: la identificación de la fila dejó de hacerse con la condición
`tipo_solicitud IN [...]` y pasó a ser estructural, por el segmento de siglas del
camino SFTT (`ANY/<siglas>/RESOLUCION`). Las 7 entradas originales con IN
multivalor se desdoblaron en 11, una por combinación, sin IN en el segmento.

Verifica:
  A) Variable tipo_solicitud sigue activa (la usan condiciones_requisito, #192);
     lo que ya no existe es su uso como discriminador de posición en plazos.
  B) 11 entradas RESOLUCION, cada una con su camino, norma y efecto.
  C) Para cada combinación cubierta, _seleccionar_catalogo devuelve la correcta
     partiendo del elemento (sin dict de variables).
  D) Combinaciones fuera de scope → None (deuda de #247).

Requieren BD con migración 785 aplicada y fixture app_ctx (conftest.py).
"""
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Combinaciones cubiertas y mapeo esperado (siglas → (valor, unidad, norma))
# ---------------------------------------------------------------------------

_COMBINACIONES_CUBIERTAS = {
    'AE_PROVISIONAL':     (1, 'MESES', 'Art. 132 bis RD 1955/2000 + DA 3ª LSE'),
    'AE_DEFINITIVA':      (1, 'MESES', 'Art. 132 ter RD 1955/2000 + DA 3ª LSE'),
    'AE_DEFINITIVA+AAT':  (1, 'MESES', 'Art. 132 ter RD 1955/2000 + DA 3ª LSE'),
    'AAP':                (3, 'MESES', 'Art. 128 RD 1955/2000'),
    'AAC':                (3, 'MESES', 'Art. 131.7 RD 1955/2000'),
    'AAP+AAC':            (3, 'MESES', 'Art. 131.7 RD 1955/2000'),
    'AAP+AAC+DUP':        (3, 'MESES', 'Art. 131.7 RD 1955/2000'),
    'AAC+DUP':            (3, 'MESES', 'Art. 131.7 RD 1955/2000'),
    'AAT':                (3, 'MESES', 'Art. 133 RD 1955/2000'),
    'CIERRE':             (3, 'MESES', 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'),
    'DUP':                (3, 'MESES', 'Art. 145.4 RD 1955/2000'),
}

_FUERA_DE_SCOPE = [
    'RAIPEE_PREVIA', 'RAIPEE_DEFINITIVA', 'RADNE',
    'AMPLIACION_PLAZO', 'CORRECCION_ERRORES',
    'DESISTIMIENTO', 'RENUNCIA', 'RECURSO', 'INTERESADO', 'OTRO',
]


def _fase_resolucion(siglas):
    """Fase RESOLUCION de una solicitud con las siglas dadas.

    Mock en vez de fila real: _seleccionar_catalogo solo necesita compilar el
    camino del elemento (ascendencia con strings) y consultar el catálogo, que sí
    es la tabla real de BD. Así el test no escribe nada.
    """
    fase = MagicMock()
    fase.tipo_fase = MagicMock(codigo='RESOLUCION')
    fase.solicitud.tipo_solicitud = MagicMock(siglas=siglas)
    fase.solicitud.expediente.tipo_expediente = MagicMock(tipo='Distribucion')
    return fase


def _entradas_resolucion():
    from app.models.catalogo_plazos import CatalogoPlazo
    return (
        CatalogoPlazo.query
        .filter(CatalogoPlazo.tipo_elemento == 'FASE',
                CatalogoPlazo.camino.like('%/RESOLUCION'),
                CatalogoPlazo.activo.is_(True))
        .all()
    )


# ---------------------------------------------------------------------------
# A) Variable tipo_solicitud
# ---------------------------------------------------------------------------

def test_variable_tipo_solicitud_existe_y_esta_activa(app_ctx):
    """Sigue viva: la usan condiciones_requisito (#192). Lo retirado en #785 es
    su uso como discriminador de posición en catalogo_plazos, no la variable."""
    from app.models.motor_reglas import CatalogoVariable
    var = CatalogoVariable.query.filter_by(nombre='tipo_solicitud').first()
    assert var is not None, 'Variable tipo_solicitud no existe en catalogo_variables'
    assert var.activa is True
    assert var.tipo_dato == 'texto'


def test_ninguna_condicion_de_plazo_usa_tipo_solicitud(app_ctx):
    """#785: el tipo de solicitud es posición en el árbol, va en el camino.

    Salvaguarda de regresión — si alguien vuelve a meterlo como condición, el
    catálogo recupera el problema de identificación que #785 vino a resolver.
    """
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.motor_reglas import CatalogoVariable
    conds = (
        CondicionPlazo.query
        .join(CatalogoVariable, CondicionPlazo.variable_id == CatalogoVariable.id)
        .filter(CatalogoVariable.nombre == 'tipo_solicitud')
        .all()
    )
    assert conds == [], (
        f'{len(conds)} condiciones_plazo siguen discriminando por tipo_solicitud '
        f'en vez de por camino: {[c.catalogo_plazo_id for c in conds]}'
    )


# ---------------------------------------------------------------------------
# B) Las 11 entradas están presentes con sus caminos y normas
# ---------------------------------------------------------------------------

def test_hay_exactamente_11_entradas_resolucion(app_ctx):
    """7 originales, desdobladas en 11 al pasar el IN multivalor a camino."""
    entradas = _entradas_resolucion()
    assert len(entradas) == 11, (
        f'Esperadas 11 entradas RESOLUCION, hay {len(entradas)}: '
        f'{[e.camino for e in entradas]}'
    )


def test_hay_una_entrada_por_combinacion_cubierta(app_ctx):
    caminos = {e.camino for e in _entradas_resolucion()}
    esperados = {f'ANY/{s}/RESOLUCION' for s in _COMBINACIONES_CUBIERTAS}
    assert caminos == esperados


def test_ningun_camino_de_resolucion_tiene_hoja_any(app_ctx):
    """Invariante de #785: la hoja es el tipo del elemento evaluado, nunca ANY."""
    for e in _entradas_resolucion():
        assert e.camino.rsplit('/', 1)[-1] == 'RESOLUCION', (
            f'Entrada {e.id} con hoja inesperada: {e.camino}'
        )


def test_cada_entrada_tiene_efecto_silencio_desestimatorio(app_ctx):
    for e in _entradas_resolucion():
        assert e.efecto_plazo.codigo == 'SILENCIO_DESESTIMATORIO', (
            f'Entrada {e.id} ({e.norma_origen}) tiene efecto inesperado '
            f'{e.efecto_plazo.codigo}'
        )


def test_normas_origen_esperadas_presentes(app_ctx):
    normas_bd = {e.norma_origen for e in _entradas_resolucion()}
    normas_esperadas = {
        'Art. 132 bis RD 1955/2000 + DA 3ª LSE',
        'Art. 132 ter RD 1955/2000 + DA 3ª LSE',
        'Art. 128 RD 1955/2000',
        'Art. 131.7 RD 1955/2000',
        'Art. 133 RD 1955/2000',
        'Art. 138 RD 1955/2000 (mod. RD 88/2026)',
        'Art. 145.4 RD 1955/2000',
    }
    assert normas_bd == normas_esperadas


def test_cierre_cita_art_138_mod_rd88_2026(app_ctx):
    """Salvaguarda regresión: la cita de CIERRE debe ser 138 (mod), NO 137."""
    citas_cierre = [
        e.norma_origen for e in _entradas_resolucion()
        if e.camino == 'ANY/CIERRE/RESOLUCION'
    ]
    assert citas_cierre, 'No hay entrada de RESOLUCION para CIERRE'
    assert any('138' in c for c in citas_cierre), (
        f'No hay entrada que cite art. 138 para CIERRE: {citas_cierre}'
    )
    assert not any('137' in c and '138' not in c for c in citas_cierre), (
        f'Aún hay cita de art. 137 para CIERRE: {citas_cierre}'
    )


def test_no_existe_resolucion_ae_sin_sufijo_codigo_muerto_del_172(app_ctx):
    """Salvaguarda: el seed 172 incluía 'RESOLUCION_AE' (sin sufijo); ninguna
    entrada debe tener 'AE' pelado en el segmento de siglas."""
    for e in _entradas_resolucion():
        siglas = e.camino.split('/')[1]
        assert siglas != 'AE', (
            f"Entrada {e.id} usa el literal 'AE' sin sufijo "
            f'(código muerto del seed 172): {e.camino}'
        )


# ---------------------------------------------------------------------------
# C) _seleccionar_catalogo devuelve la entrada correcta para cada combinación
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('siglas,esperado', list(_COMBINACIONES_CUBIERTAS.items()))
def test_seleccionar_catalogo_resolucion_para_combinacion_cubierta(app_ctx, siglas, esperado):
    """Sin dict de variables (#785): la combinación sale del camino del elemento."""
    from app.services.plazos import _seleccionar_catalogo
    valor_esp, unidad_esp, norma_esp = esperado
    entrada = _seleccionar_catalogo(_fase_resolucion(siglas), 'FASE', {})
    assert entrada is not None, (
        f'Sin plazo para tipo_solicitud={siglas} — el seed no cubre la combinación'
    )
    assert entrada.plazo_valor == valor_esp
    assert entrada.plazo_unidad == unidad_esp
    assert entrada.norma_origen == norma_esp


# ---------------------------------------------------------------------------
# D) Combinaciones fuera de scope → None (deuda de #247)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('siglas', _FUERA_DE_SCOPE)
def test_seleccionar_catalogo_resolucion_fuera_de_scope(app_ctx, siglas):
    """Plazos no cubiertos por el hotfix 448 (deuda controlada de #247)."""
    from app.services.plazos import _seleccionar_catalogo
    entrada = _seleccionar_catalogo(_fase_resolucion(siglas), 'FASE', {})
    assert entrada is None, (
        f'tipo_solicitud={siglas} no debería tener plazo de RESOLUCION '
        f'todavía (deuda de #247); recibido entrada id={getattr(entrada, "id", "?")}'
    )


# ---------------------------------------------------------------------------
# E) Coherencia con ESF.json — toda combinación válida está cubierta o
#    documentada como fuera de scope
# ---------------------------------------------------------------------------

def test_cobertura_de_combinaciones_es_completa():
    """No requiere BD — solo coherencia conceptual: las claves de los dos
    diccionarios cubren todas las siglas de tipos_solicitudes que tienen
    fase RESOLUCION en su procedimiento."""
    todas = set(_COMBINACIONES_CUBIERTAS) | set(_FUERA_DE_SCOPE)
    # Todas las siglas en BD (ver tipos_solicitudes tras paso6.5):
    siglas_bd = {
        'AAC', 'AAC+DUP', 'AAP', 'AAP+AAC', 'AAP+AAC+DUP',
        'AAT', 'AE_DEFINITIVA', 'AE_DEFINITIVA+AAT', 'AE_PROVISIONAL',
        'AMPLIACION_PLAZO', 'CIERRE', 'CORRECCION_ERRORES',
        'DESISTIMIENTO', 'DUP', 'INTERESADO', 'OTRO',
        'RADNE', 'RAIPEE_DEFINITIVA', 'RAIPEE_PREVIA',
        'RECURSO', 'RENUNCIA',
    }
    faltantes = siglas_bd - todas
    assert not faltantes, (
        f'Combinaciones no clasificadas (cubiertas ni fuera de scope): {faltantes}'
    )
