"""
Tests #967 (N5a-1) — toda NOTIFICAR guarda su destinatario (ADR-051 §B, §K).

  - La ficha nace con la tarea, con su fuente (una sola: la toma; varias o sin
    declarar: se pide), y se borra con ella.
  - Sin destinatario no admite vínculos; el escape queda en bitácora, se relata
    y deja la tarea sin destinatario para siempre.
  - «Notificar al solicitante» (§K, enmienda de #989): el representante de la
    solicitud si lo hay, con su ficha; si no, el solicitante, en la sede de la
    solicitud o su ficha. Cambiar el representante refresca lo que no ha salido.
  - El destinatario se refresca hasta el primer justificante y desde ahí es fijo.
  - Cotejo del NIF del justificante de Notifica con la ficha.
  - Representante de la solicitud: un autorizado del solicitante, validado al cambiar.
  - Rutas: PUT del destinatario, bypass al vincular, escritos no en NOTIFICAR.

Desde #968 la NOTIFICAR nace ya con su destinatario si se sabe, y solo admite a
quien corresponde por su fuente: los casos «sin destinatario» se montan en un
trámite cuyo destinatario se elige a mano y los de entidad arbitraria, en uno
sin fuentes (`ArbolESFTT.tramite_sin_destinatario` / `tramite_sin_fuentes`). Los dos tests
de la lista provisional de fuentes los sustituye el de cobertura de
`test_968_fuentes_destinatarios.py`.

BD de tests con rollback por SAVEPOINT (`arbol_aislado`) + `fs_tmp`.
"""
import pytest
from flask_login import login_user

from app import db
from app.models.bitacora import Bitacora
from app.models.direccion_notificacion import DireccionNotificacion
from app.models.entidad import Entidad
from app.models.notificaciones import Notificacion
from app.models.tareas import Tarea
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_tareas import TipoTarea
from app.services import mutaciones_arbol as svc
from app.services import notificaciones as notif_svc
from tests.conftest import documento_con_contenido_de_prueba
from tests.test_657_658_notificar import TEXTO_JUSTIFICANTE, _pdf_sintetico


@pytest.fixture
def con_usuario(app_ctx):
    """Petición con usuario autenticado: bitácora y escapes usan `current_user`."""
    from app.models.usuarios import Usuario
    usuario = Usuario.query.order_by(Usuario.id).first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    with app_ctx.test_request_context():
        login_user(usuario)
        yield usuario


def _tipo_tarea(codigo):
    tipo = TipoTarea.query.filter_by(codigo=codigo).one()
    return tipo


def _tramite(arbol, codigo_fase='ANALISIS_SOLICITUD', codigo_tramite='COMUNICACION_INICIO_ADMISION'):
    fase = arbol.fase(codigo_fase, solicitud=arbol.solicitud_propia())
    return arbol.tramite(fase, codigo_tramite)


def _crear_notificar(tramite, fuente=None):
    """NOTIFICAR por el único camino de la aplicación (`crear_tarea`). Con
    justificación para no depender del orden canónico ni del motor: aquí se
    prueba la ficha, no la precedencia."""
    res = svc.crear_tarea(tramite, _tipo_tarea('NOTIFICAR'), justificacion='test #967',
                          fuente=fuente)
    assert res.ok, res.error or res.bloqueo
    return db.session.get(Tarea, res.ids[0])


def _entidad(nombre, nif=None, **kw):
    """Entidad de prueba; `chk_al_menos_un_rol` exige un rol (titular por defecto)."""
    if not any(kw.get(r) for r in ('rol_titular', 'rol_consultado', 'rol_publicador')):
        kw['rol_titular'] = True
    e = Entidad(nombre_completo=nombre, nif=nif, activo=True, **kw)
    db.session.add(e)
    db.session.flush()
    return e


def _autorizar(titular_id, autorizado):
    """`autorizado` pasa a ser autorizado del titular: único representante posible."""
    from app.models.autorizados_titular import AutorizadoTitular
    db.session.add(AutorizadoTitular(titular_entidad_id=titular_id,
                                     autorizado_entidad_id=autorizado.id))
    db.session.flush()


