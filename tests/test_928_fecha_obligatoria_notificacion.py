"""
Tests #928 (N1) §4 — fecha administrativa obligatoria por conjunto de tipos.

Extiende la guarda de #885 (antes solo DOC_PROYECTO) a los siete tipos de
justificante de notificación: sin fecha no aportan ninguna y el fallo sería
silencioso (P1). Mismos patrones que test_885_reformados_proyecto.py bloque D
(listener, ingesta) y test_367_sugerencia_documento.py (limpieza por marcador
en el asunto para el test HTTP, que escribe de verdad — sin app_ctx).
"""
import os

import pytest

from app.services.fechas import TIPOS_FECHA_OBLIGATORIA, mensaje_fecha_obligatoria

_JUSTIFICANTES = (
    'JUSTIFICANTE_NOTIFICA_DISPOSICION',
    'JUSTIFICANTE_NOTIFICA',
    'JUSTIFICANTE_POSTAL_1ER',
    'JUSTIFICANTE_POSTAL',
    'JUSTIFICANTE_BANDEJA',
    'JUSTIFICANTE_SIR',
    'JUSTIFICANTE_SEDE',
)


def test_conjunto_tiene_doc_proyecto_y_los_siete_justificantes():
    assert TIPOS_FECHA_OBLIGATORIA == frozenset({'DOC_PROYECTO', *_JUSTIFICANTES})


def test_mensaje_no_vacio_para_cada_tipo():
    for codigo in TIPOS_FECHA_OBLIGATORIA:
        assert mensaje_fecha_obligatoria(codigo)


@pytest.mark.parametrize('codigo', _JUSTIFICANTES)
def test_justificante_sin_fecha_no_llega_a_la_bd(app_ctx, arbol_esftt, codigo):
    """El listener del modelo (documentos.py) rechaza los siete tipos nuevos,
    igual que ya hacía con DOC_PROYECTO (#885)."""
    from app import db

    sol = arbol_esftt.solicitud_nueva()
    with pytest.raises(ValueError, match='fecha administrativa'):
        arbol_esftt.documento(sol.expediente_id, codigo, f'928-{codigo}')
    db.session.rollback()


@pytest.mark.parametrize('codigo', _JUSTIFICANTES)
def test_justificante_con_fecha_se_admite(app_ctx, arbol_esftt, codigo):
    from app.services.reloj_simulado import hoy

    sol = arbol_esftt.solicitud_nueva()
    doc = arbol_esftt.documento(sol.expediente_id, codigo, f'928-con-fecha-{codigo}', fecha=hoy())
    assert doc.fecha_administrativa == hoy()


def test_la_ingesta_rechaza_un_justificante_sin_fecha_antes_de_escribir(app_ctx, arbol_aislado):
    """Mismo patrón que #885 (`ingestar_en_pool`): la puerta que escribe
    pregunta antes de tocar el disco — no deja fichero huérfano."""
    from app.models.tipos_documentos import TipoDocumento
    from app.services.ingesta_pool import ingestar_en_pool
    from app.services.rutas_esftt import ruta_pool_documento

    expediente = arbol_aislado.solicitud_propia().expediente
    tipo = TipoDocumento.query.filter_by(codigo='JUSTIFICANTE_NOTIFICA_DISPOSICION').first()
    assert tipo is not None, 'la semilla debe traer JUSTIFICANTE_NOTIFICA_DISPOSICION'

    with pytest.raises(ValueError, match='fecha administrativa'):
        ingestar_en_pool(expediente, b'contenido', 'disposicion-928.pdf',
                         tipo_doc_id=tipo.id, fecha_administrativa=None)

    directorio = ruta_pool_documento(expediente)
    presentes = os.listdir(directorio) if os.path.isdir(directorio) else []
    assert not any('disposicion-928' in nombre for nombre in presentes), \
        'no debe quedar fichero huérfano en el pool'


# ---------------------------------------------------------------------------
# pool_editar_documento traduce el ValueError a 422 (hallazgo del checklist:
# no lo hacía, ni siquiera ya para DOC_PROYECTO — catch genérico a 500).
# ---------------------------------------------------------------------------

@pytest.fixture
def _limpiar_documentos_928(app):
    yield
    with app.app_context():
        from app import db
        from app.models.documentos import Documento
        Documento.query.filter(
            Documento.asunto.like('%#928 test%')
        ).delete(synchronize_session=False)
        db.session.commit()


def test_pool_editar_documento_traduce_valueerror_a_422(
    usuario_supervisor, expediente_seed, app, _limpiar_documentos_928,
):
    from app import db
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento

    with app.app_context():
        tipo_sede = TipoDocumento.query.filter_by(codigo='JUSTIFICANTE_SEDE').first()
        assert tipo_sede is not None, 'la semilla debe traer JUSTIFICANTE_SEDE'
        doc = Documento(
            expediente_id=expediente_seed, url='bddat://test-928/sin-fecha',
            asunto='#928 test — pool_editar_documento 422',
        )
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id
        tipo_sede_id = tipo_sede.id

    r = usuario_supervisor.post(
        f'/expedientes/{expediente_seed}/documentos/{doc_id}/editar',
        json={'tipo_doc_id': tipo_sede_id})

    assert r.status_code == 422, r.get_data(as_text=True)
    assert 'fecha administrativa' in r.get_json()['error']
