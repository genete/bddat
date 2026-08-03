"""
Tests #725/#719 — orden canónico de tareas no vinculante (ADR-037 §C).

Con SQL real (fixture `arbol_esftt`), sin mocks. REQUERIMIENTO_SUBSANACION
tiene patrón conocido: ELABORAR(1) -> NOTIFICAR(2) -> ESPERAR_PLAZO(3) ->
ANALIZAR(4) — confirmado contra BD real antes de escribir estos tests.
"""
import pytest
from flask_login import login_user


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


class TestCheckOrdenTarea:
    """Unidad: app/services/vocabulario_esftt.py::check_orden_tarea"""

    def test_tramite_sin_patron_no_bloquea(self, app_ctx):
        from app.services.vocabulario_esftt import check_orden_tarea

        stub = type('TramiteStub', (), {'tipo_tramite_id': -1, 'tareas': []})()
        assert check_orden_tarea(stub, tipo_tarea=None) is None

    def test_primera_tarea_correcta_no_bloquea(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services.vocabulario_esftt import check_orden_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        elaborar = _tipo(TipoTarea, 'ELABORAR')

        assert check_orden_tarea(tramite, elaborar) is None

    def test_tarea_fuera_de_orden_bloquea_escapable(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services.vocabulario_esftt import check_orden_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        notificar = _tipo(TipoTarea, 'NOTIFICAR')  # toca ELABORAR, no NOTIFICAR

        res = check_orden_tarea(tramite, notificar)

        assert res is not None
        assert res.permitido is False
        assert res.puede_escapar is True
        assert 'ELABORAR' in res.norma_compilada

    def test_segunda_tarea_correcta_tras_la_primera(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services.vocabulario_esftt import check_orden_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        arbol_esftt.tarea(tramite, 'ELABORAR')
        notificar = _tipo(TipoTarea, 'NOTIFICAR')

        assert check_orden_tarea(tramite, notificar) is None

    def test_patron_agotado_no_bloquea(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services.vocabulario_esftt import check_orden_tarea

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        for codigo in ('ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR'):
            arbol_esftt.tarea(tramite, codigo)

        otro_analizar = _tipo(TipoTarea, 'ANALIZAR')
        assert check_orden_tarea(tramite, otro_analizar) is None


class TestCrearTareaConOrden:
    """Integración: app/services/mutaciones_arbol.py::crear_tarea"""

    def test_crear_tarea_fuera_de_orden_bloquea_sin_justificacion(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        notificar = _tipo(TipoTarea, 'NOTIFICAR')

        res = svc.crear_tarea(tramite, notificar, justificacion=None)

        assert res.ok is False
        assert res.bloqueo.puede_escapar is True

    def test_crear_tarea_fuera_de_orden_se_fuerza_con_justificacion(self, arbol_esftt, app_ctx):
        from app.models.tipos_tareas import TipoTarea
        from app.models.tareas import Tarea
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        notificar = _tipo(TipoTarea, 'NOTIFICAR')

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.crear_tarea(tramite, notificar, justificacion='Caso urgente, se notifica antes')

        assert res.ok is True
        creada = Tarea.query.get(res.ids[0])
        assert creada.tipo_tarea_id == notificar.id

    def test_crear_tarea_en_orden_no_pide_justificacion(self, arbol_esftt):
        from app.models.tipos_tareas import TipoTarea
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        elaborar = _tipo(TipoTarea, 'ELABORAR')

        res = svc.crear_tarea(tramite, elaborar, justificacion=None)

        assert res.ok is True
