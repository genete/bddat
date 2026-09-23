"""
Tests #928 (N1, 928c) — endpoints del contenedor NOTIFICAR (§6 del issue).

  - GET .../notificar: payload nuevo (lista `notificaciones`, `fechas`
    calculadas, `sede`, `estado`, `resultados_validos`, huecos N2/N5).
  - POST .../notificar y .../notificar/parsear: eliminados (ADR-049 §B).
  - PATCH .../notificar: cada 422 de §6; `sede_justificacion` deja bitácora;
    clave ausente conserva (#832/#834); todo se valida antes de vincular.
  - POST .../notificar/parsear_documento: `resultado_sugerido`; no escribe nada.

HTTP real contra la BD de tests: el árbol se commitea sobre `expediente_seed`
y se borra al terminar (la Fase arrastra por CASCADE trámite, tarea, vínculos
y notificación; los documentos se borran por asunto). Documentos `bddat://`,
sin fichero físico: `mover_a_esftt` no los toca.
"""
import pytest

from app import db

ASUNTO = '#928c api test'


@pytest.fixture
def montar(app, expediente_seed):
    """Fábrica: NOTIFICAR commiteada con `vinculos` [(codigo_tipo, rol|None)]
    —rol None deja el documento en el pool sin vincular— y, si `notificacion`
    no es None, su fila con esos kwargs. Devuelve (tarea_id, {codigo: doc_id})."""
    fases = []

    def _montar(vinculos=(), notificacion=None):
        from app.models.solicitudes import Solicitud
        from app.services.reloj_simulado import hoy
        from tests.conftest import ArbolESFTT
        with app.app_context():
            arbol = ArbolESFTT(db)
            solicitud = Solicitud.query.filter_by(expediente_id=expediente_seed).first()
            assert solicitud is not None, 'la semilla debe traer una solicitud en el expediente'
            fase = arbol.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
            tarea = arbol.tarea(arbol.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
            docs = {}
            for codigo, rol in vinculos:
                doc = arbol.documento(expediente_seed, codigo, f'928c-{tarea.id}-{codigo}',
                                      fecha=hoy())
                doc.asunto = ASUNTO
                if rol:
                    arbol.vincular(tarea, doc, rol)
                docs[codigo] = doc.id
            if notificacion is not None:
                arbol.notificacion(tarea, **notificacion)
            db.session.commit()
            fases.append(fase.id)
            return tarea.id, docs

    yield _montar

    with app.app_context():
        from app.models.fases import Fase
        from app.models.documentos import Documento
        db.session.rollback()
        for fase_id in fases:
            Fase.query.filter_by(id=fase_id).delete()
        Documento.query.filter(Documento.asunto == ASUNTO).delete(synchronize_session=False)
        db.session.commit()


def _url(expediente_id, tarea_id, sufijo=''):
    return f'/api/expedientes/{expediente_id}/nodo/tarea/{tarea_id}/notificar{sufijo}'


def _notif(app, tarea_id):
    from app.models.notificaciones import Notificacion
    with app.app_context():
        n = Notificacion.query.filter_by(tarea_id=tarea_id).first()
        return None if n is None else {
            c: getattr(n, c) for c in ('id', 'canal', 'resultado', 'numero_intento',
                                       'observaciones', 'sede_justificacion', 'documento_id')
        }


# ---------------------------------------------------------------------------
# GET y endpoints eliminados
# ---------------------------------------------------------------------------

def test_get_payload_nuevo(usuario_supervisor, expediente_seed, montar):
    tarea_id, docs = montar(
        [('RESOLUCION', 'CONSUMIDO'), ('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO'),
         ('JUSTIFICANTE_POSTAL', 'PRODUCIDO')],
        notificacion={'canal': 'POSTAL', 'resultado': 'CORRECTA', 'numero_intento': 2})

    r = usuario_supervisor.get(_url(expediente_seed, tarea_id))

    assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
    assert len(d['notificaciones']) == 1
    fila = d['notificaciones'][0]
    assert fila['canal'] == 'POSTAL' and fila['resultado'] == 'CORRECTA'
    assert fila['destinatario'] is None                     # hueco N5
    assert 'fecha_puesta_disposicion' not in fila and 'fecha_resultado' not in fila
    assert d['documento_producido']['id'] == docs['JUSTIFICANTE_POSTAL']
    assert [p['id'] for p in d['justificantes_previos']] == [docs['JUSTIFICANTE_POSTAL_1ER']]
    assert d['fechas']['cumplimiento']['documento_id'] == docs['JUSTIFICANTE_POSTAL_1ER']
    assert d['fechas']['efectos']['documento_id'] == docs['JUSTIFICANTE_POSTAL']
    assert d['sede'] == {'aplica': True, 'estado': 'PENDIENTE'}
    assert d['estado'] == 'PENDIENTE_SEDE'
    assert d['resultados_validos'] == ['CORRECTA', 'RECHAZADA', 'INCORRECTA']
    assert d['es_notificacion_del_titular'] is False        # fase no finalizadora


def test_get_sin_fila(usuario_supervisor, expediente_seed, montar):
    tarea_id, _ = montar([('RESOLUCION', 'CONSUMIDO')])

    d = usuario_supervisor.get(_url(expediente_seed, tarea_id)).get_json()

    assert d['notificaciones'] == []
    assert d['fechas'] == {'cumplimiento': None, 'efectos': None}
    assert d['sede'] == {'aplica': False, 'estado': None}
    assert d['estado'] == 'PENDIENTE_NOTIFICAR'


def test_registrar_puesta_a_disposicion_y_parseo_transitorio_eliminados(
        usuario_supervisor, expediente_seed, montar):
    tarea_id, _ = montar()
    assert usuario_supervisor.post(_url(expediente_seed, tarea_id), json={}).status_code == 405
    assert usuario_supervisor.post(_url(expediente_seed, tarea_id, '/parsear')).status_code == 404


# ---------------------------------------------------------------------------
# PATCH: validaciones (422)
# ---------------------------------------------------------------------------

def test_patch_sin_fila_ni_documento_422(usuario_supervisor, expediente_seed, montar):
    tarea_id, _ = montar([('RESOLUCION', 'CONSUMIDO')])

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'resultado': 'CORRECTA'})

    assert r.status_code == 422
    assert 'justificante' in r.get_json()['motivo']


