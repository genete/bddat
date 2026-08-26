"""
Tests #396 bloque 2 — alta/edición/borrado de organismo consultado (ADR-042 §C).

Monta el árbol de verdad en BD (mismo patrón que test_722/test_723,
test_471_crear_traslado): `crear_organismo`/`editar_organismo`/`borrar_organismo`
llaman a `check_invariante` y al motor, que consultan relaciones y catálogo
reales. SAVEPOINT de `app_ctx` aísla cada test — nada persiste.
"""
import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _fase_consultas():
    """Fase CONSULTAS nueva sobre la primera solicitud de la BD de desarrollo."""
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tipos_fases import TipoFase

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'CONSULTAS').id)
    db.session.add(fase)
    db.session.flush()
    return fase


def _entidad_consultada():
    from app.models.entidad import Entidad
    entidad = Entidad.query.filter_by(rol_consultado=True).first()
    if entidad is None:
        pytest.skip('No hay entidades rol_consultado=True en la BD de desarrollo')
    return entidad


def _entidad_no_consultada():
    from app.models.entidad import Entidad
    entidad = Entidad.query.filter_by(rol_consultado=False).first()
    if entidad is None:
        pytest.skip('No hay entidades rol_consultado=False en la BD de desarrollo')
    return entidad


def _documento_expediente(expediente_id):
    from app.models.documentos import Documento
    doc = Documento.query.filter_by(expediente_id=expediente_id).first()
    if doc is None:
        pytest.skip('No hay documentos en el expediente de prueba')
    return doc


def _documento_otro_expediente(expediente_id):
    from app.models.documentos import Documento
    doc = Documento.query.filter(Documento.expediente_id != expediente_id).first()
    if doc is None:
        pytest.skip('No hay documentos de otro expediente en la BD de desarrollo')
    return doc


def _crear_organismo(fase=None, via='consulta', documento_id=None):
    """Alta vía svc.crear_organismo, con fase/entidad por defecto. Devuelve la instancia."""
    from app.services import mutaciones_arbol as svc
    from app.models.organismos_expediente import OrganismoExpediente

    fase = fase or _fase_consultas()
    entidad = _entidad_consultada()
    res = svc.crear_organismo(fase, entidad, via=via, documento_id=documento_id)
    assert res.ok, res.error
    return OrganismoExpediente.query.get(res.ids[0])


# ---------------------------------------------------------------------------
# A) crear_organismo
# ---------------------------------------------------------------------------

