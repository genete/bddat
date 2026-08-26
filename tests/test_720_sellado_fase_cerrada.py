"""
Tests #720 — sellado de fase cerrada (ADR-036).

Monta el árbol de verdad en BD (mismo patrón que test_722/test_714: app_ctx
con SAVEPOINT — join_transaction_mode='create_savepoint' reabre el savepoint
tras cada commit del código de aplicación, ver conftest) porque
check_invariante('MUTAR'/'REABRIR', ...) y el hook de sesión consultan
relaciones reales. `current_user` necesita contexto de petición real donde
hace falta (reabrir_fase con éxito registra bitácora) — test_request_context
anidado, mismo patrón que test_714/test_616.

Ejes que cubren:
  - check_invariante('MUTAR', ...) bloquea FASE/TRAMITE/TAREA bajo una fase
    cerrada; permite bajo una fase abierta (control) — ADR-036 §7.
  - editar_fase bloquea reeditar el resultado tras el cierre sin pasar por
    reabrir_fase antes: el bug concreto verificado en AT-2004.
  - reabrir_fase: caso normal (éxito + bitácora), sin justificación, fase no
    cerrada, puerta cerrada (solicitud ya resuelta y notificada, ADR-036 §4).
  - Hook de sesión (capa 3, sellado_fase_sesion.py): escritura directa en
    DocumentoTarea/Tarea/OrganismoExpediente (#396) sin pasar por el servicio,
    bajo fase cerrada, queda bloqueada; bajo fase abierta no interfiere (control).
  - Endpoint HTTP POST .../nodo/fase/<id>/reabrir: camino feliz + rechazo sin
    justificación (BD real, limpieza manual — mismo patrón que
    TestRevertirDiagnosticoCircuito de test_678).
"""
from datetime import date

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _fase_con_tramite_y_tarea(codigo_tipo_tramite, codigo_tipo_tarea,
                               *, tipo_fase_codigo='ANALISIS_SOLICITUD'):
    """Monta Fase → Trámite → Tarea sobre la primera solicitud de la BD de desarrollo.

    Devuelve (solicitud, fase, tramite, tarea). Mismo patrón que test_722.
    """
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, tipo_fase_codigo).id)
    db.session.add(fase)
    db.session.flush()

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=_tipo(TipoTramite, codigo_tipo_tramite).id)
    db.session.add(tramite)
    db.session.flush()

    tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, codigo_tipo_tarea).id)
    db.session.add(tarea)
    db.session.flush()

    return solicitud, fase, tramite, tarea


def _cerrar_fase(fase):
    """Fija documento_resultado_id (+ resultado_fase_id si hay catálogo) directo,
    sin pasar por editar_fase — solo prepara el escenario, no ejercita el cierre."""
    from app import db
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    from app.models.tipos_resultados_fases import TipoResultadoFase

    tipo_doc = TipoDocumento.query.first()
    if tipo_doc is None:
        pytest.skip('No hay tipos de documento en el catálogo')
    solicitud = fase.solicitud
    doc = Documento(expediente_id=solicitud.expediente_id, tipo_doc_id=tipo_doc.id,
                     url=f'bddat://test-720/cierre-{fase.id}')
    db.session.add(doc)
    db.session.flush()
    fase.documento_resultado_id = doc.id
    tipo_res = TipoResultadoFase.query.first()
    if tipo_res is not None:
        fase.resultado_fase_id = tipo_res.id
    db.session.flush()
    return doc


# ---------------------------------------------------------------------------
# check_invariante('MUTAR', ...) — capa 2 (servicio de dominio)
# ---------------------------------------------------------------------------

