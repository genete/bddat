"""
Tests #574 — fecha_administrativa en certificados internos (bddat://).

Antes de este fix, `_validar_url` forzaba fecha_administrativa=None para
CUALQUIER documento con esquema bddat://, acoplando el campo al mecanismo
de almacenamiento en vez de a la naturaleza jurídica del documento. Esto
dejaba CERT_PLAZO_CUMPLIDO y CERT_FIN_IP_CONSULTAS invisibles para
consultas ordenadas/filtradas por fecha_administrativa.

Alcance reducido (sin #572): no se toca integra_expediente; DIAGNOSTICO
sigue en NULL por simple omisión (nadie se la asigna), no por el esquema.

Sección A: _validar_url ya no fuerza NULL (sin BD).
Sección B: crear_cert_fin_ip_consultas asigna fecha_fin_ultima_fase (BD real,
           función sin commit propio → rollback automático de app_ctx).
Sección C: crear_cert (CERT_PLAZO_CUMPLIDO) asigna fecha_vencimiento (BD real,
           función CON commit propio → limpieza manual, mismo patrón que
           test_442_analizar_diagnostico.py Sección D).
Sección D: DIAGNOSTICO sigue en NULL tras el fix (regresión).
"""
import time
from datetime import date

import pytest

from app.models.tareas import Tarea


@pytest.fixture(autouse=True)
def _fs_tmp(fs_tmp):
    """FILESYSTEM_BASE redirigido a tmp_path — este módulo genera certificados
    internos que pueden tocar el servidor de ficheros de desarrollo (#674)."""
    pass


# ---------------------------------------------------------------------------
# A) _validar_url ya no fuerza fecha_administrativa=None (sin BD)
# ---------------------------------------------------------------------------

class TestValidarUrlNoFuerzaFechaNone:

    def test_bddat_url_no_fuerza_fecha_none(self):
        from app.models.documentos import Documento

        doc = Documento(fecha_administrativa=date(2026, 1, 1))
        doc.url = 'bddat://certificados/1'
        assert doc.fecha_administrativa == date(2026, 1, 1)

    def test_esquema_no_bddat_sigue_validando_igual(self):
        """El resto de la validación de esquema (http/https/bddat) no cambia."""
        from app.models.documentos import Documento

        doc = Documento()
        with pytest.raises(ValueError):
            doc.url = 'ftp://no-admitido/1'


# ---------------------------------------------------------------------------
# Helpers de construcción — mismo patrón que tests/test_373_cert_fase.py
# ---------------------------------------------------------------------------

def _crear_expediente(db):
    from app.models import Expediente, Proyecto, TipoExpediente

    tipo_exp = TipoExpediente.query.first()
    assert tipo_exp is not None, 'Catálogo TipoExpediente vacío — seed necesario'

    proyecto = Proyecto(
        titulo='Test #574 fecha_administrativa',
        descripcion='Test', fecha=date(2026, 1, 1),
        finalidad='Test', emplazamiento='Test',
    )
    db.session.add(proyecto)
    db.session.flush()
    numero_at = int(time.time() * 1000) % 10_000_000
    exp = Expediente(numero_at=numero_at, proyecto=proyecto, tipo_expediente=tipo_exp)
    db.session.add(exp)
    db.session.flush()
    return exp


def _crear_solicitud(db, expediente):
    from app.models import Solicitud, Entidad, TipoSolicitud

    entidad = Entidad.query.first()
    assert entidad is not None, 'Tabla entidades vacía — seed necesario'
    tipo_sol = TipoSolicitud.query.first()
    assert tipo_sol is not None, 'Catálogo TipoSolicitud vacío — seed necesario'

    sol = Solicitud(expediente=expediente, tipo_solicitud=tipo_sol, entidad=entidad)
    db.session.add(sol)
    db.session.flush()
    return sol


def _crear_fase_finalizada(db, solicitud, codigo_fase, fecha_fin):
    """Crea una fase habilitante finalizada (documento_resultado con fecha)."""
    from app.models import Fase, Documento, TipoFase

    tipo_fase = TipoFase.query.filter_by(codigo=codigo_fase).first()
    assert tipo_fase is not None, f'TipoFase {codigo_fase!r} no encontrado'

    doc = Documento(
        expediente=solicitud.expediente,
        url=f'test-doc-{codigo_fase}-{time.time()}',
        fecha_administrativa=fecha_fin,
    )
    db.session.add(doc)
    db.session.flush()
    fase = Fase(solicitud=solicitud, tipo_fase=tipo_fase, documento_resultado=doc)
    db.session.add(fase)
    db.session.flush()
    return fase


# ---------------------------------------------------------------------------
# B) crear_cert_fin_ip_consultas — asigna fecha_fin_ultima_fase (BD real)
# ---------------------------------------------------------------------------

