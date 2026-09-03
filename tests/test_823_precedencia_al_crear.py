"""
Tests #823 — rama CREAR de `check_invariante`: precedencia al crear nodos del árbol.

Con SQL real (fixture `arbol_esftt`, #715) — nada de mocks de `db.session`.

Los dos checks del issue, más el contrato de la rama:
  - Punto 1: un ESPERAR_PLAZO exige que TODAS las tareas NOTIFICAR de su propio
    trámite estén completas (producido + Notificacion.resultado CORRECTA, mismo
    criterio que Tramite.finalizado). Sin ninguna NOTIFICAR instanciada también
    bloquea: la lista vacía no vale por vacuidad.
  - Punto 2: no se abre otro trámite de la cadena de subsanación con el anterior
    DE LA CADENA sin finalizar — filtrando por TRAMITES_CADENA_SUBSANACION, no por
    "el trámite anterior de la fase" (que con un COMUNICACION_INICIO_ADMISION
    intercalado no vería el requerimiento vivo).
  - Ambos son puerta cerrada: `puede_escapar=False` y `justificacion` no los abre.

Verificado en catálogo antes de escribir esto: los 19 tipos de trámite con
ESPERAR_PLAZO tienen NOTIFICAR antes, así que el punto 1 es universal.
"""
import pytest
from flask_login import login_user


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _tipo_tarea(codigo):
    from app.models.tipos_tareas import TipoTarea
    fila = TipoTarea.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'TipoTarea {codigo!r} no está en el catálogo de esta BD')
    return fila


def _tipo_tramite(codigo):
    from app.models.tipos_tramites import TipoTramite
    fila = TipoTramite.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'TipoTramite {codigo!r} no está en el catálogo de esta BD')
    return fila


_SIN_FILA = object()  # distinto de None: "no hay fila Notificacion", no "sin resultado"


def _notificar(arbol, tramite, *, consumido=True, producido=False, resultado=_SIN_FILA):
    """Tarea NOTIFICAR en `tramite`, montada hasta el punto que se quiera probar.

    Los cuatro escalones reales del acto de notificar (ADR-034): documento a
    notificar consumido → justificante producido → fila Notificacion registrada →
    resultado resuelto. `resultado=None` crea la fila con el resultado pendiente
    (estado azul PENDIENTE_RESULTADO_NOTIFICACION); omitirlo la deja sin crear.
    """
    expediente_id = tramite.fase.solicitud.expediente_id
    tarea = arbol.tarea(tramite, 'NOTIFICAR')
    if consumido:
        doc = arbol.documento(expediente_id, 'OFICIO_REQUERIMIENTO', f'oficio-{tarea.id}')
        arbol.vincular(tarea, doc, 'CONSUMIDO')
    if producido:
        just = arbol.documento(expediente_id, 'JUSTIFICANTE_NOTIFICA', f'justif-{tarea.id}')
        arbol.vincular(tarea, just, 'PRODUCIDO')
    if resultado is not _SIN_FILA:
        arbol.notificacion(tarea, resultado)
    return tarea


def _completar_tramite_requerimiento(arbol, tramite):
    """Deja `tramite` con Tramite.finalizado True: una NOTIFICAR completa basta,
    porque el resto de tipos que exigen producido no están instanciados."""
    _notificar(arbol, tramite, producido=True, resultado='CORRECTA')
    assert tramite.finalizado is True
    return tramite


# ---------------------------------------------------------------------------
# A) Punto 1 — ESPERAR_PLAZO exige el NOTIFICAR del trámite completo
# ---------------------------------------------------------------------------

