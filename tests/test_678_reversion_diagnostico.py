"""
Tests #678 — reversión controlada del diagnóstico producido (ADR-033 §5,
enmienda ADR-005).

Sección A: revertir_diagnostico() — validaciones de negocio con stubs (sin BD).
Sección B: revertir_diagnostico() — circuito completo (con BD real).
Sección C: candado servidor (_candado_diagnostico_producido) — sin BD.

NOTA sobre aislamiento (mismo criterio que test_442_analizar_diagnostico.py):
revertir_diagnostico() hace commit() real. El SAVEPOINT de app_ctx no protege
frente a un commit() explícito, así que la Sección B limpia explícitamente en
un finally lo que crea/deja pendiente en vez de confiar en el rollback de la
fixture.
"""
import pytest

from app.models.tareas import Tarea


# ---------------------------------------------------------------------------
# Stubs compartidos (mismo patrón que test_442_analizar_diagnostico.py) —
# reproducen la doble navegación real: tarea.vinculos_documento (sus propios
# vínculos) y documento.vinculos_tarea (backref, todos los vínculos de
# cualquier tarea sobre ese documento — así es como se detecta el consumo por
# OTRA tarea, no la que produjo el diagnóstico).
# ---------------------------------------------------------------------------

class _TipoTareaStub:
    def __init__(self, nombre):
        self.nombre = nombre


class _TipoTramiteStub:
    def __init__(self, nombre):
        self.nombre = nombre


class _TramiteStub:
    def __init__(self, nombre_tipo):
        self.tipo_tramite = _TipoTramiteStub(nombre_tipo)


class _TareaConsumidoraStub:
    def __init__(self, id_, nombre_tarea, nombre_tramite):
        self.id = id_
        self.tipo_tarea = _TipoTareaStub(nombre_tarea)
        self.tramite = _TramiteStub(nombre_tramite)


class _VinculoStub:
    def __init__(self, rol, tarea, documento):
        self.rol = rol
        self.tarea = tarea
        self.documento = documento


class _DocumentoStub:
    def __init__(self):
        self.id = 888888
        self.vinculos_tarea = []
        self.diagnostico = None


class _TareaStub:
    def __init__(self, vinculos=None):
        self.id = 999999
        self.vinculos_documento = vinculos or []

    @property
    def documento_producido(self):
        return Tarea.documento_producido.fget(self)


# ---------------------------------------------------------------------------
# A) revertir_diagnostico() — validaciones sin BD
# ---------------------------------------------------------------------------

class TestRevertirDiagnosticoValidaciones:

    def test_sin_documento_producido_lanza_valueerror(self):
        from app.services.diagnosticos import revertir_diagnostico

        tarea = _TareaStub()
        with pytest.raises(ValueError, match='no tiene documento producido'):
            revertir_diagnostico(tarea)

    def test_consumido_lanza_diagnosticoconsumidoerror_con_motivo_legible(self):
        from app.services.diagnosticos import revertir_diagnostico, DiagnosticoConsumidoError

        tarea = _TareaStub()
        doc = _DocumentoStub()
        otra_tarea = _TareaConsumidoraStub(
            123, 'Elaborar escrito', 'Requerimiento de subsanación',
        )

        v_producido = _VinculoStub('PRODUCIDO', tarea, doc)
        v_consumido = _VinculoStub('CONSUMIDO', otra_tarea, doc)
        tarea.vinculos_documento = [v_producido]
        doc.vinculos_tarea = [v_producido, v_consumido]

        with pytest.raises(DiagnosticoConsumidoError) as exc_info:
            revertir_diagnostico(tarea)

        assert exc_info.value.tarea_consumidora is otra_tarea
        mensaje = str(exc_info.value)
        assert 'Elaborar escrito' in mensaje
        assert 'Requerimiento de subsanación' in mensaje


# ---------------------------------------------------------------------------
# B) revertir_diagnostico() — circuito bddat:// completo (BD real, limpieza manual)
# ---------------------------------------------------------------------------

