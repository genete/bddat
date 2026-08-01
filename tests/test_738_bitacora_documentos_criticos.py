"""
Tests #738 — bitácora y guardas de documentos justificante (JUSTIFICANTE_*).

Contexto: desvincular o borrar el justificante de una notificación (o de
cualquier publicación BOE/BOP/BOJA/PRENSA/PORTAL) era completamente silencioso
— sin bitácora, sin guarda temprana. El issue no cierra ninguna puerta (la
vinculación pudo hacerse por error): solo exige que quede rastro.

Cuatro frentes, cada uno en su propia clase:
  1. editar_tarea registra en bitácora al desvincular un documento crítico
     (mismo patrón app_ctx SAVEPOINT + test_request_context/login_user que
     test_720, porque la bitácora necesita current_user real).
  2. _documento_es_referenciado (routes.py) mira también doc.notificacion —
     bugfix directo, sin current_user de por medio.
  3. pool_borrar_documento registra en bitácora al borrar un documento crítico
     permitido — vía HTTP real (BD real, limpieza manual, mismo patrón que
     TestEndpointReabrirFase de test_720/test_678).
  4. advertir_documentos_criticos_huerfanos (invariantes_esftt.py) y su enganche
     en editar_fase — guarda temprana no bloqueante (ADVERTIR).
"""
from datetime import date

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _tipo_doc_critico(codigo='JUSTIFICANTE_NOTIFICA'):
    from app.models.tipos_documentos import TipoDocumento
    return _tipo(TipoDocumento, codigo)


def _tipo_doc_generico():
    from app.models.tipos_documentos import TipoDocumento
    tipo = TipoDocumento.query.filter(~TipoDocumento.codigo.like('JUSTIFICANTE_%')).first()
    if tipo is None:
        pytest.skip('No hay tipos de documento ajenos a JUSTIFICANTE_* en el catálogo')
    return tipo


def _fase_con_tramite_y_tarea(codigo_tipo_tramite, codigo_tipo_tarea,
                               *, tipo_fase_codigo='ANALISIS_SOLICITUD'):
    """Monta Fase → Trámite → Tarea sobre la primera solicitud de la BD de
    desarrollo. Mismo patrón que test_720/test_722."""
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


def _documento(expediente_id, tipo_doc_id, *, url=None):
    from app import db
    from app.models.documentos import Documento
    doc = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_doc_id,
                     url=url or f'bddat://test-738/doc-{id(object())}')
    db.session.add(doc)
    db.session.flush()
    return doc


# ---------------------------------------------------------------------------
# 1) editar_tarea — bitácora al desvincular un documento crítico (punto 1)
# ---------------------------------------------------------------------------

