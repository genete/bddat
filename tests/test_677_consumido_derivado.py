"""
Tests #677 — casar un requisito documental ⇒ consumido derivado (ADR-033 §1).

sincronizar_consumido_documental(): deriva el vínculo DocumentoTarea CONSUMIDO
sin gesto manual en la Despensa (oculta para ANALIZAR extendido). BD real con
rollback por SAVEPOINT — join_transaction_mode='create_savepoint' en
conftest.py absorbe también los commit() explícitos, ver su docstring. Vincular
es solo una fila: no mueve ningún fichero (ADR-050 §C).
"""
from unittest.mock import patch

import pytest

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.services import mutaciones_arbol as svc


def _tarea_real():
    """Tarea ANALIZAR sin vínculos documentales previos, fabricada por el test (#428).

    Fabricarla, además de no saltar nunca, garantiza lo que el test necesita de
    verdad: que el diff de `sincronizar_consumido_documental()` no pise ni libere
    documentos ajenos, cosa que la tarea encontrada solo cumplía mientras nadie
    tramitara por ahí.

    El test que la llame debe traer `app_ctx` y `fs_tmp`: el expediente nace por
    la vía real, que guarda el documento de solicitud en el almacén.
    """
    from tests.conftest import ArbolESFTT

    return ArbolESFTT(db).tarea_propia('ANALIZAR')


def _documento_prueba(expediente_id, asunto):
    doc = Documento(
        expediente_id=expediente_id,
        url='no-relevante-para-este-test.pdf',  # nada lo lee ni lo mueve: vincular es solo una fila
        asunto=asunto,
    )
    db.session.add(doc)
    db.session.flush()
    return doc


def _stub_evaluar_requisitos(documentos):
    """Forma mínima que consume sincronizar_consumido_documental."""
    return {'items': [{'documento': doc} for doc in documentos], 'error': False}


def _dos_tareas_analizar_cadena(app_ctx):
    """Dos tareas ANALIZAR en trámites distintos de la cadena de subsanación
    (ANALISIS_DOCUMENTAL, REQUERIMIENTO_SUBSANACION), montadas en una fase nueva
    de una solicitud real — evita interferir con vínculos ya existentes en BD
    (#826, mismo patrón de montaje que test_711_cierre_fase_cadena._montar_fase)."""
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    def _tipo(modelo, codigo):
        fila = modelo.query.filter_by(codigo=codigo).first()
        if fila is None:
            pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
        return fila

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    tipo_analizar = _tipo(TipoTarea, 'ANALIZAR')
    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
    db.session.add(fase)
    db.session.flush()

    tareas = []
    for codigo_tramite in ('ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION'):
        tramite = Tramite(fase_id=fase.id, tipo_tramite_id=_tipo(TipoTramite, codigo_tramite).id)
        db.session.add(tramite)
        db.session.flush()
        tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_analizar.id)
        db.session.add(tarea)
        db.session.flush()
        tareas.append(tarea)

    return tareas[0], tareas[1]


class TestSincronizarConsumidoDocumental:

    def test_casar_requisito_deriva_el_consumido(self, app_ctx, fs_tmp):
        tarea = _tarea_real()
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — casar requisito')

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)

        consumidos = {v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO'}
        assert consumidos == {doc.id}

    def test_descasar_ultimo_quita_el_consumido(self, app_ctx, fs_tmp):
        tarea = _tarea_real()
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — descasar')

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([])):
            svc.sincronizar_consumido_documental(tarea)

        assert not [v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_reguardado_sin_cambios_no_duplica_el_vinculo(self, app_ctx, fs_tmp):
        tarea = _tarea_real()
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — reguardado')

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)
            svc.sincronizar_consumido_documental(tarea)  # re-cómputo idéntico

        consumidos = [v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']
        assert [v.documento_id for v in consumidos] == [doc.id]  # el segundo pase no repite el vínculo

    def test_sin_requisitos_casados_es_no_op(self, app_ctx, fs_tmp):
        tarea = _tarea_real()

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([])):
            svc.sincronizar_consumido_documental(tarea)

        assert not tarea.vinculos_documento

    def test_error_evaluar_requisitos_es_no_op(self, app_ctx, fs_tmp):
        tarea = _tarea_real()

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value={'items': [], 'error': True}):
            svc.sincronizar_consumido_documental(tarea)

        assert not tarea.vinculos_documento


class TestNoAcumulaEntreVueltas:
    """#826 — evaluar_requisitos casa por solicitud, no por vuelta: sin acotar a
    la cadena, cada ANALIZAR reclamaría también lo que ya consumió una vuelta
    anterior."""

    def test_no_reclama_lo_consumido_por_otra_tarea_de_la_cadena(self, app_ctx):
        tarea_anterior, tarea_actual = _dos_tareas_analizar_cadena(app_ctx)
        expediente = tarea_actual.tramite.fase.solicitud.expediente
        doc_vuelta_anterior = _documento_prueba(expediente.id, '#826 test — ya consumido en vuelta anterior')
        doc_esta_vuelta = _documento_prueba(expediente.id, '#826 test — nuevo de esta vuelta')

        tarea_anterior.vinculos_documento.append(
            DocumentoTarea(documento_id=doc_vuelta_anterior.id, rol='CONSUMIDO'))
        db.session.flush()

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc_vuelta_anterior, doc_esta_vuelta])):
            svc.sincronizar_consumido_documental(tarea_actual)

        consumidos = {v.documento_id for v in tarea_actual.vinculos_documento if v.rol == 'CONSUMIDO'}
        assert consumidos == {doc_esta_vuelta.id}, (
            'La tarea actual no debe reclamar un documento que ya consumió otra '
            'tarea ANALIZAR de la misma cadena de subsanación'
        )

    def test_no_toca_lo_ya_consumido_por_la_vuelta_anterior(self, app_ctx):
        """La exclusión no debe quitarle el vínculo a la tarea anterior (esa tarea
        no es la que se está sincronizando)."""
        tarea_anterior, tarea_actual = _dos_tareas_analizar_cadena(app_ctx)
        expediente = tarea_actual.tramite.fase.solicitud.expediente
        doc_vuelta_anterior = _documento_prueba(expediente.id, '#826 test — no debe tocarse')

        tarea_anterior.vinculos_documento.append(
            DocumentoTarea(documento_id=doc_vuelta_anterior.id, rol='CONSUMIDO'))
        db.session.flush()

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc_vuelta_anterior])):
            svc.sincronizar_consumido_documental(tarea_actual)

        consumidos_anterior = {v.documento_id for v in tarea_anterior.vinculos_documento if v.rol == 'CONSUMIDO'}
        assert consumidos_anterior == {doc_vuelta_anterior.id}
