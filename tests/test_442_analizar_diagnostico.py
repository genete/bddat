"""
Tests #442 — contenedor de la tarea ANALIZAR: consolidación de defectos y
producción del documento de diagnóstico.

Sección A: consolidar_defectos() — degradación permisiva (sin BD).
Sección B: whitelist de trámites con secciones extendidas (sin BD).
Sección C: crear_diagnostico() — validación de negocio con stub (sin BD).
Sección D: crear_diagnostico() — circuito bddat:// completo (con BD real).

NOTA sobre aislamiento: crear_diagnostico() llama a db.session.commit() (parte
real de su contrato, igual que crear_cert()). El SAVEPOINT de app_ctx
(conftest.py) NO protege frente a un commit() explícito del código bajo
prueba — un commit() real consume el SAVEPOINT y persiste de verdad, dejando
el rollback final de la fixture sin nada que deshacer (comprobado: dejó
filas huérfanas en la BD de desarrollo la primera vez que se escribió este
fichero). Por eso la Sección D limpia explícitamente en un finally lo que
crea, en vez de confiar en el rollback de app_ctx.
"""
import pytest

from app.models.tareas import Tarea


# ---------------------------------------------------------------------------
# Stub compartido (mismo patrón que test_362_cert_plazo_cumplido.py)
# ---------------------------------------------------------------------------

class _Vinculo:
    def __init__(self, rol):
        self.rol = rol
        self.documento = object()


class _StubTarea:
    def __init__(self, vinculos=None):
        self.id = 999999
        self.vinculos_documento = vinculos or []

    @property
    def documento_producido(self):
        return Tarea.documento_producido.fget(self)


# ---------------------------------------------------------------------------
# A) consolidar_defectos() — degradación permisiva
# ---------------------------------------------------------------------------

class TestConsolidarDefectos:

    def test_degrada_permisivo_sin_proveedores(self):
        """Ningún proveedor (#495/#581/#440) existe todavía — lista vacía y completo=True."""
        from app.services.consolidacion_defectos import consolidar_defectos

        resultado = consolidar_defectos(_StubTarea())
        assert resultado == {'items': [], 'completo': True, 'error': False}


# ---------------------------------------------------------------------------
# B) Whitelist de trámites con secciones extendidas
# ---------------------------------------------------------------------------

class TestSeccionesExtendidas:

    def test_analisis_documental_y_requerimiento_subsanacion_llevan_secciones(self):
        from app.routes.api_expedientes import _TRAMITES_CON_SECCIONES_ANALISIS
        assert 'ANALISIS_DOCUMENTAL' in _TRAMITES_CON_SECCIONES_ANALISIS
        assert 'REQUERIMIENTO_SUBSANACION' in _TRAMITES_CON_SECCIONES_ANALISIS

    def test_consulta_separata_no_lleva_secciones(self):
        """CONSULTA_SEPARATA solo necesita el núcleo común (resultado + producir)."""
        from app.routes.api_expedientes import _TRAMITES_CON_SECCIONES_ANALISIS
        assert 'CONSULTA_SEPARATA' not in _TRAMITES_CON_SECCIONES_ANALISIS


# ---------------------------------------------------------------------------
# C) crear_diagnostico() — validaciones sin BD
# ---------------------------------------------------------------------------

class TestCrearDiagnosticoValidaciones:

    def test_tarea_con_documento_producido_lanza_valueerror(self):
        """Un solo tiro por tarea — mismo criterio que crear_cert."""
        from app.services.diagnosticos import crear_diagnostico

        tarea = _StubTarea(vinculos=[_Vinculo('PRODUCIDO')])
        with pytest.raises(ValueError, match='ya tiene documento producido'):
            crear_diagnostico(tarea, 'favorable', [])


# ---------------------------------------------------------------------------
# D) crear_diagnostico() — circuito bddat:// completo (BD real, rollback auto)
# ---------------------------------------------------------------------------

class TestCrearDiagnosticoCircuito:

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

    def _limpiar(self, tarea_id, doc_id, diag_id, *, bitacora_ids=()):
        """Borra explícitamente lo creado por el test (ver nota de aislamiento arriba).

        Usa el mismo app-context/sesión ya activo (el de app_ctx) — no abre uno
        nuevo: crear_diagnostico ya hizo commit real sobre esa conexión, y una
        conexión sigue operativa para nuevas transacciones tras un commit.
        """
        from app import db
        from app.models.diagnosticos import Diagnostico
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.bitacora import Bitacora

        db.session.rollback()  # defensivo: si el test falló a mitad de un flush, limpia el estado roto
        if doc_id is not None:
            DocumentoTarea.query.filter_by(tarea_id=tarea_id, documento_id=doc_id, rol='PRODUCIDO').delete()
        if diag_id is not None:
            Diagnostico.query.filter_by(id=diag_id).delete()
        if doc_id is not None:
            Documento.query.filter_by(id=doc_id).delete()
        for bid in bitacora_ids:
            Bitacora.query.filter_by(id=bid).delete()
        db.session.commit()

    def test_crea_documento_bddat_y_diagnostico(self, app_ctx):
        from app.services.diagnosticos import crear_diagnostico
        from app.models.diagnosticos import Diagnostico

        tarea = self._tarea_analizar_libre()
        defectos = [{'texto': 'defecto de prueba', 'origen': 'documental', 'tarea_id': tarea.id}]

        doc_id = diag_id = None
        try:
            doc = crear_diagnostico(tarea, 'desfavorable', defectos)
            doc_id = doc.id

            assert doc.url.startswith('bddat://diagnosticos/')
            assert doc.tipo_doc.codigo == 'DIAGNOSTICO'

            diag = Diagnostico.query.filter_by(documento_id=doc.id).first()
            assert diag is not None
            diag_id = diag.id
            assert diag.resultado == 'desfavorable'
            assert diag.defectos == defectos

            assert tarea.documento_producido is not None
            assert tarea.documento_producido.id == doc.id
        finally:
            self._limpiar(tarea.id, doc_id, diag_id)

    def test_justificacion_registra_bitacora_de_escape(self, app_ctx):
        from unittest.mock import patch
        from app.models.usuarios import Usuario
        from app.services.diagnosticos import crear_diagnostico
        from app.models.bitacora import Bitacora

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        tarea = self._tarea_analizar_libre()
        doc_id = diag_id = None
        try:
            # Se mockea current_user en vez de empujar un test_request_context anidado:
            # este último crearía su propio scope de sesión, potencialmente desligado
            # de la conexión que usa este test.
            with patch('app.services.diagnosticos.current_user', usuario):
                doc = crear_diagnostico(tarea, 'favorable', [], justificacion='revisado a mano, se fuerza')
            doc_id = doc.id
            diag_id = doc.diagnostico.id if doc.diagnostico else None

            entrada = (
                Bitacora.query.filter_by(operacion='ALTERAR', tabla='tareas', registro_id=tarea.id)
                .order_by(Bitacora.id.desc()).first()
            )
            assert entrada is not None
            assert entrada.detalle['escape'] is True
            assert entrada.detalle['justificacion'] == 'revisado a mano, se fuerza'
            bitacora_ids = (entrada.id,)
        finally:
            self._limpiar(tarea.id, doc_id, diag_id, bitacora_ids=locals().get('bitacora_ids', ()))