class TestCertFinIpConsultasFechaAdministrativa:

    def test_asigna_fecha_fin_ultima_fase(self, app_ctx):
        from app import db
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        from app.models.documentos import Documento

        exp = _crear_expediente(db)
        sol = _crear_solicitud(db, exp)
        _crear_fase_finalizada(db, sol, 'INFORMACION_PUBLICA', date(2026, 3, 10))
        _crear_fase_finalizada(db, sol, 'CONSULTAS', date(2026, 4, 5))

        cert = crear_cert_fin_ip_consultas(exp, sol)
        assert cert is not None

        doc = Documento.query.get(cert.documento_id)
        assert doc.fecha_administrativa == date(2026, 4, 5)

        # "ordenable/visible por fecha": antes del fix esta fila quedaba
        # excluida de cualquier consulta filtrada por fecha_administrativa IS NOT NULL.
        visibles = (
            Documento.query
            .filter(Documento.fecha_administrativa.isnot(None))
            .filter_by(id=doc.id)
            .all()
        )
        assert len(visibles) == 1

    def test_sin_fecha_en_ninguna_fase_habilitante_deja_null(self, app_ctx):
        """Si ninguna fase habilitante tiene fecha (caso límite), no se inventa una."""
        from app import db
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        from app.models.documentos import Documento
        from app.models import Fase, TipoFase

        exp = _crear_expediente(db)
        sol = _crear_solicitud(db, exp)

        tipo_fase = TipoFase.query.filter_by(codigo='CONSULTAS').first()
        assert tipo_fase is not None
        doc_sin_fecha = Documento(
            expediente=exp, url=f'test-doc-sin-fecha-{time.time()}',
            fecha_administrativa=None,
        )
        db.session.add(doc_sin_fecha)
        db.session.flush()
        fase = Fase(solicitud=sol, tipo_fase=tipo_fase, documento_resultado=doc_sin_fecha)
        db.session.add(fase)
        db.session.flush()

        cert = crear_cert_fin_ip_consultas(exp, sol)
        assert cert is not None

        doc = Documento.query.get(cert.documento_id)
        assert doc.fecha_administrativa is None


# ---------------------------------------------------------------------------
# C) crear_cert (CERT_PLAZO_CUMPLIDO) — asigna fecha_vencimiento (BD real)
# ---------------------------------------------------------------------------

class TestCrearCertFechaAdministrativa:

    def _tarea_esperar_plazo_vencida_libre(self):
        """Primera tarea ESPERAR_PLAZO vencida y sin documento producido en
        la BD de desarrollo. Mismo criterio de skip que
        test_442_analizar_diagnostico.py: _tarea_analizar_libre()."""
        from app.models.tipos_tareas import TipoTarea
        from app.services.plazos import obtener_estado_plazo

        candidatas = (
            Tarea.query.join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
            .filter(TipoTarea.codigo == 'ESPERAR_PLAZO')
            .all()
        )
        for t in candidatas:
            if t.documento_producido is not None:
                continue
            try:
                # Sin dict de variables desde #785: el catálogo resuelve el
                # camino SFTT desde la propia tarea.
                ep = obtener_estado_plazo(t, 'TAREA')
            except Exception:
                continue
            if ep.estado == 'VENCIDO' and ep.fecha_limite is not None:
                return t, ep
        pytest.skip(
            'No hay ninguna tarea ESPERAR_PLAZO vencida sin certificado '
            'en la BD de desarrollo'
        )

    def _limpiar(self, tarea_id, doc_id, cert_id):
        from app import db
        from app.models.certificados import Certificado
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea

        db.session.rollback()
        if doc_id is not None:
            DocumentoTarea.query.filter_by(
                tarea_id=tarea_id, documento_id=doc_id, rol='PRODUCIDO'
            ).delete()
        if cert_id is not None:
            Certificado.query.filter_by(id=cert_id).delete()
        if doc_id is not None:
            Documento.query.filter_by(id=doc_id).delete()
        db.session.commit()

    def test_crea_documento_con_fecha_administrativa_no_nula(self, app_ctx):
        from app.services.certificados import crear_cert
        from app.models.certificados import Certificado
        from app.models.documentos import Documento

        tarea, ep_esperado = self._tarea_esperar_plazo_vencida_libre()

        doc_id = cert_id = None
        try:
            doc = crear_cert(tarea)
            doc_id = doc.id
            cert = Certificado.query.filter_by(documento_id=doc.id).first()
            cert_id = cert.id if cert else None

            assert doc.fecha_administrativa == ep_esperado.fecha_limite

            visibles = (
                Documento.query
                .filter(Documento.fecha_administrativa.isnot(None))
                .filter_by(id=doc.id)
                .all()
            )
            assert len(visibles) == 1
        finally:
            self._limpiar(tarea.id, doc_id, cert_id)


# ---------------------------------------------------------------------------
# D) DIAGNOSTICO sigue en NULL tras el fix (regresión)
# ---------------------------------------------------------------------------

class TestDiagnosticoSigueNulo:

    def _tarea_analizar_libre(self):
        from app.models.tipos_tareas import TipoTarea

        candidatas = (
            Tarea.query.join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
            .filter(TipoTarea.codigo == 'ANALIZAR')
            .all()
        )
        for t in candidatas:
            if t.documento_producido is None:
                return t
        pytest.skip('No hay ninguna tarea ANALIZAR sin documento producido en la BD de desarrollo')

    def test_diagnostico_fecha_administrativa_sigue_nula(self, app_ctx):
        from app import db
        from app.services.diagnosticos import crear_diagnostico
        from app.models.diagnosticos import Diagnostico
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea

        tarea = self._tarea_analizar_libre()
        defectos = [{'texto': 'defecto de prueba #574', 'origen': 'documental', 'tarea_id': tarea.id}]

        doc_id = diag_id = None
        try:
            doc = crear_diagnostico(tarea, 'desfavorable', defectos)
            doc_id = doc.id
            assert doc.url.startswith('bddat://diagnosticos/')

            diag = Diagnostico.query.filter_by(documento_id=doc.id).first()
            diag_id = diag.id if diag else None

            assert doc.fecha_administrativa is None
        finally:
            db.session.rollback()
            if doc_id is not None:
                DocumentoTarea.query.filter_by(
                    tarea_id=tarea.id, documento_id=doc_id, rol='PRODUCIDO'
                ).delete()
            if diag_id is not None:
                Diagnostico.query.filter_by(id=diag_id).delete()
            if doc_id is not None:
                Documento.query.filter_by(id=doc_id).delete()
            db.session.commit()
