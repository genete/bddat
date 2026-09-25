"""Tests de #956 (N4b, ADR-049 §F) — CERT_CIERRE_FASE.

El certificado que cierra la fase finalizadora: informe «¿cómo voy?» siempre,
emisión solo sin pendientes (y con el certificado de cumplimiento), foto fija en
`datos`, sin escape a nivel de fase, y se deshace reabriendo la fase.

Con SQL real (`arbol_aislado`) y las rutas llamadas dentro de
`test_request_context`, como `test_947`.

  A) Catálogo
  B) Revisar
  C) Emitir
  D) Foto fija
  E) Reabrir
  F) editar_fase y el editor (D6)
  G) Pool
  H) Vista, apertura, inspector y endpoints
"""
from contextlib import contextmanager
from datetime import date

import pytest
from flask import session
from flask_login import login_user
from werkzeug.exceptions import HTTPException

_CODIGO = 'CERT_CIERRE_FASE'
_FRASE = 'cerrar finalizadora'
_F1 = date(2025, 3, 3)
_F2 = date(2025, 3, 10)
_DISPARO = date(2025, 1, 7)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _usuario(rol):
    from app.models.usuarios import Rol, Usuario
    usuario = (Usuario.query.join(Usuario.roles)
               .filter(Rol.nombre == rol, Usuario.activo.is_(True))
               .order_by(Usuario.id).first())
    assert usuario is not None, f'la semilla debe traer un usuario {rol} activo'
    return usuario


@contextmanager
def _peticion(app_ctx, rol='SUPERVISOR', **kwargs):
    with app_ctx.test_request_context(**kwargs):
        login_user(_usuario(rol))
        session['rol_activo_nombre'] = rol
        yield


def _respuesta(resultado):
    if isinstance(resultado, tuple):
        return resultado[1], resultado[0].get_json()
    return resultado.status_code, resultado.get_json()


def _resultado(codigo='FAVORABLE'):
    from app.models.tipos_resultados_fases import TipoResultadoFase
    tipo = TipoResultadoFase.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el resultado de fase {codigo!r}'
    return tipo


_NOTIFICA = [('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO'),
             ('JUSTIFICANTE_NOTIFICA', _F2, 'PRODUCIDO')]
_POSTAL = [('JUSTIFICANTE_POSTAL', _F1, 'PRODUCIDO')]


def _fase(arbol, justificantes=_NOTIFICA, *, canal='NOTIFICA', resultado='CORRECTA',
          sede_justificacion=None, con_resultado=True, solicitud=None,
          codigo_fase='RESOLUCION'):
    """Fase finalizadora con su NOTIFICACION › NOTIFICAR completa: la resolución
    consumida, los justificantes y la fila `notificaciones`. Devuelve (fase, tarea, docs)."""
    from app.models.tipos_solicitudes import TipoSolicitud
    if solicitud is None:
        solicitud = arbol.solicitud_propia()
        solicitud.tipo_solicitud = TipoSolicitud.query.filter_by(siglas='AAP').first()
        solicitud.documento_solicitud.fecha_administrativa = _DISPARO
    fase = arbol.fase(codigo_fase, solicitud=solicitud)
    tarea = arbol.tarea(arbol.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    exp_id = solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'956-{tarea.id}-res'),
                   'CONSUMIDO')
    docs = []
    for i, (tipo, fecha, rol) in enumerate(justificantes):
        doc = arbol.documento(exp_id, tipo, f'956-{tarea.id}-{i}', fecha=fecha)
        arbol.vincular(tarea, doc, rol)
        docs.append(doc)
    if resultado is not None:
        arbol.notificacion(tarea, resultado=resultado, canal=canal,
                           sede_justificacion=sede_justificacion)
    if con_resultado:
        fase.resultado_fase = _resultado()
    arbol.db.session.flush()
    arbol.db.session.expire(fase, ['tramites'])
    arbol.db.session.expire(tarea)
    return fase, tarea, docs


def _cumplir(app_ctx, fase):
    from app.services.cert_cumplimiento_fase import emitir
    with _peticion(app_ctx):
        res = emitir(fase)
    assert res.emitido, res.error or res.revision.falta
    return res


def _fase_lista(app_ctx, arbol, **kwargs):
    """Fase sin nada pendiente: notificada, con resultado y cumplimiento certificado."""
    fase, tarea, docs = _fase(arbol, **kwargs)
    _cumplir(app_ctx, fase)
    return fase, tarea, docs


