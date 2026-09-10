"""Tests #899 — Las coberturas del análisis por versión (ADR-044 §E bis, R4).

Contra SQL real (app_ctx, SAVEPOINT revertido al terminar), mismo patrón que
test_895_reformado_id_fase.py y el builder ArbolESFTT de conftest.py.

Dos bloques:
  A) Los dos índices únicos parciales de documentos_requisito.
  B) Los dos índices únicos parciales de coberturas_item_tecnico.

No se repite aquí la lógica de evaluar_requisitos/evaluar_items_tecnicos/
tasa_impagada — ya cubierta con stubs en test_192, test_660 y
test_582 respectivamente. Esto prueba lo que esos stubs no pueden: que la
propia BD impide la fila duplicada que la lógica de negocio da por
imposible.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app import db


def _requisito_documental():
    from app.models.requisitos_documentales import RequisitoDocumental
    from app.models.tipos_documentos import TipoDocumento
    tipo_doc = TipoDocumento.query.first()
    assert tipo_doc is not None, 'la semilla debe traer al menos un TipoDocumento'
    req = RequisitoDocumental(tipo_documento_id=tipo_doc.id)
    db.session.add(req)
    db.session.flush()
    return req


def _item_tecnico():
    from app.models.items_tecnicos import ItemTecnico
    item = ItemTecnico(descripcion='#899 test — apartado de prueba')
    db.session.add(item)
    db.session.flush()
    return item


# ---------------------------------------------------------------------------
# A) documentos_requisito — uq_documentos_requisito_no_afectado / _por_version
# ---------------------------------------------------------------------------

class TestIndicesParcialesDocumentosRequisito:

    def test_dos_vinculaciones_version_inicial_colisionan(self, app_ctx):
        """Dos filas reformado_id NULL para el mismo (requisito, solicitud):
        uq_documentos_requisito_no_afectado las rechaza — Postgres no
        deduplica NULL por sí solo en un índice multi-columna."""
        from tests.conftest import ArbolESFTT
        from app.models.requisitos_documentales import DocumentoRequisito

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        requisito = _requisito_documental()
        doc_a = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-a')
        doc_b = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-b')

        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_a.id, reformado_id=None,
        ))
        db.session.flush()

        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_b.id, reformado_id=None,
        ))
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_dos_vinculaciones_misma_version_colisionan(self, app_ctx):
        """Dos filas para el mismo reformado_id (misma versión, no NULL):
        uq_documentos_requisito_por_version las rechaza."""
        from tests.conftest import ArbolESFTT
        from app.models.requisitos_documentales import DocumentoRequisito

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        requisito = _requisito_documental()
        reformado = arbol.reformado(solicitud.expediente_id)
        doc_a = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-a')
        doc_b = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-b')

        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_a.id, reformado_id=reformado.id,
        ))
        db.session.flush()

        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_b.id, reformado_id=reformado.id,
        ))
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_version_inicial_y_version_vigente_coexisten(self, app_ctx):
        """La vinculación de la versión inicial (NULL) y la de un reformado
        concreto SÍ pueden coexistir — es el caso de un requisito afectado
        (p.ej. la tasa) con la tasa antigua y la complementaria del reformado."""
        from tests.conftest import ArbolESFTT
        from app.models.requisitos_documentales import DocumentoRequisito

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        requisito = _requisito_documental()
        reformado = arbol.reformado(solicitud.expediente_id)
        doc_inicial = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-inicial')
        doc_complementaria = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD', '899-compl')

        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_inicial.id, reformado_id=None,
        ))
        db.session.add(DocumentoRequisito(
            requisito_id=requisito.id, solicitud_id=solicitud.id,
            documento_id=doc_complementaria.id, reformado_id=reformado.id,
        ))
        db.session.flush()  # no debe lanzar

        filas = DocumentoRequisito.query.filter_by(
            requisito_id=requisito.id, solicitud_id=solicitud.id
        ).all()
        assert {f.reformado_id for f in filas} == {None, reformado.id}


# ---------------------------------------------------------------------------
# B) coberturas_item_tecnico — uq_coberturas_item_tecnico_no_afectado / _por_version
# ---------------------------------------------------------------------------

class TestIndicesParcialesCoberturaItemTecnico:

    def test_dos_coberturas_version_inicial_colisionan(self, app_ctx):
        from tests.conftest import ArbolESFTT
        from app.models.items_tecnicos import CoberturaItemTecnico

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        item = _item_tecnico()

        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='primera', cubierto=True, reformado_id=None,
        ))
        db.session.flush()

        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='segunda', cubierto=True, reformado_id=None,
        ))
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_dos_coberturas_misma_version_colisionan(self, app_ctx):
        from tests.conftest import ArbolESFTT
        from app.models.items_tecnicos import CoberturaItemTecnico

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        item = _item_tecnico()
        reformado = arbol.reformado(solicitud.expediente_id)

        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='primera', cubierto=True, reformado_id=reformado.id,
        ))
        db.session.flush()

        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='segunda', cubierto=True, reformado_id=reformado.id,
        ))
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_version_inicial_y_version_vigente_coexisten(self, app_ctx):
        """A diferencia de documentos_requisito no hay flag de afección —
        todo ítem técnico es solicitud+versión por definición—, pero el par
        de índices es el mismo: NULL y una versión concreta coexisten."""
        from tests.conftest import ArbolESFTT
        from app.models.items_tecnicos import CoberturaItemTecnico

        arbol = ArbolESFTT(db)
        solicitud = arbol.solicitud_nueva()
        item = _item_tecnico()
        reformado = arbol.reformado(solicitud.expediente_id)

        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='versión inicial', cubierto=True, reformado_id=None,
        ))
        db.session.add(CoberturaItemTecnico(
            item_tecnico_id=item.id, solicitud_id=solicitud.id,
            texto='versión vigente', cubierto=False, reformado_id=reformado.id,
        ))
        db.session.flush()  # no debe lanzar

        filas = CoberturaItemTecnico.query.filter_by(
            item_tecnico_id=item.id, solicitud_id=solicitud.id
        ).all()
        assert {f.reformado_id for f in filas} == {None, reformado.id}