class TestCheckInvarianteMutar:

    def test_fase_cerrada_bloquea(self, app_ctx):
        from app.services.invariantes_esftt import check_invariante

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        res = check_invariante('MUTAR', 'FASE', fase.id)
        assert res is not None
        assert 'cerrada' in res.norma_compilada
        assert res.puede_escapar is False

    def test_tramite_bajo_fase_cerrada_bloquea(self, app_ctx):
        from app.services.invariantes_esftt import check_invariante

        _, fase, tramite, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        assert check_invariante('MUTAR', 'TRAMITE', tramite.id) is not None

    def test_tarea_bajo_fase_cerrada_bloquea(self, app_ctx):
        from app.services.invariantes_esftt import check_invariante

        _, fase, _, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        assert check_invariante('MUTAR', 'TAREA', tarea.id) is not None

    def test_fase_abierta_no_bloquea(self, app_ctx):
        """Control: sin cierre, ningún nivel bloquea — no hay falso positivo."""
        from app.services.invariantes_esftt import check_invariante

        _, fase, tramite, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')

        assert check_invariante('MUTAR', 'FASE', fase.id) is None
        assert check_invariante('MUTAR', 'TRAMITE', tramite.id) is None
        assert check_invariante('MUTAR', 'TAREA', tarea.id) is None


# ---------------------------------------------------------------------------
# editar_fase — bloquea reescritura tras cierre sin reabrir (AT-2004)
# ---------------------------------------------------------------------------

class TestEditarFaseBloqueaTrasCierre:

    def test_reeditar_resultado_tras_cierre_bloqueado(self, app_ctx):
        """El bug concreto verificado en AT-2004 (fase 8): cerrada la fase, volver
        a llamar editar_fase sin pasar por reabrir_fase antes debe bloquear."""
        from app.services import mutaciones_arbol as svc

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        doc = _cerrar_fase(fase)
        resultado_original = fase.resultado_fase_id

        res = svc.editar_fase(fase, resultado_fase_id=resultado_original,
                               documento_resultado_id=doc.id,
                               observaciones='intento tras cierre, no debería aplicarse')
        assert not res.ok
        assert res.bloqueo is not None
        assert 'cerrada' in res.bloqueo.norma_compilada
        assert fase.observaciones != 'intento tras cierre, no debería aplicarse'


# ---------------------------------------------------------------------------
# reabrir_fase — servicio de dominio
# ---------------------------------------------------------------------------

