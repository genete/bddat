"""
Tests #776 — disparo del plazo de ELABORAR de COMUNICACION_INICIO_ADMISION
(art. 21.4 LPACAP): la solicitud si no hubo requerimiento previo en la fase,
la última subsanación si lo hubo.

Monta el árbol de verdad en BD (mismo patrón que test_717_consumido_diagnostico.py:
app_ctx con rollback por SAVEPOINT) porque `tramite_anterior_en_fase` depende de
relaciones reales (fase.tramites) que un stub no reproduce fielmente.
"""
import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _fase_con_analisis_documental(solicitud):
    """Fase ANALISIS_SOLICITUD con un ANALISIS_DOCUMENTAL ya creado (primer
    trámite, sin requerimiento todavía)."""
    from app import db
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
    db.session.add(fase)
    db.session.flush()

    tramite_analisis = Tramite(fase_id=fase.id,
                               tipo_tramite_id=_tipo(TipoTramite, 'ANALISIS_DOCUMENTAL').id)
    db.session.add(tramite_analisis)
    db.session.flush()
    return fase, tramite_analisis


def _tramite_comunicacion_con_elaborar(fase):
    from app import db
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    tramite = Tramite(fase_id=fase.id,
                      tipo_tramite_id=_tipo(TipoTramite, 'COMUNICACION_INICIO_ADMISION').id)
    db.session.add(tramite)
    db.session.flush()

    tarea_elaborar = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, 'ELABORAR').id)
    db.session.add(tarea_elaborar)
    db.session.flush()
    return tramite, tarea_elaborar


def _añadir_requerimiento_con_subsanacion(fase):
    """Añade a la fase un REQUERIMIENTO_SUBSANACION con su ESPERAR_PLAZO
    produciendo el documento SUBSANACION —el que cumple el plazo del art.
    68.1 LPACAP, catalogo_plazos, `ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/
    ESPERAR_PLAZO`— y su ANALIZAR (#825: la SUBSANACION no cubre ningún
    requisito documental, así que el ANALIZAR no la consume). Devuelve el
    documento SUBSANACION."""
    from app import db
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_documentos import TipoDocumento

    tramite_req = Tramite(fase_id=fase.id,
                          tipo_tramite_id=_tipo(TipoTramite, 'REQUERIMIENTO_SUBSANACION').id)
    db.session.add(tramite_req)
    db.session.flush()

    doc_subsanacion = Documento(
        expediente_id=fase.solicitud.expediente_id,
        tipo_doc_id=_tipo(TipoDocumento, 'SUBSANACION').id,
        url='bddat://test-776/subsanacion',
    )
    db.session.add(doc_subsanacion)
    db.session.flush()

    tarea_esperar_plazo = Tarea(tramite_id=tramite_req.id, tipo_tarea_id=_tipo(TipoTarea, 'ESPERAR_PLAZO').id)
    db.session.add(tarea_esperar_plazo)
    db.session.flush()
    db.session.add(DocumentoTarea(tarea_id=tarea_esperar_plazo.id, documento_id=doc_subsanacion.id, rol='PRODUCIDO'))

    tarea_analizar = Tarea(tramite_id=tramite_req.id, tipo_tarea_id=_tipo(TipoTarea, 'ANALIZAR').id)
    db.session.add(tarea_analizar)
    db.session.flush()

    return doc_subsanacion


def _solicitud_con_documento(app_ctx):
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    if solicitud.documento_solicitud_id is None:
        doc = Documento(
            expediente_id=solicitud.expediente_id,
            tipo_doc_id=_tipo(TipoDocumento, 'MODELO_SOLICITUD').id,
            url='bddat://test-776/modelo-solicitud',
        )
        db.session.add(doc)
        db.session.flush()
        solicitud.documento_solicitud_id = doc.id
        db.session.flush()
    return solicitud


# ---------------------------------------------------------------------------
# documento_disparo_comunicacion_admision
# ---------------------------------------------------------------------------

