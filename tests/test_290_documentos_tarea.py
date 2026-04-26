"""
Tests issue #290 — tabla documentos_tarea (INCORPORAR multi-doc v5.5).

Tres bloques:
  A) Propiedades Tarea.ejecutada / planificada — sin BD, sin app context.
  B) Invariantes _check_finalizar_tarea — con patching de Tarea.query.
  C) API endpoints /api/bc/tarea/<id>/incorporar/* — Flask test client + BD real.
"""
import pytest
from unittest.mock import MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# A) Propiedades Tarea.ejecutada / planificada
#    Se invoca directamente el fget de la property sobre un objeto stub,
#    evitando SQLAlchemy por completo.
# ═══════════════════════════════════════════════════════════════════════════════

class _StubTarea:
    """Stub mínimo que implementa los atributos que leen las properties."""
    def __init__(self, codigo, documentos_tarea=None,
                 doc_producido_id=None, doc_usado_id=None):
        self.tipo_tarea = MagicMock(codigo=codigo)
        self.documentos_tarea = documentos_tarea or []
        self.documento_producido_id = doc_producido_id
        self.documento_usado_id = doc_usado_id


def _ejecutada(stub):
    from app.models.tareas import Tarea
    return Tarea.ejecutada.fget(stub)


def _planificada(stub):
    from app.models.tareas import Tarea
    return Tarea.planificada.fget(stub)


def _en_curso(stub):
    # en_curso depende de planificada y ejecutada; se resuelven explícitamente
    return not _planificada(stub) and not _ejecutada(stub)


class TestTareaEjecutadaIncorporar:

    def test_incorporar_sin_docs_no_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _ejecutada(t) is False

    def test_incorporar_con_un_doc_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _ejecutada(t) is True

    def test_incorporar_con_varios_docs_ejecutada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock(), MagicMock()])
        assert _ejecutada(t) is True

    def test_incorporar_sin_docs_planificada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _planificada(t) is True

    def test_incorporar_con_doc_no_planificada(self):
        t = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _planificada(t) is False

    def test_incorporar_en_curso_siempre_false(self):
        # INCORPORAR no tiene estado intermedio: o planificada o ejecutada
        sin_docs = _StubTarea('INCORPORAR', documentos_tarea=[])
        assert _en_curso(sin_docs) is False
        con_docs = _StubTarea('INCORPORAR', documentos_tarea=[MagicMock()])
        assert _en_curso(con_docs) is False

    def test_analisis_sin_doc_producido_no_ejecutada(self):
        t = _StubTarea('ANALISIS', doc_producido_id=None)
        assert _ejecutada(t) is False

    def test_analisis_con_doc_producido_ejecutada(self):
        t = _StubTarea('ANALISIS', doc_producido_id=42)
        assert _ejecutada(t) is True

    def test_analisis_con_doc_usado_en_curso(self):
        t = _StubTarea('ANALISIS', doc_producido_id=None, doc_usado_id=7)
        assert _planificada(t) is False
        assert _ejecutada(t) is False
        assert _en_curso(t) is True


# ═══════════════════════════════════════════════════════════════════════════════
# B) Invariante _check_finalizar_tarea
#    Se parchea Tarea.query.get para devolver un stub — sin tocar la BD.
# ═══════════════════════════════════════════════════════════════════════════════

def _check_finalizar_tarea(tarea_id):
    from app.services.invariantes_esftt import _check_finalizar_tarea as fn
    return fn(tarea_id)