class TestReabrirFase:

    def test_caso_normal_exito(self, app_ctx):
        from flask_login import login_user
        from app import db
        from app.models.usuarios import Usuario
        from app.services import mutaciones_arbol as svc
        from sqlalchemy import text

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)
        fase_id = fase.id

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.reabrir_fase(fase, justificacion='motivo de prueba #720')

        assert res.ok
        assert fase.resultado_fase_id is None
        assert fase.documento_resultado_id is None
        assert not fase.finalizada

        fila = db.session.execute(text(
            "select operacion, detalle from bitacora "
            "where tabla='fases' and registro_id=:fid order by id desc limit 1"
        ), {'fid': fase_id}).fetchone()
        assert fila is not None
        assert fila[0] == 'ALTERAR'
        assert fila[1]['accion'] == 'REABRIR'
        assert fila[1]['justificacion'] == 'motivo de prueba #720'

    def test_sin_justificacion_rechaza(self, app_ctx):
        from app.services import mutaciones_arbol as svc

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        res = svc.reabrir_fase(fase, justificacion='')
        assert not res.ok
        assert fase.finalizada  # nada se tocó

    def test_fase_no_cerrada_rechaza(self, app_ctx):
        from app.services import mutaciones_arbol as svc

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')

        res = svc.reabrir_fase(fase, justificacion='motivo')
        assert not res.ok
        assert res.error == 'La fase no está cerrada.'

    def test_puerta_cerrada_solicitud_resuelta_notificada(self, app_ctx):
        """ADR-036 §4: si la solicitud ya está resuelta (todas sus fases cerradas)
        y notificada en su fase finalizadora, ninguna de sus fases se reabre —
        ni con justificación."""
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.fases import Fase
        from app.models.tramites import Tramite
        from app.models.tareas import Tarea
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_tramites import TipoTramite
        from app.models.tipos_tareas import TipoTarea
        from app.models.notificaciones import Notificacion
        from app.services import mutaciones_arbol as svc

        base = Solicitud.query.first()
        if base is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        tipo_fase_fin = TipoFase.query.filter_by(es_finalizadora=True).first()
        if tipo_fase_fin is None:
            pytest.skip('No hay TipoFase con es_finalizadora=True en el catálogo')

        solicitud = Solicitud(expediente_id=base.expediente_id, entidad_id=base.entidad_id,
                               tipo_solicitud_id=base.tipo_solicitud_id)
        db.session.add(solicitud)
        db.session.flush()

        fase_simple = Fase(solicitud_id=solicitud.id,
                            tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
        db.session.add(fase_simple)
        db.session.flush()
        _cerrar_fase(fase_simple)

        fase_fin = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo_fase_fin.id)
        db.session.add(fase_fin)
        db.session.flush()

        # Trámite/tarea/notificación se montan ANTES de cerrar fase_fin: el hook de
        # sesión (capa 3) bloquearía crearlos bajo una fase ya cerrada — igual que
        # bloquearía cualquier mutación real, aquí solo se prepara el escenario.
        tramite = Tramite(fase_id=fase_fin.id,
                           tipo_tramite_id=_tipo(TipoTramite, 'ANALISIS_DOCUMENTAL').id)
        db.session.add(tramite)
        db.session.flush()
        tarea_notif = Tarea(tramite_id=tramite.id,
                             tipo_tarea_id=_tipo(TipoTarea, 'NOTIFICAR').id)
        db.session.add(tarea_notif)
        db.session.flush()
        db.session.add(Notificacion(tarea_id=tarea_notif.id, canal='NOTIFICA',
                                     fecha_puesta_disposicion=date.today()))
        db.session.flush()

        _cerrar_fase(fase_fin)

        assert solicitud.estado.startswith('RESUELTA')

        res = svc.reabrir_fase(fase_simple, justificacion='lo necesito igualmente')
        assert not res.ok
        assert res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert fase_simple.finalizada

        res_fin = svc.reabrir_fase(fase_fin, justificacion='lo necesito igualmente')
        assert not res_fin.ok
        assert res_fin.bloqueo is not None
        assert fase_fin.finalizada


# ---------------------------------------------------------------------------
# Hook de sesión (capa 3) — before_flush sobre las 4 tablas
# ---------------------------------------------------------------------------

class TestHookSesion:

    def test_documento_tarea_directo_bajo_fase_cerrada_bloquea(self, app_ctx):
        """Simula el escenario que motivó la capa 3: un asignador automático que
        inserta directo en documentos_tarea sin pasar por editar_tarea."""
        from app import db
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.tipos_documentos import TipoDocumento
        from app.services.sellado_fase_sesion import SelladoFaseVioladoError

        _, fase, _, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        tipo_doc = TipoDocumento.query.first()
        if tipo_doc is None:
            pytest.skip('No hay tipos de documento en el catálogo')
        doc = Documento(expediente_id=fase.solicitud.expediente_id, tipo_doc_id=tipo_doc.id,
                         url=f'bddat://test-720/hook-{tarea.id}')
        db.session.add(doc)
        db.session.flush()

        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='CONSUMIDO'))
        with pytest.raises(SelladoFaseVioladoError):
            db.session.flush()

    def test_tarea_nueva_directa_bajo_fase_cerrada_bloquea(self, app_ctx):
        from app import db
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea
        from app.services.sellado_fase_sesion import SelladoFaseVioladoError

        _, fase, tramite, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        _cerrar_fase(fase)

        nueva = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, 'ELABORAR').id)
        db.session.add(nueva)
        with pytest.raises(SelladoFaseVioladoError):
            db.session.flush()

    def test_organismo_directo_bajo_fase_cerrada_bloquea(self, app_ctx):
        """#396: OrganismoExpediente cuelga de fase_id igual que Tramite — la
        capa 3 debe vigilarlo igual, no solo las capas 1/2 de mutaciones_arbol."""
        from app import db
        from app.models.fases import Fase
        from app.models.tipos_fases import TipoFase
        from app.models.entidad import Entidad
        from app.models.organismos_expediente import OrganismoExpediente
        from app.services.sellado_fase_sesion import SelladoFaseVioladoError

        solicitud, _, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'CONSULTAS').id)
        db.session.add(fase)
        db.session.flush()

        entidad = Entidad.query.filter_by(rol_consultado=True).first()
        if entidad is None:
            pytest.skip('No hay entidades rol_consultado=True en la BD de desarrollo')

        oe = OrganismoExpediente(expediente_id=solicitud.expediente_id, fase_id=fase.id,
                                  organismo_id=entidad.id, via='consulta')
        db.session.add(oe)
        db.session.flush()

        _cerrar_fase(fase)

        oe.resultado = 'cerrado_favorable'
        with pytest.raises(SelladoFaseVioladoError):
            db.session.flush()

    def test_bajo_fase_abierta_no_bloquea(self, app_ctx):
        """Control: sin fase cerrada, el hook no interfiere — no hay falso positivo."""
        from app import db
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea

        _, _, tramite, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        nueva = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, 'ELABORAR').id)
        db.session.add(nueva)
        db.session.flush()  # no debe lanzar
        assert nueva.id is not None