class TestDocumentoDisparoComunicacionAdmision:

    def test_sin_requerimiento_devuelve_documento_solicitud(self, app_ctx):
        from app.services.invariantes_esftt import documento_disparo_comunicacion_admision

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        tramite, _ = _tramite_comunicacion_con_elaborar(fase)

        doc = documento_disparo_comunicacion_admision(tramite)

        assert doc is not None
        assert doc.id == solicitud.documento_solicitud_id

    def test_con_requerimiento_devuelve_documento_subsanacion(self, app_ctx):
        from app.services.invariantes_esftt import documento_disparo_comunicacion_admision

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        doc_subsanacion = _añadir_requerimiento_con_subsanacion(fase)
        tramite, _ = _tramite_comunicacion_con_elaborar(fase)

        doc = documento_disparo_comunicacion_admision(tramite)

        assert doc is not None
        assert doc.id == doc_subsanacion.id

    def test_con_requerimiento_ignora_los_consumidos_del_analizar(self, app_ctx):
        """Regresión #825: antes se leía `consumidos[0]` del ANALIZAR, que ni
        siquiera incluye el escrito de subsanación (no cubre ningún requisito
        documental) y puede acumular anexos de vueltas anteriores (#826). El
        criterio correcto —el PRODUCIDO de la ESPERAR_PLAZO— no depende en
        absoluto de esos vínculos."""
        from app import db
        from app.services.invariantes_esftt import documento_disparo_comunicacion_admision
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.tipos_documentos import TipoDocumento

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        doc_subsanacion = _añadir_requerimiento_con_subsanacion(fase)

        # El ANALIZAR de esa misma vuelta consume un anexo ajeno (p.ej. NIF_TITULAR),
        # nunca la propia SUBSANACION — simula el escenario real de AT-19.
        tramite_req = next(t for t in fase.tramites if t.tipo_tramite.codigo == 'REQUERIMIENTO_SUBSANACION')
        tarea_analizar = next(t for t in tramite_req.tareas if t.tipo_tarea.codigo == 'ANALIZAR')
        doc_anexo = Documento(
            expediente_id=solicitud.expediente_id,
            tipo_doc_id=_tipo(TipoDocumento, 'NIF_TITULAR').id,
            url='bddat://test-776/anexo',
        )
        db.session.add(doc_anexo)
        db.session.flush()
        db.session.add(DocumentoTarea(tarea_id=tarea_analizar.id, documento_id=doc_anexo.id, rol='CONSUMIDO'))
        db.session.flush()

        tramite, _ = _tramite_comunicacion_con_elaborar(fase)

        doc = documento_disparo_comunicacion_admision(tramite)

        assert doc is not None
        assert doc.id == doc_subsanacion.id

    def test_primer_tramite_de_la_fase_devuelve_documento_solicitud(self, app_ctx):
        """Caso degenerado: COMUNICACION_INICIO_ADMISION es el primer trámite
        de su fase (no debería ocurrir en el flujo normal, pero no debe romper)."""
        from app import db
        from app.services.invariantes_esftt import documento_disparo_comunicacion_admision
        from app.models.fases import Fase
        from app.models.tipos_fases import TipoFase

        solicitud = _solicitud_con_documento(app_ctx)
        fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
        db.session.add(fase)
        db.session.flush()
        tramite, _ = _tramite_comunicacion_con_elaborar(fase)

        doc = documento_disparo_comunicacion_admision(tramite)

        assert doc is not None
        assert doc.id == solicitud.documento_solicitud_id


# ---------------------------------------------------------------------------
# Hook #776 — llamado directamente
# ---------------------------------------------------------------------------