class TestCheckFinalizarTareaIncorporar:

    def _mock_tarea(self, codigo, documentos_tarea=None,
                    doc_producido_id=None, doc_usado_id=None):
        t = MagicMock()
        t.tipo_tarea = MagicMock(codigo=codigo)
        t.documentos_tarea = documentos_tarea if documentos_tarea is not None else []
        t.documento_producido_id = doc_producido_id
        t.documento_usado_id = doc_usado_id
        return t

    def test_incorporar_sin_docs_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('INCORPORAR', documentos_tarea=[])
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is not None
            assert resultado.permitido is False
            assert 'INCORPORAR' in resultado.norma_compilada or 'documento' in resultado.norma_compilada.lower()

    def test_incorporar_con_docs_no_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('INCORPORAR', documentos_tarea=[MagicMock()])
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is None

    def test_analisis_sin_doc_producido_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('ANALISIS', doc_producido_id=None)
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is not None
            assert resultado.permitido is False

    def test_analisis_con_ambos_docs_no_bloquea(self, app):
        with app.app_context():
            tarea = self._mock_tarea('ANALISIS', doc_producido_id=5, doc_usado_id=3)
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = tarea
                resultado = _check_finalizar_tarea(99)
            assert resultado is None

    def test_tarea_inexistente_no_bloquea(self, app):
        with app.app_context():
            with patch('app.services.invariantes_esftt.Tarea') as MockTarea:
                MockTarea.query.get.return_value = None
                resultado = _check_finalizar_tarea(9999)
            assert resultado is None


# ═══════════════════════════════════════════════════════════════════════════════
# C) Endpoints API — Flask test client con BD real + limpieza
#    Se crea data mínima, se prueba, se elimina.
# ═══════════════════════════════════════════════════════════════════════════════

def _setup_incorporar():
    """Crea fixture mínimo en la BD. Llamar dentro de with app.app_context()."""
    from app.models.expedientes import Expediente
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.documentos import Documento
    from app.models.tipos_tareas import TipoTarea
    from app import db

    tipo_incorporar = TipoTarea.query.filter_by(codigo='INCORPORAR').first()
    if not tipo_incorporar:
        return None  # El llamador hace pytest.skip si es None

    exp = Expediente.query.first()
    if not exp:
        return None

    sol = Solicitud(expediente_id=exp.id,
                    entidad_id=exp.titular_id or 1,
                    tipo_solicitud_id=1)
    db.session.add(sol)
    db.session.flush()

    fase = Fase(solicitud_id=sol.id, tipo_fase_id=1)
    db.session.add(fase)
    db.session.flush()

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=1)
    db.session.add(tramite)
    db.session.flush()

    tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_incorporar.id)
    db.session.add(tarea)
    db.session.flush()

    doc = Documento(expediente_id=exp.id, url='/tmp/test_incorporar.pdf',
                    tipo_doc_id=1)
    db.session.add(doc)
    db.session.flush()

    db.session.commit()
    return {
        'exp_id': exp.id, 'sol_id': sol.id, 'fase_id': fase.id,
        'tramite_id': tramite.id, 'tarea_id': tarea.id, 'doc_id': doc.id,
    }


def _teardown_incorporar(ids):
    """Elimina el fixture. Llamar dentro de with app.app_context()."""
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.tareas import Tarea
    from app.models.tramites import Tramite
    from app.models.fases import Fase
    from app.models.solicitudes import Solicitud
    from app.models.documentos import Documento
    from app import db

    DocumentoTarea.query.filter_by(tarea_id=ids['tarea_id']).delete()
    Tarea.query.filter_by(id=ids['tarea_id']).delete()
    Tramite.query.filter_by(id=ids['tramite_id']).delete()
    Fase.query.filter_by(id=ids['fase_id']).delete()
    Solicitud.query.filter_by(id=ids['sol_id']).delete()
    Documento.query.filter_by(id=ids['doc_id']).delete()
    db.session.commit()


def _get_test_user_id(app):
    """Devuelve el ID del primer usuario activo para injectar en sesión."""
    from app.models.usuarios import Usuario
    with app.app_context():
        user = Usuario.query.filter_by(activo=True).first()
        return user.id if user else None