def _revisar(app_ctx, fase):
    from app.services.cert_cierre_fase import revisar
    with _peticion(app_ctx):
        return revisar(fase)


def _emitir(app_ctx, fase, confirmacion=None):
    from app.services.cert_cierre_fase import emitir
    with _peticion(app_ctx):
        return emitir(fase, confirmacion=confirmacion)


def _reabrir(app_ctx, fase, justificacion='Faltaba notificar a un interesado'):
    from app.services import mutaciones_arbol as svc
    with _peticion(app_ctx):
        return svc.reabrir_fase(fase, justificacion=justificacion)


def _segunda_finalizadora(arbol, fase):
    """Otra finalizadora abierta en la misma solicitud (RESOLUCION + RESOLUCION_DUP):
    cerrar la primera no la resuelve."""
    return arbol.fase('RESOLUCION_DUP', solicitud=fase.solicitud)


def _cierres_de(fase):
    from app.models.certificados import Certificado
    return Certificado.query.filter_by(fase_id=fase.id, tipo=_CODIGO).all()


def _ultima_bitacora(tabla, registro_id):
    from app.models.bitacora import Bitacora
    return (Bitacora.query.filter_by(tabla=tabla, registro_id=registro_id)
            .order_by(Bitacora.id.desc()).first())


def _lineas(bloques, campo):
    return [linea for b in bloques for linea in getattr(b, campo)]


# ---------------------------------------------------------------------------
# A) Catálogo
# ---------------------------------------------------------------------------

def test_el_tipo_existe_y_es_requerido(app_ctx):
    from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS
    from app.models.tipos_documentos import TipoDocumento
    tipo = TipoDocumento.query.filter_by(codigo=_CODIGO).first()
    assert tipo is not None and tipo.origen == 'INTERNO'
    assert _CODIGO in REGISTROS_REQUERIDOS['TipoDocumento']


# ---------------------------------------------------------------------------
# B) Revisar
# ---------------------------------------------------------------------------