def test_patch_documento_previo_como_producido_422(usuario_supervisor, expediente_seed, montar, app):
    tarea_id, docs = montar([('JUSTIFICANTE_NOTIFICA_DISPOSICION', None)])

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id),
                                 json={'documento_id': docs['JUSTIFICANTE_NOTIFICA_DISPOSICION']})

    assert r.status_code == 422
    assert 'consumido' in r.get_json()['error']
    assert _notif(app, tarea_id) is None


def test_patch_rechazada_en_bandeja_422(usuario_supervisor, expediente_seed, montar):
    tarea_id, _ = montar([('JUSTIFICANTE_BANDEJA', 'PRODUCIDO')], notificacion={'canal': 'BANDEJA'})

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'resultado': 'RECHAZADA'})

    assert r.status_code == 422
    assert 'BANDEJA' in r.get_json()['error']


def test_patch_correcta_sin_producido_422_e_incorrecta_si(usuario_supervisor, expediente_seed,
                                                          montar, app):
    tarea_id, _ = montar([('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO')], notificacion={'canal': 'POSTAL'})

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'resultado': 'CORRECTA'})
    assert r.status_code == 422
    assert 'producido' in r.get_json()['error']

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'resultado': 'INCORRECTA'})
    assert r.status_code == 200, r.get_data(as_text=True)
    assert _notif(app, tarea_id)['resultado'] == 'INCORRECTA'


def test_patch_intento_2_solo_en_postal(usuario_supervisor, expediente_seed, montar):
    notifica_id, _ = montar([('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO')], notificacion={'canal': 'NOTIFICA'})
    postal_id, _ = montar([('JUSTIFICANTE_POSTAL', 'PRODUCIDO')], notificacion={'canal': 'POSTAL'})

    assert usuario_supervisor.patch(_url(expediente_seed, notifica_id),
                                    json={'numero_intento': 2}).status_code == 422
    assert usuario_supervisor.patch(_url(expediente_seed, postal_id),
                                    json={'numero_intento': 2}).status_code == 200


def test_patch_sede_justificacion_solo_postal(usuario_supervisor, expediente_seed, montar):
    tarea_id, _ = montar([('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO')], notificacion={'canal': 'NOTIFICA'})

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id),
                                 json={'sede_justificacion': 'Sin acceso'})

    assert r.status_code == 422
    assert '42.1' in r.get_json()['error']


def test_patch_notificacion_id_ajena_422(usuario_supervisor, expediente_seed, montar, app):
    tarea_id, _ = montar([('JUSTIFICANTE_SIR', 'PRODUCIDO')], notificacion={'canal': 'SIR'})
    notif_id = _notif(app, tarea_id)['id']

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id),
                                 json={'notificacion_id': notif_id + 100000})

    assert r.status_code == 422


# ---------------------------------------------------------------------------
# PATCH: escritura
# ---------------------------------------------------------------------------

