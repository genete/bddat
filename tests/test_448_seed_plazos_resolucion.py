"""Tests issue #448 — seed catalogo_plazos para fase RESOLUCION.

Verifica el resultado de la migración `448_seed_plazos_resolucion`:
  A) Variable tipo_solicitud activa en catalogo_variables.
  B) 7 entradas en catalogo_plazos con tipo_elemento_codigo='RESOLUCION',
     cada una con su norma_origen y la condición IN sobre tipo_solicitud.
  C) Para cada combinación de tipo_solicitud cubierta por el seed,
     _seleccionar_catalogo devuelve exactamente la entrada correcta.
  D) Para combinaciones fuera de scope (RAIPEE_*, RADNE, DESISTIMIENTO, …),
     _seleccionar_catalogo devuelve None.

Requieren BD con migración 448 aplicada y fixture app_ctx (conftest.py).
"""
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


# ---------------------------------------------------------------------------
# A) Variable tipo_solicitud
# ---------------------------------------------------------------------------

def test_variable_tipo_solicitud_existe_y_esta_activa(app_ctx):
    from app.models.motor_reglas import CatalogoVariable
    var = CatalogoVariable.query.filter_by(nombre='tipo_solicitud').first()
    assert var is not None, 'Variable tipo_solicitud no existe en catalogo_variables'
    assert var.activa is True
    assert var.tipo_dato == 'texto'


# ---------------------------------------------------------------------------
# B) Las 7 entradas del seed están presentes con sus normas
# ---------------------------------------------------------------------------

def test_hay_exactamente_7_entradas_resolucion(app_ctx):
    from app.models.catalogo_plazos import CatalogoPlazo
    entradas = (
        CatalogoPlazo.query
        .filter_by(tipo_elemento='FASE', tipo_elemento_codigo='RESOLUCION', activo=True)
        .all()
    )
    assert len(entradas) == 7, (
        f'Esperadas 7 entradas RESOLUCION, hay {len(entradas)}: '
        f'{[e.norma_origen for e in entradas]}'
    )


def test_cada_entrada_tiene_efecto_silencio_desestimatorio(app_ctx):
    from app.models.catalogo_plazos import CatalogoPlazo
    entradas = (
        CatalogoPlazo.query
        .filter_by(tipo_elemento='FASE', tipo_elemento_codigo='RESOLUCION', activo=True)
        .all()
    )
    for e in entradas:
        assert e.efecto_plazo.codigo == 'SILENCIO_DESESTIMATORIO', (
            f'Entrada {e.id} ({e.norma_origen}) tiene efecto inesperado '
            f'{e.efecto_plazo.codigo}'
        )


def test_normas_origen_esperadas_presentes(app_ctx):
    from app.models.catalogo_plazos import CatalogoPlazo
    normas_bd = {
        e.norma_origen
        for e in CatalogoPlazo.query
        .filter_by(tipo_elemento='FASE', tipo_elemento_codigo='RESOLUCION', activo=True)
        .all()
    }
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
    from app.models.catalogo_plazos import CatalogoPlazo
    entradas = CatalogoPlazo.query.filter_by(
        tipo_elemento='FASE', tipo_elemento_codigo='RESOLUCION', activo=True
    ).all()
    citas_cierre = [e.norma_origen for e in entradas if 'CIERRE' in str(e.condiciones[0].valor) if e.condiciones]
    assert any('138' in c for c in citas_cierre), (
        f'No hay entrada que cite art. 138 para CIERRE: {citas_cierre}'
    )
    assert not any('137' in c and '138' not in c for c in citas_cierre), (
        f'Aún hay cita de art. 137 para CIERRE: {citas_cierre}'
    )


def test_no_existe_resolucion_ae_sin_sufijo_codigo_muerto_del_172(app_ctx):
    """Salvaguarda: el seed 172 incluía 'RESOLUCION_AE' (sin sufijo); no debe
    haber ninguna condición IN que contenga el literal 'AE' sin sufijo."""
    from app.models.condiciones_plazo import CondicionPlazo
    from app.models.catalogo_plazos import CatalogoPlazo
    conds = (
        CondicionPlazo.query
        .join(CatalogoPlazo, CondicionPlazo.catalogo_plazo_id == CatalogoPlazo.id)
        .filter(CatalogoPlazo.tipo_elemento_codigo == 'RESOLUCION')
        .all()
    )
    for c in conds:
        valor = c.valor if isinstance(c.valor, list) else [c.valor]
        assert 'AE' not in valor, (
            f"Condición {c.id} incluye literal 'AE' sin sufijo "
            f"(código muerto del seed 172): {valor}"
        )


# ---------------------------------------------------------------------------
# C) _seleccionar_catalogo devuelve la entrada correcta para cada combinación
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('siglas,esperado', list(_COMBINACIONES_CUBIERTAS.items()))
def test_seleccionar_catalogo_resolucion_para_combinacion_cubierta(app_ctx, siglas, esperado):
    from app.services.plazos import _seleccionar_catalogo
    valor_esp, unidad_esp, norma_esp = esperado
    entrada = _seleccionar_catalogo(
        'FASE', 'RESOLUCION', {'tipo_solicitud': siglas}
    )
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
    entrada = _seleccionar_catalogo(
        'FASE', 'RESOLUCION', {'tipo_solicitud': siglas}
    )
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
