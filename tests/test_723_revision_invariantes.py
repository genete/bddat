"""
Tests #723 — revisión de invariantes: vías de escape, guardia de completitud del
cierre de fase, y motivo veraz del candado de diagnóstico producido.

Con SQL real (fixture `arbol_esftt`, #715) — nada de mocks de `db.session`.

Ejes que cubren:
  - Fix de raíz: Tramite.finalizado ya no confunde "vacío" con "hecho" (antes
    devolvía True por vacuidad del bucle sobre 0 tareas).
  - _check_completitud_cierre (editar_fase): vacío estructural (fase sin
    trámites, trámite sin tareas) bloquea sin escape; incompleto con contenido
    (trámite con tareas a medias) es forzable con justificación, con rastro en
    bitácora.
  - _check_cierre_fase (caso 1 del issue): forzable con justificación, con
    rastro en bitácora.
  - motivo_bloqueo_reversion / _candado_diagnostico_producido (caso 3 del
    issue): el candado deja de prometer "revierte antes" cuando revertir
    también está bloqueado.
"""
import datetime

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


def _doc_cierre(arbol_esftt, expediente_id, sufijo='cierre'):
    """Documento cualquiera, válido como documento_resultado_id de una fase."""
    return arbol_esftt.documento(expediente_id, 'CERT_FIN_INSTRUCCION', sufijo)


def _bitacora_ultima(tabla, registro_id, operacion='ALTERAR'):
    from app.models.bitacora import Bitacora
    return (
        Bitacora.query
        .filter_by(tabla=tabla, registro_id=registro_id, operacion=operacion)
        .order_by(Bitacora.id.desc())
        .first()
    )


def _montar_cadena_subsanacion(specs):
    """Monta una fase ANALISIS_SOLICITUD con una tarea ANALIZAR por spec.

    `specs`: lista de (codigo_tramite, resultado_diagnostico, notificado_antes).
    Mismo patrón que test_714_reversion_diagnostico_superado.py::_montar_fase
    (cada fichero de test tiene su propio helper autocontenible).
    """
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico
    from app.models.notificaciones import Notificacion
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_documentos import TipoDocumento

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    tipo_analizar = _tipo(TipoTarea, 'ANALIZAR')
    tipo_notificar = _tipo(TipoTarea, 'NOTIFICAR')
    tipo_diagnostico = _tipo(TipoDocumento, 'DIAGNOSTICO')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
    db.session.add(fase)
    db.session.flush()

    tareas_analizar = []
    for codigo_tramite, resultado, notificado in specs:
        tramite = Tramite(fase_id=fase.id, tipo_tramite_id=_tipo(TipoTramite, codigo_tramite).id)
        db.session.add(tramite)
        db.session.flush()

        if notificado:
            notificar = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_notificar.id)
            db.session.add(notificar)
            db.session.flush()
            db.session.add(Notificacion(
                tarea_id=notificar.id, canal='NOTIFICA',
                fecha_puesta_disposicion=datetime.date(2026, 7, 20), numero_intento=1,
            ))
            db.session.flush()

        tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_analizar.id)
        db.session.add(tarea)
        db.session.flush()
        tareas_analizar.append(tarea)

        if resultado is None:
            continue

        doc = Documento(expediente_id=solicitud.expediente_id, tipo_doc_id=tipo_diagnostico.id,
                        url=f'bddat://diagnosticos/test-723-{tarea.id}')
        db.session.add(doc)
        db.session.flush()
        db.session.add(Diagnostico(documento_id=doc.id, resultado=resultado, defectos=[]))
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()

    return fase, tareas_analizar


# ---------------------------------------------------------------------------
# A) Fix de raíz: Tramite.finalizado ya no confunde vacío con hecho
# ---------------------------------------------------------------------------

class TestTramiteFinalizadoVacio:

    def test_tramite_sin_tareas_no_finalizado(self, arbol_esftt):
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        assert tramite.finalizado is False
        # Antes del fix, un trámite vacío hacía pdte_cierre=True por vacuidad —
        # la fase "parecía" lista para cerrar sin tener nada dentro.
        assert fase.pdte_cierre is False


# ---------------------------------------------------------------------------
# B) _check_completitud_cierre — vacío estructural, puerta cerrada
# ---------------------------------------------------------------------------