def _inject_session(client, user_id):
    """Inyecta sesión de Flask-Login sin pasar por el formulario de login."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True


class TestApiIncorporarVincular:
    """
    Tests de integración — usa BD real.
    Patrón: setup en app_context → requests con test_client → teardown en app_context.
    Los tres bloques son SECUENCIALES, nunca anidados.
    """

    def test_vincular_documento_ok(self, app):
        user_id = _get_test_user_id(app)
        if not user_id:
            pytest.skip('No hay usuarios activos en BD de test')

        with app.app_context():
            ids = _setup_incorporar()
        if not ids:
            pytest.skip('Datos maestros insuficientes en BD de test')

        try:
            with app.test_client() as c:
                _inject_session(c, user_id)
                resp = c.post(
                    f'/api/bc/tarea/{ids["tarea_id"]}/incorporar/vincular',
                    data={'documento_id': ids['doc_id']}
                )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['ok'] is True
            assert 'vinculo_id' in data
        finally:
            with app.app_context():
                _teardown_incorporar(ids)

    def test_vincular_doc_duplicado_error(self, app):
        user_id = _get_test_user_id(app)
        if not user_id:
            pytest.skip('No hay usuarios activos en BD de test')

        with app.app_context():
            ids = _setup_incorporar()
        if not ids:
            pytest.skip('Datos maestros insuficientes en BD de test')

        try:
            with app.test_client() as c:
                _inject_session(c, user_id)
                url = f'/api/bc/tarea/{ids["tarea_id"]}/incorporar/vincular'
                c.post(url, data={'documento_id': ids['doc_id']})
                resp = c.post(url, data={'documento_id': ids['doc_id']})
            assert resp.status_code == 422
            assert resp.get_json()['ok'] is False
        finally:
            with app.app_context():
                _teardown_incorporar(ids)

    def test_vincular_sin_documento_id_error(self, app):
        user_id = _get_test_user_id(app)
        if not user_id:
            pytest.skip('No hay usuarios activos en BD de test')

        with app.app_context():
            ids = _setup_incorporar()
        if not ids:
            pytest.skip('Datos maestros insuficientes en BD de test')

        try:
            with app.test_client() as c:
                _inject_session(c, user_id)
                resp = c.post(
                    f'/api/bc/tarea/{ids["tarea_id"]}/incorporar/vincular',
                    data={}
                )
            assert resp.status_code == 400
        finally:
            with app.app_context():
                _teardown_incorporar(ids)

    def test_desvincular_ok(self, app):
        user_id = _get_test_user_id(app)
        if not user_id:
            pytest.skip('No hay usuarios activos en BD de test')

        with app.app_context():
            ids = _setup_incorporar()
        if not ids:
            pytest.skip('Datos maestros insuficientes en BD de test')

        try:
            with app.test_client() as c:
                _inject_session(c, user_id)
                resp_v = c.post(
                    f'/api/bc/tarea/{ids["tarea_id"]}/incorporar/vincular',
                    data={'documento_id': ids['doc_id']}
                )
                vinculo_id = resp_v.get_json()['vinculo_id']
                resp_d = c.post(
                    f'/api/bc/tarea/{ids["tarea_id"]}/incorporar/{vinculo_id}/desvincular'
                )
            assert resp_d.status_code == 200
            assert resp_d.get_json()['ok'] is True
        finally:
            with app.app_context():
                _teardown_incorporar(ids)

    def test_finalizar_incorporar_sin_docs_bloquea(self, app):
        user_id = _get_test_user_id(app)
        if not user_id:
            pytest.skip('No hay usuarios activos en BD de test')

        with app.app_context():
            ids = _setup_incorporar()
        if not ids:
            pytest.skip('Datos maestros insuficientes en BD de test')

        try:
            with app.test_client() as c:
                _inject_session(c, user_id)
                resp = c.post(f'/api/bc/tarea/{ids["tarea_id"]}/finalizar')
            assert resp.status_code == 422
            assert resp.get_json()['ok'] is False
        finally:
            with app.app_context():
                _teardown_incorporar(ids)
