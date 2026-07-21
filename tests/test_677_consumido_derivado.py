"""
Tests #677 — casar un requisito documental ⇒ consumido derivado (ADR-033 §1).

sincronizar_consumido_documental(): deriva el vínculo DocumentoTarea CONSUMIDO
sin gesto manual en la Despensa (oculta para ANALIZAR extendido). Mismo patrón
de test que #667 (mover_a_esftt/mover_a_pool monkeypatcheados, BD real de
desarrollo con rollback por SAVEPOINT — join_transaction_mode='create_savepoint'
en conftest.py absorbe también los commit() explícitos, ver su docstring).
"""
from unittest.mock import patch

import pytest

from app.services import mutaciones_arbol as svc
from tests.test_667_mover_documento_esftt import _tarea_real, _documento_prueba


def _stub_evaluar_requisitos(documentos):
    """Forma mínima que consume sincronizar_consumido_documental."""
    return {'items': [{'documento': doc} for doc in documentos], 'error': False}


class TestSincronizarConsumidoDocumental:

    def test_casar_requisito_llama_mover_a_esftt(self, app_ctx, monkeypatch):
        tarea = _tarea_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — casar requisito')

        llamadas = []
        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: llamadas.append((d.id, t.id)))
        monkeypatch.setattr(svc, 'mover_a_pool', lambda d, e: pytest.fail('no debería llamarse'))

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)

        assert llamadas == [(doc.id, tarea.id)]
        consumidos = {v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO'}
        assert consumidos == {doc.id}

    def test_descasar_ultimo_llama_mover_a_pool(self, app_ctx, monkeypatch):
        tarea = _tarea_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — descasar')

        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: None)
        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)

        llamadas_pool = []
        monkeypatch.setattr(svc, 'mover_a_pool', lambda d, e: llamadas_pool.append(d.id))
        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: pytest.fail('no debería llamarse'))

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([])):
            svc.sincronizar_consumido_documental(tarea)

        assert llamadas_pool == [doc.id]
        assert not [v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_reguardado_sin_cambios_no_repite_movimiento(self, app_ctx, monkeypatch):
        tarea = _tarea_real(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        doc = _documento_prueba(expediente.id, '#677 test — reguardado')

        llamadas = []
        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: llamadas.append(d.id))
        monkeypatch.setattr(svc, 'mover_a_pool', lambda d, e: llamadas.append(('pool', d.id)))

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([doc])):
            svc.sincronizar_consumido_documental(tarea)
            svc.sincronizar_consumido_documental(tarea)  # re-cómputo idéntico

        assert llamadas == [doc.id]  # el segundo pase no repite el movimiento

    def test_sin_requisitos_casados_es_no_op(self, app_ctx, monkeypatch):
        tarea = _tarea_real(app_ctx)
        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: pytest.fail('no debería llamarse'))
        monkeypatch.setattr(svc, 'mover_a_pool', lambda d, e: pytest.fail('no debería llamarse'))

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value=_stub_evaluar_requisitos([])):
            svc.sincronizar_consumido_documental(tarea)

    def test_error_evaluar_requisitos_es_no_op(self, app_ctx, monkeypatch):
        tarea = _tarea_real(app_ctx)
        monkeypatch.setattr(svc, 'mover_a_esftt', lambda d, t: pytest.fail('no debería llamarse'))

        with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
             patch('app.services.mutaciones_arbol.evaluar_requisitos',
                   return_value={'items': [], 'error': True}):
            svc.sincronizar_consumido_documental(tarea)