class TestCrearOrganismo:

    def test_camino_feliz_via_consulta(self, app_ctx):
        oe = _crear_organismo()
        assert oe.via == 'consulta'
        assert oe.resultado is None  # en curso, no exonerado
        assert oe.fase is not None

    def test_declaracion_responsable_fuerza_resultado_exonerado(self, app_ctx):
        fase = _fase_consultas()
        doc = _documento_expediente(fase.solicitud.expediente_id)
        oe = _crear_organismo(fase=fase, via='declaracion_responsable', documento_id=doc.id)
        assert oe.resultado == 'exonerado'
        assert oe.documento_id == doc.id

    def test_entidad_sin_rol_consultado_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_no_consultada()
        res = svc.crear_organismo(fase, entidad, via='consulta')
        assert not res.ok
        assert 'rol de organismo consultado' in res.error

    def test_via_invalida_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        res = svc.crear_organismo(fase, entidad, via='otra_cosa')
        assert not res.ok
        assert 'via debe ser' in res.error

    def test_declaracion_responsable_sin_documento_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        res = svc.crear_organismo(fase, entidad, via='declaracion_responsable')
        assert not res.ok
        assert 'documento_id es obligatorio' in res.error

    def test_consulta_con_documento_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        doc = _documento_expediente(fase.solicitud.expediente_id)
        res = svc.crear_organismo(fase, entidad, via='consulta', documento_id=doc.id)
        assert not res.ok
        assert 'solo aplica a la vía declaracion_responsable' in res.error

    def test_documento_de_otro_expediente_rechazado(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        doc_otro = _documento_otro_expediente(fase.solicitud.expediente_id)
        res = svc.crear_organismo(fase, entidad, via='declaracion_responsable', documento_id=doc_otro.id)
        assert not res.ok
        assert 'no válido para este expediente' in res.error

    def test_duplicado_en_misma_fase_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        res1 = svc.crear_organismo(fase, entidad, via='consulta')
        assert res1.ok, res1.error
        res2 = svc.crear_organismo(fase, entidad, via='consulta')
        assert not res2.ok
        assert 'ya está registrado' in res2.error

    def test_misma_entidad_en_fases_distintas_permitido(self, app_ctx):
        """#396 §8: el UNIQUE es por fase (ronda), no por expediente — habilita
        una segunda ronda de consultas por modificado de proyecto."""
        from app.services import mutaciones_arbol as svc
        entidad = _entidad_consultada()
        fase1 = _fase_consultas()
        fase2 = _fase_consultas()
        res1 = svc.crear_organismo(fase1, entidad, via='consulta')
        res2 = svc.crear_organismo(fase2, entidad, via='consulta')
        assert res1.ok, res1.error
        assert res2.ok, res2.error

    def test_fase_cerrada_bloquea(self, app_ctx):
        from app import db
        from app.services import mutaciones_arbol as svc
        fase = _fase_consultas()
        entidad = _entidad_consultada()
        fase.documento_resultado_id = _documento_expediente(fase.solicitud.expediente_id).id
        db.session.flush()
        assert fase.finalizada

        res = svc.crear_organismo(fase, entidad, via='consulta')
        assert not res.ok
        assert res.bloqueo is not None


# ---------------------------------------------------------------------------
# B) editar_organismo
# ---------------------------------------------------------------------------

class TestEditarOrganismo:

    def test_cambia_resultado(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        res = svc.editar_organismo(oe, via='consulta', resultado='cerrado_favorable',
                                    direccion_notificacion_id=None, documento_id=None)
        assert res.ok, res.error
        assert oe.resultado == 'cerrado_favorable'

    def test_resultado_exonerado_con_via_consulta_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        res = svc.editar_organismo(oe, via='consulta', resultado='exonerado',
                                    direccion_notificacion_id=None, documento_id=None)
        assert not res.ok
        assert 'solo aplica a la vía declaracion_responsable' in res.error

    def test_cambiar_a_declaracion_responsable_sin_documento_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        res = svc.editar_organismo(oe, via='declaracion_responsable', resultado=None,
                                    direccion_notificacion_id=None, documento_id=None)
        assert not res.ok
        assert 'documento_id es obligatorio' in res.error

    def test_cambiar_a_declaracion_responsable_fuerza_exonerado(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        doc = _documento_expediente(oe.expediente_id)
        # Pide 'cerrado_favorable' a propósito: la vía manda, no lo que se pida.
        res = svc.editar_organismo(oe, via='declaracion_responsable', resultado='cerrado_favorable',
                                    direccion_notificacion_id=None, documento_id=doc.id)
        assert res.ok, res.error
        assert oe.resultado == 'exonerado'

    def test_resultado_invalido_bloquea(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        res = svc.editar_organismo(oe, via='consulta', resultado='tramitado',
                                    direccion_notificacion_id=None, documento_id=None)
        assert not res.ok
        assert 'resultado debe ser' in res.error

    def test_fase_cerrada_bloquea(self, app_ctx):
        from app import db
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        oe.fase.documento_resultado_id = _documento_expediente(oe.expediente_id).id
        db.session.flush()

        res = svc.editar_organismo(oe, via='consulta', resultado='cerrado_favorable',
                                    direccion_notificacion_id=None, documento_id=None)
        assert not res.ok
        assert res.bloqueo is not None


# ---------------------------------------------------------------------------
# C) borrar_organismo
# ---------------------------------------------------------------------------

class TestBorrarOrganismo:

    def test_camino_feliz(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.organismos_expediente import OrganismoExpediente
        oe = _crear_organismo()
        oe_id = oe.id

        res = svc.borrar_organismo(oe)
        assert res.ok, res.error
        assert OrganismoExpediente.query.get(oe_id) is None

    def test_con_tramite_vinculado_bloquea(self, app_ctx):
        from app import db
        from app.services import mutaciones_arbol as svc
        from app.models.tramites import Tramite
        from app.models.tramites_organismos import TramiteOrganismo
        from app.models.tipos_tramites import TipoTramite

        oe = _crear_organismo()
        tt = _tipo(TipoTramite, 'CONSULTA_SEPARATA')
        tramite = Tramite(fase_id=oe.fase_id, tipo_tramite_id=tt.id)
        db.session.add(tramite)
        db.session.flush()
        db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
        db.session.flush()

        res = svc.borrar_organismo(oe)
        assert not res.ok
        assert res.bloqueo is not None
        assert 'trámites vinculados' in res.bloqueo.norma_compilada

        from app.models.organismos_expediente import OrganismoExpediente
        assert OrganismoExpediente.query.get(oe.id) is not None

    def test_fase_cerrada_bloquea(self, app_ctx):
        from app import db
        from app.services import mutaciones_arbol as svc
        oe = _crear_organismo()
        oe.fase.documento_resultado_id = _documento_expediente(oe.expediente_id).id
        db.session.flush()

        res = svc.borrar_organismo(oe)
        assert not res.ok
        assert res.bloqueo is not None


# ---------------------------------------------------------------------------
# D) Invariantes — dispatcher directo (sin pasar por mutaciones_arbol)
# ---------------------------------------------------------------------------

class TestInvariantesOrganismo:

    def test_fase_de_organismo(self, app_ctx):
        from app.services.invariantes_esftt import _fase_de
        oe = _crear_organismo()
        assert _fase_de('ORGANISMO', oe.id).id == oe.fase_id

    def test_fase_de_organismo_inexistente_none(self, app_ctx):
        from app.services.invariantes_esftt import _fase_de
        assert _fase_de('ORGANISMO', 0) is None


# ---------------------------------------------------------------------------
# E) Endpoint HTTP — POST .../nodo/fase/<id>/organismos
#
# BD real (sin app_ctx: sin precedente de combinarlo con el test_client en esta
# suite, ver TestEndpointReabrirFase de test_720) — limpieza manual en finally.
# ---------------------------------------------------------------------------

class TestEndpointCrearOrganismo:

    def _fase_consultas(self, app):
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.fases import Fase
        from app.models.tipos_fases import TipoFase

        with app.app_context():
            base = Solicitud.query.first()
            if base is None:
                pytest.skip('No hay solicitudes en la BD de desarrollo')
            tipo_fase = TipoFase.query.filter_by(codigo='CONSULTAS').first()
            if tipo_fase is None:
                pytest.skip("TipoFase 'CONSULTAS' no está en el catálogo")

            fase = Fase(solicitud_id=base.id, tipo_fase_id=tipo_fase.id)
            db.session.add(fase)
            db.session.commit()
            return base.expediente_id, fase.id

    def _limpiar(self, app, fase_id):
        from app import db
        from app.models.fases import Fase
        with app.app_context():
            db.session.rollback()
            Fase.query.filter_by(id=fase_id).delete()
            db.session.commit()

    def test_alta_exito_via_http(self, usuario_supervisor, app):
        from app.models.entidad import Entidad

        with app.app_context():
            entidad = Entidad.query.filter_by(rol_consultado=True).first()
            if entidad is None:
                pytest.skip('No hay entidades rol_consultado=True en la BD de desarrollo')
            organismo_id = entidad.id

        exp_id, fase_id = self._fase_consultas(app)
        try:
            r = usuario_supervisor.post(
                f'/api/expedientes/{exp_id}/nodo/fase/{fase_id}/organismos',
                json={'organismo_id': organismo_id, 'via': 'consulta'})
            assert r.status_code == 201, r.get_json()
            data = r.get_json()
            assert data['ok'] is True
            assert len(data['ids']) == 1

            with app.app_context():
                from app.models.organismos_expediente import OrganismoExpediente
                oe = OrganismoExpediente.query.get(data['ids'][0])
                assert oe is not None
                assert oe.fase_id == fase_id
                assert oe.organismo_id == organismo_id
        finally:
            self._limpiar(app, fase_id)

    def test_alta_sin_organismo_id_422(self, usuario_supervisor, app):
        exp_id, fase_id = self._fase_consultas(app)
        try:
            r = usuario_supervisor.post(
                f'/api/expedientes/{exp_id}/nodo/fase/{fase_id}/organismos',
                json={'via': 'consulta'})
            assert r.status_code == 422
        finally:
            self._limpiar(app, fase_id)

    def test_alta_entidad_inexistente_404(self, usuario_supervisor, app):
        exp_id, fase_id = self._fase_consultas(app)
        try:
            r = usuario_supervisor.post(
                f'/api/expedientes/{exp_id}/nodo/fase/{fase_id}/organismos',
                json={'organismo_id': 999999999, 'via': 'consulta'})
            assert r.status_code == 404
        finally:
            self._limpiar(app, fase_id)
