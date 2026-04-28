"""
Tests issue #296 — señal de resultado en Tarea y Trámite.

Bloques:
  A) Tarea.resultado / Tarea.estado        — stubs, sin BD ni app context.
  B) Tramite.finalizado / Tramite.estado   — stubs, sin BD ni app context.
  C) Fase.estado / Solicitud.estado        — stubs, sin BD ni app context.
  D) Invariantes _check_finalizar_tramite y _check_finalizar_fase
     con NOTIFICAR INCORRECTA             — app context + mock de db.session.
"""
import pytest
from unittest.mock import MagicMock, patch


# ───────────────────────────────────────────────────────────────────────────────
# Helpers de construcción de stubs
# ───────────────────────────────────────────────────────────────────────────────

def _tipo_tarea(codigo):
    return MagicMock(codigo=codigo)


def _resultado_doc(efecto):
    """Stub de ResultadoDocumento con efecto_tarea dado."""
    rd = MagicMock()
    rd.tipo_resultado = MagicMock(efecto_tarea=efecto)
    return rd


def _doc_producido(efecto=None):
    """Stub de Documento con resultado_doc opcional."""
    doc = MagicMock()
    doc.resultado_doc = _resultado_doc(efecto) if efecto else None
    return doc


class _StubTarea:
    """Stub de Tarea con atributos mínimos para las properties.

    Expone `planificada` y `ejecutada` delegando al fget del modelo,
    de forma que `Tarea.estado.fget(stub)` funciona sin instanciar SQLAlchemy.
    """
    def __init__(self, codigo, doc_producido=None, doc_producido_id=None,
                 doc_usado_id=None, documentos_tarea=None):
        self.tipo_tarea = _tipo_tarea(codigo)
        self.documento_producido = doc_producido
        self.documento_producido_id = doc_producido_id
        self.documento_usado_id = doc_usado_id
        self.documentos_tarea = documentos_tarea or []

    @property
    def planificada(self):
        from app.models.tareas import Tarea
        return Tarea.planificada.fget(self)

    @property
    def ejecutada(self):
        from app.models.tareas import Tarea
        return Tarea.ejecutada.fget(self)


class _StubTramite:
    """Stub de Tramite.

    Expone `planificado` y `finalizado` delegando al fget del modelo.
    Las tareas deben tener `resultado` como atributo directo.
    """
    def __init__(self, tareas=None):
        self.tareas = tareas or []

    @property
    def planificado(self):
        from app.models.tramites import Tramite
        return Tramite.planificado.fget(self)

    @property
    def finalizado(self):
        from app.models.tramites import Tramite
        return Tramite.finalizado.fget(self)


class _StubFase:
    """Stub de Fase.

    Expone `finalizada`, `planificada` y `pdte_cierre` delegando al fget del modelo.
    Los tramites deben tener `finalizado` como atributo directo (MagicMock basta).
    """
    def __init__(self, tramites=None, documento_resultado_id=None):
        self.tramites = tramites or []
        self.documento_resultado_id = documento_resultado_id

    @property
    def finalizada(self):
        from app.models.fases import Fase
        return Fase.finalizada.fget(self)

    @property
    def planificada(self):
        from app.models.fases import Fase
        return Fase.planificada.fget(self)

    @property
    def pdte_cierre(self):
        from app.models.fases import Fase
        return Fase.pdte_cierre.fget(self)


class _StubTareaConResultado(_StubTarea):
    """Extiende _StubTarea con un atributo `resultado` explícito.

    Tramite.finalizado llama t.resultado; en stubs lo exponemos como atributo
    directo para controlar el valor sin necesidad de ResultadoDocumento en BD.
    """
    def __init__(self, codigo, doc_producido_id=None, resultado='INDIFERENTE'):
        super().__init__(codigo, doc_producido_id=doc_producido_id)
        self._resultado_override = resultado

    @property
    def resultado(self):
        return self._resultado_override


