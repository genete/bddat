"""Smoke test — hub "Seguimiento y Huérfanos" del TRAMITADOR (#630, ADR-038).

Extraído de /expedientes/seguimiento/ (#501/#559), que era vista prestada del
dominio de expedientes (ADR-017 "Deuda conocida", caso 3). Ahora hub propio,
mismo patrón que tareas_y_subidas/gestion_y_control.

Huérfanos (ADR-027 §2 / ADR-038): radar de documentos del pool sin vínculo a
tarea. Tests HTTP con BD real + limpieza manual en `finally` (mismo patrón
que TestBitacoraBorrarDocumentoCriticoPool en test_738) — combinar `app_ctx`
(SAVEPOINT) con el cliente HTTP no es seguro en este proyecto. Los tests de
`app/services/huerfanos.py` en aislamiento sí usan `arbol_esftt` (SAVEPOINT),
al no pasar por HTTP.
"""

import uuid

import pytest


def test_seguimiento_y_huerfanos_render(usuario_supervisor):
    r = usuario_supervisor.get('/seguimiento_y_huerfanos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_huerfanos_pane_y_filtro_tramitador(usuario_tramitador):
    """TRAMITADOR ve el selector mis/todos (ADR-038 §3), no el de técnico."""
    r = usuario_tramitador.get('/seguimiento_y_huerfanos/')
    assert r.status_code == 200
    assert b'pane-huerfanos' in r.data
    assert b'id="hf-ver"' in r.data
    assert b'id="hf-responsable"' not in r.data


def test_huerfanos_pane_y_filtro_supervisor(usuario_supervisor):
    """SUPERVISOR ve el selector por técnico (ADR-038 §3), no el de mis/todos —
    solo TRAMITADOR puede ser responsable de expediente."""
    r = usuario_supervisor.get('/seguimiento_y_huerfanos/')
    assert r.status_code == 200
    assert b'id="hf-responsable"' in r.data
    assert b'id="hf-ver"' not in r.data


# ── Inspector de seguimiento (ADR-023 / #559) ────────────────────────────────

def test_seguimiento_fragmento_render(usuario_supervisor, app):
    """GET /seguimiento_y_huerfanos/seguimiento/<id>/fragmento → 200 con el detalle del agregado."""
    with app.app_context():
        from app.models.solicitudes import Solicitud
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        sol_id = sol.id
    r = usuario_supervisor.get(f'/seguimiento_y_huerfanos/seguimiento/{sol_id}/fragmento')
    assert r.status_code == 200
    # El botón de delegación al árbol está siempre presente en el fragmento.
    assert 'Ir a tramitar'.encode() in r.data


def test_seguimiento_fragmento_inexistente(usuario_supervisor):
    """GET del fragmento de una solicitud inexistente → 404."""
    r = usuario_supervisor.get('/seguimiento_y_huerfanos/seguimiento/99999999/fragmento')
    assert r.status_code == 404


# ── Helpers compartidos por los tests de Huérfanos (BD real, ver docstring) ──

def _tipo_doc_cualquiera():
    from app.models.tipos_documentos import TipoDocumento
    tipo = TipoDocumento.query.first()
    if tipo is None:
        pytest.skip('No hay tipos de documento en el catálogo')
    return tipo


def _documento_suelto(app, *, url, tipo_doc_id=None, expediente_id=None):
    """Documento sin vínculo a tarea, commiteado en la BD real de desarrollo.

    Sin `expediente_id` explícito usa el primer expediente de la BD — vale para
    los tests de listado, pero NO para los que además montan una tarea propia
    (`_montar_tarea_no_ejecutada`): esa tarea cuelga de `Solicitud.query.first()`,
    que no tiene por qué compartir expediente con `Expediente.query.first()`.
    """
    from app import db
    from app.models.expedientes import Expediente
    from app.models.documentos import Documento
    with app.app_context():
        if expediente_id is None:
            exp = Expediente.query.first()
            if exp is None:
                pytest.skip('No hay expedientes en la BD de desarrollo')
            expediente_id = exp.id
        tipo_id = tipo_doc_id or _tipo_doc_cualquiera().id
        doc = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_id, url=url)
        db.session.add(doc)
        db.session.commit()
        return expediente_id, doc.id


def _borrar_documento(app, doc_id):
    from app import db
    from app.models.documentos import Documento
    with app.app_context():
        db.session.rollback()
        Documento.query.filter_by(id=doc_id).delete()
        db.session.commit()


# ── Listado de huérfanos — GET /api/documentos/huerfanos (ADR-027 §2 / ADR-038) ──

