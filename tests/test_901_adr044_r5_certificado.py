"""Tests issue #901 — ADR-044 R5 §H: ámbito, observaciones de cierre, cabecera
de versión y agrupación por versión en el certificado de fin de instrucción.

No repite lo que ya cubren otros ficheros: `fase_ip_finalizada` /
`existe_fase_finalizadora_cerrada` están en test_470, `Solicitud.estado` en
test_296, el aislamiento de alegaciones en test_394.
"""
from datetime import date

from app import db


def _cerrar(arbol, fase, fecha=None):
    """Mismo patrón que test_827_cert_fin_instruccion._cerrar."""
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'cierre-901-{fase.id}')
    if fecha is not None:
        doc.fecha_administrativa = fecha
    fase.documento_resultado_id = doc.id
    db.session.flush()
    return fase


# ---------------------------------------------------------------------------
# A) Bloque.ambito (informe_instruccion._ambito_fase)
# ---------------------------------------------------------------------------

class TestAmbitoDeFase:

    def test_sin_reformado_version_inicial(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        informe = revisar(sol)
        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert bloque.ambito == 'el proyecto en su redacción original'

    def test_con_reformado_cita_su_fecha(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        reformado.documento.fecha_administrativa = date(2026, 5, 20)
        db.session.flush()

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        fase.reformado_id = reformado.id
        db.session.flush()
        _cerrar(arbol_esftt, fase)

        informe = revisar(sol)
        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert bloque.ambito == 'el reformado de fecha 20/05/2026'


# ---------------------------------------------------------------------------
# B) Observaciones de cierre, siempre
# ---------------------------------------------------------------------------

class TestObservacionesDeCierre:

    def test_con_observaciones_suben_al_relato(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        fase.observaciones = 'Cierre conjunto con la fase ambiental del reformado.'
        _cerrar(arbol_esftt, fase)

        informe = revisar(sol)
        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert ('Observaciones al cierre: Cierre conjunto con la fase ambiental '
                'del reformado..') in bloque.relato

    def test_sin_observaciones_dice_guion(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        _cerrar(arbol_esftt, fase)

        informe = revisar(sol)
        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert 'Observaciones al cierre: -.' in bloque.relato


# ---------------------------------------------------------------------------
# C) Cabecera de versión en el bloque propio de la solicitud
# ---------------------------------------------------------------------------

class TestCabeceraDeVersion:

    def test_sin_reformados_no_menciona_version(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        _cerrar(arbol_esftt, fase)

        informe = revisar(sol)
        propio = next(b for b in informe.bloques if b.nodo == ('solicitud', sol.id))
        assert not any('reformado' in linea.lower() for linea in propio.relato)

    def test_con_reformado_cita_vigente_y_redaccion_original(self, arbol_esftt):
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        reformado.documento.fecha_administrativa = date(2026, 6, 1)
        db.session.flush()

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        fase.reformado_id = reformado.id
        db.session.flush()
        _cerrar(arbol_esftt, fase)

        informe = revisar(sol)
        propio = next(b for b in informe.bloques if b.nodo == ('solicitud', sol.id))
        texto = ' '.join(propio.relato)
        assert 'Se resuelve sobre el reformado de fecha 01/06/2026.' in texto
        assert 'el proyecto en su redacción original' in texto


# ---------------------------------------------------------------------------
# D) Agrupación por versión en el PDF (generador_cert._secciones_del_informe)
# ---------------------------------------------------------------------------

def _bloque(ambito, *relato, nodo=None):
    from app.services.informe_instruccion import Bloque, PASA
    return Bloque(PASA, 'x', relato=tuple(relato), ambito=ambito, nodo=nodo)


class _InformeFalso:
    def __init__(self, bloques):
        self.bloques = bloques
        self.salvados = []


class TestAgrupacionPorVersion:

    def _params_reportlab(self):
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, Spacer
        estilo = ParagraphStyle('normal')
        return Paragraph, Spacer, cm, estilo, estilo

    def test_una_sola_version_no_agrupa(self):
        """Sin reformados (una sola versión) el texto sigue llano: sin
        cabeceras "Sobre..." de por medio."""
        from app.services.generador_cert import _secciones_del_informe

        bloques = [
            _bloque(None, 'Solicitud #1.'),
            _bloque('el proyecto en su redacción original', 'Fase A — cerrada.'),
        ]
        Paragraph, Spacer, cm, e1, e2 = self._params_reportlab()
        secciones = _secciones_del_informe(_InformeFalso(bloques), Paragraph, Spacer, cm, e1, e2)

        textos = [s.text for s in secciones if isinstance(s, Paragraph)]
        assert not any(t.startswith('Sobre ') for t in textos)
        assert 'Solicitud #1.' in textos
        assert 'Fase A — cerrada.' in textos

    def test_dos_versiones_agrupa_con_cabecera(self):
        from app.services.generador_cert import _secciones_del_informe

        bloques = [
            _bloque(None, 'Solicitud #1.'),
            _bloque('el proyecto en su redacción original', 'ANALISIS_SOLICITUD — cerrada.'),
            _bloque('el reformado de fecha 20/05/2026', 'CONSULTAS — cerrada.'),
            # Una segunda fase de la versión inicial, no contigua: debe seguir
            # cayendo en el mismo grupo que la primera.
            _bloque('el proyecto en su redacción original', 'INFORMACION_PUBLICA — cerrada.'),
        ]
        Paragraph, Spacer, cm, e1, e2 = self._params_reportlab()
        secciones = _secciones_del_informe(_InformeFalso(bloques), Paragraph, Spacer, cm, e1, e2)

        textos = [s.text for s in secciones if isinstance(s, Paragraph)]
        assert 'Sobre el proyecto en su redacción original:' in textos
        assert 'Sobre el reformado de fecha 20/05/2026:' in textos

        idx_original = textos.index('Sobre el proyecto en su redacción original:')
        idx_analisis = textos.index('ANALISIS_SOLICITUD — cerrada.')
        idx_ip = textos.index('INFORMACION_PUBLICA — cerrada.')
        idx_reformado = textos.index('Sobre el reformado de fecha 20/05/2026:')
        idx_consultas = textos.index('CONSULTAS — cerrada.')
        # Las dos fases de la versión inicial caen bajo su cabecera, aunque no
        # sean contiguas en el árbol; la del reformado, bajo la suya.
        assert idx_original < idx_analisis < idx_ip
        assert idx_reformado < idx_consultas