def test_patch_sede_justificacion_deja_bitacora(usuario_supervisor, expediente_seed, montar, app):
    from sqlalchemy import text
    tarea_id, _ = montar([('RESOLUCION', 'CONSUMIDO'), ('JUSTIFICANTE_POSTAL', 'PRODUCIDO')],
                         notificacion={'canal': 'POSTAL', 'resultado': 'CORRECTA'})
    notif_id = _notif(app, tarea_id)['id']

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id),
                                 json={'sede_justificacion': 'Destinatario sin acceso a sede'})

    assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
    assert d['sede'] == {'aplica': True, 'estado': 'JUSTIFICADA'}
    assert d['estado'] == 'FIN'
    with app.app_context():
        detalle = db.session.execute(text(
            "select detalle from bitacora where tabla='notificaciones' and registro_id=:id "
            "order by id desc limit 1"), {'id': notif_id}).scalar()
    assert detalle['accion'] == 'JUSTIFICAR_SEDE'
    assert detalle['texto'] == 'Destinatario sin acceso a sede'


def test_patch_clave_ausente_conserva(usuario_supervisor, expediente_seed, montar, app):
    tarea_id, _ = montar([('JUSTIFICANTE_POSTAL', 'PRODUCIDO')],
                         notificacion={'canal': 'POSTAL', 'resultado': 'RECHAZADA'})
    assert usuario_supervisor.patch(_url(expediente_seed, tarea_id),
                                    json={'observaciones': 'Rechazo expreso'}).status_code == 200

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'numero_intento': 2})

    assert r.status_code == 200, r.get_data(as_text=True)
    notif = _notif(app, tarea_id)
    assert notif['resultado'] == 'RECHAZADA'
    assert notif['observaciones'] == 'Rechazo expreso'
    assert notif['numero_intento'] == 2


def test_patch_null_vacia(usuario_supervisor, expediente_seed, montar, app):
    tarea_id, _ = montar([('JUSTIFICANTE_POSTAL', 'PRODUCIDO')],
                         notificacion={'canal': 'POSTAL', 'resultado': 'CORRECTA'})

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={'resultado': None})

    assert r.status_code == 200, r.get_data(as_text=True)
    assert _notif(app, tarea_id)['resultado'] is None


def test_patch_documento_final_vincula_y_fija_resultado(usuario_supervisor, expediente_seed,
                                                        montar, app):
    """Acto 3 de #712: fila creada por el previo; el PATCH vincula el final
    como producido y fija el resultado en la misma llamada."""
    tarea_id, docs = montar(
        [('RESOLUCION', 'CONSUMIDO'), ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO'),
         ('JUSTIFICANTE_NOTIFICA', None)],
        notificacion={'canal': 'NOTIFICA'})

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={
        'documento_id': docs['JUSTIFICANTE_NOTIFICA'], 'resultado': 'RECHAZADA'})

    assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
    assert d['documento_producido']['id'] == docs['JUSTIFICANTE_NOTIFICA']
    assert d['notificaciones'][0]['resultado'] == 'RECHAZADA'
    assert d['notificaciones'][0]['documento_id'] == docs['JUSTIFICANTE_NOTIFICA']
    assert d['fechas']['efectos']['documento_id'] == docs['JUSTIFICANTE_NOTIFICA']
    assert d['estado'] == 'FIN'


def test_patch_422_no_deja_la_vinculacion_a_medias(usuario_supervisor, expediente_seed, montar):
    """Todo se valida antes de vincular: un resultado inválido no deja el
    producido vinculado."""
    tarea_id, docs = montar([('JUSTIFICANTE_SIR', None)])

    r = usuario_supervisor.patch(_url(expediente_seed, tarea_id), json={
        'documento_id': docs['JUSTIFICANTE_SIR'], 'resultado': 'RECHAZADA'})

    assert r.status_code == 422
    d = usuario_supervisor.get(_url(expediente_seed, tarea_id)).get_json()
    assert d['documento_producido'] is None
    assert d['notificaciones'] == []


# ---------------------------------------------------------------------------
# parsear_documento: resultado_sugerido, sin escribir nada
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('codigo,sugerido', [
    ('JUSTIFICANTE_BANDEJA', 'CORRECTA'),
    ('JUSTIFICANTE_SIR', 'CORRECTA'),
    ('ANUNCIO_PUBLICADO', 'CORRECTA'),
    ('JUSTIFICANTE_POSTAL', None),
    ('JUSTIFICANTE_NOTIFICA', None),   # bddat://, sin fichero que parsear
])
def test_parsear_documento_resultado_sugerido(usuario_supervisor, expediente_seed, montar, app,
                                              codigo, sugerido):
    tarea_id, docs = montar([(codigo, None)])

    r = usuario_supervisor.post(_url(expediente_seed, tarea_id, '/parsear_documento'),
                                json={'documento_id': docs[codigo]})

    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json()['resultado_sugerido'] == sugerido
    assert _notif(app, tarea_id) is None


def test_parsear_documento_rechaza_tipo_ajeno(usuario_supervisor, expediente_seed, montar):
    tarea_id, docs = montar([('RESOLUCION', None)])

    r = usuario_supervisor.post(_url(expediente_seed, tarea_id, '/parsear_documento'),
                                json={'documento_id': docs['RESOLUCION']})

    assert r.status_code == 422
