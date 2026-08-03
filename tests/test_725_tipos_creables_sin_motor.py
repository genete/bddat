"""
Tests #725 — tipos_creables.py sin motor: listado didáctico (ADR-037 §D).

Con SQL real (fixture `arbol_esftt`), sin mocks. Verifica canónicos/resto por
nivel y que los trámites de traslado no aparecen en ninguno de los dos grupos.
"""
import pytest


def _codigos(items):
    return {i['codigo'] for i in items}


class TestCreablesSolicitudYFase:
    """Sin vocabulario propio — todo en canonicos, resto vacío (ADR-037)."""

    def test_creables_solicitud_todo_en_canonicos(self, arbol_esftt, app_ctx):
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.tipos_creables import _creables_solicitud

        sol = arbol_esftt.solicitud_existente()
        data = _creables_solicitud(sol.expediente, sol.expediente_id)

        assert data['resto'] == []
        assert len(data['canonicos']) == TipoSolicitud.query.count()

    def test_creables_fase_todo_en_canonicos(self, arbol_esftt, app_ctx):
        from app.models.tipos_fases import TipoFase
        from app.services.tipos_creables import _creables_fase

        sol = arbol_esftt.solicitud_existente()
        data = _creables_fase(sol.expediente, sol.id)

        assert data['resto'] == []
        assert len(data['canonicos']) == TipoFase.query.count()


class TestCreablesTramite:
    """Vocabulario fases_tramites: canónicos/resto, traslados nunca visibles."""

    def test_analisis_solicitud_tiene_sus_tres_canonicos(self, arbol_esftt, app_ctx):
        from app.services.tipos_creables import _creables_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        data = _creables_tramite(fase.solicitud.expediente, fase.id)

        assert _codigos(data['canonicos']) == {
            'ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION', 'COMUNICACION_INICIO',
        }

    def test_traslados_no_aparecen_ni_en_canonicos_ni_en_resto(self, arbol_esftt, app_ctx):
        from app.services.tipos_creables import _creables_tramite

        fase = arbol_esftt.fase('CONSULTAS')
        data = _creables_tramite(fase.solicitud.expediente, fase.id)

        todos = _codigos(data['canonicos']) | _codigos(data['resto'])
        assert 'CONSULTA_TRASLADO_TITULAR' not in todos
        assert 'CONSULTA_TRASLADO_ORGANISMO' not in todos
        assert 'CONSULTA_SEPARATA' in _codigos(data['canonicos'])

    def test_tramite_fuera_de_vocabulario_cae_en_resto(self, arbol_esftt, app_ctx):
        from app.services.tipos_creables import _creables_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        data = _creables_tramite(fase.solicitud.expediente, fase.id)

        # ANUNCIO_BOE pertenece al vocabulario de INFORMACION_PUBLICA, no al de ANALISIS_SOLICITUD.
        assert 'ANUNCIO_BOE' in _codigos(data['resto'])
        assert 'ANUNCIO_BOE' not in _codigos(data['canonicos'])


class TestCreablesTarea:
    """Patrón tramites_tareas: canónicos con siguiente marcada, resto = fuera de patrón."""

    def test_analisis_documental_patron_parcial(self, arbol_esftt, app_ctx):
        from app.services.tipos_creables import _creables_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        data = _creables_tarea(tramite.fase.solicitud.expediente, tramite.id)

        assert _codigos(data['canonicos']) == {'ANALIZAR'}
        assert _codigos(data['resto']) == {'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO'}
        assert data['canonicos'][0].get('es_siguiente') is True

    def test_requerimiento_subsanacion_siguiente_avanza_con_creacion(self, arbol_esftt, app_ctx):
        from app.services.tipos_creables import _creables_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')

        data = _creables_tarea(tramite.fase.solicitud.expediente, tramite.id)
        siguientes = [i['codigo'] for i in data['canonicos'] if i.get('es_siguiente')]
        assert siguientes == ['ELABORAR']

        arbol_esftt.tarea(tramite, 'ELABORAR')
        arbol_esftt.db.session.expire(tramite, ['tareas'])
        data = _creables_tarea(tramite.fase.solicitud.expediente, tramite.id)
        siguientes = [i['codigo'] for i in data['canonicos'] if i.get('es_siguiente')]
        assert siguientes == ['NOTIFICAR']