def _direccion(entidad, *, titular=False, consultado=False, direccion='Calle Mayor 1',
               nif=None):
    d = DireccionNotificacion(
        entidad_id=entidad.id, direccion=direccion, codigo_postal='41001', nif=nif,
        tipo_rol=DireccionNotificacion.calcular_tipo_rol(es_titular=titular,
                                                         es_consultado=consultado),
    )
    db.session.add(d)
    db.session.flush()
    return d


def _doc(tarea, codigo, contenido=b'%PDF-1.4 justificante'):
    from app.services.reloj_simulado import hoy
    tipo = TipoDocumento.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el tipo de documento {codigo}'
    return documento_con_contenido_de_prueba(
        f'967-{codigo.lower()}-{tarea.id}.pdf', contenido,
        expediente_id=tarea.tramite.fase.solicitud.expediente_id, tipo_doc_id=tipo.id,
        asunto='#967 test', fecha_administrativa=hoy())


def _vincular(tarea, consumidos=(), producido=None, justificacion=None):
    return svc.editar_tarea(
        tarea, documentos_consumidos_ids=[d.id for d in consumidos],
        documento_producido_id=producido.id if producido else None, notas=None,
        justificacion=justificacion)


# ---------------------------------------------------------------------------
# La ficha nace con la tarea, con su fuente
# ---------------------------------------------------------------------------

def test_la_ficha_nace_con_la_tarea_y_su_unica_fuente(con_usuario, arbol_aislado):
    tarea = _crear_notificar(_tramite(arbol_aislado))

    notif = Notificacion.query.filter_by(tarea_id=tarea.id).one()
    assert notif.fuente == 'SOLICITANTE'
    # Desde #968 nace ya con su destinatario: el solicitante.
    assert notif.entidad_id == tarea.tramite.fase.solicitud.entidad_id
    assert notif.canal is None and not notif.registrada


def test_las_demas_tareas_no_tienen_ficha(con_usuario, arbol_aislado):
    tramite = _tramite(arbol_aislado)
    res = svc.crear_tarea(tramite, _tipo_tarea('ELABORAR'), justificacion='test #967')
    assert res.ok, res.error
    assert Notificacion.query.filter_by(tarea_id=res.ids[0]).first() is None


def test_varias_fuentes_hay_que_indicarla(con_usuario, arbol_aislado):
    tramite = _tramite(arbol_aislado, 'RESOLUCION', 'NOTIFICACION')

    res = svc.crear_tarea(tramite, _tipo_tarea('NOTIFICAR'), justificacion='test #967')
    assert not res.ok
    assert 'ORGANISMOS_CONSULTADOS' in res.error          # le dice las opciones

    res = svc.crear_tarea(tramite, _tipo_tarea('NOTIFICAR'), justificacion='test #967',
                          fuente='PROPIETARIOS_DUP')      # no es de la AAP/AAC
    assert not res.ok

    tarea = _crear_notificar(tramite, fuente='ORGANISMOS_CONSULTADOS')
    assert tarea.notificacion.fuente == 'ORGANISMOS_CONSULTADOS'


def test_tramite_sin_fuentes_declaradas_admite_cualquiera_indicada(con_usuario, arbol_aislado):
    """Una NOTIFICAR forzada fuera de la secuencia (`ANUNCIO_BOE` no la lleva
    desde #964) no tiene fuentes declaradas: se indica a mano."""
    tramite = _tramite(arbol_aislado, 'INFORMACION_PUBLICA', 'ANUNCIO_BOE')
    res = svc.crear_tarea(tramite, _tipo_tarea('NOTIFICAR'), justificacion='test #967')
    assert not res.ok
    assert _crear_notificar(tramite, fuente='BOLETIN').notificacion.fuente == 'BOLETIN'


def test_la_ficha_se_borra_con_la_tarea(con_usuario, arbol_aislado):
    """Regresión de la auditoría de #967: sin cascada, el ORM intentaba dejar
    la ficha huérfana (`tarea_id` NOT NULL) y ninguna NOTIFICAR se borraba."""
    tarea = _crear_notificar(_tramite(arbol_aislado))
    tarea_id = tarea.id

    res = svc.borrar_tarea(tarea)

    assert res.ok, res.error or res.bloqueo
    assert Notificacion.query.filter_by(tarea_id=tarea_id).first() is None


