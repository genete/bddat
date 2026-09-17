"""Tests #918 — RESOLUCION_AAP/RESOLUCION_AAC como acto partido (ADR-047).

Tres bloques:
  A) Variables `existe_resolucion_conjunta`/`existe_resolucion_partida`/
     `tiene_aap_favorable_misma_solicitud` en aislado (stubs, patrón #341).
  B) Exclusión mutua RESOLUCION vs. RESOLUCION_AAP/RESOLUCION_AAC de punta a
     punta (ADR-047 §B), patrón `auditar_multi` de #895.
  C) Regla de orden AAP→AAC de punta a punta (ADR-047 §F), ancla en
     `crear_tramite` (no en la tarea ELABORAR — ver calculado.py).

El 4º escenario que pide el issue #918 (`tiene_aac_previa` detectando
RESOLUCION_AAC partida) depende de #891, todavía bloqueado por este mismo
issue — no es testable aquí.
"""
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# A) Variables en aislado
# ---------------------------------------------------------------------------

def _get_variable(nombre: str):
    import app.services.variables.calculado  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no encontrada en _REGISTRY'
    return fn


class _StubTipoFase:
    def __init__(self, codigo, es_finalizadora=True):
        self.codigo = codigo
        self.es_finalizadora = es_finalizadora


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
    def __init__(self, fases=None):
        self.fases = fases or []


class _StubCtxCrearFase:
    """Contexto de `crear_fase`: dict {'solicitud','tipo_fase'} — ctx.fase es None."""
    def __init__(self, solicitud):
        self.solicitud = solicitud
        self.fase = None


class _StubCtxCrearTramite:
    """Contexto de `crear_tramite`: ctx.fase existe, ctx.solicitud es None (#895)."""
    def __init__(self, fase):
        self.fase = fase
        self.solicitud = None


class TestVariableExisteResolucionConjunta:

    def test_sin_fases_false(self):
        sol = _StubSolicitud(fases=[])
        assert _get_variable('existe_resolucion_conjunta')(_StubCtxCrearFase(sol)) is False

    def test_con_resolucion_true(self):
        sol = _StubSolicitud(fases=[_StubFase('RESOLUCION')])
        assert _get_variable('existe_resolucion_conjunta')(_StubCtxCrearFase(sol)) is True

    def test_con_solo_partida_false(self):
        sol = _StubSolicitud(fases=[_StubFase('RESOLUCION_AAP')])
        assert _get_variable('existe_resolucion_conjunta')(_StubCtxCrearFase(sol)) is False

    def test_no_dispara_con_fase_existente_en_contexto(self):
        fase = _StubFase('ELABORACION')
        assert _get_variable('existe_resolucion_conjunta')(_StubCtxCrearTramite(fase)) is False


class TestVariableExisteResolucionPartida:

    def test_sin_fases_false(self):
        sol = _StubSolicitud(fases=[])
        assert _get_variable('existe_resolucion_partida')(_StubCtxCrearFase(sol)) is False

    def test_con_aap_true(self):
        sol = _StubSolicitud(fases=[_StubFase('RESOLUCION_AAP')])
        assert _get_variable('existe_resolucion_partida')(_StubCtxCrearFase(sol)) is True

    def test_con_aac_true(self):
        sol = _StubSolicitud(fases=[_StubFase('RESOLUCION_AAC')])
        assert _get_variable('existe_resolucion_partida')(_StubCtxCrearFase(sol)) is True

    def test_con_solo_conjunta_false(self):
        sol = _StubSolicitud(fases=[_StubFase('RESOLUCION')])
        assert _get_variable('existe_resolucion_partida')(_StubCtxCrearFase(sol)) is False