class TestRevisar:

    def test_sin_cumplimiento_pendiente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase(arbol_aislado)
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio
        assert any(b.titulo == 'Notificación al titular' for b in informe.pendientes)

    def test_limpia_y_la_fase_pendiente_de_cerrar_no_cuenta(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        assert fase.pdte_cierre
        informe = _revisar(app_ctx, fase)
        assert informe.limpio, [b.pendiente for b in informe.pendientes]
        relato = _lineas(informe.bloques, 'relato')
        assert any('Consta la notificación al titular' in r for r in relato)
        assert any('Resultado de la fase: ' in r for r in relato)

    def test_tramite_sin_terminar_pendiente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        tramite = arbol_aislado.tramite(fase, 'ELABORACION')
        arbol_aislado.tarea(tramite, 'ELABORAR')
        arbol_aislado.db.session.expire(fase, ['tramites'])
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio
        assert any(b.nodo == ('tramite', tramite.id) for b in informe.pendientes)

    def test_sede_pendiente_pendiente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado, justificantes=_POSTAL, canal='POSTAL')
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio
        assert any('sede electrónica' in p for p in _lineas(informe.pendientes, 'pendiente'))

    def test_sede_justificada_salvado_con_su_texto(self, app_ctx, arbol_aislado):
        from app.services import bitacora as bitacora_svc
        fase, tarea, _ = _fase_lista(app_ctx, arbol_aislado, justificantes=_POSTAL,
                                     canal='POSTAL',
                                     sede_justificacion='El titular no tiene sede')
        usuario = _usuario('SUPERVISOR')
        bitacora_svc.registrar(usuario.id, 'ALTERAR', 'notificaciones', tarea.notificacion.id,
                               detalle={'accion': 'JUSTIFICAR_SEDE',
                                        'texto': 'El titular no tiene sede'})

        informe = _revisar(app_ctx, fase)

        assert informe.limpio, [b.pendiente for b in informe.pendientes]
        salvado = _lineas(informe.salvados, 'salvado')
        assert len(salvado) == 1
        assert 'sede electrónica' in salvado[0]
        assert '«El titular no tiene sede»' in salvado[0]
        assert 'forzó' not in salvado[0]
        if usuario.siglas:
            assert usuario.siglas in salvado[0]

    def test_notificar_incorrecta_pendiente(self, app_ctx, arbol_aislado):
        fase, tarea, _ = _fase(arbol_aislado, resultado='INCORRECTA')
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio
        assert any(b.nodo == ('tramite', tarea.tramite_id) for b in informe.pendientes)

    def test_sin_resultado_pendiente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado, con_resultado=False)
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio
        assert any('resultado de la fase' in p
                   for p in _lineas(informe.pendientes, 'pendiente'))

    def test_sin_tramites_pendiente(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        informe = _revisar(app_ctx, fase)
        assert not informe.limpio

    def test_no_finalizadora(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        informe = _revisar(app_ctx, fase)
        assert not informe.finalizadora and not informe.limpio and informe.falta

    def test_cierra_solicitud_con_una_y_con_dos_finalizadoras(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        assert _revisar(app_ctx, fase).cierra_solicitud is True

        otra = _segunda_finalizadora(arbol_aislado, fase)
        assert _revisar(app_ctx, fase).cierra_solicitud is False

        doc = arbol_aislado.documento(fase.solicitud.expediente_id, 'RESOLUCION', 'dup-cerrada')
        otra.documento_resultado_id = doc.id
        arbol_aislado.db.session.flush()
        assert _revisar(app_ctx, fase).cierra_solicitud is True


# ---------------------------------------------------------------------------
# C) Emitir
# ---------------------------------------------------------------------------

class TestEmitir:

    def test_con_pendientes_informe_y_nada_creado(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        fase, _, _ = _fase(arbol_aislado)
        exp_id = fase.solicitud.expediente_id
        antes = Documento.query.filter_by(expediente_id=exp_id).count()

        res = _emitir(app_ctx, fase, _FRASE)

        assert not res.emitido and res.error is None and res.bloqueo is None
        assert res.informe.pendientes
        assert Documento.query.filter_by(expediente_id=exp_id).count() == antes
        assert _cierres_de(fase) == [] and not fase.finalizada

    def test_limpio_emite_y_cierra(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        _segunda_finalizadora(arbol_aislado, fase)   # sin confirmación: no resuelve

        res = _emitir(app_ctx, fase)

        assert res.emitido and not res.ya_emitido, res.error
        (cert,) = _cierres_de(fase)
        assert (cert.id, cert.fase_id) == (res.certificado_id, fase.id)
        assert cert.datos['bloques'] and cert.datos['fase']
        doc = cert.documento
        assert doc.fecha_administrativa is None
        assert doc.url == f'bddat://certificados/{cert.id}'
        assert doc.tipo_doc.codigo == _CODIGO
        assert fase.documento_resultado_id == doc.id
        assert fase.estado == 'FINALIZADA'
        entrada = _ultima_bitacora('documentos', doc.id)
        assert entrada.operacion == 'CREAR' and entrada.detalle['certificado_id'] == cert.id

    def test_segunda_emision_devuelve_el_existente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        primera = _emitir(app_ctx, fase, _FRASE)
        segunda = _emitir(app_ctx, fase, _FRASE)
        assert segunda.emitido and segunda.ya_emitido
        assert segunda.certificado_id == primera.certificado_id
        assert len(_cierres_de(fase)) == 1

    def test_fase_no_finalizadora_bloquea(self, app_ctx, arbol_aislado):
        from app.services.invariantes_esftt import check_invariante
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        res = _emitir(app_ctx, fase)
        assert res.error and not res.emitido
        bloqueo = check_invariante('EMITIR', 'FASE', fase.id, tipo_codigo=_CODIGO)
        assert bloqueo is not None and bloqueo.puede_escapar is False

    def test_cierra_solicitud_sin_confirmacion_error_y_nada_creado(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        for confirmacion in (None, '', 'cerrar'):
            res = _emitir(app_ctx, fase, confirmacion)
            assert res.requiere_confirmacion and res.error and not res.emitido
        assert _cierres_de(fase) == [] and not fase.finalizada

        res = _emitir(app_ctx, fase, '  Cerrar Finalizadora ')
        assert res.emitido
        assert fase.solicitud.estado.startswith('RESUELTA')

    def test_la_puerta_cerrada(self, app_ctx, arbol_aislado):
        from app.services.invariantes_esftt import check_invariante
        sin_cumplimiento, _, _ = _fase(arbol_aislado)
        lista, _, _ = _fase_lista(app_ctx, arbol_aislado)

        def emitir(fase):
            return check_invariante('EMITIR', 'FASE', fase.id, tipo_codigo=_CODIGO)

        assert emitir(sin_cumplimiento) is not None
        assert emitir(sin_cumplimiento).puede_escapar is False
        assert emitir(lista) is None


# ---------------------------------------------------------------------------
# D) Foto fija (D4)
# ---------------------------------------------------------------------------

def _vista_html(app_ctx, fase):
    from app.modules.expedientes.routes import cert_cierre_fase_vista
    with _peticion(app_ctx):
        return cert_cierre_fase_vista(fase.solicitud.expediente_id, fase.id)


def test_foto_fija_no_cambia_si_cambia_un_documento(app_ctx, arbol_aislado):
    fase, _, (disposicion, _final) = _fase_lista(app_ctx, arbol_aislado)
    _emitir(app_ctx, fase, _FRASE)
    antes = _vista_html(app_ctx, fase)
    assert '03/03/2025' in antes

    # El sellado de ADR-036 no protege la fecha de los documentos (#954): se cambia
    # en la BD a pelo, como podría cambiar por cualquier otra vía.
    disposicion.fecha_administrativa = date(2025, 2, 1)
    arbol_aislado.db.session.flush()

    despues = _vista_html(app_ctx, fase)
    assert '03/03/2025' in despues and '01/02/2025' not in despues


# ---------------------------------------------------------------------------
# E) Reabrir
# ---------------------------------------------------------------------------

class TestReabrir:

    def test_borra_certificado_y_documento_y_vacia_los_campos(self, app_ctx, arbol_aislado):
        from app.models.certificados import Certificado
        from app.models.documentos import Documento
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        _segunda_finalizadora(arbol_aislado, fase)
        emision = _emitir(app_ctx, fase)

        res = _reabrir(app_ctx, fase)

        assert res.ok, res.error or res.bloqueo
        assert arbol_aislado.db.session.get(Certificado, emision.certificado_id) is None
        assert arbol_aislado.db.session.get(Documento, emision.documento_id) is None
        assert fase.documento_resultado_id is None and fase.resultado_fase_id is None
        entrada = _ultima_bitacora('fases', fase.id)
        assert entrada.operacion == 'ALTERAR'
        assert entrada.detalle['accion'] == 'REABRIR' and entrada.detalle['escape'] is True
        assert entrada.detalle['justificacion'] == 'Faltaba notificar a un interesado'
        assert entrada.detalle['documento_id'] == emision.documento_id
        assert entrada.detalle['certificado_id'] == emision.certificado_id

    def test_sin_justificacion(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        _segunda_finalizadora(arbol_aislado, fase)
        _emitir(app_ctx, fase)
        res = _reabrir(app_ctx, fase, justificacion='')
        assert not res.ok and len(_cierres_de(fase)) == 1

    def test_resolucion_firme_bloquea_sin_cambios(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        emision = _emitir(app_ctx, fase, _FRASE)

        res = _reabrir(app_ctx, fase)

        assert not res.ok and res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert 'resolución es firme' in res.bloqueo.norma_compilada
        assert fase.documento_resultado_id == emision.documento_id
        assert len(_cierres_de(fase)) == 1

    def test_el_siguiente_certificado_relata_la_reversion(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        _segunda_finalizadora(arbol_aislado, fase)
        _emitir(app_ctx, fase)
        assert _reabrir(app_ctx, fase).ok
        arbol_aislado.db.session.expire(fase, ['certificados_cumplimiento'])
        fase.resultado_fase = _resultado()
        arbol_aislado.db.session.flush()

        res = _emitir(app_ctx, fase)

        assert res.emitido, res.error or [b.pendiente for b in res.informe.pendientes]
        (cert,) = _cierres_de(fase)
        relato = [r for b in cert.datos['bloques'] for r in b['relato']]
        assert any('dejó sin efecto su certificado de cierre anterior' in r
                   and '«Faltaba notificar a un interesado»' in r for r in relato)
        # Relatada como historia, no como escape salvado.
        salvado = [s for b in cert.datos['bloques'] for s in b['salvado']]
        assert not any('reabrir' in s for s in salvado)

    def test_legado_cerrada_con_documento_se_reabre(self, app_ctx, arbol_aislado):
        """Una finalizadora cerrada antes de #956 (documento del pool, sin certificado)."""
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        _segunda_finalizadora(arbol_aislado, fase)
        doc = arbol_aislado.documento(fase.solicitud.expediente_id, 'RESOLUCION', 'legado')
        fase.documento_resultado_id = doc.id
        arbol_aislado.db.session.flush()

        res = _reabrir(app_ctx, fase)

        assert res.ok, res.error or res.bloqueo
        assert fase.documento_resultado_id is None


# ---------------------------------------------------------------------------
# F) editar_fase y el editor (D6)
# ---------------------------------------------------------------------------

def _editar_fase(app_ctx, fase, **kwargs):
    from app.services import mutaciones_arbol as svc
    datos = dict(resultado_fase_id=fase.resultado_fase_id,
                 documento_resultado_id=fase.documento_resultado_id,
                 observaciones=fase.observaciones)
    datos.update(kwargs)
    with _peticion(app_ctx):
        return svc.editar_fase(fase, **datos)


class TestEditarFase:

    def test_finalizadora_con_documento_resultado_bloquea(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        doc = arbol_aislado.documento(fase.solicitud.expediente_id, 'RESOLUCION', 'editor')

        res = _editar_fase(app_ctx, fase, documento_resultado_id=doc.id,
                           justificacion='Quiero cerrarla así')

        assert not res.ok and res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert 'Cierre de la fase' in res.bloqueo.norma_compilada
        assert not fase.finalizada

    def test_finalizadora_resultado_y_observaciones_si(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase(arbol_aislado, con_resultado=False)
        res = _editar_fase(app_ctx, fase, resultado_fase_id=_resultado().id,
                           observaciones='Revisado')
        assert res.ok, res.error or res.bloqueo
        assert fase.resultado_fase_id == _resultado().id and fase.observaciones == 'Revisado'

    def test_no_finalizadora_como_hoy_con_el_forzable(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        arbol_aislado.tarea(arbol_aislado.tramite(fase, 'ANALISIS_DOCUMENTAL'), 'ANALIZAR')
        arbol_aislado.db.session.expire(fase, ['tramites'])
        doc = arbol_aislado.documento(solicitud.expediente_id, 'RESOLUCION', 'no-final')

        res = _editar_fase(app_ctx, fase, documento_resultado_id=doc.id)
        assert not res.ok and res.bloqueo.puede_escapar is True

        res = _editar_fase(app_ctx, fase, documento_resultado_id=doc.id,
                           justificacion='Se cierra igualmente')
        assert res.ok and fase.finalizada

    def test_esquema_del_editor(self, app_ctx, arbol_aislado):
        from app.services.esquema_editable import esquema_de_nodo
        fase, _, _ = _fase(arbol_aislado)
        no_final = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=fase.solicitud)
        expediente = fase.solicitud.expediente

        def campos(f):
            return [c['campo'] for c in esquema_de_nodo(expediente, 'fase', f.id)['campos']]

        assert campos(fase) == ['resultado_fase_id', 'observaciones']
        assert 'documento_resultado_id' in campos(no_final)


# ---------------------------------------------------------------------------
# G) Pool
# ---------------------------------------------------------------------------

class TestPool:

    @pytest.fixture
    def doc_cert(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        emision = _emitir(app_ctx, fase, _FRASE)
        return arbol_aislado.db.session.get(Documento, emision.documento_id)

    def test_editar_el_certificado_422(self, app_ctx, doc_cert):
        from app.modules.expedientes.routes import pool_editar_documento
        with _peticion(app_ctx, method='POST', json={'fecha_administrativa': '2025-03-01'}):
            status, datos = _respuesta(pool_editar_documento(doc_cert.expediente_id, doc_cert.id))
        assert status == 422 and 'certificado de cierre de la fase' in datos['error']

    def test_borrar_el_certificado_422_con_la_salida(self, app_ctx, arbol_aislado, doc_cert):
        from app.models.documentos import Documento
        from app.modules.expedientes.routes import pool_borrar_documento
        with _peticion(app_ctx, method='POST'):
            status, datos = _respuesta(pool_borrar_documento(doc_cert.expediente_id, doc_cert.id))
        assert status == 422 and 'reabra la fase' in datos['error']
        assert arbol_aislado.db.session.get(Documento, doc_cert.id) is not None


# ---------------------------------------------------------------------------
# H) Vista, apertura, inspector y endpoints
# ---------------------------------------------------------------------------

class TestVista:

    def test_sin_emitir_200_y_nada_creado(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase(arbol_aislado)
        html = _vista_html(app_ctx, fase)
        assert 'Qué falta' in html and 'Notificación al titular' in html
        assert _cierres_de(fase) == []

    def test_lista_avisa_de_la_irreversibilidad(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        html = _vista_html(app_ctx, fase)
        assert 'lista para cerrar' in html and 'no podrá reabrirse' in html

    def test_emitido_con_huella(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        emision = _emitir(app_ctx, fase, _FRASE)
        html = _vista_html(app_ctx, fase)
        assert 'Fase cerrada — certificado emitido' in html
        assert f'Certificado nº {emision.certificado_id}' in html
        assert f'Documento nº {emision.documento_id}' in html
        assert f'Fase nº {fase.id}' in html

    def test_apertura_y_descarga(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        from app.modules.expedientes.routes import pool_descargar_documento
        from app.services.detalle_nodo import info_apertura_documento
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        emision = _emitir(app_ctx, fase, _FRASE)
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        with _peticion(app_ctx):
            apertura = info_apertura_documento(doc_cert.expediente_id, doc_cert)
            with pytest.raises(HTTPException) as exc:
                pool_descargar_documento(doc_cert.expediente_id, doc_cert.id)
        assert apertura['abrir_en'] == 'modal'
        assert apertura['enlace'].endswith(f'/fases/{fase.id}/certificado-cierre')
        assert exc.value.code == 400

    def test_inspector_de_la_fase(self, app_ctx, arbol_aislado):
        from app.services.detalle_nodo import detalle_de_nodo
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        expediente = fase.solicitud.expediente
        no_final = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=fase.solicitud)
        with _peticion(app_ctx):
            assert 'cert_cierre' not in detalle_de_nodo(expediente, 'fase', no_final.id)
            antes = detalle_de_nodo(expediente, 'fase', fase.id)['cert_cierre']
        # Con la fase de análisis abierta, cerrar la de resolución no resuelve.
        assert antes['emitido'] is False and antes['cierra_solicitud'] is False
        assert antes['enlace_vista'].endswith('/certificado-cierre')

        no_final.documento_resultado_id = arbol_aislado.documento(
            expediente.id, 'RESOLUCION', 'cierre-no-final').id
        arbol_aislado.db.session.flush()
        emision = _emitir(app_ctx, fase, _FRASE)
        with _peticion(app_ctx):
            despues = detalle_de_nodo(expediente, 'fase', fase.id)
        assert despues['cert_cierre']['emitido'] is True
        assert despues['cert_cierre']['certificado_id'] == emision.certificado_id
        assert any(d['id'] == emision.documento_id and d['abrir_en'] == 'modal'
                   for d in despues['documentos'])


def _post(app_ctx, fase, cuerpo=None, *, rol='SUPERVISOR', expediente_id=None):
    from app.routes.api_expedientes import emitir_cert_cierre_fase_nodo
    with _peticion(app_ctx, rol=rol, method='POST', json=cuerpo or {}):
        return _respuesta(emitir_cert_cierre_fase_nodo(
            expediente_id or fase.solicitud.expediente_id, fase.id))


class TestEndpoints:

    def test_sin_gestionar_estructura_403(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        status, _ = _post(app_ctx, fase, {'confirmacion': _FRASE}, rol='ADMINISTRATIVO')
        assert status == 403 and _cierres_de(fase) == []

    def test_fase_de_otro_expediente_404(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        otro = arbol_aislado.solicitud_propia().expediente_id
        status, _ = _post(app_ctx, fase, expediente_id=otro)
        assert status == 404

    def test_con_pendientes_200_y_nada_creado(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase(arbol_aislado)
        status, datos = _post(app_ctx, fase)
        assert status == 200 and datos['emitido'] is False and datos['pendientes']
        assert datos['enlace_vista'].endswith(f'/fases/{fase.id}/certificado-cierre')
        assert _cierres_de(fase) == []

    def test_frase_obligatoria_y_despues_emite(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_lista(app_ctx, arbol_aislado)
        status, datos = _post(app_ctx, fase)
        assert status == 422 and datos['requiere_confirmacion'] is True
        assert _cierres_de(fase) == []

        status, datos = _post(app_ctx, fase, {'confirmacion': _FRASE})
        assert status == 200 and datos['emitido'] is True and datos['ya_emitido'] is False

        # Con la fase ya cerrada por él, devuelve el existente.
        status, datos = _post(app_ctx, fase)
        assert status == 200 and datos['ya_emitido'] is True