# ---------------------------------------------------------------------------
# Sin destinatario no avanza
# ---------------------------------------------------------------------------

def test_vincular_sin_destinatario_se_bloquea_con_escape(con_usuario, arbol_aislado, fs_tmp):
    tarea = _crear_notificar(arbol_aislado.tramite_sin_destinatario())
    doc = _doc(tarea, 'JUSTIFICANTE_NOTIFICA')

    res = _vincular(tarea, producido=doc)

    assert not res.ok
    assert res.bloqueo is not None and res.bloqueo.puede_escapar is True
    assert 'destinatario' in res.bloqueo.norma_compilada
    db.session.refresh(tarea)
    assert tarea.vinculos_documento == []
    assert not tarea.ejecutada


def test_escape_sin_destinatario_queda_en_bitacora_y_es_para_siempre(
        con_usuario, arbol_aislado, fs_tmp):
    tarea = _crear_notificar(arbol_aislado.tramite_sin_destinatario())
    doc = _doc(tarea, 'JUSTIFICANTE_NOTIFICA')

    res = _vincular(tarea, producido=doc, justificacion='Se notificó en papel en ventanilla')

    assert res.ok, res.error or res.bloqueo
    assert tarea.ejecutada
    entradas = [b for b in Bitacora.query.filter_by(tabla='tareas', registro_id=tarea.id)
                if (b.detalle or {}).get('accion') == notif_svc.ACCION_SIN_DESTINATARIO]
    assert len(entradas) == 1
    assert entradas[0].detalle['escape'] is True
    assert entradas[0].detalle['justificacion'] == 'Se notificó en papel en ventanilla'
    assert notif_svc.tuvo_escape_sin_destinatario(tarea)
    assert not notif_svc.falta_destinatario(tarea)

    # Ya no admite fijarlo, aunque se desvincule todo.
    assert _vincular(tarea).ok
    res = svc.fijar_destinatario(tarea)
    assert not res.ok and 'escape' in res.error


def test_escape_sin_destinatario_se_relata(con_usuario, arbol_aislado, fs_tmp):
    from app.services.informe_instruccion import escapes_de_fase, relato_escapes
    tarea = _crear_notificar(arbol_aislado.tramite_sin_destinatario())
    doc = _doc(tarea, 'JUSTIFICANTE_NOTIFICA')
    assert _vincular(tarea, producido=doc, justificacion='Motivo del escape').ok

    frases = relato_escapes(escapes_de_fase(tarea.tramite.fase), 'tareas', tarea.id,
                            'la tarea «Notificar»')

    frase = next(f for f in frases if 'destinatario' in f)
    assert 'sin haber fijado su destinatario' in frase
    assert 'Motivo del escape' in frase


def test_desvincular_no_se_bloquea(con_usuario, arbol_aislado, fs_tmp):
    """Solo añadir vínculos exige destinatario; quitar sigue libre."""
    tarea = _crear_notificar(_tramite(arbol_aislado))
    assert svc.fijar_destinatario(tarea).ok
    doc = _doc(tarea, 'RESOLUCION')
    assert _vincular(tarea, consumidos=[doc]).ok
    # Quitar el destinatario a mano no es un camino de la aplicación; simula
    # una ficha anterior al destinatario para ver que desvincular no pregunta.
    tarea.notificacion.entidad_id = None
    db.session.flush()

    assert _vincular(tarea).ok


# ---------------------------------------------------------------------------
# «Notificar al solicitante» (§K) y copia del destinatario
# ---------------------------------------------------------------------------