class TestRevertirDiagnosticoCircuito:

    def _tarea_analizar_libre(self, excluir_ids=()):
        """Primera tarea ANALIZAR sin documento producido en la BD de desarrollo."""
        from app.models.tipos_tareas import TipoTarea
        candidatas = (
            Tarea.query.join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
            .filter(TipoTarea.codigo == 'ANALIZAR')
            .all()
        )
        for t in candidatas:
            if t.id not in excluir_ids and t.documento_producido is None:
                return t
        pytest.skip('No hay ninguna tarea ANALIZAR sin documento producido en la BD de desarrollo')

    def _limpiar(self, tarea_id, doc_id, diag_id, *, otra_tarea_id=None):
        from app import db
        from app.models.diagnosticos import Diagnostico
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea

        db.session.rollback()
        if doc_id is not None:
            DocumentoTarea.query.filter_by(tarea_id=tarea_id, documento_id=doc_id, rol='PRODUCIDO').delete()
            if otra_tarea_id is not None:
                DocumentoTarea.query.filter_by(
                    tarea_id=otra_tarea_id, documento_id=doc_id, rol='CONSUMIDO'
                ).delete()
        if diag_id is not None:
            Diagnostico.query.filter_by(id=diag_id).delete()
        if doc_id is not None:
            Documento.query.filter_by(id=doc_id).delete()
        db.session.commit()

    def test_revertir_borra_diagnostico_documento_y_vinculo(self, app_ctx):
        from app.services.diagnosticos import crear_diagnostico, revertir_diagnostico
        from app.models.diagnosticos import Diagnostico
        from app.models.documentos import Documento

        tarea = self._tarea_analizar_libre()
        defectos = [{'texto': 'defecto de prueba', 'origen': 'documental', 'tarea_id': tarea.id}]

        doc = crear_diagnostico(tarea, 'desfavorable', defectos)
        doc_id = doc.id
        diag_id = doc.diagnostico.id

        try:
            revertir_diagnostico(tarea)

            assert tarea.documento_producido is None
            assert Diagnostico.query.filter_by(id=diag_id).first() is None
            assert Documento.query.get(doc_id) is None
        finally:
            self._limpiar(tarea.id, doc_id, diag_id)

    def test_revertir_consumido_no_borra_nada(self, app_ctx):
        """Puerta cerrada (escalón 3): si otra tarea consumió el documento, la
        reversión no toca nada — ni el diagnóstico ni el vínculo PRODUCIDO."""
        from app import db
        from app.services.diagnosticos import crear_diagnostico, revertir_diagnostico, DiagnosticoConsumidoError
        from app.models.diagnosticos import Diagnostico
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea

        tarea = self._tarea_analizar_libre()
        otra_tarea = Tarea.query.filter(Tarea.id != tarea.id).first()
        if otra_tarea is None:
            pytest.skip('No hay otra tarea en la BD de desarrollo para simular el consumo')

        defectos = [{'texto': 'defecto de prueba', 'origen': 'documental', 'tarea_id': tarea.id}]
        doc = crear_diagnostico(tarea, 'desfavorable', defectos)
        doc_id = doc.id
        diag_id = doc.diagnostico.id

        db.session.add(DocumentoTarea(tarea_id=otra_tarea.id, documento_id=doc_id, rol='CONSUMIDO'))
        db.session.commit()

        try:
            with pytest.raises(DiagnosticoConsumidoError):
                revertir_diagnostico(tarea)

            assert Diagnostico.query.filter_by(id=diag_id).first() is not None
            assert Documento.query.get(doc_id) is not None
            assert tarea.documento_producido is not None
        finally:
            self._limpiar(tarea.id, doc_id, diag_id, otra_tarea_id=otra_tarea.id)


# ---------------------------------------------------------------------------
# C) _candado_diagnostico_producido() — sin BD
# ---------------------------------------------------------------------------

class TestCandadoDiagnosticoProducido:

    def test_sin_producido_no_bloquea(self):
        from app.routes.api_expedientes import _candado_diagnostico_producido

        tarea = _TareaStub()
        assert _candado_diagnostico_producido(tarea) is None

    def test_con_producido_bloquea_422_no_forzable(self, app):
        from app.routes.api_expedientes import _candado_diagnostico_producido

        tarea = _TareaStub()
        doc = _DocumentoStub()
        vinculo = _VinculoStub('PRODUCIDO', tarea, doc)
        tarea.vinculos_documento = [vinculo]

        with app.app_context():
            resp, status = _candado_diagnostico_producido(tarea)
            payload = resp.get_json()

        assert status == 422
        assert payload['puede_escapar'] is False
        assert 'motivo' in payload
