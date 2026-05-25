"""Tests #463 — seed catalogo_plazos para CONSULTAS.

Patrón: fakes SimpleNamespace que replican las 4 entradas del seed.
Se ejercita _evaluar_condiciones_plazo directamente (lógica pura) y
se simula la selección por orden para verificar prioridad 15 vs 30 días.
Sin BD real ni SQLAlchemy.
"""
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Helpers: fakes que replican el seed
# ---------------------------------------------------------------------------

def _var(nombre):
    return SimpleNamespace(nombre=nombre)


def _cond(nombre_var, operador, valor, orden):
    return SimpleNamespace(variable=_var(nombre_var), operador=operador,
                           valor=valor, orden=orden)


def _plazo(plazo_valor, plazo_unidad, efecto_codigo, orden, condiciones):
    return SimpleNamespace(
        plazo_valor=plazo_valor,
        plazo_unidad=plazo_unidad,
        efecto_codigo=efecto_codigo,
        orden=orden,
        condiciones=condiciones,
        activo=True,
    )


# Réplica exacta del seed de la migración 463
_SEPARATA_PRIO = _plazo(
    15, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA', 10,
    [
        _cond('es_solicitud_aac_pura', 'EQ', True, 1),
        _cond('tiene_solicitud_aap_favorable', 'EQ', True, 2),
    ],
)
_SEPARATA_FALLBACK = _plazo(
    30, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA', 20, [],
)
_TRASLADO_TITULAR = _plazo(
    15, 'DIAS_HABILES', 'SIN_EFECTO_AUTOMATICO', 10, [],
)
_TRASLADO_ORGANISMO = _plazo(
    15, 'DIAS_HABILES', 'CONFORMIDAD_PRESUNTA', 10, [],
)


def _seleccionar(entradas, variables):
    """Replica la lógica de _seleccionar_catalogo sobre una lista en memoria."""
    from app.services.plazos import _evaluar_condiciones_plazo
    for entrada in sorted(entradas, key=lambda e: e.orden):
        if not entrada.condiciones:
            return entrada
        if _evaluar_condiciones_plazo(entrada.condiciones, variables):
            return entrada
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSeedPlazosConsultas:

    # --- CONSULTA_SEPARATA ---

    def test_separata_15_dias_aac_pura_con_aap_favorable(self):
        """Ambas condiciones cumplidas → plazo reducido de 15 días."""
        entrada = _seleccionar(
            [_SEPARATA_PRIO, _SEPARATA_FALLBACK],
            {'es_solicitud_aac_pura': True, 'tiene_solicitud_aap_favorable': True},
        )
        assert entrada is not None
        assert entrada.plazo_valor == 15
        assert entrada.plazo_unidad == 'DIAS_HABILES'
        assert entrada.efecto_codigo == 'CONFORMIDAD_PRESUNTA'

    def test_separata_30_dias_fallback_sin_aac_pura(self):
        """Sin AAC pura → condición prioritaria no cumplida → fallback 30 días."""
        entrada = _seleccionar(
            [_SEPARATA_PRIO, _SEPARATA_FALLBACK],
            {'es_solicitud_aac_pura': False, 'tiene_solicitud_aap_favorable': True},
        )
        assert entrada is not None
        assert entrada.plazo_valor == 30

    def test_separata_30_dias_fallback_sin_aap_favorable(self):
        """AAC pura pero sin AAP favorable → AND incompleto → fallback 30 días."""
        entrada = _seleccionar(
            [_SEPARATA_PRIO, _SEPARATA_FALLBACK],
            {'es_solicitud_aac_pura': True, 'tiene_solicitud_aap_favorable': False},
        )
        assert entrada is not None
        assert entrada.plazo_valor == 30

    def test_separata_30_dias_fallback_ninguna_variable(self):
        """Sin ninguna de las variables → fallback 30 días."""
        entrada = _seleccionar(
            [_SEPARATA_PRIO, _SEPARATA_FALLBACK],
            {'es_solicitud_aac_pura': False, 'tiene_solicitud_aap_favorable': False},
        )
        assert entrada is not None
        assert entrada.plazo_valor == 30

    # --- CONSULTA_TRASLADO_TITULAR ---

    def test_traslado_titular_15_dias_sin_efecto_automatico(self):
        """Traslado al titular → 15 días hábiles, efecto SIN_EFECTO_AUTOMATICO."""
        entrada = _seleccionar([_TRASLADO_TITULAR], {})
        assert entrada is not None
        assert entrada.plazo_valor == 15
        assert entrada.plazo_unidad == 'DIAS_HABILES'
        assert entrada.efecto_codigo == 'SIN_EFECTO_AUTOMATICO'

    # --- CONSULTA_TRASLADO_ORGANISMO ---

    def test_traslado_organismo_15_dias_conformidad_presunta(self):
        """Traslado al organismo → 15 días hábiles, efecto CONFORMIDAD_PRESUNTA."""
        entrada = _seleccionar([_TRASLADO_ORGANISMO], {})
        assert entrada is not None
        assert entrada.plazo_valor == 15
        assert entrada.plazo_unidad == 'DIAS_HABILES'
        assert entrada.efecto_codigo == 'CONFORMIDAD_PRESUNTA'
