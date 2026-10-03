"""#1007 (ADR-050 §C) — `documentos.nombre_fichero`: el nombre que se enseña.

Fallo silencioso que evita: el nombre original de un fichero (el que le puso quien lo
subió) se pierde sin error —la url solo lo guarda saneado y con el prefijo del hash— o
sigue enseñándose el de un fichero que ya no es el del documento.

Se llama a la vista como función dentro del SAVEPOINT de `app_ctx` (como `test_824`):
por HTTP el commit escaparía a la BD (#641).
"""
import pytest
from flask_login import login_user


def _documento_ingerido(alta_propia, nombre_original):
    """Un documento entrado al pool por la vía real, con su fecha y su tipo."""
    from app import db
    from app.models.tipos_documentos import TipoDocumento
    from app.services.ingesta_pool import ingestar_en_pool
    from app.services.reloj_simulado import hoy

    tipo = TipoDocumento.query.filter_by(codigo='MODELO_SOLICITUD').first()
    assert tipo is not None, "la semilla debe traer el TipoDocumento 'MODELO_SOLICITUD'"
    resultado = ingestar_en_pool(
        alta_propia.expediente, b'%PDF-1.4 contenido de prueba', nombre_original,
        tipo_doc_id=tipo.id, fecha_administrativa=hoy())
    db.session.flush()
    return resultado.documento


def _editar(app_ctx, expediente_id, doc_id, payload):
    from flask import session
    from app.models.usuarios import Usuario
    from app.modules.expedientes.routes import pool_editar_documento

    usuario = Usuario.query.order_by(Usuario.id).first()
    assert usuario is not None, 'la semilla debe traer algún usuario'
    with app_ctx.test_request_context(json=payload):
        login_user(usuario)
        session['rol_activo_nombre'] = 'SUPERVISOR'
        resultado = pool_editar_documento(expediente_id, doc_id)
    respuesta, codigo = resultado if isinstance(resultado, tuple) else (resultado, 200)
    return respuesta.get_json(), codigo


class TestIngesta:

    def test_guarda_el_original_saneado_sin_el_prefijo_del_pool(self, alta_propia):
        """El `?` y el salto de línea no valen en un nombre de fichero de Windows; el
        prefijo del hash sí está en la url, pero no es lo que se enseña."""
        doc = _documento_ingerido(alta_propia, 'Informe técnico?\n2026.pdf')

        assert doc.nombre_fichero == 'Informe técnico__2026.pdf'
        assert doc.url.endswith('_Informe técnico__2026.pdf'), 'la url sí lleva el prefijo del hash'
        assert doc.nombre_visible() == 'Informe técnico__2026.pdf'


class TestEdicionDeLaUrl:

    def test_cambiar_la_url_suelta_el_nombre_del_fichero_anterior(self, alta_propia, app_ctx):
        doc = _documento_ingerido(alta_propia, 'antiguo.pdf')

        cuerpo, _ = _editar(app_ctx, doc.expediente_id, doc.id, {'url': 'otra/carpeta/nuevo.pdf'})

        assert cuerpo['ok'] is True
        assert doc.nombre_fichero is None
        assert doc.nombre_visible() == 'nuevo.pdf'

    @pytest.mark.parametrize('payload', [{'asunto': 'Solo cambia el asunto'}, {'url': None}])
    def test_si_la_url_no_cambia_conserva_el_nombre(self, alta_propia, app_ctx, payload):
        doc = _documento_ingerido(alta_propia, 'antiguo.pdf')

        cuerpo, _ = _editar(app_ctx, doc.expediente_id, doc.id, payload)

        assert cuerpo['ok'] is True
        assert doc.nombre_fichero == 'antiguo.pdf'