# ───────────────────────────────────────────────────────────────────────────────
# A) Tarea.resultado y Tarea.estado
# ───────────────────────────────────────────────────────────────────────────────

def _tarea_resultado(stub):
    from app.models.tareas import Tarea
    return Tarea.resultado.fget(stub)


def _tarea_estado(stub):
    from app.models.tareas import Tarea
    return Tarea.estado.fget(stub)


class TestTareaResultado:

    def test_sin_doc_producido_es_indiferente(self):
        t = _StubTarea('NOTIFICAR', doc_producido=None)
        assert _tarea_resultado(t) == 'INDIFERENTE'

    def test_doc_sin_resultado_doc_es_indiferente(self):
        t = _StubTarea('NOTIFICAR', doc_producido=_doc_producido(efecto=None))
        assert _tarea_resultado(t) == 'INDIFERENTE'

    def test_doc_con_resultado_incorrecta(self):
        t = _StubTarea('NOTIFICAR', doc_producido=_doc_producido('INCORRECTA'))
        assert _tarea_resultado(t) == 'INCORRECTA'

    def test_doc_con_resultado_correcta(self):
        t = _StubTarea('NOTIFICAR', doc_producido=_doc_producido('CORRECTA'))
        assert _tarea_resultado(t) == 'CORRECTA'

    def test_analisis_siempre_indiferente(self):
        # ANALISIS no puede tener resultado != INDIFERENTE por diseño
        t = _StubTarea('ANALISIS', doc_producido=_doc_producido(efecto=None))
        assert _tarea_resultado(t) == 'INDIFERENTE'


class TestTareaEstado:

    def test_planificada_devuelve_planificada(self):
        t = _StubTarea('ANALISIS', doc_producido_id=None, doc_usado_id=None)
        assert _tarea_estado(t) == 'PLANIFICADA'

    def test_ejecutada_devuelve_ejecutada(self):
        t = _StubTarea('ANALISIS', doc_producido_id=5)
        assert _tarea_estado(t) == 'EJECUTADA'

    def test_en_curso_devuelve_en_curso(self):
        t = _StubTarea('ANALISIS', doc_producido_id=None, doc_usado_id=3)
        assert _tarea_estado(t) == 'EN_CURSO'

    def test_incorporar_sin_docs_planificada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _tarea_estado(t) == 'PLANIFICADA'

    def test_incorporar_con_docs_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _tarea_estado(t) == 'EJECUTADA'


# ───────────────────────────────────────────────────────────────────────────────
# B) Tramite.finalizado (actualizado) y Tramite.estado
# ───────────────────────────────────────────────────────────────────────────────

def _tramite_finalizado(stub):
    from app.models.tramites import Tramite
    return Tramite.finalizado.fget(stub)


def _tramite_estado(stub):
    from app.models.tramites import Tramite
    return Tramite.estado.fget(stub)


class TestTramiteFinalizadoConResultado:

    def test_sin_tareas_finalizado(self):
        tr = _StubTramite(tareas=[])
        assert _tramite_finalizado(tr) is True

    def test_notificar_doc_producido_indiferente_finalizado(self):
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='INDIFERENTE')
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is True

    def test_notificar_doc_producido_correcta_finalizado(self):
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='CORRECTA')
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is True

    def test_notificar_sin_doc_producido_no_finalizado(self):
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=None)
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is False

    def test_notificar_doc_producido_incorrecta_no_finalizado(self):
        """Clave de #296: NOTIFICAR con INCORRECTA bloquea aunque haya doc_producido."""
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='INCORRECTA')
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is False

    def test_mix_correcta_e_incorrecta_no_finalizado(self):
        t1 = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='CORRECTA')
        t2 = _StubTareaConResultado('NOTIFICAR', doc_producido_id=11, resultado='INCORRECTA')
        tr = _StubTramite(tareas=[t1, t2])
        assert _tramite_finalizado(tr) is False

    def test_analisis_sin_doc_no_finalizado(self):
        t = _StubTareaConResultado('ANALISIS', doc_producido_id=None)
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is False

    def test_esperar_plazo_no_bloquea(self):
        """ESPERAR_PLAZO no forma parte de _requieren — no impide finalizar."""
        t = _StubTareaConResultado('ESPERAR_PLAZO', doc_producido_id=None)
        tr = _StubTramite(tareas=[t])
        assert _tramite_finalizado(tr) is True