class TestBitacoraDesvincularDocumentoCritico:

    def test_desvincular_producido_critico_registra_bitacora(self, app_ctx):
        from flask_login import login_user
        from app import db
        from app.models.usuarios import Usuario
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.notificaciones import Notificacion
        from app.services import mutaciones_arbol as svc
        from sqlalchemy import text

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        _, _, tramite, tarea = _fase_con_tramite_y_tarea(
            _primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc = _tipo_doc_critico('JUSTIFICANTE_NOTIFICA')
        doc = _documento(expediente_id, tipo_doc.id)

        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.add(Notificacion(
            tarea_id=tarea.id, documento_id=doc.id, canal='NOTIFICA',
            identificador_envio='82541676', fecha_puesta_disposicion=date(2026, 5, 28),
            resultado='CORRECTA',
        ))
        db.session.flush()
        tarea_id, doc_id = tarea.id, doc.id

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.editar_tarea(
                tarea, documentos_consumidos_ids=[], documento_producido_id=None, notas=None)

        assert res.ok is True

        # El vínculo estructural desaparece...
        assert DocumentoTarea.query.filter_by(tarea_id=tarea_id, documento_id=doc_id).first() is None
        # ...pero la fila Notificacion sigue viva (el hueco original, #738 contexto):
        # esto es justo lo que ya no debe pasar en silencio.
        assert Notificacion.query.filter_by(tarea_id=tarea_id).first() is not None

        fila = db.session.execute(text(
            "select operacion, detalle from bitacora "
            "where tabla='tareas' and registro_id=:tid order by id desc limit 1"
        ), {'tid': tarea_id}).fetchone()
        assert fila is not None
        assert fila[0] == 'ALTERAR'
        assert fila[1]['accion'] == 'DESVINCULAR_DOCUMENTO_CRITICO'
        assert fila[1]['documento_id'] == doc_id
        assert fila[1]['tipo_documento'] == 'JUSTIFICANTE_NOTIFICA'
        assert fila[1]['rol'] == 'PRODUCIDO'

    def test_desvincular_documento_generico_no_registra_bitacora(self, app_ctx):
        """Control negativo: un documento sin prefijo JUSTIFICANTE_ no genera
        rastro — la bitácora no debe llenarse de ruido para vínculos ordinarios."""
        from flask_login import login_user
        from app import db
        from app.models.usuarios import Usuario
        from app.models.documentos_tarea import DocumentoTarea
        from app.services import mutaciones_arbol as svc
        from sqlalchemy import text

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        _, _, tramite, tarea = _fase_con_tramite_y_tarea(
            _primer_tipo_tramite_codigo(), 'ELABORAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc = _tipo_doc_generico()
        doc = _documento(expediente_id, tipo_doc.id)

        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()
        tarea_id = tarea.id

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.editar_tarea(
                tarea, documentos_consumidos_ids=[], documento_producido_id=None, notas=None)

        assert res.ok is True
        fila = db.session.execute(text(
            "select id from bitacora where tabla='tareas' and registro_id=:tid "
            "and detalle->>'accion' = 'DESVINCULAR_DOCUMENTO_CRITICO'"
        ), {'tid': tarea_id}).fetchone()
        assert fila is None


def _primer_tipo_tramite_codigo():
    from app.models.tipos_tramites import TipoTramite
    tipo = TipoTramite.query.first()
    if tipo is None:
        pytest.skip('No hay tipos de trámite en el catálogo')
    return tipo.codigo


# ---------------------------------------------------------------------------
# 2) _documento_es_referenciado — mira doc.notificacion (punto 2, bugfix)
# ---------------------------------------------------------------------------

class TestDocumentoEsReferenciadoNotificacion:

    def test_documento_con_notificacion_huerfana_es_referenciado(self, app_ctx):
        """El escenario exacto del bug: Notificacion.documento_id apunta a un
        documento que ya no tiene ningún DocumentoTarea (desvinculado, punto 1).
        Antes del fix esto pasaba desapercibido y el borrado se permitía."""
        from app import db
        from app.models.notificaciones import Notificacion
        from app.modules.expedientes.routes import _documento_es_referenciado

        _, _, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc = _tipo_doc_critico('JUSTIFICANTE_NOTIFICA')
        doc = _documento(expediente_id, tipo_doc.id)

        db.session.add(Notificacion(
            tarea_id=tarea.id, documento_id=doc.id, canal='NOTIFICA',
            fecha_puesta_disposicion=date(2026, 5, 28), resultado='CORRECTA',
        ))
        db.session.flush()

        assert doc.vinculos_tarea == []  # sin vínculo estructural — el estado del bug
        assert _documento_es_referenciado(doc) is True

    def test_documento_libre_no_es_referenciado(self, app_ctx):
        """Control: sin proyecto, sin vínculo de tarea y sin notificación → libre."""
        from app.modules.expedientes.routes import _documento_es_referenciado

        _, _, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento(expediente_id, _tipo_doc_critico('JUSTIFICANTE_NOTIFICA').id)

        assert _documento_es_referenciado(doc) is False


# ---------------------------------------------------------------------------
# 3) pool_borrar_documento — bitácora al borrar documento crítico permitido
#    (punto 3). Vía HTTP real: BD real, limpieza manual (mismo patrón que
#    TestEndpointReabrirFase de test_720).
# ---------------------------------------------------------------------------

class TestBitacoraBorrarDocumentoCriticoPool:

    def _documento_critico_suelto(self, app):
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.documentos import Documento
        from app.models.tipos_documentos import TipoDocumento

        with app.app_context():
            base = Solicitud.query.first()
            if base is None:
                pytest.skip('No hay solicitudes en la BD de desarrollo')
            tipo_doc = TipoDocumento.query.filter_by(codigo='JUSTIFICANTE_BOE').first()
            if tipo_doc is None:
                pytest.skip("TipoDocumento 'JUSTIFICANTE_BOE' no está en el catálogo")

            doc = Documento(expediente_id=base.expediente_id, tipo_doc_id=tipo_doc.id,
                             url='bddat://test-738/pool-suelto')
            db.session.add(doc)
            db.session.commit()
            return base.expediente_id, doc.id

    def _limpiar(self, app, doc_id):
        from app import db
        from app.models.documentos import Documento
        with app.app_context():
            db.session.rollback()
            Documento.query.filter_by(id=doc_id).delete()
            db.session.commit()

    def test_borrar_documento_critico_permitido_registra_bitacora(self, usuario_supervisor, app):
        from sqlalchemy import text
        exp_id, doc_id = self._documento_critico_suelto(app)
        try:
            r = usuario_supervisor.post(f'/expedientes/{exp_id}/documentos/{doc_id}/borrar')
            assert r.status_code == 200
            assert r.get_json()['ok'] is True

            with app.app_context():
                from app import db
                from app.models.documentos import Documento
                assert Documento.query.get(doc_id) is None

                fila = db.session.execute(text(
                    "select operacion, detalle from bitacora "
                    "where tabla='documentos' and registro_id=:did order by id desc limit 1"
                ), {'did': doc_id}).fetchone()
                assert fila is not None
                assert fila[0] == 'BORRAR'
                assert fila[1]['tipo_documento'] == 'JUSTIFICANTE_BOE'
        finally:
            self._limpiar(app, doc_id)


# ---------------------------------------------------------------------------
# 4) advertir_documentos_criticos_huerfanos — guarda temprana ADVERTIR (punto 4)
# ---------------------------------------------------------------------------

class TestAdvertenciaDocumentosCriticosHuerfanos:

    def test_documento_critico_huerfano_genera_advertencia(self, app_ctx):
        from app.services.invariantes_esftt import advertir_documentos_criticos_huerfanos

        _, _, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento(expediente_id, _tipo_doc_critico('JUSTIFICANTE_BOE').id,
                          url='bddat://test-738/huerfano')

        advertencia = advertir_documentos_criticos_huerfanos(expediente_id)
        assert advertencia is not None
        assert 'motivo' in advertencia

    def test_sin_documentos_huerfanos_no_advierte(self, app_ctx):
        from app.services.invariantes_esftt import advertir_documentos_criticos_huerfanos

        _, _, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id

        assert advertir_documentos_criticos_huerfanos(expediente_id) is None

    def test_documento_critico_vinculado_no_es_huerfano(self, app_ctx):
        """Control: el mismo tipo de documento, pero con vínculo DocumentoTarea
        activo, no debe contar como huérfano."""
        from app import db
        from app.models.documentos_tarea import DocumentoTarea
        from app.services.invariantes_esftt import advertir_documentos_criticos_huerfanos

        _, _, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        doc = _documento(expediente_id, _tipo_doc_critico('JUSTIFICANTE_BOE').id,
                          url='bddat://test-738/vinculado')
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()

        assert advertir_documentos_criticos_huerfanos(expediente_id) is None

    def test_editar_fase_propaga_advertencia_al_cerrar(self, app_ctx):
        """Integración: cerrar una fase con un justificante huérfano en el pool
        del expediente devuelve advertencia no bloqueante (ADVERTIR, no BLOQUEAR
        — el pool es del expediente, no de esta fase)."""
        from app import db
        from app.services import mutaciones_arbol as svc

        _, fase, _, tarea = _fase_con_tramite_y_tarea(_primer_tipo_tramite_codigo(), 'NOTIFICAR')
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc_generico = _tipo_doc_generico()
        doc_cierre = _documento(expediente_id, tipo_doc_generico.id, url='bddat://test-738/cierre')
        _documento(expediente_id, _tipo_doc_critico('JUSTIFICANTE_BOE').id,
                   url='bddat://test-738/huerfano-cierre')
        db.session.flush()

        res = svc.editar_fase(fase, resultado_fase_id=None,
                               documento_resultado_id=doc_cierre.id, observaciones=None)

        assert res.ok is True
        assert res.advertencia is not None
        assert 'motivo' in res.advertencia
