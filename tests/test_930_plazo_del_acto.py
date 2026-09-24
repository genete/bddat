"""#930 (N2 de ADR-049): el plazo de resolver es del acto; su cumplimiento se
calcula de la notificación al titular.

Bloques:
  A) El acto y la fase que lo resuelve (`actos_solicitud`, fuente única, D4).
  B) `informe_instruccion.codigos_fase_finalizadora` derivada de los actos.
  C) Catálogo de fases: `es_finalizadora` == `FASES_RESOLUTORAS`.
"""
import pytest


def _sol(siglas, fases=()):
    """Solicitud mínima para el mapa: tipo, sus actos (con la misma propiedad
    del modelo, no una copia) y las fases que constan en el árbol."""
    from types import SimpleNamespace
    from app.models.solicitudes import Solicitud

    class _Sol:
        tipos_simples = Solicitud.tipos_simples

        def __init__(self):
            self.tipo_solicitud = SimpleNamespace(siglas=siglas) if siglas else None
            self.fases = [SimpleNamespace(tipo_fase=SimpleNamespace(codigo=c)) for c in fases]

    return _Sol()


# ---------------------------------------------------------------------------
# A) El acto y la fase que lo resuelve
# ---------------------------------------------------------------------------

class TestActos:

    @pytest.mark.parametrize('siglas, actos', [
        ('AAP', ['AAP']),
        ('AAP+AAC', ['AAP', 'AAC']),
        ('AAP+AAC+DUP', ['AAP', 'AAC', 'DUP']),
        ('AE_DEFINITIVA+AAT', ['AE_DEFINITIVA', 'AAT']),
        ('DUP', ['DUP']),
        ('INTERESADO', ['INTERESADO']),
        (None, []),
    ])
    def test_un_acto_por_tipo_atomico(self, siglas, actos):
        from app.services.actos_solicitud import actos_de
        sol = _sol(siglas)
        resultado = actos_de(sol)
        assert [a.siglas for a in resultado] == actos
        assert all(a.solicitud is sol for a in resultado)

    @pytest.mark.parametrize('siglas, acto, fases, esperada', [
        ('DUP', 'DUP', (), 'RESOLUCION_DUP'),
        ('INTERESADO', 'INTERESADO', (), 'RECONOCIMIENTO_INTERESADO'),
        ('AAT', 'AAT', (), 'RESOLUCION'),
        ('AE_DEFINITIVA+AAT', 'AE_DEFINITIVA', (), 'RESOLUCION'),
        ('RECURSO', 'RECURSO', (), 'RESOLUCION'),
        # Conjunta: sin elección todavía
        ('AAP+AAC', 'AAP', (), 'RESOLUCION'),
        ('AAP+AAC', 'AAC', ('RESOLUCION',), 'RESOLUCION'),
        ('AAP+AAC+DUP', 'DUP', ('RESOLUCION_AAP',), 'RESOLUCION_DUP'),
        # Partida: basta con que conste una de las dos
        ('AAP+AAC', 'AAP', ('RESOLUCION_AAP', 'RESOLUCION_AAC'), 'RESOLUCION_AAP'),
        ('AAP+AAC', 'AAC', ('RESOLUCION_AAP',), 'RESOLUCION_AAC'),
        ('AAP+AAC+DUP', 'AAP', ('RESOLUCION_AAC',), 'RESOLUCION_AAP'),
        # La partida solo cabe en las solicitudes que piden AAP y AAC a la vez
        ('AAP+DUP', 'AAP', ('RESOLUCION_AAP',), 'RESOLUCION'),
        ('AAP', 'AAP', ('RESOLUCION_AAP',), 'RESOLUCION'),
    ])
    def test_fase_resolutora(self, siglas, acto, fases, esperada):
        from app.services.actos_solicitud import fase_resolutora
        assert fase_resolutora(_sol(siglas, fases), acto) == esperada

    def test_toda_fase_emitible_esta_en_fases_resolutoras(self):
        """`FASES_RESOLUTORAS` es lo que el guardián compara con el catálogo:
        si el mapa pudiera emitir un código que no está ahí, el guardián no lo
        vería."""
        from app.services import actos_solicitud as m
        emitibles = (set(m._FASE_DE_ACTO.values()) | set(m._FASE_DE_ACTO_PARTIDA.values())
                     | {m._FASE_POR_DEFECTO})
        assert emitibles == m.FASES_RESOLUTORAS


# ---------------------------------------------------------------------------
# B) codigos_fase_finalizadora derivada de los actos (refactor puro, D4)
# ---------------------------------------------------------------------------

