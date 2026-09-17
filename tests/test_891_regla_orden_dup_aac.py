"""Tests #891 — RESOLUCION_DUP no se elabora sin AAC previa (ADR-045 §C).

Dos bloques:
  A) Variable `tiene_aac_previa` en aislado (stubs, patrón #341/#918).
  B) Regla de orden DUP→AAC de punta a punta, ancla en `crear_tramite`
     (mismo criterio que la regla de orden AAP→AAC de #918).
"""
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# A) Variable en aislado
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


class _StubTipoFase:
    def __init__(self, codigo):
        self.codigo = codigo


class _StubResultadoFase:
    def __init__(self, codigo):
        self.codigo = codigo


class _StubFase:
    def __init__(self, codigo, *, finalizada=False, resultado_codigo=None, solicitud=None):
        self.tipo_fase = _StubTipoFase(codigo)
        self._finalizada = finalizada
        self.resultado_fase = _StubResultadoFase(resultado_codigo) if resultado_codigo else None
        self.solicitud = solicitud

    @property
    def finalizada(self):
        return self._finalizada


class _StubSolicitud:
    def __init__(self, fases=None, *, contiene_aac=False, expediente=None):
        self.fases = fases or []
        self._contiene_aac = contiene_aac
        self.expediente = expediente

    def contiene_tipo(self, siglas):
        return siglas == 'AAC' and self._contiene_aac


class _StubExpediente:
    def __init__(self, solicitudes=None):
        self.solicitudes = solicitudes or []


class _StubCtxCrearTramite:
    """Contexto de `crear_tramite`: ctx.fase existe, ctx.solicitud es None (#895)."""
    def __init__(self, fase):
        self.fase = fase
        self.solicitud = None


class TestVariableTieneAacPrevia:

    def test_sin_fase_en_contexto_false(self):
        ctx = MagicMock(fase=None)
        assert _get_variable('tiene_aac_previa')(ctx) is False

    def test_aac_favorable_misma_solicitud_true(self):
        aac = _StubFase('RESOLUCION_AAC', finalizada=True, resultado_codigo='FAVORABLE')
        sol = _StubSolicitud(fases=[aac])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol)
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is True

    def test_resolucion_conjunta_favorable_misma_solicitud_true(self):
        """Camino conjunto AAP+AAC (ADR-047 §E): tipo_fase.codigo == 'RESOLUCION'."""
        conjunta = _StubFase('RESOLUCION', finalizada=True, resultado_codigo='FAVORABLE_CONDICIONADO')
        sol = _StubSolicitud(fases=[conjunta])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol)
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is True

    def test_aac_no_finalizada_misma_solicitud_false(self):
        aac = _StubFase('RESOLUCION_AAC', finalizada=False)
        sol = _StubSolicitud(fases=[aac])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol)
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is False

    def test_aac_desfavorable_misma_solicitud_false(self):
        aac = _StubFase('RESOLUCION_AAC', finalizada=True, resultado_codigo='DESFAVORABLE')
        sol = _StubSolicitud(fases=[aac])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol)
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is False

    def test_aac_previa_en_otra_solicitud_true(self):
        """DUP autónoma tras AAC ya resuelta en solicitud anterior del expediente."""
        aac = _StubFase('RESOLUCION_AAC', finalizada=True, resultado_codigo='FAVORABLE')
        sol_aac = _StubSolicitud(fases=[aac], contiene_aac=True)
        sol_dup = _StubSolicitud(fases=[])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol_dup)
        sol_dup.expediente = _StubExpediente(solicitudes=[sol_aac, sol_dup])
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is True

    def test_otra_solicitud_sin_aac_en_su_tipo_false(self):
        sol_otra = _StubSolicitud(fases=[], contiene_aac=False)
        sol_dup = _StubSolicitud(fases=[])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol_dup)
        sol_dup.expediente = _StubExpediente(solicitudes=[sol_otra, sol_dup])
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is False

    def test_sin_aac_en_absoluto_false(self):
        sol = _StubSolicitud(fases=[])
        dup = _StubFase('RESOLUCION_DUP', solicitud=sol)
        assert _get_variable('tiene_aac_previa')(_StubCtxCrearTramite(dup)) is False


# ---------------------------------------------------------------------------
# Helpers de integración (patrón #895/#918)
# ---------------------------------------------------------------------------

def _tipo_tramite(codigo):
    from app.models.tipos_tramites import TipoTramite
    tipo = TipoTramite.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el TipoTramite {codigo}'
    return tipo


def _solicitud_de_tipo(arbol, siglas, *, expediente_id=None):
    from app.models.solicitudes import Solicitud
    from app.models.tipos_solicitudes import TipoSolicitud
    from tests.conftest import documento_ancla_de_prueba
    from app.models.expedientes import Expediente
    from app.models.entidad import Entidad
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el TipoSolicitud {siglas}'
    if expediente_id is None:
        exp = Expediente.query.first()
        assert exp is not None, 'la semilla debe traer un Expediente'
        expediente_id = exp.id
    ent = Entidad.query.first()
    assert ent is not None, 'la semilla debe traer una Entidad'
    sol = Solicitud(
        expediente_id=expediente_id, entidad_id=ent.id, tipo_solicitud_id=tipo.id,
        documento_solicitud_id=documento_ancla_de_prueba(expediente_id).id)
    arbol.db.session.add(sol)
    arbol.db.session.flush()
    return sol