class TestVariableTieneAapFavorableMismaSolicitud:

    def test_sin_fase_en_contexto_false(self):
        ctx = MagicMock(fase=None)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(ctx) is False

    def test_aap_favorable_true(self):
        aap = _StubFase('RESOLUCION_AAP', finalizada=True, resultado_codigo='FAVORABLE')
        sol = _StubSolicitud(fases=[aap])
        aap.solicitud = sol
        aac = _StubFase('RESOLUCION_AAC', solicitud=sol)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(
            _StubCtxCrearTramite(aac)) is True

    def test_aap_favorable_condicionado_true(self):
        aap = _StubFase('RESOLUCION_AAP', finalizada=True, resultado_codigo='FAVORABLE_CONDICIONADO')
        sol = _StubSolicitud(fases=[aap])
        aac = _StubFase('RESOLUCION_AAC', solicitud=sol)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(
            _StubCtxCrearTramite(aac)) is True

    def test_aap_no_finalizada_false(self):
        aap = _StubFase('RESOLUCION_AAP', finalizada=False)
        sol = _StubSolicitud(fases=[aap])
        aac = _StubFase('RESOLUCION_AAC', solicitud=sol)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(
            _StubCtxCrearTramite(aac)) is False

    def test_aap_desfavorable_false(self):
        aap = _StubFase('RESOLUCION_AAP', finalizada=True, resultado_codigo='DESFAVORABLE')
        sol = _StubSolicitud(fases=[aap])
        aac = _StubFase('RESOLUCION_AAC', solicitud=sol)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(
            _StubCtxCrearTramite(aac)) is False

    def test_sin_aap_en_absoluto_false(self):
        sol = _StubSolicitud(fases=[])
        aac = _StubFase('RESOLUCION_AAC', solicitud=sol)
        assert _get_variable('tiene_aap_favorable_misma_solicitud')(
            _StubCtxCrearTramite(aac)) is False


# ---------------------------------------------------------------------------
# Helpers de integración (patrón #895)
# ---------------------------------------------------------------------------

def _tipo_fase(codigo):
    from app.models.tipos_fases import TipoFase
    tipo = TipoFase.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el TipoFase {codigo}'
    return tipo


def _tipo_tramite(codigo):
    from app.models.tipos_tramites import TipoTramite
    tipo = TipoTramite.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el TipoTramite {codigo}'
    return tipo


def _solicitud_aap_aac(arbol):
    from app import db
    from app.models.tipos_solicitudes import TipoSolicitud
    sol = arbol.solicitud_nueva()
    tipo = TipoSolicitud.query.filter_by(siglas='AAP+AAC').first()
    assert tipo is not None, 'la semilla debe traer el TipoSolicitud AAP+AAC'
    sol.tipo_solicitud_id = tipo.id
    db.session.flush()
    return sol


def _finalizar_favorable(arbol, fase):
    from app import db
    from app.models.tipos_resultados_fases import TipoResultadoFase
    favorable = TipoResultadoFase.query.filter_by(codigo='FAVORABLE').first()
    assert favorable is not None, 'la semilla debe traer TipoResultadoFase FAVORABLE'
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'918-resultado-{fase.id}')
    fase.resultado_fase_id = favorable.id
    fase.documento_resultado_id = doc.id
    db.session.flush()


def _reglas_disparadas(solicitud, tipo_fase, *, contiene):
    """AAP+AAC es combinada: `auditar_multi` evalúa una vez por tipo simple
    (AAP, AAC) y acumula — nuestras reglas usan sujeto 'ANY' en ese segmento
    a propósito, así que disparan igual en las dos vueltas. Dedupe por
    `regla_id`, no es una duplicación real de la regla."""
    from app.services.assembler import auditar_multi
    resultado = auditar_multi('CREAR', solicitud.expediente,
                              {'solicitud': solicitud, 'tipo_fase': tipo_fase})
    vistas = {}
    for r in resultado.reglas_evaluadas:
        if contiene in (r.descripcion or '') and r.disparada:
            vistas[r.regla_id] = r
    return list(vistas.values())


def _reglas_disparadas_tramite(fase, tipo_tramite, *, contiene):
    from app.services.assembler import auditar_multi
    resultado = auditar_multi('CREAR', fase.solicitud.expediente,
                              {'fase': fase, 'tipo_tramite': tipo_tramite})
    return [r for r in resultado.reglas_evaluadas
            if contiene in (r.descripcion or '') and r.disparada]


# ---------------------------------------------------------------------------
# B) Exclusión mutua RESOLUCION vs. RESOLUCION_AAP/RESOLUCION_AAC (ADR-047 §B)
# ---------------------------------------------------------------------------

