"""Tests de #947 (N4, ADR-049 §E/§F) — CERT_CUMPLIMIENTO_FASE.

El certificado que sella el cumplimiento del plazo de resolver: con sello se lee,
sin sello se calcula; el documento citado queda protegido y la única salida es
deshacer el certificado.

Con SQL real (`arbol_aislado`: árbol de un expediente fabricado en el propio test,
sobre el SAVEPOINT de `app_ctx`). Las rutas se llaman directamente dentro de
`test_request_context`, como `test_932::test_ruta_pdf_del_certificado`: así ven
las filas del test sin que salgan de su transacción.

  A) Catálogo
  B) Emitir
  C) Con sello se lee
  D) Deshacer
  E) Protección del documento citado y del propio certificado (D4, punto 5)
  F) Vista y apertura
  G) Endpoints de la API
"""
from contextlib import contextmanager
from datetime import date

import pytest
from flask import session
from flask_login import login_user
from werkzeug.exceptions import HTTPException

_CODIGO = 'CERT_CUMPLIMIENTO_FASE'
_F0 = date(2025, 2, 24)
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
    """Petición con usuario y rol activo: lo que piden la bitácora (`current_user`)
    y `verificar_acceso_expediente` (el rol de la sesión)."""
    with app_ctx.test_request_context(**kwargs):
        login_user(_usuario(rol))
        session['rol_activo_nombre'] = rol
        yield


def _respuesta(resultado):
    """(status, json) de lo que devuelve una vista: `Response` o `(Response, status)`."""
    if isinstance(resultado, tuple):
        return resultado[1], resultado[0].get_json()
    return resultado.status_code, resultado.get_json()


def _con_tipo(solicitud, siglas):
    from app.models.tipos_solicitudes import TipoSolicitud
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el tipo de solicitud {siglas!r}'
    solicitud.tipo_solicitud = tipo
    return solicitud


def _fase_notificada(arbol, justificantes, *, siglas='AAP', codigo_fase='RESOLUCION'):
    """Fase finalizadora con su NOTIFICACION › NOTIFICAR, la resolución consumida
    y los justificantes `[(tipo_doc, fecha, rol)]`. Devuelve (fase, tarea, docs)."""
    solicitud = _con_tipo(arbol.solicitud_propia(), siglas)
    solicitud.documento_solicitud.fecha_administrativa = _DISPARO
    fase = arbol.fase(codigo_fase, solicitud=solicitud)
    tarea = arbol.tarea(arbol.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    exp_id = solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'947-{tarea.id}-res'),
                   'CONSUMIDO')
    docs = []
    for i, (tipo, fecha, rol) in enumerate(justificantes):
        doc = arbol.documento(exp_id, tipo, f'947-{tarea.id}-{i}', fecha=fecha)
        arbol.vincular(tarea, doc, rol)
        docs.append(doc)
    arbol.db.session.expire(fase, ['tramites'])
    return fase, tarea, docs


_NOTIFICA = [('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO'),
             ('JUSTIFICANTE_NOTIFICA', _F2, 'PRODUCIDO')]


def _emitir(app_ctx, fase):
    from app.services.cert_cumplimiento_fase import emitir
    with _peticion(app_ctx):
        return emitir(fase)


def _deshacer(app_ctx, fase, justificacion='El justificante citado no era el bueno'):
    from app.services.cert_cumplimiento_fase import deshacer
    with _peticion(app_ctx):
        return deshacer(fase, justificacion=justificacion)


def _cerrar(arbol, fase):
    """`Fase.finalizada` es exactamente `documento_resultado_id NOT NULL`."""
    doc = arbol.documento(fase.solicitud.expediente_id, 'RESOLUCION', f'cierre-947-{fase.id}')
    fase.documento_resultado_id = doc.id
    arbol.db.session.flush()
    return doc


def _certificados_de(fase):
    from app.models.certificados import Certificado
    return Certificado.query.filter_by(fase_id=fase.id).all()


def _ultima_bitacora(tabla, registro_id):
    from app.models.bitacora import Bitacora
    return (Bitacora.query.filter_by(tabla=tabla, registro_id=registro_id)
            .order_by(Bitacora.id.desc()).first())


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
# B) Emitir
# ---------------------------------------------------------------------------