def _finalizar_favorable(arbol, fase):
    from app.models.tipos_resultados_fases import TipoResultadoFase
    favorable = TipoResultadoFase.query.filter_by(codigo='FAVORABLE').first()
    assert favorable is not None, 'la semilla debe traer TipoResultadoFase FAVORABLE'
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'891-resultado-{fase.id}')
    fase.resultado_fase_id = favorable.id
    fase.documento_resultado_id = doc.id
    arbol.db.session.flush()


def _reglas_disparadas_tramite(fase, tipo_tramite, *, contiene):
    from app.services.assembler import auditar_multi
    resultado = auditar_multi('CREAR', fase.solicitud.expediente,
                              {'fase': fase, 'tipo_tramite': tipo_tramite})
    return [r for r in resultado.reglas_evaluadas
            if contiene in (r.descripcion or '') and r.disparada]


# ---------------------------------------------------------------------------
# B) Regla de orden DUP→AAC (ADR-045 §C)
# ---------------------------------------------------------------------------

class TestReglaDeOrden:

    def test_dup_autonoma_sin_aac_previa_bloquea(self, app_ctx, arbol_esftt):
        sol = _solicitud_de_tipo(arbol_esftt, 'DUP')
        dup = arbol_esftt.fase('RESOLUCION_DUP', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(
            dup, _tipo_tramite('ELABORACION'), contiene='proyecto de ejecución')

        assert len(disparadas) == 1
        assert disparadas[0].efecto == 'BLOQUEAR'

    def test_dup_autonoma_con_aac_previa_en_solicitud_anterior_permite(self, app_ctx, arbol_esftt):
        sol_aac = _solicitud_de_tipo(arbol_esftt, 'AAC')
        aac = arbol_esftt.fase('RESOLUCION', solicitud=sol_aac)
        _finalizar_favorable(arbol_esftt, aac)

        sol_dup = _solicitud_de_tipo(arbol_esftt, 'DUP', expediente_id=sol_aac.expediente_id)
        dup = arbol_esftt.fase('RESOLUCION_DUP', solicitud=sol_dup)

        disparadas = _reglas_disparadas_tramite(
            dup, _tipo_tramite('ELABORACION'), contiene='proyecto de ejecución')

        assert not disparadas

    def test_aap_aac_dup_con_resolucion_conjunta_favorable_permite(self, app_ctx, arbol_esftt):
        sol = _solicitud_de_tipo(arbol_esftt, 'AAP+AAC+DUP')
        conjunta = arbol_esftt.fase('RESOLUCION', solicitud=sol)
        _finalizar_favorable(arbol_esftt, conjunta)
        dup = arbol_esftt.fase('RESOLUCION_DUP', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(
            dup, _tipo_tramite('ELABORACION'), contiene='proyecto de ejecución')

        assert not disparadas

    def test_aac_dup_con_aap_previa_en_solicitud_anterior_permite(self, app_ctx, arbol_esftt):
        """AAP resuelta en solicitud anterior; esta solicitud AAC+DUP resuelve la
        AAC (fase RESOLUCION, no RESOLUCION_AAC — esta solicitud no incluye AAP)."""
        sol_aap = _solicitud_de_tipo(arbol_esftt, 'AAP')
        aap = arbol_esftt.fase('RESOLUCION', solicitud=sol_aap)
        _finalizar_favorable(arbol_esftt, aap)

        sol_aac_dup = _solicitud_de_tipo(arbol_esftt, 'AAC+DUP', expediente_id=sol_aap.expediente_id)
        aac = arbol_esftt.fase('RESOLUCION', solicitud=sol_aac_dup)
        _finalizar_favorable(arbol_esftt, aac)
        dup = arbol_esftt.fase('RESOLUCION_DUP', solicitud=sol_aac_dup)

        disparadas = _reglas_disparadas_tramite(
            dup, _tipo_tramite('ELABORACION'), contiene='proyecto de ejecución')

        assert not disparadas

    def test_aac_partida_favorable_misma_solicitud_permite(self, app_ctx, arbol_esftt):
        """Proyecto de ejecución aprobado por el camino partido (ADR-047 §E):
        fase hermana RESOLUCION_AAC, no RESOLUCION conjunta."""
        sol = _solicitud_de_tipo(arbol_esftt, 'AAP+AAC+DUP')
        aap = arbol_esftt.fase('RESOLUCION_AAP', solicitud=sol)
        _finalizar_favorable(arbol_esftt, aap)
        aac = arbol_esftt.fase('RESOLUCION_AAC', solicitud=sol)
        _finalizar_favorable(arbol_esftt, aac)
        dup = arbol_esftt.fase('RESOLUCION_DUP', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(
            dup, _tipo_tramite('ELABORACION'), contiene='proyecto de ejecución')

        assert not disparadas