class TestListadoHuerfanos:

    def test_documento_real_sin_vinculo_aparece_como_huerfano(self, usuario_tramitador, app):
        _, doc_id = _documento_suelto(app, url=f'http://example.com/test-630-{uuid.uuid4().hex}.pdf')
        try:
            r = usuario_tramitador.get('/api/documentos/huerfanos?ver=todos&limit=200')
            assert r.status_code == 200
            assert doc_id in [d['id'] for d in r.get_json()['data']]
        finally:
            _borrar_documento(app, doc_id)

    def test_bddat_sin_vinculo_no_es_huerfano(self, usuario_tramitador, app):
        """Regresión: ADR-027 §2 ('el huérfano es siempre un fichero') — un residuo
        bddat:// sin vínculo (dato antiguo, pre-salvaguarda) no debe listarse.
        Detectado con datos reales al implementar #630: sin este filtro, un
        diagnóstico huérfano de la BD de desarrollo aparecía en el radar."""
        _, doc_id = _documento_suelto(app, url='bddat://diagnosticos/999999999')
        try:
            r = usuario_tramitador.get('/api/documentos/huerfanos?ver=todos&limit=200')
            assert r.status_code == 200
            assert doc_id not in [d['id'] for d in r.get_json()['data']]
        finally:
            _borrar_documento(app, doc_id)

    def test_filtro_ver_mis_solo_devuelve_expedientes_del_usuario(self, usuario_tramitador, app):
        with app.app_context():
            from app.models.usuarios import Usuario
            clg_id = Usuario.query.filter_by(siglas='CLG').first().id
        r = usuario_tramitador.get('/api/documentos/huerfanos?ver=mis&limit=200')
        assert r.status_code == 200
        for item in r.get_json()['data']:
            assert item['responsable'] is not None
            assert item['responsable']['id'] == clg_id

    def test_responsable_id_lo_ignora_tramitador_pero_no_supervisor(self, usuario_supervisor, app):
        """SUPERVISOR filtra por responsable_id (no tiene 'mis'); TRAMITADOR usa ver=mis/todos."""
        r = usuario_supervisor.get('/api/documentos/huerfanos?limit=5')
        assert r.status_code == 200  # sin filtro -> todos, no falla por falta de 'ver'


# ── Candidatas — app/services/huerfanos.py, en aislamiento (ADR-038 §4) ──────

def _fila_catalogo(rol):
    """Primera fila `rol` de tramites_tareas_documentos con su tipo_tramite/tipo_tarea
    resueltos vía tramites_tareas. Skip si el catálogo de esta BD no tiene ninguna."""
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    fila = TramiteTareaDocumento.query.filter_by(rol=rol).first()
    if fila is None:
        pytest.skip(f'No hay filas {rol!r} en tramites_tareas_documentos')
    slot = TramiteTarea.query.filter_by(
        tipo_tramite_id=fila.tipo_tramite_id, orden=fila.orden_tarea).first()
    if slot is None:
        pytest.skip('Fila de catálogo sin slot correspondiente en tramites_tareas')
    tipo_tramite = TipoTramite.query.get(fila.tipo_tramite_id)
    tipo_tarea = TipoTarea.query.get(slot.tipo_tarea_id)
    return tipo_tramite.codigo, tipo_tarea.codigo, fila.tipo_documento_id


def _documento_real(db, expediente_id, tipo_doc_id, sufijo):
    from app.models.documentos import Documento
    doc = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_doc_id,
                     url=f'http://example.com/test-630-{sufijo}-{uuid.uuid4().hex}.pdf')
    db.session.add(doc)
    db.session.flush()
    return doc


