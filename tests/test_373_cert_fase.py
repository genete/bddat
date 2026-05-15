"""Tests de integración issue #373 — generación automática de CERT_FIN_INSTRUCCION.

Requieren:
  - BD con migración 373_cert_fin_instruccion aplicada.
  - Fixture app_ctx (rollback automático por test).

Escenarios:
  A) Crear fase RESOLUCION con condiciones válidas → cert en BD + PDF en disco
  B) Motor bloquea la creación → no se genera cert
  C) reglas_evaluadas del cert contiene las reglas esperadas
  D) PDF existe en la ruta ruta_pdf del cert
"""
import os
import time
from datetime import date

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tipo(model_class, **filtros):
    obj = model_class.query.filter_by(**filtros).first()
    assert obj is not None, (
        f'{model_class.__name__} con {filtros} no encontrado — '
        f'¿migración 373 aplicada?'
    )
    return obj


def _crear_expediente(db, tipo_exp):
    from app.models import Expediente, Proyecto
    proyecto = Proyecto(
        titulo='Test cert fase #373',
        descripcion='Test',
        fecha=date(2026, 1, 1),
        finalidad='Test',
        emplazamiento='Test',
    )
    db.session.add(proyecto)
    db.session.flush()
    numero_at = int(time.time() * 1000) % 10_000_000
    exp = Expediente(numero_at=numero_at, proyecto=proyecto, tipo_expediente=tipo_exp)
    db.session.add(exp)
    db.session.flush()
    return exp


def _crear_solicitud(db, expediente, tipo_solicitud):
    from app.models import Solicitud, Entidad
    entidad = Entidad.query.first()
    assert entidad is not None, 'Tabla entidades vacía — seed necesario'
    sol = Solicitud(expediente=expediente, tipo_solicitud=tipo_solicitud, entidad=entidad)
    db.session.add(sol)
    db.session.flush()
    return sol


def _crear_fase_doc(db, solicitud, tipo_fase, resultado=None):
    """Crea una fase con documento_resultado (fase finalizada)."""
    from app.models import Fase, Documento
    doc = Documento(
        expediente=solicitud.expediente,
        url=f'test://doc-{tipo_fase.codigo}',
        fecha_administrativa=date(2025, 1, 1),
    )
    db.session.add(doc)
    db.session.flush()
    fase = Fase(
        solicitud=solicitud,
        tipo_fase=tipo_fase,
        resultado_fase=resultado,
        documento_resultado=doc,
    )
    db.session.add(fase)
    db.session.flush()
    return fase


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def ctx(app_ctx):
    from app.models import TipoFase, TipoSolicitud, TipoExpediente, TipoResultadoFase
    return {
        'tf_resolucion': _get_tipo(TipoFase, codigo='RESOLUCION'),
        'ts_aap':        _get_tipo(TipoSolicitud, siglas='AAP'),
        'resultado_fav': _get_tipo(TipoResultadoFase, codigo='FAVORABLE'),
        'tipo_exp':      TipoExpediente.query.first(),
    }


# ---------------------------------------------------------------------------
# A) Crear fase RESOLUCION → se genera cert en BD
# ---------------------------------------------------------------------------

def test_crear_fase_genera_cert_en_bd(app_ctx, ctx):
    """Al crear fase RESOLUCION, se persiste CertificadoFase en BD."""
    from app import db
    from app.models import TipoFase
    from app.models.certificados_fase import CertificadoFase
    from app.services.generador_cert import generar_certificado_fase
    from app.services.assembler import auditar_multi
    from app.services.motor_reglas import AuditoriaResult

    exp = _crear_expediente(db, ctx['tipo_exp'])
    sol = _crear_solicitud(db, exp, ctx['ts_aap'])

    tipo_fase = ctx['tf_resolucion']
    from app.models import Fase
    fase = Fase(solicitud=sol, tipo_fase=tipo_fase)
    db.session.add(fase)
    db.session.flush()

    # Crear auditoría sintética (sin reglas reales configuradas en test)
    auditoria = AuditoriaResult(
        permitido=True,
        accion='CREAR',
        sujeto=f'Distribucion/AAP/RESOLUCION',
        reglas_evaluadas=[],
        variables_ctx={},
    )

    cert = generar_certificado_fase(exp, fase, auditoria, 'CERT_FIN_INSTRUCCION')
    db.session.flush()

    assert cert.id is not None
    assert cert.tipo_cert == 'CERT_FIN_INSTRUCCION'
    assert cert.expediente_id == exp.id
    assert cert.fase_id == fase.id
    assert cert.accion == 'CREAR'
    assert cert.reglas_evaluadas == []

    # Verificar que existe en BD
    cert_bd = CertificadoFase.query.filter_by(
        expediente_id=exp.id, tipo_cert='CERT_FIN_INSTRUCCION'
    ).first()
    assert cert_bd is not None