def test_sin_representante_va_a_la_sede_de_la_solicitud(con_usuario, arbol_aislado):
    """#989: con varias sedes, la de la solicitud y no la más reciente; sin
    sede, la ficha. Evita enviar la notificación a otra sede."""
    tarea = _crear_notificar(_tramite(arbol_aislado))
    solicitud = tarea.tramite.fase.solicitud
    solicitud.entidad.direccion = 'Ribera del Loira 60'
    sede = _direccion(solicitud.entidad, titular=True, direccion='Avda. de la Borbolla 5')
    sede.email = 'registro_sede@empresa.es'
    _direccion(solicitud.entidad, titular=True, direccion='Sede más reciente')
    db.session.flush()

    # Sin sede en la solicitud: la ficha, no la sede más reciente.
    assert svc.fijar_destinatario(tarea).ok
    notif = tarea.notificacion
    assert notif.direccion_origen_id is None
    assert notif.dest_direccion == 'Ribera del Loira 60'

    solicitud.direccion_notificacion_id = sede.id
    db.session.flush()
    db.session.expire(solicitud, ['sede'])
    res = svc.fijar_destinatario(tarea)

    assert res.ok, res.error
    assert notif.entidad_id == solicitud.entidad_id
    assert notif.en_nombre_de_entidad_id is None
    assert notif.direccion_origen_id == sede.id
    assert notif.dest_direccion == 'Avda. de la Borbolla 5'
    assert notif.dest_email == 'registro_sede@empresa.es'
    assert notif.dest_nif == solicitud.entidad.nif
    assert notif.dest_nombre == solicitud.entidad.nombre_completo
    assert notif.destinatario_fijado_en is not None


def test_con_representante_se_notifica_al_representante(con_usuario, arbol_aislado):
    tarea = _crear_notificar(_tramite(arbol_aislado))
    solicitud = tarea.tramite.fase.solicitud
    representante = _entidad('Gestoría Representante S.L.', nif='B11111111',
                             direccion='Plaza de la Gestoría 3')
    solicitud.representante_entidad_id = representante.id
    db.session.flush()

    assert svc.fijar_destinatario(tarea).ok

    notif = tarea.notificacion
    assert notif.entidad_id == representante.id
    assert notif.en_nombre_de_entidad_id == solicitud.entidad_id
    # El representante no tiene sede: siempre su ficha (#989).
    assert notif.direccion_origen_id is None
    assert notif.dest_direccion == 'Plaza de la Gestoría 3'
    assert notif.dest_nif == 'B11111111'


def test_entidad_indicada_toma_la_direccion_del_rol_de_su_fuente(con_usuario, arbol_aislado):
    from app.models.organismos_expediente import OrganismoExpediente
    tramite = _tramite(arbol_aislado, 'RESOLUCION', 'NOTIFICACION')
    solicitud = tramite.fase.solicitud
    organismo = _entidad('Confederación Hidrográfica de Prueba', rol_consultado=True)
    _direccion(organismo, titular=True, direccion='Dirección de titular')
    consultado = _direccion(organismo, consultado=True, direccion='Registro de consultas')
    consultas = arbol_aislado.fase('CONSULTAS', solicitud=solicitud)
    db.session.add(OrganismoExpediente(expediente_id=solicitud.expediente_id,
                                       fase_id=consultas.id, organismo_id=organismo.id,
                                       via='consulta'))
    db.session.flush()

    tarea = _crear_notificar(tramite, fuente='ORGANISMOS_CONSULTADOS')

    # Nace con el organismo consultado, en su dirección de consultado (#968).
    assert tarea.notificacion.entidad_id == organismo.id
    assert tarea.notificacion.direccion_origen_id == consultado.id
    assert tarea.notificacion.dest_direccion == 'Registro de consultas'
    # Una entidad que no es de la fuente no se admite.
    otra = _entidad('No consultada', rol_consultado=True)
    assert not svc.fijar_destinatario(tarea, entidad_id=otra.id).ok


def test_direccion_de_otra_entidad_se_rechaza(con_usuario, arbol_aislado):
    tarea = _crear_notificar(_tramite(arbol_aislado))
    ajena = _direccion(_entidad('Otra entidad'), titular=True)
    res = svc.fijar_destinatario(tarea, entidad_id=tarea.tramite.fase.solicitud.entidad_id,
                                 direccion_id=ajena.id)
    assert not res.ok


