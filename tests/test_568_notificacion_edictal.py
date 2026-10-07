"""
Tests #568 (ADR-052 §G) — aplicar el anuncio publicado de un NOTIFICACION_EDICTAL
a las notificaciones que cierra: una copia del anuncio por NOTIFICAR, como
producido y con resultado CORRECTA. Fichero propio porque la acción es nueva y
ningún test existente cubre `aplicar_anuncio_edicto`.

Fallo silencioso que evita: que la copia del anuncio de algún interesado lleve
otra fecha que la del BOE (su fecha de efectos) o se aplique a una notificación
que no estaba agotada, y ese interesado quede notificado en falso sin que nada
lo avise.

Lo demás del edicto lo cubren tests existentes, ajustados en #568: la escalada
por acuses (test_558), el canal EDICTO del edicto directo (test_928_hook) y las
fechas de cumplimiento y efectos (test_928_notificaciones_fechas).

BD de tests con rollback por SAVEPOINT (`arbol_aislado`, que trae `almacen_tmp`: el
almacén de pruebas donde los documentos guardan su contenido).
"""
import pytest

from app import db
from app.models.tipos_documentos import TipoDocumento
from app.services import mutaciones_arbol as svc
from app.services.notificaciones import fecha_efectos
from tests.conftest import documento_con_contenido_de_prueba


@pytest.fixture
def con_usuario(app_ctx):
    """La bitácora de `editar_tarea` necesita `current_user` real."""
    from flask_login import login_user
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    with app_ctx.test_request_context():
        login_user(usuario)
        yield usuario


def _doc(expediente_id, codigo, nombre, fecha):
    tipo = TipoDocumento.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el tipo de documento {codigo}'
    return documento_con_contenido_de_prueba(
        nombre, b'%PDF-1.4 ' + nombre.encode(), expediente_id=expediente_id,
        tipo_doc_id=tipo.id, asunto='#568 test', fecha_administrativa=fecha)


def _guardar(tarea, consumidos=(), producido=None):
    res = svc.editar_tarea(tarea, documentos_consumidos_ids=[d.id for d in consumidos],
                           documento_producido_id=producido.id if producido else None,
                           notas=None)
    assert res.ok, res.error
    return res


def test_el_anuncio_se_aplica_con_su_fecha_a_cada_notificacion(con_usuario, arbol_aislado):
    """Dos notificaciones de la fase —una postal agotada, otra sin ningún
    justificante (edicto directo)— se cierran con el mismo anuncio publicado.
    Una tercera con un solo intento fallido no se ofrece ni se admite."""
    from datetime import timedelta
    from app.services.reloj_simulado import hoy

    def hace(dias):
        return hoy() - timedelta(days=dias)

    arbol = arbol_aislado
    fase = arbol.fase('RESOLUCION_DUP', solicitud=arbol.solicitud_propia())
    exp_id = fase.solicitud.expediente_id
    notificacion = arbol.tramite(fase, 'NOTIFICACION')
    resolucion = _doc(exp_id, 'RESOLUCION', 'resolucion.pdf', hace(40))

    agotada = arbol.tarea(notificacion, 'NOTIFICAR')
    _guardar(agotada, consumidos=[
        resolucion,
        _doc(exp_id, 'JUSTIFICANTE_POSTAL_1ER', '1er.pdf', hace(35)),
        _doc(exp_id, 'JUSTIFICANTE_POSTAL_2DO', '2do.pdf', hace(33)),
    ])
    directa = arbol.tarea(notificacion, 'NOTIFICAR')
    _guardar(directa, consumidos=[resolucion])
    un_intento = arbol.tarea(notificacion, 'NOTIFICAR')
    _guardar(un_intento, consumidos=[
        resolucion, _doc(exp_id, 'JUSTIFICANTE_POSTAL_1ER', '1er-b.pdf', hace(35))])

    edicto = arbol.tramite(fase, 'NOTIFICACION_EDICTAL')
    espera = arbol.tarea(edicto, 'ESPERAR_PLAZO')
    publicacion = hace(5)
    _guardar(espera, producido=_doc(exp_id, 'ANUNCIO_PUBLICADO', 'boe.pdf', publicacion))

    assert {t.id for t in svc.notificaciones_edictables(edicto)} == {agotada.id, directa.id}
    assert not svc.aplicar_anuncio_edicto(edicto, [un_intento.id]).ok

    res = svc.aplicar_anuncio_edicto(edicto, [agotada.id, directa.id])

    assert res.ok, res.error
    assert res.ids == [agotada.id, directa.id]
    for tarea, canal in ((agotada, 'POSTAL'), (directa, 'EDICTO')):
        db.session.refresh(tarea)
        assert tarea.notificacion.resultado == 'CORRECTA'
        assert tarea.notificacion.canal == canal
        assert fecha_efectos(tarea).fecha == publicacion