class TestExclusionMutua:

    def test_conjunta_sin_fases_previas_no_bloquea(self, app_ctx, arbol_esftt):
        """Sin elección previa, crear RESOLUCION no cambia de comportamiento."""
        sol = _solicitud_aap_aac(arbol_esftt)

        disparadas = _reglas_disparadas(sol, _tipo_fase('RESOLUCION'),
                                        contiene='resolución partida')

        assert not disparadas

    def test_conjunta_existente_bloquea_crear_aap(self, app_ctx, arbol_esftt):
        sol = _solicitud_aap_aac(arbol_esftt)
        arbol_esftt.fase('RESOLUCION', solicitud=sol)

        disparadas = _reglas_disparadas(sol, _tipo_fase('RESOLUCION_AAP'),
                                        contiene='RESOLUCION conjunta')

        assert len(disparadas) == 1
        assert disparadas[0].efecto == 'BLOQUEAR'

    def test_conjunta_existente_bloquea_crear_aac(self, app_ctx, arbol_esftt):
        sol = _solicitud_aap_aac(arbol_esftt)
        arbol_esftt.fase('RESOLUCION', solicitud=sol)

        disparadas = _reglas_disparadas(sol, _tipo_fase('RESOLUCION_AAC'),
                                        contiene='RESOLUCION conjunta')

        assert len(disparadas) == 1

    def test_partida_existente_bloquea_crear_conjunta(self, app_ctx, arbol_esftt):
        sol = _solicitud_aap_aac(arbol_esftt)
        arbol_esftt.fase('RESOLUCION_AAP', solicitud=sol)

        disparadas = _reglas_disparadas(sol, _tipo_fase('RESOLUCION'),
                                        contiene='resolución partida')

        assert len(disparadas) == 1
        assert disparadas[0].efecto == 'BLOQUEAR'

    def test_partida_con_solo_aac_tambien_bloquea_conjunta(self, app_ctx, arbol_esftt):
        """No hace falta que estén las dos mitades: una sola ya elige el camino."""
        sol = _solicitud_aap_aac(arbol_esftt)
        arbol_esftt.fase('RESOLUCION_AAC', solicitud=sol)

        disparadas = _reglas_disparadas(sol, _tipo_fase('RESOLUCION'),
                                        contiene='resolución partida')

        assert len(disparadas) == 1


# ---------------------------------------------------------------------------
# C) Regla de orden AAP→AAC (ADR-047 §F)
# ---------------------------------------------------------------------------

class TestReglaDeOrden:

    def test_aac_sin_aap_bloquea_elaboracion(self, app_ctx, arbol_esftt):
        """AAP+AAC resuelta partida sin AAP favorable: bloquea abrir ELABORACION de AAC."""
        sol = _solicitud_aap_aac(arbol_esftt)
        arbol_esftt.fase('RESOLUCION_AAP', solicitud=sol)   # sin finalizar
        aac = arbol_esftt.fase('RESOLUCION_AAC', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(aac, _tipo_tramite('ELABORACION'),
                                                contiene='no consta finalizada')

        assert len(disparadas) == 1
        assert disparadas[0].efecto == 'BLOQUEAR'

    def test_aac_con_aap_favorable_permite_elaboracion(self, app_ctx, arbol_esftt):
        """AAP+AAC resuelta partida, AAP favorable: permite abrir ELABORACION de AAC."""
        sol = _solicitud_aap_aac(arbol_esftt)
        aap = arbol_esftt.fase('RESOLUCION_AAP', solicitud=sol)
        _finalizar_favorable(arbol_esftt, aap)
        aac = arbol_esftt.fase('RESOLUCION_AAC', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(aac, _tipo_tramite('ELABORACION'),
                                                contiene='no consta finalizada')

        assert not disparadas

    def test_no_dispara_sobre_resolucion_conjunta(self, app_ctx, arbol_esftt):
        """La regla de orden solo aplica a RESOLUCION_AAC — RESOLUCION conjunta no
        tiene AAP/AAC que ordenar entre sí (ADR-047 §F, 'no aplica')."""
        sol = _solicitud_aap_aac(arbol_esftt)
        conjunta = arbol_esftt.fase('RESOLUCION', solicitud=sol)

        disparadas = _reglas_disparadas_tramite(conjunta, _tipo_tramite('ELABORACION'),
                                                contiene='no consta finalizada')

        assert not disparadas
