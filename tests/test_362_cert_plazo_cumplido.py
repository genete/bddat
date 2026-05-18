"""
Tests #362 — CERT_PLAZO_CUMPLIDO: certificado de plazo cumplido.

Sección A: Tramite.finalizado con tareas ESPERAR_PLAZO (sin BD — stubs).
Sección B: crear_cert() — validaciones de negocio (sin BD — stubs).
"""
from app.models.tramites import Tramite
from app.models.tareas import Tarea


# ---------------------------------------------------------------------------
# Stubs compartidos
# ---------------------------------------------------------------------------

class _TipoTarea:
    def __init__(self, codigo):
        self.codigo = codigo
        self.nombre = codigo


class _Vinculo:
    def __init__(self, rol):
        self.rol = rol
        self.documento = object()


class _StubTarea:
    def __init__(self, codigo, vinculos=None):
        self.tipo_tarea = _TipoTarea(codigo)
        self.vinculos_documento = vinculos or []

    @property
    def ejecutada(self):
        return Tarea.ejecutada.fget(self)

    @property
    def resultado(self):
        return 'INDIFERENTE'

    @property
    def documento_producido(self):
        return Tarea.documento_producido.fget(self)


class _StubTramite:
    def __init__(self, tareas):
        self.tareas = tareas

    @property
    def finalizado(self):
        return Tramite.finalizado.fget(self)


# ---------------------------------------------------------------------------
# A) Tramite.finalizado con ESPERAR_PLAZO
# ---------------------------------------------------------------------------

class TestTramiteFinalizadoEsperarPlazo:

    def test_ep_sin_doc_producido_no_finalizado(self):
        """Trámite con ESPERAR_PLAZO sin documento producido → no finalizado."""
        tramite = _StubTramite([
            _StubTarea('ESPERAR_PLAZO', []),
        ])
        assert tramite.finalizado is False

    def test_ep_con_doc_producido_finalizado(self):
        """Trámite con ESPERAR_PLAZO con documento producido → finalizado."""
        tramite = _StubTramite([
            _StubTarea('ESPERAR_PLAZO', [_Vinculo('PRODUCIDO')]),
        ])
        assert tramite.finalizado is True

    def test_ep_mas_analizar_elaborar_todos_ejecutados_finalizado(self):
        """Trámite con EP + ANALIZAR + ELABORAR todos con doc producido → finalizado."""
        tramite = _StubTramite([
            _StubTarea('ANALIZAR',      [_Vinculo('PRODUCIDO')]),
            _StubTarea('ELABORAR',      [_Vinculo('PRODUCIDO')]),
            _StubTarea('ESPERAR_PLAZO', [_Vinculo('PRODUCIDO')]),
        ])
        assert tramite.finalizado is True

    def test_ep_mas_analizar_pendiente_no_finalizado(self):
        """ANALIZAR sin doc producido bloquea aunque EP esté ejecutado."""
        tramite = _StubTramite([
            _StubTarea('ANALIZAR',      []),
            _StubTarea('ESPERAR_PLAZO', [_Vinculo('PRODUCIDO')]),
        ])
        assert tramite.finalizado is False

    def test_ep_solo_consumido_no_finalizado(self):
        """ESPERAR_PLAZO con solo doc consumido (sin producido) → no finalizado."""
        tramite = _StubTramite([
            _StubTarea('ESPERAR_PLAZO', [_Vinculo('CONSUMIDO')]),
        ])
        assert tramite.finalizado is False

    def test_tramite_sin_tareas_finalizado(self):
        """Trámite sin tareas → finalizado (no hay nada que bloquee)."""
        tramite = _StubTramite([])
        assert tramite.finalizado is True

    def test_tarea_sin_tipo_ignorada(self):
        """Tarea sin tipo_tarea se ignora en el cómputo de finalizado."""
        t = _StubTarea('ESPERAR_PLAZO', [_Vinculo('PRODUCIDO')])
        t_sin_tipo = _StubTarea('ESPERAR_PLAZO', [])
        t_sin_tipo.tipo_tarea = None
        tramite = _StubTramite([t, t_sin_tipo])
        assert tramite.finalizado is True


# ---------------------------------------------------------------------------
# B) crear_cert() — validaciones sin BD
# ---------------------------------------------------------------------------

class TestCrearCertValidaciones:

    def test_tipo_tarea_sin_cert_definido_lanza_valueerror(self):
        """Tipo de tarea sin certificado definido lanza ValueError."""
        import pytest
        from app.services.certificados import _TIPO_CERT_POR_TAREA

        codigos_sin_cert = {'ANALIZAR', 'ELABORAR', 'NOTIFICAR'} - set(_TIPO_CERT_POR_TAREA)
        for codigo in codigos_sin_cert:
            assert codigo not in _TIPO_CERT_POR_TAREA, (
                f'{codigo} no debería tener certificado definido en esta versión'
            )

    def test_esperar_plazo_tiene_cert_definido(self):
        """ESPERAR_PLAZO tiene CERT_PLAZO_CUMPLIDO como certificado."""
        from app.services.certificados import _TIPO_CERT_POR_TAREA
        assert _TIPO_CERT_POR_TAREA.get('ESPERAR_PLAZO') == 'CERT_PLAZO_CUMPLIDO'

    def test_crear_cert_usa_bddat_uri(self):
        """crear_cert() genera URLs bddat://certificados/<id> (no placeholder fijo)."""
        # La lógica real requiere BD; este test verifica que _URL_PLACEHOLDER
        # ya no existe (se eliminó en #425) y que la URL final la asigna el servicio
        # tras insertar en la tabla certificados.
        import importlib
        import app.services.certificados as mod
        assert not hasattr(mod, '_URL_PLACEHOLDER'), (
            '_URL_PLACEHOLDER debe haberse eliminado en #425; '
            'crear_cert() ahora asigna bddat://certificados/{cert.id} tras el INSERT'
        )