class TestTramiteEstado:

    def test_sin_tareas_planificado(self):
        tr = _StubTramite(tareas=[])
        assert _tramite_estado(tr) == 'PLANIFICADO'

    def test_notificar_incorrecta_en_curso(self):
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='INCORRECTA')
        tr = _StubTramite(tareas=[t])
        assert _tramite_estado(tr) == 'EN_CURSO'

    def test_todas_correctas_finalizado(self):
        t = _StubTareaConResultado('NOTIFICAR', doc_producido_id=10, resultado='CORRECTA')
        tr = _StubTramite(tareas=[t])
        assert _tramite_estado(tr) == 'FINALIZADO'


# ───────────────────────────────────────────────────────────────────────────────
# C) Fase.estado y Solicitud.estado
# ───────────────────────────────────────────────────────────────────────────────

def _fase_estado(stub):
    from app.models.fases import Fase
    return Fase.estado.fget(stub)


def _solicitud_estado(stub):
    from app.models.solicitudes import Solicitud
    return Solicitud.estado.fget(stub)


class TestFaseEstado:

    def _tramite_finalizado_stub(self, finalizado=True):
        t = MagicMock()
        t.finalizado = finalizado
        return t

    def test_sin_tramites_planificada(self):
        f = _StubFase(tramites=[], documento_resultado_id=None)
        assert _fase_estado(f) == 'PLANIFICADA'

    def test_doc_resultado_finalizada(self):
        tr = self._tramite_finalizado_stub()
        f = _StubFase(tramites=[tr], documento_resultado_id=99)
        assert _fase_estado(f) == 'FINALIZADA'

    def test_tramites_finalizados_sin_doc_resultado_pdte_cierre(self):
        tr = self._tramite_finalizado_stub(finalizado=True)
        f = _StubFase(tramites=[tr], documento_resultado_id=None)
        assert _fase_estado(f) == 'PDTE_CIERRE'

    def test_tramites_sin_finalizar_en_curso(self):
        tr = self._tramite_finalizado_stub(finalizado=False)
        f = _StubFase(tramites=[tr], documento_resultado_id=None)
        assert _fase_estado(f) == 'EN_CURSO'


class TestSolicitudEstado:

    def _fase_stub(self, finalizada, es_finalizadora=False, codigo_resultado=None):
        f = MagicMock()
        f.finalizada = finalizada
        f.tipo_fase = MagicMock(es_finalizadora=es_finalizadora)
        if codigo_resultado:
            f.resultado_fase = MagicMock(codigo=codigo_resultado)
        else:
            f.resultado_fase = None
        return f

    def test_sin_fases_en_tramite(self):
        s = MagicMock()
        s.fases = []
        assert _solicitud_estado(s) == 'EN_TRAMITE'

    def test_fases_no_finalizadas_en_tramite(self):
        s = MagicMock()
        s.fases = [self._fase_stub(finalizada=False)]
        assert _solicitud_estado(s) == 'EN_TRAMITE'

    def test_todas_finalizadas_sin_finalizadora_resuelta(self):
        s = MagicMock()
        s.fases = [self._fase_stub(finalizada=True, es_finalizadora=False)]
        assert _solicitud_estado(s) == 'RESUELTA'

    def test_finalizadora_favorable_resuelta_favorable(self):
        s = MagicMock()
        s.fases = [
            self._fase_stub(finalizada=True, es_finalizadora=False),
            self._fase_stub(finalizada=True, es_finalizadora=True, codigo_resultado='FAVORABLE'),
        ]
        assert _solicitud_estado(s) == 'RESUELTA_FAVORABLE'

    def test_finalizadora_desfavorable(self):
        s = MagicMock()
        s.fases = [
            self._fase_stub(finalizada=True, es_finalizadora=True, codigo_resultado='DESFAVORABLE'),
        ]
        assert _solicitud_estado(s) == 'RESUELTA_DESFAVORABLE'

    def test_finalizadora_sin_resultado_resuelta(self):
        s = MagicMock()
        s.fases = [
            self._fase_stub(finalizada=True, es_finalizadora=True, codigo_resultado=None),
        ]
        assert _solicitud_estado(s) == 'RESUELTA'

    def test_mezcla_fases_una_sin_finalizar_en_tramite(self):
        s = MagicMock()
        s.fases = [
            self._fase_stub(finalizada=True),
            self._fase_stub(finalizada=False),
        ]
        assert _solicitud_estado(s) == 'EN_TRAMITE'