def test_destinatario_se_refresca_hasta_el_primer_justificante(con_usuario, arbol_aislado,
                                                              fs_tmp):
    tarea = _crear_notificar(_tramite(arbol_aislado))
    solicitud = tarea.tramite.fase.solicitud
    assert svc.fijar_destinatario(tarea).ok

    # Cambia la sede antes de enviar nada: refrescar copia la nueva.
    solicitud.direccion_notificacion_id = _direccion(
        solicitud.entidad, titular=True, direccion='Dirección nueva').id
    db.session.flush()
    db.session.expire(solicitud, ['sede'])
    assert svc.fijar_destinatario(tarea).ok
    assert tarea.notificacion.dest_direccion == 'Dirección nueva'

    # Un documento que no es justificante no congela.
    resolucion = _doc(tarea, 'RESOLUCION')
    assert _vincular(tarea, consumidos=[resolucion]).ok
    assert svc.fijar_destinatario(tarea).ok

    # El primer justificante, aunque sea previo, sí.
    disposicion = _doc(tarea, 'JUSTIFICANTE_NOTIFICA_DISPOSICION')
    assert _vincular(tarea, consumidos=[resolucion, disposicion]).ok
    res = svc.fijar_destinatario(tarea)
    assert not res.ok and 'justificante' in res.error


def test_fijar_destinatario_deja_bitacora(con_usuario, arbol_aislado):
    tarea = _crear_notificar(_tramite(arbol_aislado))
    assert svc.fijar_destinatario(tarea).ok
    entrada = (Bitacora.query
               .filter_by(tabla='notificaciones', registro_id=tarea.notificacion.id)
               .order_by(Bitacora.id.desc()).first())
    assert entrada.detalle['accion'] == notif_svc.ACCION_FIJAR_DESTINATARIO
    assert entrada.detalle['entidad_id'] == tarea.notificacion.entidad_id


# ---------------------------------------------------------------------------
# Cotejo del NIF del justificante de Notifica (A00000000 en el texto de muestra)
# ---------------------------------------------------------------------------

def test_cotejo_del_nif(con_usuario, arbol_aislado, fs_tmp):
    """El justificante va dirigido a A00000000 y el destinatario registrado es B99999999:
    avisa, sin bloquear."""
    tarea = _crear_notificar(arbol_aislado.tramite_sin_fuentes(), fuente='BOLETIN')
    receptor = _entidad('Receptor', nif='B99999999')
    assert svc.fijar_destinatario(tarea, entidad_id=receptor.id).ok
    doc = _doc(tarea, 'JUSTIFICANTE_NOTIFICA', _pdf_sintetico(TEXTO_JUSTIFICANTE))

    res = _vincular(tarea, producido=doc)

    assert res.ok, res.error or res.bloqueo
    assert res.advertencia is not None and 'NIF' in res.advertencia['motivo']


# ---------------------------------------------------------------------------
# Representante de la solicitud (§K)
# ---------------------------------------------------------------------------

def test_representante_autorizado_del_solicitante(con_usuario, arbol_aislado):
    solicitud = arbol_aislado.solicitud_propia()

    autorizado = _entidad('Representante autorizado')
    _autorizar(solicitud.entidad_id, autorizado)
    res = svc.editar_solicitud(solicitud, observaciones=None,
                               representante_entidad_id=autorizado.id)
    assert res.ok and res.advertencia is None
    assert solicitud.representante_entidad_id == autorizado.id

    res = svc.editar_solicitud(solicitud, observaciones=None,
                               representante_entidad_id=solicitud.entidad_id)
    assert not res.ok

    assert svc.editar_solicitud(solicitud, observaciones=None,
                                representante_entidad_id=None).ok
    assert solicitud.representante_entidad_id is None


