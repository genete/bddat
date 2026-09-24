"""Tests #932 (N3, ADR-049 §F) — `certificados.tipo` y `certificados.fase_id`.

Cuatro bloques:
  A) Esquema real: columnas, FK e índice único parcial tal y como quedan en BD.
  B) El índice único (fase_id, tipo): uno por tipo y fase; libre sin fase.
  C) La migración: el backfill de `tipo` sobre filas que ya existían.
  D) Los dos servicios que crean certificados rellenan `tipo`; los backrefs de
     `Fase` no colisionan.
"""
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError


def _cert(db, documento, tipo, *, fase=None):
    from app.models.certificados import Certificado
    cert = Certificado(documento_id=documento.id, tipo=tipo,
                       fase_id=fase.id if fase else None, datos={})
    db.session.add(cert)
    db.session.flush()
    return cert


# ---------------------------------------------------------------------------
# A) Esquema real
# ---------------------------------------------------------------------------

class TestEsquema:

    def test_columnas(self, app_ctx):
        from app import db
        filas = db.session.execute(db.text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'certificados'
              AND column_name IN ('tipo', 'fase_id')
        """)).mappings().all()
        columnas = {f['column_name']: f for f in filas}

        assert columnas['tipo']['data_type'] == 'character varying'
        assert columnas['tipo']['character_maximum_length'] == 50
        assert columnas['tipo']['is_nullable'] == 'NO'
        assert columnas['fase_id']['data_type'] == 'integer'
        assert columnas['fase_id']['is_nullable'] == 'YES'

    def test_fk_fase_restrict(self, app_ctx):
        from app import db
        fila = db.session.execute(db.text("""
            SELECT confrelid::regclass::text AS padre, confdeltype AS regla
            FROM pg_constraint
            WHERE conname = 'fk_certificado_fase'
              AND conrelid = 'public.certificados'::regclass
        """)).mappings().one()

        assert fila['padre'] == 'fases'
        assert fila['regla'] == 'r'   # RESTRICT

    def test_indice_unico_parcial(self, app_ctx):
        from app import db
        definicion = db.session.execute(db.text("""
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND indexname = 'uq_certificado_fase_tipo'
        """)).scalar()

        assert definicion is not None
        assert 'UNIQUE' in definicion
        assert '(fase_id, tipo)' in definicion
        assert 'WHERE (fase_id IS NOT NULL)' in definicion


# ---------------------------------------------------------------------------
# B) El índice único (fase_id, tipo)
# ---------------------------------------------------------------------------

class TestIndiceUnico:

    def test_dos_del_mismo_tipo_en_la_misma_fase_chocan(self, app_ctx, arbol_esftt):
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('RESOLUCION', solicitud=sol)
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-a'),
              'CERT_PLAZO_CUMPLIDO', fase=fase)

        with pytest.raises(IntegrityError):
            _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-b'),
                  'CERT_PLAZO_CUMPLIDO', fase=fase)
        db.session.rollback()

    def test_distinto_tipo_en_la_misma_fase_convive(self, app_ctx, arbol_esftt):
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('RESOLUCION', solicitud=sol)
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-c'),
              'CERT_PLAZO_CUMPLIDO', fase=fase)
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_FIN_IP_CONSULTAS', '932-d'),
              'CERT_FIN_IP_CONSULTAS', fase=fase)

        assert len(fase.certificados_cumplimiento) == 2

    def test_sin_fase_no_hay_limite(self, app_ctx, arbol_esftt):
        """Los CERT_PLAZO_CUMPLIDO de hoy van sin fase_id, uno por tarea: el
        índice no debe confundirlos entre sí."""
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-e'),
              'CERT_PLAZO_CUMPLIDO')
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-f'),
              'CERT_PLAZO_CUMPLIDO')

    def test_borrar_la_fase_lo_niega_la_bd(self, app_ctx, arbol_esftt):
        """passive_deletes=True: el ORM no anula la FK en silencio; la BD aplica
        el RESTRICT (mismo criterio que #895 con reformado_id)."""
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('RESOLUCION', solicitud=sol)
        _cert(db, arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-g'),
              'CERT_PLAZO_CUMPLIDO', fase=fase)

        db.session.delete(fase)
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()


# ---------------------------------------------------------------------------
# C) La migración: backfill de `tipo`
# ---------------------------------------------------------------------------

def _migracion_932():
    ruta = (Path(__file__).resolve().parent.parent
            / 'migrations' / 'versions' / '932_certificados_tipo_fase.py')
    spec = importlib.util.spec_from_file_location('migracion_932', ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_backfill_de_tipo_desde_el_documento(app_ctx, arbol_esftt):
    """Deshace y rehace la migración dentro de la transacción del test (el DDL
    de Postgres es transaccional: el rollback final lo revierte todo). Entre
    medias inserta certificados como los de antes de #932, sin `tipo`, y
    comprueba que el upgrade lo rellena desde tipos_documentos."""
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from app import db

    sol = arbol_esftt.solicitud_nueva()
    doc_plazo = arbol_esftt.documento(sol.expediente_id, 'CERT_PLAZO_CUMPLIDO', '932-bf1')
    doc_ip = arbol_esftt.documento(sol.expediente_id, 'CERT_FIN_IP_CONSULTAS', '932-bf2')

    migracion = _migracion_932()
    conexion = db.session.connection()
    with Operations.context(MigrationContext.configure(conexion)):
        migracion.downgrade()

        ids = {}
        for doc in (doc_plazo, doc_ip):
            ids[doc.id] = conexion.execute(db.text(
                "INSERT INTO public.certificados (documento_id, generado_en, datos) "
                "VALUES (:d, :g, '{}') RETURNING id"
            ), {'d': doc.id, 'g': datetime.utcnow()}).scalar()

        migracion.upgrade()

    tipos = dict(conexion.execute(db.text(
        "SELECT id, tipo FROM public.certificados WHERE id = ANY(:ids)"
    ), {'ids': list(ids.values())}).all())
    assert tipos[ids[doc_plazo.id]] == 'CERT_PLAZO_CUMPLIDO'
    assert tipos[ids[doc_ip.id]] == 'CERT_FIN_IP_CONSULTAS'

    sin_tipo = conexion.execute(db.text(
        "SELECT count(*) FROM public.certificados WHERE tipo IS NULL"
    )).scalar()
    assert sin_tipo == 0


# ---------------------------------------------------------------------------
# D) Servicios y backrefs
# ---------------------------------------------------------------------------

class TestServicios:

    def test_crear_cert_plazo_cumplido_rellena_tipo(self, app_ctx, arbol_esftt, monkeypatch):
        """El cálculo del vencimiento no es lo que se prueba aquí (lo cubren
        test_362 y test_574): se sustituye para aislar la construcción del
        Certificado."""
        import app.services.certificados as mod
        monkeypatch.setattr(mod, '_datos_plazo_vencido', lambda tarea: {
            'tarea_id': tarea.id, 'fecha_vencimiento': '2026-01-15',
        })
        tarea = arbol_esftt.tarea(
            arbol_esftt.tramite(
                arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=arbol_esftt.solicitud_nueva()),
                'ANALISIS_DOCUMENTAL'),
            'ESPERAR_PLAZO')

        doc = mod.crear_cert(tarea)

        assert doc.certificado.tipo == 'CERT_PLAZO_CUMPLIDO'
        assert doc.certificado.tipo == doc.tipo_doc.codigo
        assert doc.certificado.fase_id is None

    def test_crear_cert_fin_ip_consultas_rellena_tipo(self, app_ctx, arbol_esftt):
        from app import db
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        sol = arbol_esftt.solicitud_nueva()
        fase_ip = arbol_esftt.fase('INFORMACION_PUBLICA', solicitud=sol)
        fase_ip.documento_resultado_id = arbol_esftt.documento(
            sol.expediente_id, 'MODELO_SOLICITUD', '932-cierre-ip').id
        db.session.flush()

        cert = crear_cert_fin_ip_consultas(sol.expediente, sol)

        assert cert is not None
        assert cert.tipo == 'CERT_FIN_IP_CONSULTAS'
        assert cert.tipo == cert.documento.tipo_doc.codigo
        assert cert.fase_id is None


def test_ruta_pdf_del_certificado(app_ctx, arbol_esftt, monkeypatch):
    """La ruta leía `cert.documento.tipo_documento`, que `Documento` no tiene
    (la relación es `tipo_doc`): toda petición acababa en AttributeError desde
    #425. Ahora lee `cert.tipo`."""
    from flask import session
    from flask_login import login_user
    from app.models.usuarios import Rol, Usuario
    from app.modules.expedientes.routes import cert_pdf
    import app.services.certificados as mod

    monkeypatch.setattr(mod, '_datos_plazo_vencido', lambda tarea: {
        'tarea_id': tarea.id, 'fecha_vencimiento': '2026-01-15',
    })
    tarea = arbol_esftt.tarea(
        arbol_esftt.tramite(
            arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=arbol_esftt.solicitud_nueva()),
            'ANALISIS_DOCUMENTAL'),
        'ESPERAR_PLAZO')
    cert = mod.crear_cert(tarea).certificado

    admin = (Usuario.query.join(Usuario.roles)
             .filter(Rol.nombre == 'ADMIN', Usuario.activo.is_(True))
             .order_by(Usuario.id).first())
    assert admin is not None, 'la semilla debe traer un usuario ADMIN activo'

    with app_ctx.test_request_context():
        login_user(admin)
        session['rol_activo_nombre'] = 'ADMIN'
        respuesta = cert_pdf(cert.id)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == 'application/pdf'
    assert f'cert_CERT_PLAZO_CUMPLIDO_{cert.id}.pdf' in respuesta.headers['Content-Disposition']


class TestBackrefsDeFase:

    def test_los_dos_backrefs_existen_y_son_independientes(self, app_ctx, arbol_esftt):
        """`Fase.certificados` (CertificadoFase, auditoría del motor) y
        `Fase.certificados_cumplimiento` (Certificado) conviven en el modelo."""
        from sqlalchemy.orm import configure_mappers
        from app.models.certificados import Certificado
        from app.models.certificados_fase import CertificadoFase
        from app.models.fases import Fase

        configure_mappers()   # los backrefs solo existen tras configurar los mappers
        assert Fase.certificados.property.mapper.class_ is CertificadoFase
        assert Fase.certificados_cumplimiento.property.mapper.class_ is Certificado

        fase = arbol_esftt.fase('RESOLUCION', solicitud=arbol_esftt.solicitud_nueva())
        assert fase.certificados == []
        assert fase.certificados_cumplimiento == []
        assert fase.certificados is not fase.certificados_cumplimiento