# ───────────────────────────────────────────────────────────────────────────────
# D) Invariantes — app context + mock de db.session
# ───────────────────────────────────────────────────────────────────────────────

def _make_query_chain(first_returns):
    """Devuelve un mock de db.session.query() cuyo .first() responde
    secuencialmente con los valores de `first_returns`."""
    q = MagicMock()
    q.join.return_value = q
    q.outerjoin.return_value = q
    q.filter.return_value = q
    q.first.side_effect = list(first_returns)
    return q


class TestCheckFinalizarTramiteNotificar:

    def test_notificar_incorrecta_bloquea(self, app):
        """La tercera query encuentra una NOTIFICAR INCORRECTA → bloquea."""
        from app.services.invariantes_esftt import _check_finalizar_tramite as fn
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                q = _make_query_chain([None, None, MagicMock()])
                mock_db.session.query.return_value = q
                resultado = fn(tramite_id=99)
        assert resultado is not None
        assert resultado.permitido is False
        assert 'notificaci' in resultado.norma_compilada.lower()

    def test_sin_notificar_incorrecta_no_bloquea(self, app):
        """Las tres queries devuelven None → sin bloqueo."""
        from app.services.invariantes_esftt import _check_finalizar_tramite as fn
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                q = _make_query_chain([None, None, None])
                mock_db.session.query.return_value = q
                resultado = fn(tramite_id=99)
        assert resultado is None

    def test_tarea_sin_doc_producido_bloquea_antes(self, app):
        """La primera query encuentra tarea sin doc_producido → bloquea sin llegar a NOTIFICAR."""
        from app.services.invariantes_esftt import _check_finalizar_tramite as fn
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                q = _make_query_chain([MagicMock(), None, None])
                mock_db.session.query.return_value = q
                resultado = fn(tramite_id=99)
        assert resultado is not None
        assert resultado.permitido is False


class TestCheckFinalizarFaseNotificar:

    def test_notificar_incorrecta_en_fase_bloquea(self, app):
        """La tercera query de _check_finalizar_fase detecta NOTIFICAR INCORRECTA."""
        from app.services.invariantes_esftt import _check_finalizar_fase as fn
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                q = _make_query_chain([None, None, MagicMock()])
                mock_db.session.query.return_value = q
                resultado = fn(fase_id=99)
        assert resultado is not None
        assert resultado.permitido is False
        assert 'notificaci' in resultado.norma_compilada.lower()

    def test_sin_problemas_no_bloquea(self, app):
        from app.services.invariantes_esftt import _check_finalizar_fase as fn
        with app.app_context():
            with patch('app.services.invariantes_esftt.db') as mock_db:
                q = _make_query_chain([None, None, None])
                mock_db.session.query.return_value = q
                resultado = fn(fase_id=99)
        assert resultado is None