def test_cambiar_representante_refresca_lo_que_no_ha_salido(con_usuario, arbol_aislado,
                                                            fs_tmp):
    """#989: la NOTIFICAR al solicitante sin justificante pasa al nuevo
    representante; la que ya lo tiene no se toca, y la respuesta lo cuenta.
    Evita que la notificación salga a quien ya no representa."""
    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
    enviada = _crear_notificar(arbol_aislado.tramite(fase, 'REQUERIMIENTO_SUBSANACION'))
    pendiente = _crear_notificar(arbol_aislado.tramite(fase, 'COMUNICACION_INICIO_ADMISION'))
    assert _vincular(enviada, consumidos=[
        _doc(enviada, 'JUSTIFICANTE_NOTIFICA_DISPOSICION')]).ok
    gestora = _entidad('Ingeniería de Prueba S.L.', nif='B98765432')
    _autorizar(solicitud.entidad_id, gestora)

    res = svc.editar_solicitud(solicitud, observaciones=None,
                               representante_entidad_id=gestora.id)

    assert res.ok, res.error
    assert pendiente.notificacion.entidad_id == gestora.id
    assert pendiente.notificacion.en_nombre_de_entidad_id == solicitud.entidad_id
    assert pendiente.notificacion.dest_nif == 'B98765432'
    assert enviada.notificacion.entidad_id == solicitud.entidad_id
    assert res.advertencia['refrescadas'] == [pendiente.id]
    assert res.advertencia['ya_enviadas'] == [enviada.id]
    entrada = (Bitacora.query
               .filter_by(tabla='notificaciones', registro_id=pendiente.notificacion.id)
               .order_by(Bitacora.id.desc()).first())
    assert entrada.detalle['origen'] == 'CAMBIO_SOLICITUD'


@pytest.mark.parametrize('caso,vale', [
    ('propia', True),
    ('mismo_nif', True),
    ('de_otra_entidad', False),
    ('dada_de_baja', False),
    ('no_es_de_titular', False),
    ('otro_nif', False),
])
def test_la_sede_es_del_solicitante(con_usuario, arbol_aislado, caso, vale):
    """#989: solo una dirección del solicitante, activa, de titular y sin otro
    NIF. Evita enviar a otra sociedad —otro NIF lo es— como si fuera una sede."""
    solicitud = arbol_aislado.solicitud_propia()
    titular = solicitud.entidad
    titular.nif = 'B12345678'
    duena = _entidad('Otra sociedad') if caso == 'de_otra_entidad' else titular
    d = _direccion(duena, titular=caso != 'no_es_de_titular',
                   consultado=caso == 'no_es_de_titular',
                   nif={'mismo_nif': 'b-12345678', 'otro_nif': 'B87654321'}.get(caso))
    d.activo = caso != 'dada_de_baja'
    db.session.flush()

    res = svc.editar_solicitud(solicitud, observaciones=None, direccion_notificacion_id=d.id)

    assert res.ok is vale, res.error
    assert (solicitud.direccion_notificacion_id == d.id) is vale


def test_editar_solicitud_sin_representante_no_lo_toca(con_usuario, arbol_aislado):
    solicitud = arbol_aislado.solicitud_propia()
    rep = _entidad('Representante')
    solicitud.representante_entidad_id = rep.id
    db.session.flush()
    assert svc.editar_solicitud(solicitud, observaciones='nota').ok
    assert solicitud.representante_entidad_id == rep.id


# ---------------------------------------------------------------------------
# Relato
# ---------------------------------------------------------------------------

def test_la_frase_del_escape_usa_la_accion_del_servicio():
    from app.services.informe_instruccion import _FIN_DEL_ESCAPE
    assert ('ALTERAR', notif_svc.ACCION_SIN_DESTINATARIO) in _FIN_DEL_ESCAPE


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@pytest.fixture
def notificar_http(app, expediente_seed):
    """NOTIFICAR sin destinatario, commiteada (las rutas no pasan por
    `app_ctx`, #836), y su limpieza."""
    fases = []

    def _montar(codigo_fase='ANALISIS_SOLICITUD', codigo_tramite='COMUNICACION_INICIO_ADMISION',
                fuente='SOLICITANTE'):
        from app.models.solicitudes import Solicitud
        from tests.conftest import ArbolESFTT
        with app.app_context():
            arbol = ArbolESFTT(db)
            solicitud = (Solicitud.query.filter_by(expediente_id=expediente_seed)
                         .order_by(Solicitud.id).first())
            assert solicitud is not None, 'la semilla debe traer una solicitud en el expediente'
            fase = arbol.fase(codigo_fase, solicitud=solicitud)
            tarea = arbol.notificar_sin_destinatario(arbol.tramite(fase, codigo_tramite), fuente)
            db.session.commit()
            fases.append(fase.id)
            return tarea.id

    yield _montar

    with app.app_context():
        from app.models.fases import Fase
        db.session.rollback()
        for fase_id in fases:
            Fase.query.filter_by(id=fase_id).delete()
        db.session.commit()