class TestGuardiaCompletitudVacia:

    def test_fase_sin_tramites_bloquea_sin_escape(self, arbol_esftt):
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        doc = _doc_cierre(arbol_esftt, fase.solicitud.expediente_id)

        res = svc.editar_fase(fase, resultado_fase_id=None, documento_resultado_id=doc.id,
                              observaciones=None, justificacion='lo necesito igual')

        assert res.ok is False
        assert res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert 'no tiene trámites' in res.bloqueo.norma_compilada
        assert fase.documento_resultado_id is None

    def test_fase_con_tramite_vacio_bloquea_sin_escape_aunque_otro_este_completo(self, arbol_esftt):
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        expediente_id = fase.solicitud.expediente_id

        # Trámite completo: ESPERAR_PLAZO con documento producido.
        tramite_ok = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        tarea_ok = arbol_esftt.tarea(tramite_ok, 'ESPERAR_PLAZO')
        doc_ok = arbol_esftt.documento(expediente_id, 'CERT_PLAZO_CUMPLIDO', 'ok')
        arbol_esftt.vincular(tarea_ok, doc_ok, 'PRODUCIDO')
        assert tramite_ok.finalizado is True

        # Trámite vacío colgando en la misma fase.
        arbol_esftt.tramite(fase, 'REQUERIMIENTO_SUBSANACION')

        doc_cierre = _doc_cierre(arbol_esftt, expediente_id)
        res = svc.editar_fase(fase, resultado_fase_id=None, documento_resultado_id=doc_cierre.id,
                              observaciones=None, justificacion='lo necesito igual')

        assert res.ok is False
        assert res.bloqueo.puede_escapar is False
        assert 'no tiene tareas' in res.bloqueo.norma_compilada


# ---------------------------------------------------------------------------
# C) _check_completitud_cierre — incompleto con contenido, forzable
# ---------------------------------------------------------------------------

class TestGuardiaCompletitudIncompleta:

    def test_tramite_con_tarea_sin_terminar_bloquea_sin_justificacion(self, arbol_esftt):
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        arbol_esftt.tarea(tramite, 'ANALIZAR')  # sin documento producido
        doc = _doc_cierre(arbol_esftt, fase.solicitud.expediente_id)

        res = svc.editar_fase(fase, resultado_fase_id=None, documento_resultado_id=doc.id,
                              observaciones=None, justificacion=None)

        assert res.ok is False
        assert res.bloqueo.puede_escapar is True
        assert 'no está completo' in res.bloqueo.norma_compilada

    def test_tramite_con_tarea_sin_terminar_se_fuerza_y_registra_bitacora(self, arbol_esftt, app_ctx):
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        arbol_esftt.tarea(tramite, 'ANALIZAR')
        doc = _doc_cierre(arbol_esftt, fase.solicitud.expediente_id)

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.editar_fase(fase, resultado_fase_id=None, documento_resultado_id=doc.id,
                                  observaciones=None, justificacion='Ya se corrigió a mano')

        assert res.ok is True
        assert fase.documento_resultado_id == doc.id

        entrada = _bitacora_ultima('fases', fase.id)
        assert entrada is not None
        assert entrada.detalle['escape'] is True
        assert entrada.detalle['justificacion'] == 'Ya se corrigió a mano'


# ---------------------------------------------------------------------------
# D) _check_cierre_fase (caso 1 del issue) — forzable con justificación
# ---------------------------------------------------------------------------