# Lo que devolvía `codigos_fase_finalizadora` ANTES del refactor, en estado por
# defecto (sin fases en el árbol). Escrito a mano, no derivado del mapa nuevo:
# es la red que dice que el refactor no cambió nada.
_INFORME_HOY = {
    'AAP': ['RESOLUCION'],
    'AAC': ['RESOLUCION'],
    'DUP': ['RESOLUCION_DUP'],
    'AAP+AAC': ['RESOLUCION'],
    'AAP+AAC+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAC+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAP+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAT': ['RESOLUCION'],
    'AE_PROVISIONAL': ['RESOLUCION'],
    'AE_DEFINITIVA': ['RESOLUCION'],
    'AE_DEFINITIVA+AAT': ['RESOLUCION'],
    'CIERRE': ['RESOLUCION'],
    'INTERESADO': ['RECONOCIMIENTO_INTERESADO'],
    'AMPLIACION_PLAZO': ['RESOLUCION'],
    'CORRECCION_ERRORES': ['RESOLUCION'],
    'DESISTIMIENTO': ['RESOLUCION'],
    'OTRO': ['RESOLUCION'],
    'RADNE': ['RESOLUCION'],
    'RAIPEE_DEFINITIVA': ['RESOLUCION'],
    'RAIPEE_PREVIA': ['RESOLUCION'],
    'RECURSO': ['RESOLUCION'],
    'RENUNCIA': ['RESOLUCION'],
}


class TestCodigosFaseFinalizadora:

    def test_la_tabla_cubre_todo_el_catalogo_de_tipos(self, app_ctx):
        """Un tipo de solicitud nuevo obliga a decir aquí qué fase lo resuelve."""
        from app.models.tipos_solicitudes import TipoSolicitud
        siglas = {t.siglas for t in TipoSolicitud.query.all()}
        assert siglas == set(_INFORME_HOY)

    @pytest.mark.parametrize('siglas', sorted(_INFORME_HOY))
    def test_estado_por_defecto_igual_que_antes(self, siglas):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        assert codigos_fase_finalizadora(_sol(siglas)) == _INFORME_HOY[siglas]

    def test_sin_tipo_resolucion(self):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        assert codigos_fase_finalizadora(_sol(None)) == ['RESOLUCION']

    @pytest.mark.parametrize('siglas, esperada', [
        ('AAP+AAC', ['RESOLUCION_AAP', 'RESOLUCION_AAC']),
        ('AAP+AAC+DUP', ['RESOLUCION_AAP', 'RESOLUCION_AAC', 'RESOLUCION_DUP']),
    ])
    def test_partida_completa(self, siglas, esperada):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol(siglas, ('ANALISIS_SOLICITUD', 'RESOLUCION_AAP', 'RESOLUCION_AAC'))
        assert codigos_fase_finalizadora(sol) == esperada

    def test_partida_a_medias_audita_tambien_la_que_falta(self):
        """Único cambio de comportamiento del refactor (D4): antes solo
        `[RESOLUCION_AAP]`. Inocuo: las reglas CREAR de RESOLUCION_AAC son las
        mismas que las de RESOLUCION_AAP."""
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol('AAP+AAC', ('RESOLUCION_AAP',))
        assert codigos_fase_finalizadora(sol) == ['RESOLUCION_AAP', 'RESOLUCION_AAC']

    def test_aap_dup_no_se_parte_aunque_conste_resolucion_aap(self):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol('AAP+DUP', ('RESOLUCION_AAP',))
        assert codigos_fase_finalizadora(sol) == ['RESOLUCION', 'RESOLUCION_DUP']

    def test_con_solicitud_real_partida(self, arbol_aislado):
        """Lo mismo sobre filas reales: el mapa lee `solicitud.fases` del ORM."""
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.informe_instruccion import codigos_fase_finalizadora

        solicitud = arbol_aislado.solicitud_propia()
        tipo = TipoSolicitud.query.filter_by(siglas='AAP+AAC+DUP').first()
        assert tipo is not None, "la semilla debe traer el tipo 'AAP+AAC+DUP'"
        solicitud.tipo_solicitud = tipo
        assert codigos_fase_finalizadora(solicitud) == ['RESOLUCION', 'RESOLUCION_DUP']

        arbol_aislado.fase('RESOLUCION_AAC', solicitud=solicitud)
        assert codigos_fase_finalizadora(solicitud) == [
            'RESOLUCION_AAP', 'RESOLUCION_AAC', 'RESOLUCION_DUP']


# ---------------------------------------------------------------------------
# C) Catálogo de fases: las finalizadoras son exactamente las del mapa
# ---------------------------------------------------------------------------

class TestCatalogoDeFases:

    def test_es_finalizadora_igual_a_fases_resolutoras(self, app_ctx):
        """En los dos sentidos: una finalizadora que el mapa no conoce se
        auditaría contra otra fase y ningún acto mediría su plazo contra ella;
        un código del mapa que no es finalizadora no cerraría nada."""
        from app.models.tipos_fases import TipoFase
        from app.services.actos_solicitud import FASES_RESOLUTORAS
        finalizadoras = {t.codigo for t in TipoFase.query.filter_by(es_finalizadora=True).all()}
        assert finalizadoras == FASES_RESOLUTORAS

    def test_el_guardian_de_arranque_no_avisa(self, app_ctx):
        from app.checks.catalogo_requerido import _validar_finalizadoras_con_regla
        assert _validar_finalizadoras_con_regla() == []