class TestEmitir:

    def test_fase_no_finalizadora_es_error(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        res = _emitir(app_ctx, fase)
        assert res.error and not res.emitido
        assert _certificados_de(fase) == []

    def test_sin_notificacion_informe_y_nada_creado(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        fase, _tarea, _ = _fase_notificada(arbol_aislado, [])
        exp_id = fase.solicitud.expediente_id
        antes = Documento.query.filter_by(expediente_id=exp_id).count()

        res = _emitir(app_ctx, fase)

        assert not res.emitido and res.error is None and res.bloqueo is None
        assert 'No consta la notificación al titular' in res.a_dict()['falta']
        assert Documento.query.filter_by(expediente_id=exp_id).count() == antes
        assert _certificados_de(fase) == []

    def test_sin_la_tarea_notificar_lo_dice(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        res = _emitir(app_ctx, fase)
        assert 'todavía no tiene la tarea' in res.a_dict()['falta']

    def test_con_notificacion_emite(self, app_ctx, arbol_aislado):
        fase, _tarea, (disposicion, _final) = _fase_notificada(arbol_aislado, _NOTIFICA)

        res = _emitir(app_ctx, fase)

        assert res.emitido and not res.ya_emitido
        (cert,) = _certificados_de(fase)
        assert cert.id == res.certificado_id
        assert (cert.tipo, cert.fase_id) == (_CODIGO, fase.id)
        assert cert.datos == {'documento_id': disposicion.id}
        doc = cert.documento
        assert doc.id == res.documento_id
        assert doc.fecha_administrativa is None
        assert doc.url == f'bddat://certificados/{cert.id}'
        assert doc.tipo_doc.codigo == _CODIGO
        assert doc.vinculos_tarea == []
        entrada = _ultima_bitacora('documentos', doc.id)
        assert entrada.operacion == 'CREAR'
        assert entrada.detalle['documento_citado_id'] == disposicion.id

    def test_segunda_emision_devuelve_el_existente(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        primera = _emitir(app_ctx, fase)
        segunda = _emitir(app_ctx, fase)
        assert segunda.emitido and segunda.ya_emitido and segunda.error is None
        assert segunda.certificado_id == primera.certificado_id
        assert len(_certificados_de(fase)) == 1

    def test_con_la_fase_cerrada_se_permite(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _cerrar(arbol_aislado, fase)
        assert _emitir(app_ctx, fase).emitido

    def test_la_puerta_cerrada(self, app_ctx, arbol_aislado):
        from app.services.invariantes_esftt import check_invariante
        sin, _, _ = _fase_notificada(arbol_aislado, [])
        con, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        no_final = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=con.solicitud)

        def emitir(fase):
            return check_invariante('EMITIR', 'FASE', fase.id, tipo_codigo=_CODIGO)

        assert emitir(sin) is not None and emitir(sin).puede_escapar is False
        assert emitir(no_final) is not None
        assert emitir(con) is None


# ---------------------------------------------------------------------------
# C) Con sello se lee
# ---------------------------------------------------------------------------

class TestLecturaDelSello:

    def _justificante_anterior(self, arbol, fase, tarea):
        """Tras emitir, se vincula a la misma tarea un justificante con fecha
        anterior: el cálculo lo elegiría a él."""
        doc = arbol.documento(fase.solicitud.expediente_id, 'JUSTIFICANTE_POSTAL_1ER',
                              f'947-anterior-{tarea.id}', fecha=_F0)
        arbol.vincular(tarea, doc, 'CONSUMIDO')
        arbol.db.session.expire(tarea, ['vinculos_documento'])
        return doc

    def test_se_lee_el_citado_aunque_haya_otro_anterior(self, app_ctx, arbol_aislado):
        from app.services.notificaciones import (
            calcular_documento_cumplimiento_fase, documento_cumplimiento_fase,
        )
        fase, tarea, (disposicion, _) = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        anterior = self._justificante_anterior(arbol_aislado, fase, tarea)

        assert calcular_documento_cumplimiento_fase(fase) is anterior
        assert documento_cumplimiento_fase(fase) is disposicion

    def test_el_plazo_del_acto_cumple_con_la_fecha_del_citado(
            self, app_ctx, arbol_aislado, monkeypatch):
        from app.services.plazos import plazos_de_la_solicitud
        monkeypatch.setattr('app.services.plazos._hoy', lambda: date(2025, 4, 1))
        fase, tarea, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        self._justificante_anterior(arbol_aislado, fase, tarea)

        (aap,) = plazos_de_la_solicitud(fase.solicitud)
        assert aap.estado == 'CUMPLIDO'
        assert aap.fecha_cumplimiento == _F1

    def test_aap_y_aac_en_una_resolucion_leen_el_mismo_sello(self, app_ctx, arbol_aislado):
        from app.services.actos_solicitud import actos_de
        fase, tarea, (disposicion, _) = _fase_notificada(arbol_aislado, _NOTIFICA,
                                                         siglas='AAP+AAC')
        _emitir(app_ctx, fase)
        self._justificante_anterior(arbol_aislado, fase, tarea)

        actos = {a.siglas: a.documento_cumplimiento for a in actos_de(fase.solicitud)}
        assert actos['AAP'] is disposicion and actos['AAC'] is disposicion

    def test_tras_deshacer_vuelve_el_calculo(self, app_ctx, arbol_aislado):
        from app.services.notificaciones import documento_cumplimiento_fase
        fase, tarea, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        anterior = self._justificante_anterior(arbol_aislado, fase, tarea)

        assert _deshacer(app_ctx, fase).ok
        arbol_aislado.db.session.expire(fase, ['certificados_cumplimiento'])
        assert documento_cumplimiento_fase(fase) is anterior


# ---------------------------------------------------------------------------
# D) Deshacer
# ---------------------------------------------------------------------------

class TestDeshacer:

    def test_sin_justificacion(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        res = _deshacer(app_ctx, fase, justificacion='  ')
        assert not res.ok and 'justificación' in res.error
        assert len(_certificados_de(fase)) == 1

    def test_sin_certificado(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        res = _deshacer(app_ctx, fase)
        assert not res.ok and 'no tiene certificado' in res.error

    def test_con_la_fase_cerrada_bloquea(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        _cerrar(arbol_aislado, fase)

        res = _deshacer(app_ctx, fase)

        assert not res.ok and res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert 'Reábrala' in res.bloqueo.norma_compilada
        assert len(_certificados_de(fase)) == 1

    def test_borra_certificado_y_documento_y_deja_rastro(self, app_ctx, arbol_aislado):
        from app.models.certificados import Certificado
        from app.models.documentos import Documento
        fase, _, (disposicion, _) = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)

        res = _deshacer(app_ctx, fase)

        assert res.ok
        assert arbol_aislado.db.session.get(Certificado, emision.certificado_id) is None
        assert arbol_aislado.db.session.get(Documento, emision.documento_id) is None
        entrada = _ultima_bitacora('fases', fase.id)
        assert entrada.operacion == 'ALTERAR'
        assert entrada.detalle['accion'] == 'DESHACER_CERT_CUMPLIMIENTO_FASE'
        assert entrada.detalle['justificacion'] == 'El justificante citado no era el bueno'
        assert entrada.detalle['documento_citado_id'] == disposicion.id
        assert 'escape' not in entrada.detalle

    def test_vinculado_a_una_tarea_lo_dice_y_no_borra(self, app_ctx, arbol_aislado):
        """H2: la Despensa deja vincular el certificado; borrarlo con el vínculo
        vivo moriría en IntegrityError."""
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        from app.models.documentos import Documento
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        elaborar = arbol_aislado.tarea(arbol_aislado.tramite(fase, 'ELABORACION'), 'ELABORAR')
        arbol_aislado.vincular(elaborar, doc_cert, 'CONSUMIDO')
        arbol_aislado.db.session.expire(doc_cert, ['vinculos_tarea'])

        res = _deshacer(app_ctx, fase)

        assert not res.ok and 'desvincúlelo' in res.error
        assert len(_certificados_de(fase)) == 1


# ---------------------------------------------------------------------------
# E) Protección (D4 y punto 5)
# ---------------------------------------------------------------------------

def _editar_en_pool(app_ctx, doc, cuerpo):
    from app.modules.expedientes.routes import pool_editar_documento
    with _peticion(app_ctx, method='POST', json=cuerpo):
        return _respuesta(pool_editar_documento(doc.expediente_id, doc.id))


def _borrar_en_pool(app_ctx, doc):
    from app.modules.expedientes.routes import pool_borrar_documento
    with _peticion(app_ctx, method='POST'):
        return _respuesta(pool_borrar_documento(doc.expediente_id, doc.id))


class TestProteccionEnElPool:

    @pytest.fixture
    def citado(self, app_ctx, arbol_aislado):
        fase, _, (disposicion, _) = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        return disposicion

    @pytest.mark.parametrize('cuerpo', [
        {'fecha_administrativa': '2025-03-01'},
        {'fecha_administrativa': ''},
        {'url': 'otra/ruta.pdf'},
    ])
    def test_fecha_o_fichero_del_citado(self, app_ctx, citado, cuerpo):
        status, datos = _editar_en_pool(app_ctx, citado, cuerpo)
        assert status == 422
        assert 'deshaga el certificado de cumplimiento' in datos['error']
        assert citado.fecha_administrativa == _F1

    def test_tipo_del_citado(self, app_ctx, citado):
        from app.models.tipos_documentos import TipoDocumento
        otro = TipoDocumento.query.filter_by(codigo='JUSTIFICANTE_POSTAL_1ER').first()
        status, _ = _editar_en_pool(app_ctx, citado, {'tipo_doc_id': otro.id})
        assert status == 422

    def test_el_asunto_del_citado_si(self, app_ctx, citado):
        status, datos = _editar_en_pool(app_ctx, citado, {'asunto': 'Puesta a disposición'})
        assert (status, datos['ok']) == (200, True)
        assert citado.asunto == 'Puesta a disposición'

    def test_reenviar_los_mismos_valores_si(self, app_ctx, citado):
        """El formulario completo del pool manda todo aunque no cambie."""
        status, _ = _editar_en_pool(app_ctx, citado, {
            'fecha_administrativa': _F1.isoformat(),
            'tipo_doc_id': citado.tipo_doc_id,
            'url': '',
            'observaciones': 'revisado',
        })
        assert status == 200

    def test_el_propio_certificado_no_se_edita(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        from app.models.documentos import Documento
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        status, datos = _editar_en_pool(app_ctx, doc_cert, {'fecha_administrativa': '2025-03-01'})
        assert status == 422 and 'certificado de cumplimiento de la fase' in datos['error']

    def test_borrar_el_citado_dice_por_que(self, app_ctx, citado):
        status, datos = _borrar_en_pool(app_ctx, citado)
        assert status == 422 and 'deshaga el certificado de cumplimiento' in datos['error']

    def test_borrar_el_certificado_422_y_no_500(self, app_ctx, arbol_aislado):
        """Hallazgo del issue: no cuelga de ninguna tarea ni FK de anclaje."""
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        from app.models.documentos import Documento
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        status, datos = _borrar_en_pool(app_ctx, doc_cert)
        assert status == 422 and 'deshágalo desde el inspector de la fase' in datos['error']
        assert arbol_aislado.db.session.get(Documento, emision.documento_id) is not None

    def test_borrar_el_documento_que_cierra_una_fase_422(self, app_ctx, arbol_aislado):
        """H4: `fases.documento_resultado_id` sin ON DELETE, sin vínculo a tarea."""
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        doc = _cerrar(arbol_aislado, fase)
        status, datos = _borrar_en_pool(app_ctx, doc)
        assert status == 422 and 'cierra la fase' in datos['error']


class TestProteccionDelVinculo:

    def _editar(self, app_ctx, tarea, consumidos, producido):
        from app.services import mutaciones_arbol as svc
        with _peticion(app_ctx):
            return svc.editar_tarea(tarea, documentos_consumidos_ids=consumidos,
                                    documento_producido_id=producido, notas=None)

    def test_desvincular_el_citado_bloquea(self, app_ctx, arbol_aislado):
        fase, tarea, (disposicion, final) = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        res_consumida = next(v.documento_id for v in tarea.vinculos_documento
                             if v.documento_id not in (disposicion.id, final.id))

        res = self._editar(app_ctx, tarea, [res_consumida], final.id)

        assert not res.ok and res.bloqueo is not None
        assert 'deshaga el certificado' in res.bloqueo.norma_compilada
        assert any(v.documento_id == disposicion.id for v in tarea.vinculos_documento)

    def test_cambiar_el_rol_del_citado_bloquea(self, app_ctx, arbol_aislado):
        """POSTAL con el 1.er intento correcto: el citado es el PRODUCIDO."""
        fase, tarea, (postal,) = _fase_notificada(
            arbol_aislado, [('JUSTIFICANTE_POSTAL', _F1, 'PRODUCIDO')])
        _emitir(app_ctx, fase)
        consumidos = [v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']

        res = self._editar(app_ctx, tarea, consumidos + [postal.id], None)

        assert not res.ok and res.bloqueo is not None

    def test_postal_el_segundo_intento_llega_despues(self, app_ctx, arbol_aislado):
        """D4: se certifica con el acuse del 1.er intento fallido; el justificante
        del 2.º llega después a la misma tarea."""
        fase, tarea, (primero,) = _fase_notificada(
            arbol_aislado, [('JUSTIFICANTE_POSTAL_1ER', _F1, 'CONSUMIDO')])
        assert _emitir(app_ctx, fase).emitido
        segundo = arbol_aislado.documento(fase.solicitud.expediente_id, 'JUSTIFICANTE_POSTAL',
                                          f'947-2o-{tarea.id}', fecha=_F2)
        consumidos = [v.documento_id for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']

        res = self._editar(app_ctx, tarea, consumidos, segundo.id)

        assert res.ok, res.error or res.bloqueo
        assert tarea.documento_producido.id == segundo.id

    def test_otro_documento_de_la_tarea_si_se_desvincula(self, app_ctx, arbol_aislado):
        fase, tarea, (disposicion, final) = _fase_notificada(arbol_aislado, _NOTIFICA)
        _emitir(app_ctx, fase)
        res = self._editar(app_ctx, tarea, [disposicion.id], final.id)
        assert res.ok, res.error or res.bloqueo


# ---------------------------------------------------------------------------
# F) Vista y apertura
# ---------------------------------------------------------------------------

def _vista_html(app_ctx, fase):
    from app.modules.expedientes.routes import cert_cumplimiento_fase_vista
    with _peticion(app_ctx):
        return cert_cumplimiento_fase_vista(fase.solicitud.expediente_id, fase.id)


class TestVista:

    def test_sin_emitir_borrador_y_nada_creado(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA, siglas='AAP+AAC')
        html = _vista_html(app_ctx, fase)
        assert 'Borrador — sin emitir' in html
        assert 'Documento que se citaría' in html
        assert 'AAP, AAC' in html
        assert _certificados_de(fase) == []

    def test_sin_notificacion_dice_que_falta(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, [])
        html = _vista_html(app_ctx, fase)
        assert 'No consta la notificación al titular' in html
        assert 'No se ha creado ningún documento' in html

    def test_emitido_con_huella(self, app_ctx, arbol_aislado):
        fase, _, (disposicion, _) = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        html = _vista_html(app_ctx, fase)
        assert 'Certificado emitido' in html
        assert f'Certificado nº {emision.certificado_id}' in html
        assert f'Documento nº {emision.documento_id}' in html
        assert f'nº {disposicion.id}' in html
        assert 'Notifica (electrónica)' in html

    def test_fase_no_finalizadora_404(self, app_ctx, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        with pytest.raises(HTTPException) as exc:
            _vista_html(app_ctx, fase)
        assert exc.value.code == 404

    def test_apertura_del_documento_del_certificado_en_modal(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        from app.services.detalle_nodo import info_apertura_documento
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        with _peticion(app_ctx):
            apertura = info_apertura_documento(doc_cert.expediente_id, doc_cert)
        assert apertura['abrir_en'] == 'modal'
        assert apertura['enlace'].endswith(f'/fases/{fase.id}/certificado-cumplimiento')

    def test_acceso_directo_al_pdf_400(self, app_ctx, arbol_aislado):
        from app.models.documentos import Documento
        from app.modules.expedientes.routes import cert_pdf, pool_descargar_documento
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        emision = _emitir(app_ctx, fase)
        doc_cert = arbol_aislado.db.session.get(Documento, emision.documento_id)
        with _peticion(app_ctx):
            for llamada in (lambda: pool_descargar_documento(doc_cert.expediente_id, doc_cert.id),
                            lambda: cert_pdf(emision.certificado_id)):
                with pytest.raises(HTTPException) as exc:
                    llamada()
                assert exc.value.code == 400

    def test_inspector_de_la_fase(self, app_ctx, arbol_aislado):
        from app.services.detalle_nodo import detalle_de_nodo
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        expediente = fase.solicitud.expediente
        no_final = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=fase.solicitud)
        with _peticion(app_ctx):
            antes = detalle_de_nodo(expediente, 'fase', fase.id)
            assert 'cert_cumplimiento' not in detalle_de_nodo(expediente, 'fase', no_final.id)
        assert antes['cert_cumplimiento']['emitido'] is False

        emision = _emitir(app_ctx, fase)
        with _peticion(app_ctx):
            despues = detalle_de_nodo(expediente, 'fase', fase.id)
        cc = despues['cert_cumplimiento']
        assert (cc['emitido'], cc['documento_id']) == (True, emision.documento_id)
        assert any(d['id'] == emision.documento_id and d['abrir_en'] == 'modal'
                   for d in despues['documentos'])


# ---------------------------------------------------------------------------
# G) Endpoints de la API
# ---------------------------------------------------------------------------

def _post(app_ctx, fase, *, rol='SUPERVISOR', expediente_id=None):
    from app.routes.api_expedientes import emitir_cert_cumplimiento_fase_nodo
    with _peticion(app_ctx, rol=rol, method='POST', json={}):
        return _respuesta(emitir_cert_cumplimiento_fase_nodo(
            expediente_id or fase.solicitud.expediente_id, fase.id))


def _delete(app_ctx, fase, justificacion='No era el justificante bueno'):
    from app.routes.api_expedientes import deshacer_cert_cumplimiento_fase_nodo
    with _peticion(app_ctx, method='DELETE', json={'justificacion': justificacion}):
        return _respuesta(deshacer_cert_cumplimiento_fase_nodo(
            fase.solicitud.expediente_id, fase.id))


class TestEndpoints:

    def test_sin_gestionar_estructura_403(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        status, _ = _post(app_ctx, fase, rol='ADMINISTRATIVO')
        assert status == 403
        assert _certificados_de(fase) == []

    def test_fase_de_otro_expediente_404(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        otro = arbol_aislado.solicitud_propia().expediente_id
        status, _ = _post(app_ctx, fase, expediente_id=otro)
        assert status == 404

    def test_emitir_y_deshacer(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        status, datos = _post(app_ctx, fase)
        assert status == 200 and datos['emitido'] is True
        assert datos['enlace_vista'].endswith(f'/fases/{fase.id}/certificado-cumplimiento')

        status, datos = _delete(app_ctx, fase)
        assert status == 200 and datos['ok'] is True

    def test_sin_notificacion_200_con_lo_que_falta(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, [])
        status, datos = _post(app_ctx, fase)
        assert status == 200 and datos['emitido'] is False and datos['falta']

    def test_con_la_fase_cerrada_emite_y_no_deshace(self, app_ctx, arbol_aislado):
        fase, _, _ = _fase_notificada(arbol_aislado, _NOTIFICA)
        _cerrar(arbol_aislado, fase)
        status, datos = _post(app_ctx, fase)
        assert status == 200 and datos['emitido'] is True

        status, datos = _delete(app_ctx, fase)
        assert status == 422 and datos['puede_escapar'] is False
        assert 'Reábrala' in datos['motivo']
