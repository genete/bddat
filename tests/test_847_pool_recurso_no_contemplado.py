"""Tests issue #847 — un bddat:// no contemplado no debe tumbar un listado.

`info_apertura_documento` falla alto (NotImplementedError) ante un recurso
bddat:// que no es 'certificados' ni 'diagnosticos' — deliberado cuando se
pide abrir ESE documento en concreto (#610). El defecto era que el pool y
los listados que pintan varios documentos a la vez usaban el mismo criterio:
un solo dato malo tumbaba la pantalla entera junto con el resto de filas.
Verificación end-to-end (pool real con un documento bddat:// desconocido,
degradado en pantalla, borrado desde el propio pool) hecha en navegador —
ver PR de #847.
"""
import pytest


class TestInfoAperturaDocumento:

    def test_recurso_no_contemplado_falla_alto_por_defecto(self, arbol_esftt):
        """Comportamiento sin cambios para quien pide abrir un documento concreto."""
        from app.services.detalle_nodo import info_apertura_documento

        sol = arbol_esftt.solicitud_existente()
        # arbol_esftt.documento() fabrica bddat://test-715/<sufijo> — 'test-715'
        # es el recurso (primer segmento), no contemplado por info_apertura_documento.
        doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', 'recurso-desconocido')

        with pytest.raises(NotImplementedError, match='test-715'):
            info_apertura_documento(sol.expediente_id, doc)

    def test_recurso_no_contemplado_se_degrada_en_listado(self, arbol_esftt):
        """Con estricto=False la fila se degrada: sin acción de apertura, sin excepción."""
        from app.services.detalle_nodo import info_apertura_documento

        sol = arbol_esftt.solicitud_existente()
        doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', 'recurso-desconocido')

        info = info_apertura_documento(sol.expediente_id, doc, estricto=False)

        assert info == {
            'enlace': None,
            'externo': False,
            'puede_abrir': False,
            'puede_abrir_carpeta': False,
            'abrir_en': None,
        }

    def test_certificados_y_diagnosticos_no_cambian_con_estricto_false(self, arbol_esftt, app_ctx):
        """El flag solo afecta al camino de error; los recursos conocidos no cambian."""
        from app.services.detalle_nodo import info_apertura_documento

        sol = arbol_esftt.solicitud_existente()
        doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', 'diagnosticos-tmp')
        doc.url = f'bddat://diagnosticos/{doc.id}'

        with app_ctx.test_request_context():
            info_normal    = info_apertura_documento(sol.expediente_id, doc, estricto=True)
            info_degradado = info_apertura_documento(sol.expediente_id, doc, estricto=False)

        assert info_normal == info_degradado
        assert info_normal['abrir_en'] == 'modal'
        assert info_normal['puede_abrir'] is True