def _url(expediente_id, tarea_id, sufijo=''):
    return f'/api/expedientes/{expediente_id}/nodo/tarea/{tarea_id}/notificar{sufijo}'


def test_get_dice_que_falta_el_destinatario(usuario_supervisor, expediente_seed, notificar_http):
    tarea_id = notificar_http()

    d = usuario_supervisor.get(_url(expediente_seed, tarea_id)).get_json()

    assert d['destinatario'] == {'fijado': False, 'escape_sin_destinatario': False,
                                 'editable': True, 'bloquea': True,
                                 'fuentes_del_tramite': ['SOLICITANTE']}
    assert d['notificaciones'][0]['fuente'] == 'SOLICITANTE'
    assert d['notificaciones'][0]['destinatario'] is None


def test_put_destinatario_del_solicitante(usuario_supervisor, expediente_seed, notificar_http):
    tarea_id = notificar_http()

    r = usuario_supervisor.put(_url(expediente_seed, tarea_id, '/destinatario'), json={})

    assert r.status_code == 200, r.get_data(as_text=True)
    d = r.get_json()
    assert d['destinatario']['fijado'] is True and d['destinatario']['bloquea'] is False
    assert d['notificaciones'][0]['destinatario']['entidad_id'] is not None


def test_put_destinatario_sin_entidad_en_otra_fuente_422(usuario_supervisor, expediente_seed,
                                                         notificar_http):
    tarea_id = notificar_http('RESOLUCION', 'NOTIFICACION', fuente='ORGANISMOS_CONSULTADOS')

    r = usuario_supervisor.put(_url(expediente_seed, tarea_id, '/destinatario'), json={})

    # Sin organismos consultados en la solicitud no hay a quién notificar.
    assert r.status_code == 422


def test_crear_notificar_por_api_pide_la_fuente(usuario_supervisor, expediente_seed, app):
    """POST .../hijos en un trámite con varias fuentes, sin `fuente`: 422 con
    las opciones, y nada creado."""
    from app.models.solicitudes import Solicitud
    from tests.conftest import ArbolESFTT
    with app.app_context():
        solicitud = (Solicitud.query.filter_by(expediente_id=expediente_seed)
                     .order_by(Solicitud.id).first())
        fase = ArbolESFTT(db).fase('RESOLUCION', solicitud=solicitud)
        tramite = ArbolESFTT(db).tramite(fase, 'NOTIFICACION')
        tipo_id = _tipo_tarea('NOTIFICAR').id
        db.session.commit()
        fase_id, tramite_id = fase.id, tramite.id
    try:
        r = usuario_supervisor.post(
            f'/api/expedientes/{expediente_seed}/nodo/tramite/{tramite_id}/hijos',
            json={'tipo_id': tipo_id, 'bypass': True, 'justificacion': 'test #967'})
        assert r.status_code == 422
        assert 'SOLICITANTE' in r.get_json()['error']
        with app.app_context():
            assert Tarea.query.filter_by(tramite_id=tramite_id).count() == 0
    finally:
        with app.app_context():
            from app.models.fases import Fase
            Fase.query.filter_by(id=fase_id).delete()
            db.session.commit()


def test_escritos_no_se_generan_en_notificar(usuario_supervisor, expediente_seed,
                                            notificar_http, app):
    """Regresión de la auditoría de #967: /api/escritos/generar vinculaba un
    producido a cualquier tarea, saltándose el bloqueo sin destinatario."""
    from app.models.plantillas import Plantilla
    tarea_id = notificar_http()
    with app.app_context():
        plantilla = Plantilla.query.order_by(Plantilla.id).first()
        assert plantilla is not None, 'la semilla debe traer una plantilla'
        plantilla_id = plantilla.id

    r = usuario_supervisor.post('/api/escritos/generar',
                                json={'plantilla_id': plantilla_id, 'tarea_id': tarea_id})

    assert r.status_code == 422
    assert 'ELABORAR' in r.get_json()['error']
    with app.app_context():
        assert db.session.get(Tarea, tarea_id).vinculos_documento == []