# ---------------------------------------------------------------------------
# B) Crear fase RESOLUCION → se genera Documento en BD
# ---------------------------------------------------------------------------

def test_crear_fase_genera_documento_en_bd(app_ctx, ctx):
    """Al generar el cert se crea también una fila en documentos."""
    from app import db
    from app.models import Fase, Documento
    from app.models.tipos_documentos import TipoDocumento
    from app.services.generador_cert import generar_certificado_fase
    from app.services.motor_reglas import AuditoriaResult

    exp = _crear_expediente(db, ctx['tipo_exp'])
    sol = _crear_solicitud(db, exp, ctx['ts_aap'])

    fase = Fase(solicitud=sol, tipo_fase=ctx['tf_resolucion'])
    db.session.add(fase)
    db.session.flush()

    td_cert = TipoDocumento.query.filter_by(codigo='CERT_FIN_INSTRUCCION').first()
    assert td_cert is not None, 'CERT_FIN_INSTRUCCION no está en tipos_documentos — ¿migración aplicada?'

    auditoria = AuditoriaResult(
        permitido=True, accion='CREAR',
        sujeto='Distribucion/AAP/RESOLUCION',
        reglas_evaluadas=[], variables_ctx={},
    )

    cert = generar_certificado_fase(exp, fase, auditoria, 'CERT_FIN_INSTRUCCION')
    db.session.flush()

    doc = Documento.query.filter_by(
        expediente_id=exp.id, tipo_doc_id=td_cert.id
    ).first()
    assert doc is not None
    assert doc.tipo_contenido == 'application/pdf'


# ---------------------------------------------------------------------------
# C) reglas_evaluadas serializado correctamente en JSON
# ---------------------------------------------------------------------------

def test_cert_reglas_evaluadas_en_json(app_ctx, ctx):
    """cert.reglas_evaluadas contiene la lista serializada de ResultadoRegla."""
    from app import db
    from app.models import Fase
    from app.services.generador_cert import generar_certificado_fase
    from app.services.motor_reglas import AuditoriaResult, ResultadoRegla

    exp = _crear_expediente(db, ctx['tipo_exp'])
    sol = _crear_solicitud(db, exp, ctx['ts_aap'])

    fase = Fase(solicitud=sol, tipo_fase=ctx['tf_resolucion'])
    db.session.add(fase)
    db.session.flush()

    rr = ResultadoRegla(
        regla_id=99,
        sujeto_patron='Distribucion/AAP/RESOLUCION',
        descripcion='Regla de test',
        norma_compilada='Art. 1 — Ley test',
        url_norma='https://example.com',
        efecto='BLOQUEAR',
        disparada=True,
        neutralizada=True,
        variables_trigger={'var': 1},
    )
    auditoria = AuditoriaResult(
        permitido=True, accion='CREAR',
        sujeto='Distribucion/AAP/RESOLUCION',
        reglas_evaluadas=[rr], variables_ctx={'var': 1},
    )

    cert = generar_certificado_fase(exp, fase, auditoria, 'CERT_FIN_INSTRUCCION')
    db.session.flush()

    assert len(cert.reglas_evaluadas) == 1
    regla_json = cert.reglas_evaluadas[0]
    assert regla_json['regla_id'] == 99
    assert regla_json['descripcion'] == 'Regla de test'
    assert regla_json['disparada'] is True
    assert regla_json['neutralizada'] is True


# ---------------------------------------------------------------------------
# D) PDF existe en disco en la ruta guardada
# ---------------------------------------------------------------------------

def test_cert_pdf_existe_en_disco(app_ctx, ctx):
    """El PDF generado existe físicamente en la ruta cert.ruta_pdf."""
    from app import db
    from app.models import Fase
    from app.services.generador_cert import generar_certificado_fase
    from app.services.motor_reglas import AuditoriaResult

    exp = _crear_expediente(db, ctx['tipo_exp'])
    sol = _crear_solicitud(db, exp, ctx['ts_aap'])

    fase = Fase(solicitud=sol, tipo_fase=ctx['tf_resolucion'])
    db.session.add(fase)
    db.session.flush()

    auditoria = AuditoriaResult(
        permitido=True, accion='CREAR',
        sujeto='Distribucion/AAP/RESOLUCION',
        reglas_evaluadas=[], variables_ctx={},
    )

    cert = generar_certificado_fase(exp, fase, auditoria, 'CERT_FIN_INSTRUCCION')
    db.session.flush()

    assert cert.ruta_pdf is not None
    assert os.path.isfile(cert.ruta_pdf), (
        f'PDF no encontrado en disco: {cert.ruta_pdf}'
    )
    assert os.path.getsize(cert.ruta_pdf) > 0