class TestHook776Derivacion:

    def test_sin_requerimiento_vincula_documento_solicitud(self, app_ctx):
        from app.services.mutaciones_arbol import _hook_776_elaborar_consume_disparo_admision

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        _, tarea_elaborar = _tramite_comunicacion_con_elaborar(fase)

        advertencia = _hook_776_elaborar_consume_disparo_admision(tarea_elaborar)

        assert advertencia is not None
        assert 'automátic' in advertencia['motivo']
        consumidos = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(consumidos) == 1
        assert consumidos[0].documento_id == solicitud.documento_solicitud_id

    def test_con_requerimiento_vincula_documento_subsanacion(self, app_ctx):
        from app.services.mutaciones_arbol import _hook_776_elaborar_consume_disparo_admision

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        doc_subsanacion = _añadir_requerimiento_con_subsanacion(fase)
        _, tarea_elaborar = _tramite_comunicacion_con_elaborar(fase)

        advertencia = _hook_776_elaborar_consume_disparo_admision(tarea_elaborar)

        assert advertencia is not None
        consumidos = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(consumidos) == 1
        assert consumidos[0].documento_id == doc_subsanacion.id

    def test_no_dispara_para_otro_tramite(self, app_ctx):
        """Un ELABORAR de otro trámite (p.ej. REQUERIMIENTO_SUBSANACION) no se ve afectado."""
        from app import db
        from app.services.mutaciones_arbol import _hook_776_elaborar_consume_disparo_admision
        from app.models.tramites import Tramite
        from app.models.tareas import Tarea
        from app.models.tipos_tramites import TipoTramite
        from app.models.tipos_tareas import TipoTarea

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)

        tramite_req = Tramite(fase_id=fase.id,
                              tipo_tramite_id=_tipo(TipoTramite, 'REQUERIMIENTO_SUBSANACION').id)
        db.session.add(tramite_req)
        db.session.flush()
        tarea_elaborar = Tarea(tramite_id=tramite_req.id, tipo_tarea_id=_tipo(TipoTarea, 'ELABORAR').id)
        db.session.add(tarea_elaborar)
        db.session.flush()

        advertencia = _hook_776_elaborar_consume_disparo_admision(tarea_elaborar)

        assert advertencia is None
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_no_dispara_para_otra_tarea(self, app_ctx):
        """Una tarea NOTIFICAR de COMUNICACION_INICIO_ADMISION no se ve afectada."""
        from app import db
        from app.services.mutaciones_arbol import _hook_776_elaborar_consume_disparo_admision
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)
        tramite, _ = _tramite_comunicacion_con_elaborar(fase)

        tarea_notificar = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, 'NOTIFICAR').id)
        db.session.add(tarea_notificar)
        db.session.flush()

        advertencia = _hook_776_elaborar_consume_disparo_admision(tarea_notificar)

        assert advertencia is None
        assert not [v for v in tarea_notificar.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_sin_documento_solicitud_no_bloquea(self, app_ctx):
        """Degradación: si la solicitud aún no tiene documento_solicitud, el
        hook no vincula nada y no lanza excepción — el plazo simplemente
        quedará SIN_PLAZO hasta que exista el documento."""
        from app.models.solicitudes import Solicitud
        from app.services.mutaciones_arbol import _hook_776_elaborar_consume_disparo_admision

        solicitud = Solicitud.query.first()
        if solicitud is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        solicitud.documento_solicitud_id = None

        fase, _ = _fase_con_analisis_documental(solicitud)
        _, tarea_elaborar = _tramite_comunicacion_con_elaborar(fase)

        advertencia = _hook_776_elaborar_consume_disparo_admision(tarea_elaborar)

        assert advertencia is None
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']


# ---------------------------------------------------------------------------
# Integración: crear_tarea() dispara el hook automáticamente
# ---------------------------------------------------------------------------

class TestIntegracionCrearTarea:

    def test_crear_tarea_elaborar_deriva_el_vinculo(self, app_ctx):
        from flask_login import login_user
        from app import db
        from app.models.usuarios import Usuario
        from app.models.tramites import Tramite
        from app.models.tipos_tramites import TipoTramite
        from app.services.mutaciones_arbol import crear_tarea
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        solicitud = _solicitud_con_documento(app_ctx)
        fase, _ = _fase_con_analisis_documental(solicitud)

        tramite2 = Tramite(fase_id=fase.id,
                           tipo_tramite_id=_tipo(TipoTramite, 'COMUNICACION_INICIO_ADMISION').id)
        db.session.add(tramite2)
        db.session.flush()

        with app_ctx.test_request_context():
            login_user(usuario)
            resultado = crear_tarea(tramite2, _tipo(TipoTarea, 'ELABORAR'), justificacion='test #776')

        assert resultado.ok is True
        tarea = Tarea.query.get(resultado.ids[0])
        consumidos = [v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(consumidos) == 1
        assert consumidos[0].documento_id == solicitud.documento_solicitud_id