class TestCierreFaseDesfavorableForzable:

    def test_desfavorable_sin_consumir_bloquea_sin_justificacion(self, arbol_esftt):
        from app.services import mutaciones_arbol as svc
        from app.models.tipos_resultados_fases import TipoResultadoFase

        fase, _ = _montar_cadena_subsanacion([('ANALISIS_DOCUMENTAL', 'desfavorable', False)])
        doc = _doc_cierre(arbol_esftt, fase.solicitud.expediente_id)
        favorable = _tipo(TipoResultadoFase, 'FAVORABLE')

        res = svc.editar_fase(fase, resultado_fase_id=favorable.id, documento_resultado_id=doc.id,
                              observaciones=None, justificacion=None)

        assert res.ok is False
        assert res.bloqueo.puede_escapar is True
        assert 'desfavorable sin consumir' in res.bloqueo.norma_compilada

    def test_desfavorable_sin_consumir_se_fuerza_y_registra_bitacora(self, arbol_esftt, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.tipos_resultados_fases import TipoResultadoFase

        usuario = _usuario()
        fase, _ = _montar_cadena_subsanacion([('ANALISIS_DOCUMENTAL', 'desfavorable', False)])
        doc = _doc_cierre(arbol_esftt, fase.solicitud.expediente_id)
        favorable = _tipo(TipoResultadoFase, 'FAVORABLE')

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.editar_fase(fase, resultado_fase_id=favorable.id, documento_resultado_id=doc.id,
                                  observaciones=None, justificacion='El desfavorable ya está superado')

        assert res.ok is True
        assert fase.resultado_fase_id == favorable.id

        entrada = _bitacora_ultima('fases', fase.id)
        assert entrada is not None
        assert entrada.detalle['escape'] is True
        assert entrada.detalle['justificacion'] == 'El desfavorable ya está superado'


# ---------------------------------------------------------------------------
# E) motivo_bloqueo_reversion / candado — motivo veraz (caso 3 del issue)
# ---------------------------------------------------------------------------

class TestMotivoBloqueoReversion:

    def test_reversible_sin_mas_devuelve_none(self, arbol_esftt):
        from app.services.diagnosticos import motivo_bloqueo_reversion

        fase, tareas = _montar_cadena_subsanacion([('ANALISIS_DOCUMENTAL', 'desfavorable', False)])
        assert motivo_bloqueo_reversion(tareas[0]) is None

        # El candado, en ese caso, mantiene el mensaje genérico de siempre.
        from app.routes.api_expedientes import _candado_diagnostico_producido
        resp, status = _candado_diagnostico_producido(tareas[0])
        assert status == 422
        payload = resp.get_json()
        assert 'Revierte el diagnóstico antes' in payload['motivo']
        assert payload['puede_escapar'] is False

    def test_consumido_devuelve_motivo_con_tarea_consumidora(self, arbol_esftt):
        from app import db
        from app.models.tipos_tareas import TipoTarea
        from app.models.documentos_tarea import DocumentoTarea
        from app.services.diagnosticos import motivo_bloqueo_reversion

        fase, tareas = _montar_cadena_subsanacion([('ANALISIS_DOCUMENTAL', 'desfavorable', False)])
        tarea = tareas[0]
        doc = tarea.documento_producido

        consumidora = arbol_esftt.tarea(tarea.tramite, 'ELABORAR')
        db.session.add(DocumentoTarea(tarea_id=consumidora.id, documento_id=doc.id, rol='CONSUMIDO'))
        db.session.flush()

        bloqueo = motivo_bloqueo_reversion(tarea)
        assert bloqueo is not None
        assert bloqueo.puede_escapar is False
        assert 'consumido' in bloqueo.motivo.lower()

        from app.routes.api_expedientes import _candado_diagnostico_producido
        resp, status = _candado_diagnostico_producido(tarea)
        payload = resp.get_json()
        assert 'consumido' in payload['motivo'].lower()
        assert 'Revierte el diagnóstico antes' not in payload['motivo']

    def test_superado_por_vuelta_posterior_devuelve_motivo_forzable(self, arbol_esftt):
        from app.services.diagnosticos import motivo_bloqueo_reversion

        fase, tareas = _montar_cadena_subsanacion([
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', False),
        ])
        bloqueo = motivo_bloqueo_reversion(tareas[0])
        assert bloqueo is not None
        assert bloqueo.puede_escapar is True

        from app.routes.api_expedientes import _candado_diagnostico_producido
        resp, status = _candado_diagnostico_producido(tareas[0])
        payload = resp.get_json()
        assert 'superado' in payload['motivo'].lower()
        # El candado en sí sigue sin ser forzable, aunque la reversión sí lo sea.
        assert payload['puede_escapar'] is False

    def test_ya_notificado_devuelve_motivo_puerta_cerrada(self, arbol_esftt):
        from app.services.diagnosticos import motivo_bloqueo_reversion

        fase, tareas = _montar_cadena_subsanacion([
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', None, True),
        ])
        bloqueo = motivo_bloqueo_reversion(tareas[0])
        assert bloqueo is not None
        assert bloqueo.puede_escapar is False

        from app.routes.api_expedientes import _candado_diagnostico_producido
        resp, status = _candado_diagnostico_producido(tareas[0])
        payload = resp.get_json()
        assert 'comunicado al titular' in payload['motivo']
        assert payload['puede_escapar'] is False