# ---------------------------------------------------------------------------
# Endpoint HTTP — POST .../nodo/fase/<id>/reabrir
# ---------------------------------------------------------------------------

class TestEndpointReabrirFase:
    """BD real (sin app_ctx: sin precedente de combinarlo con el test_client en
    esta suite) — limpieza manual en finally, mismo patrón que
    TestRevertirDiagnosticoCircuito (test_678)."""

    def _fase_cerrada_vacia(self, app):
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.fases import Fase
        from app.models.documentos import Documento
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_documentos import TipoDocumento

        with app.app_context():
            base = Solicitud.query.first()
            if base is None:
                pytest.skip('No hay solicitudes en la BD de desarrollo')
            tipo_fase = TipoFase.query.filter_by(codigo='ANALISIS_SOLICITUD').first()
            if tipo_fase is None:
                pytest.skip("TipoFase 'ANALISIS_SOLICITUD' no está en el catálogo")
            tipo_doc = TipoDocumento.query.first()
            if tipo_doc is None:
                pytest.skip('No hay tipos de documento en el catálogo')

            fase = Fase(solicitud_id=base.id, tipo_fase_id=tipo_fase.id)
            db.session.add(fase)
            db.session.flush()
            doc = Documento(expediente_id=base.expediente_id, tipo_doc_id=tipo_doc.id,
                             url=f'bddat://test-720/http-{fase.id}')
            db.session.add(doc)
            db.session.flush()
            fase.documento_resultado_id = doc.id
            db.session.commit()
            return base.expediente_id, fase.id, doc.id

    def _limpiar(self, app, fase_id, doc_id):
        from app import db
        from app.models.fases import Fase
        from app.models.documentos import Documento
        with app.app_context():
            db.session.rollback()
            Fase.query.filter_by(id=fase_id).delete()
            Documento.query.filter_by(id=doc_id).delete()
            db.session.commit()

    def test_reabrir_exito_via_http(self, usuario_supervisor, app):
        exp_id, fase_id, doc_id = self._fase_cerrada_vacia(app)
        try:
            r = usuario_supervisor.post(
                f'/api/expedientes/{exp_id}/nodo/fase/{fase_id}/reabrir',
                json={'justificacion': 'test #720 endpoint'})
            assert r.status_code == 200
            assert r.get_json()['ok'] is True
            with app.app_context():
                from app.models.fases import Fase
                assert Fase.query.get(fase_id).documento_resultado_id is None
        finally:
            self._limpiar(app, fase_id, doc_id)

    def test_reabrir_sin_justificacion_422(self, usuario_supervisor, app):
        exp_id, fase_id, doc_id = self._fase_cerrada_vacia(app)
        try:
            r = usuario_supervisor.post(
                f'/api/expedientes/{exp_id}/nodo/fase/{fase_id}/reabrir', json={})
            assert r.status_code == 422
        finally:
            self._limpiar(app, fase_id, doc_id)