class TestCrearEsperarPlazo:

    def test_sin_notificar_instanciada_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')

        res = check_invariante('CREAR', 'TAREA', tramite.id, tipo_codigo='ESPERAR_PLAZO')

        assert res is not None
        assert res.puede_escapar is False
        assert 'no tiene la tarea de notificación' in res.norma_compilada

    def test_notificar_sin_envio_registrado_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite)  # oficio consumido, nada más

        res = check_invariante('CREAR', 'TAREA', tramite.id, tipo_codigo='ESPERAR_PLAZO')

        assert res is not None
        assert res.puede_escapar is False
        assert 'falta registrar el envío de la notificación' in res.norma_compilada

    def test_notificar_sin_resultado_bloquea(self, arbol_esftt):
        """El justificante está vinculado pero el resultado sigue pendiente
        (Notificacion.resultado NULL): aún no consta notificación practicada."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        res = check_invariante('CREAR', 'TAREA', tramite.id, tipo_codigo='ESPERAR_PLAZO')

        assert res is not None
        assert 'falta el justificante definitivo' in res.norma_compilada

    def test_notificar_incorrecta_bloquea(self, arbol_esftt):
        """INCORRECTA = caducada / rechazada / no entregada: queda 2º intento o
        procede edicto, no hay acto consumado del que contar plazo."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado='INCORRECTA')

        res = check_invariante('CREAR', 'TAREA', tramite.id, tipo_codigo='ESPERAR_PLAZO')

        assert res is not None
        assert 'la notificación falló' in res.norma_compilada

    def test_notificar_completa_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado='CORRECTA')

        assert check_invariante('CREAR', 'TAREA', tramite.id,
                                tipo_codigo='ESPERAR_PLAZO') is None

    def test_se_exigen_todas_las_notificar_no_basta_una(self, arbol_esftt):
        """Criterio "todas", por coherencia con Tramite.finalizado: los cuatro
        ANUNCIO_* tienen dos ESPERAR_PLAZO y puede haber varias NOTIFICAR."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado='CORRECTA')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        res = check_invariante('CREAR', 'TAREA', tramite.id, tipo_codigo='ESPERAR_PLAZO')

        assert res is not None
        assert 'falta el justificante definitivo' in res.norma_compilada

    def test_otro_tipo_de_tarea_no_se_ve_afectado(self, arbol_esftt):
        """El check es una dependencia semántica concreta, no "respetar
        tramites_tareas.orden" (ADR-037 §C): crear un ANALIZAR con la NOTIFICAR
        a medias no lo bloquea nada."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite)

        assert check_invariante('CREAR', 'TAREA', tramite.id,
                                tipo_codigo='ANALIZAR') is None

    def test_sin_tipo_codigo_no_evalua_nada(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')

        assert check_invariante('CREAR', 'TAREA', tramite.id) is None


# ---------------------------------------------------------------------------
# B) Punto 2 — cadena de subsanación: una vuelta cada vez
# ---------------------------------------------------------------------------

class TestCrearVueltaCadena:

    def test_primera_vuelta_sobre_fase_vacia_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')

        assert check_invariante('CREAR', 'TRAMITE', fase.id,
                                tipo_codigo='ANALISIS_DOCUMENTAL') is None

    def test_vuelta_anterior_viva_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        res = check_invariante('CREAR', 'TRAMITE', fase.id,
                               tipo_codigo='REQUERIMIENTO_SUBSANACION')

        assert res is not None
        assert res.puede_escapar is False
        assert 'sigue sin completarse' in res.norma_compilada

    def test_vuelta_anterior_vacia_bloquea(self, arbol_esftt):
        """Trámite de la cadena recién creado y sin tareas: `finalizado` es False
        desde #723 ("vacío" no es "hecho"), que es justo lo que aquí interesa."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')

        assert check_invariante('CREAR', 'TRAMITE', fase.id,
                                tipo_codigo='REQUERIMIENTO_SUBSANACION') is not None

    def test_vuelta_anterior_completa_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _completar_tramite_requerimiento(arbol_esftt, tramite)

        assert check_invariante('CREAR', 'TRAMITE', fase.id,
                                tipo_codigo='REQUERIMIENTO_SUBSANACION') is None

    def test_tramite_intercalado_no_tapa_la_vuelta_viva(self, arbol_esftt):
        """El caso que `tramite_anterior_en_fase()` no habría visto: con un
        COMUNICACION_INICIO_ADMISION creado después del requerimiento vivo, el
        "anterior por id" es ese, no el de la cadena. Se filtra por
        TRAMITES_CADENA_SUBSANACION, así que sigue bloqueando."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        vivo = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, vivo, producido=True, resultado=None)
        intercalado = arbol_esftt.tramite(fase, 'COMUNICACION_INICIO_ADMISION')
        assert intercalado.id > vivo.id

        res = check_invariante('CREAR', 'TRAMITE', fase.id,
                               tipo_codigo='REQUERIMIENTO_SUBSANACION')

        assert res is not None
        assert 'sigue sin completarse' in res.norma_compilada

    def test_tramite_fuera_de_la_cadena_no_se_ve_afectado(self, arbol_esftt):
        """En CONSULTAS los trámites son paralelos por organismo y ninguno precede
        a otro: el check no puede degenerar en "trámite anterior finalizado"."""
        from app.services.invariantes_esftt import check_invariante

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        assert check_invariante('CREAR', 'TRAMITE', fase.id,
                                tipo_codigo='COMUNICACION_INICIO_ADMISION') is None
        assert check_invariante('CREAR', 'TRAMITE', fase.id,
                                tipo_codigo='CONSULTA_SEPARATA') is None

    def test_solo_cuenta_la_cadena_de_la_propia_fase(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        fase_con_vuelta_viva = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase_con_vuelta_viva, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        otra_fase = arbol_esftt.fase('ANALISIS_SOLICITUD')

        assert check_invariante('CREAR', 'TRAMITE', otra_fase.id,
                                tipo_codigo='REQUERIMIENTO_SUBSANACION') is None


# ---------------------------------------------------------------------------
# C) Puerta cerrada de extremo a extremo — el servicio bloquea, y `justificacion`
#    no lo abre (a diferencia del vocabulario ESFTT y de las reglas del motor)
# ---------------------------------------------------------------------------

class TestPuertaCerradaEnElServicio:

    def test_crear_tarea_bloquea_tambien_con_justificacion(self, arbol_esftt, app_ctx):
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.crear_tarea(tramite, _tipo_tarea('ESPERAR_PLAZO'),
                                  justificacion='Lo necesito igual')

        assert res.ok is False
        assert res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert 'espera de plazo' in res.bloqueo.norma_compilada
        assert not [t for t in tramite.tareas
                    if t.tipo_tarea and t.tipo_tarea.codigo == 'ESPERAR_PLAZO']

    def test_crear_tramite_bloquea_tambien_con_justificacion(self, arbol_esftt, app_ctx):
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        _notificar(arbol_esftt, tramite, producido=True, resultado=None)

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.crear_tramite(fase, _tipo_tramite('REQUERIMIENTO_SUBSANACION'),
                                    justificacion='Lo necesito igual')

        assert res.ok is False
        assert res.bloqueo.puede_escapar is False
        assert 'vuelta de subsanación' in res.bloqueo.norma_compilada
        assert len(fase.tramites) == 1

    def test_crear_tarea_deja_pasar_cuando_la_notificacion_consta(self, arbol_esftt, app_ctx):
        """Camino feliz por el servicio completo: con la NOTIFICAR practicada, el
        invariante no interfiere y la tarea se crea.

        El ELABORAR previo no es decorativo: `check_orden_tarea` cuenta por
        posición (ADR-037 §C), así que sin él "la que toca" sería la NOTIFICAR y
        el bloqueo vendría del vocabulario, no de lo que aquí se prueba.
        """
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        arbol_esftt.tarea(tramite, 'ELABORAR')
        _notificar(arbol_esftt, tramite, producido=True, resultado='CORRECTA')

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.crear_tarea(tramite, _tipo_tarea('ESPERAR_PLAZO'))

        assert res.ok is True, getattr(res.bloqueo, 'norma_compilada', res.error)
        assert res.ids