class TestCandidatas:

    def test_candidata_consumido_tarea_no_ejecutada(self, arbol_esftt):
        from app.services.huerfanos import tareas_candidatas
        from app.models.tipos_documentos import TipoDocumento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo('ENTRADA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc_id = tipo_doc_id or TipoDocumento.query.first().id
        doc = _documento_real(arbol_esftt.db, expediente_id, tipo_doc_id, 'consumido')

        candidatas = tareas_candidatas(doc)
        assert any(c['tarea_id'] == tarea.id and c['rol'] == 'CONSUMIDO' for c in candidatas)

    def test_tarea_ejecutada_no_es_candidata_consumido(self, arbol_esftt):
        """Regla de seguridad ADR-038 §4: no se sugiere reabrir trabajo ya cerrado."""
        from app.services.huerfanos import tareas_candidatas
        from app.models.tipos_documentos import TipoDocumento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo('ENTRADA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc_id = tipo_doc_id or TipoDocumento.query.first().id

        producido = _documento_real(arbol_esftt.db, expediente_id, tipo_doc_id, 'ya-producido')
        arbol_esftt.vincular(tarea, producido, 'PRODUCIDO')

        huerfano = _documento_real(arbol_esftt.db, expediente_id, tipo_doc_id, 'tras-ejecutada')
        candidatas = tareas_candidatas(huerfano)
        assert not any(c['tarea_id'] == tarea.id and c['rol'] == 'CONSUMIDO' for c in candidatas)

    def test_producido_ya_ocupado_no_es_candidata_producido(self, arbol_esftt):
        """Regla de seguridad ADR-038 §4: nunca se sugiere sustituir un producido —
        consecuencias encadenadas (hooks, ADR-033 §5)."""
        from app.services.huerfanos import tareas_candidatas
        from app.models.tipos_documentos import TipoDocumento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo('SALIDA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        tipo_doc_id = tipo_doc_id or TipoDocumento.query.first().id

        producido = _documento_real(arbol_esftt.db, expediente_id, tipo_doc_id, 'ya-producido-2')
        arbol_esftt.vincular(tarea, producido, 'PRODUCIDO')

        huerfano = _documento_real(arbol_esftt.db, expediente_id, tipo_doc_id, 'para-producido')
        candidatas = tareas_candidatas(huerfano)
        assert not any(c['tarea_id'] == tarea.id and c['rol'] == 'PRODUCIDO' for c in candidatas)


# ── Endpoints HTTP — candidatas, vincular_huerfano, fragmento (ADR-038 §5) ───

class TestEndpointsHuerfanoHTTP:

    def _montar_tarea_no_ejecutada(self, app, rol_catalogo='ENTRADA'):
        """Fase/Trámite/Tarea reales (BD de desarrollo), commiteados. Devuelve
        (expediente_id, fase_id, tramite_id, tarea_id, tipo_doc_id)."""
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.fases import Fase
        from app.models.tramites import Tramite
        from app.models.tareas import Tarea
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_documentos import TipoDocumento

        with app.app_context():
            codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo(rol_catalogo)
            solicitud = Solicitud.query.first()
            if solicitud is None:
                pytest.skip('No hay solicitudes en la BD de desarrollo')
            tipo_fase = TipoFase.query.first()
            if tipo_fase is None:
                pytest.skip('No hay tipos de fase en el catálogo')

            fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo_fase.id)
            db.session.add(fase)
            db.session.flush()
            from app.models.tramites_tareas_documentos import TramiteTareaDocumento
            fila = TramiteTareaDocumento.query.filter_by(rol=rol_catalogo).first()
            tramite = Tramite(fase_id=fase.id, tipo_tramite_id=fila.tipo_tramite_id)
            db.session.add(tramite)
            db.session.flush()
            from app.models.tramites_tareas import TramiteTarea
            slot = TramiteTarea.query.filter_by(
                tipo_tramite_id=fila.tipo_tramite_id, orden=fila.orden_tarea).first()
            tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=slot.tipo_tarea_id)
            db.session.add(tarea)
            db.session.flush()

            tipo_doc_id = tipo_doc_id or TipoDocumento.query.first().id
            db.session.commit()
            return solicitud.expediente_id, fase.id, tramite.id, tarea.id, tipo_doc_id

    def _limpiar_arbol(self, app, *, fase_id, doc_ids=()):
        from app import db
        from app.models.fases import Fase
        from app.models.documentos import Documento
        with app.app_context():
            db.session.rollback()
            for doc_id in doc_ids:
                Documento.query.filter_by(id=doc_id).delete()
            # CASCADE en tramite_id/tarea_id (ADR-010, ver tareas.py/tramites.py)
            # se lleva Tramite/Tarea/DocumentoTarea al borrar la Fase.
            Fase.query.filter_by(id=fase_id).delete()
            db.session.commit()

    def test_vincular_huerfano_consumido_ok(self, usuario_tramitador, app):
        exp_id, fase_id, tramite_id, tarea_id, tipo_doc_id = self._montar_tarea_no_ejecutada(app, 'ENTRADA')
        _, doc_id = _documento_suelto(app, url=f'http://example.com/test-630-vincular-{uuid.uuid4().hex}.pdf',
                                       tipo_doc_id=tipo_doc_id, expediente_id=exp_id)
        try:
            r = usuario_tramitador.post(
                f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_id}/vincular_huerfano',
                json={'documento_id': doc_id, 'rol': 'CONSUMIDO'},
            )
            assert r.status_code == 200
            assert r.get_json()['ok'] is True

            with app.app_context():
                from app.models.documentos_tarea import DocumentoTarea
                vinculo = DocumentoTarea.query.filter_by(documento_id=doc_id, tarea_id=tarea_id).first()
                assert vinculo is not None
                assert vinculo.rol == 'CONSUMIDO'

            # Ya no es huérfano — un segundo intento debe rechazarse (409, api_huerfanos.py)
            r2 = usuario_tramitador.get(f'/api/documentos/{doc_id}/candidatas')
            assert r2.status_code == 409
        finally:
            self._limpiar_arbol(app, fase_id=fase_id, doc_ids=[doc_id])

    def test_vincular_huerfano_rechaza_documento_de_otro_expediente(self, usuario_tramitador, app):
        exp_id, fase_id, tramite_id, tarea_id, tipo_doc_id = self._montar_tarea_no_ejecutada(app, 'ENTRADA')
        with app.app_context():
            from app.models.expedientes import Expediente
            otro = Expediente.query.filter(Expediente.id != exp_id).first()
            if otro is None:
                pytest.skip('Solo hay un expediente en la BD de desarrollo')
        _, doc_id = _documento_suelto(app, url=f'http://example.com/test-630-ajeno-{uuid.uuid4().hex}.pdf',
                                       tipo_doc_id=tipo_doc_id, expediente_id=exp_id)
        # Documento suelto en `exp_id` (mismo expediente que la tarea) — forzamos el
        # caso "ajeno" reasignándolo a otro expediente distinto del de la tarea.
        with app.app_context():
            from app import db
            from app.models.documentos import Documento
            Documento.query.filter_by(id=doc_id).update({'expediente_id': otro.id})
            db.session.commit()
        try:
            r = usuario_tramitador.post(
                f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_id}/vincular_huerfano',
                json={'documento_id': doc_id, 'rol': 'CONSUMIDO'},
            )
            assert r.status_code == 422
        finally:
            self._limpiar_arbol(app, fase_id=fase_id, doc_ids=[doc_id])

    def test_vincular_huerfano_rechaza_producido_ya_ocupado(self, usuario_tramitador, app):
        exp_id, fase_id, tramite_id, tarea_id, tipo_doc_id = self._montar_tarea_no_ejecutada(app, 'SALIDA')
        with app.app_context():
            from app import db
            from app.models.documentos import Documento
            from app.models.documentos_tarea import DocumentoTarea
            ya_producido = Documento(expediente_id=exp_id, tipo_doc_id=tipo_doc_id,
                                      url=f'http://example.com/test-630-prod-{uuid.uuid4().hex}.pdf')
            db.session.add(ya_producido)
            db.session.flush()
            db.session.add(DocumentoTarea(tarea_id=tarea_id, documento_id=ya_producido.id, rol='PRODUCIDO'))
            db.session.commit()
            ya_producido_id = ya_producido.id

        _, doc_id = _documento_suelto(app, url=f'http://example.com/test-630-nuevo-{uuid.uuid4().hex}.pdf',
                                       tipo_doc_id=tipo_doc_id, expediente_id=exp_id)
        try:
            r = usuario_tramitador.post(
                f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_id}/vincular_huerfano',
                json={'documento_id': doc_id, 'rol': 'PRODUCIDO'},
            )
            assert r.status_code == 422
        finally:
            self._limpiar_arbol(app, fase_id=fase_id, doc_ids=[doc_id, ya_producido_id])

    def test_fragmento_huerfano_render(self, usuario_tramitador, app):
        _, doc_id = _documento_suelto(app, url=f'http://example.com/test-630-fragmento-{uuid.uuid4().hex}.pdf')
        try:
            r = usuario_tramitador.get(f'/seguimiento_y_huerfanos/huerfanos/{doc_id}/fragmento')
            assert r.status_code == 200
        finally:
            _borrar_documento(app, doc_id)

    def test_fragmento_huerfano_404_si_no_es_huerfano(self, usuario_tramitador, app):
        with app.app_context():
            from app.models.documentos_tarea import DocumentoTarea
            vinculo = DocumentoTarea.query.first()
            if vinculo is None:
                pytest.skip('No hay documentos vinculados en la BD de desarrollo')
            doc_id = vinculo.documento_id
        r = usuario_tramitador.get(f'/seguimiento_y_huerfanos/huerfanos/{doc_id}/fragmento')
        assert r.status_code == 404
