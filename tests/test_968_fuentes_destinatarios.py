"""
Tests #968 (N5a-2) — a quién se notifica en cada trámite (ADR-051 §C, §D, §E, §H, §L, §M).

Cada test protege un fallo que pasaría en silencio:

  - Catálogo: un trámite con NOTIFICAR sin fuentes nacería sin saber a quién
    notificar (sustituye a los dos tests de la lista provisional de #967).
  - Botón «añadir las notificaciones que faltan»: crea una por destinatario y,
    repetido, ninguna (duplicaría notificaciones); refresca la dirección antes
    del justificante y no después (cambiaría lo ya enviado); copia congelada
    del representado.
  - Órgano ambiental en la resolución: solo si la solicitud tiene fase
    ambiental (notificaría de más, o de menos).
  - Invariante: un trámite con alguien sin notificar no está terminado, y se
    pinta él mismo en rojo aunque sus tareas estén hechas; uno con una
    notificación que sobra, tampoco; una sin destinatario salvada por escape
    no lo bloquea para siempre.
  - Escritos: destinatario con representante, la separata a su organismo, la
    resolución sin destinatario y el escrito bloqueado si nadie lo eligió.
  - Rendimiento: el cálculo es por solicitud, no por trámite (§M).

BD de tests con rollback por SAVEPOINT (`arbol_aislado`, que trae `almacen_tmp`).
"""
import pytest
from flask_login import login_user

from app import db
from app.models.direccion_notificacion import DireccionNotificacion
from app.models.entidad import Entidad
from app.models.organismos_expediente import OrganismoExpediente
from app.models.tareas import Tarea
from app.models.tipos_tareas import TipoTarea
from app.services import destinatarios_notificacion as dest_svc
from app.services import mutaciones_arbol as svc
from tests.conftest import contar_consultas


@pytest.fixture
def con_usuario(app_ctx):
    """Petición con usuario autenticado: la bitácora usa `current_user`."""
    from app.models.usuarios import Usuario
    usuario = Usuario.query.order_by(Usuario.id).first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    with app_ctx.test_request_context():
        login_user(usuario)
        yield usuario


def _entidad(nombre, nif=None, **roles):
    if not any(roles.values()):
        roles['rol_titular'] = True
    e = Entidad(nombre_completo=nombre, nif=nif, activo=True, **roles)
    db.session.add(e)
    db.session.flush()
    return e


def _direccion(entidad, direccion, *, titular=False, consultado=False):
    d = DireccionNotificacion(
        entidad_id=entidad.id, direccion=direccion, codigo_postal='41001',
        tipo_rol=DireccionNotificacion.calcular_tipo_rol(es_titular=titular,
                                                         es_consultado=consultado))
    db.session.add(d)
    db.session.flush()
    return d


def _consultar(arbol, solicitud, organismo):
    """El organismo consultado en una fase CONSULTAS de la solicitud."""
    fase = next((f for f in solicitud.fases if f.tipo_fase.codigo == 'CONSULTAS'), None)
    if fase is None:
        fase = arbol.fase('CONSULTAS', solicitud=solicitud)
    oe = OrganismoExpediente(expediente_id=solicitud.expediente_id, fase_id=fase.id,
                             organismo_id=organismo.id, via='consulta')
    db.session.add(oe)
    db.session.flush()
    return oe


def _notificar(tramite):
    return [t for t in tramite.tareas if t.tipo_tarea.codigo == 'NOTIFICAR']


def _notificacion_resolucion(arbol):
    solicitud = arbol.solicitud_propia()
    fase = arbol.fase('RESOLUCION', solicitud=solicitud)
    return solicitud, arbol.tramite(fase, 'NOTIFICACION')


def _hecha(arbol, tarea):
    """Deja una NOTIFICAR efectuada (justificante final y resultado)."""
    from app.services.reloj_simulado import hoy
    expediente_id = tarea.tramite.fase.solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(expediente_id, 'RESOLUCION', f'968-r-{tarea.id}'),
                   'CONSUMIDO')
    doc = arbol.documento(expediente_id, 'JUSTIFICANTE_NOTIFICA', f'968-{tarea.id}', fecha=hoy())
    arbol.vincular(tarea, doc, 'PRODUCIDO')
    tarea.notificacion.resultado = 'CORRECTA'
    tarea.notificacion.canal = 'NOTIFICA'
    db.session.flush()


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------

def test_todo_tramite_con_notificar_tiene_fuentes(app_ctx):
    """Sin excepciones desde #964 y #966 (ADR-051 §C)."""
    from app.checks.catalogo_requerido import pares_con_notificar_sin_fuente
    assert pares_con_notificar_sin_fuente() == set()


# ---------------------------------------------------------------------------
# El botón
# ---------------------------------------------------------------------------

def test_boton_crea_una_por_destinatario_y_repetido_ninguna(con_usuario, arbol_aislado):
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    org_a = _entidad('Organismo A', rol_consultado=True)
    org_b = _entidad('Organismo B', rol_consultado=True)
    _consultar(arbol_aislado, solicitud, org_a)
    _consultar(arbol_aislado, solicitud, org_b)

    res = svc.anadir_notificaciones_que_faltan(tramite)

    assert res.ok, res.error or res.bloqueo
    assert len(res.creadas) == 3
    db.session.expire_all()
    pares = {(t.notificacion.fuente, t.notificacion.entidad_id) for t in _notificar(tramite)}
    assert pares == {('SOLICITANTE', solicitud.entidad_id),
                     ('ORGANISMOS_CONSULTADOS', org_a.id),
                     ('ORGANISMOS_CONSULTADOS', org_b.id)}

    res = svc.anadir_notificaciones_que_faltan(tramite)
    assert res.ok and res.creadas == [] and res.rellenadas == []
    assert dest_svc.estado_del_tramite(tramite).faltan == []


def test_boton_refresca_antes_del_justificante_y_no_despues(con_usuario, arbol_aislado):
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    assert svc.anadir_notificaciones_que_faltan(tramite).ok
    tarea = _notificar(tramite)[0]

    # La sede de la solicitud es la dirección del solicitante (#989).
    solicitud.direccion_notificacion_id = _direccion(
        solicitud.entidad, 'Dirección nueva', titular=True).id
    db.session.flush()
    db.session.expire(solicitud, ['sede'])
    res = svc.anadir_notificaciones_que_faltan(tramite)
    assert res.refrescadas == [tarea.id]
    assert tarea.notificacion.dest_direccion == 'Dirección nueva'

    _hecha(arbol_aislado, tarea)
    solicitud.direccion_notificacion_id = _direccion(
        solicitud.entidad, 'Dirección posterior al envío', titular=True).id
    db.session.flush()
    db.session.expire(solicitud, ['sede'])
    res = svc.anadir_notificaciones_que_faltan(tramite)
    assert res.refrescadas == []
    assert tarea.notificacion.dest_direccion == 'Dirección nueva'


def test_representante_nuevo_refresca_y_congela_al_representado(con_usuario, arbol_aislado):
    """La clave es el titular (§D): con un representante asignado después, la
    notificación sin justificante pasa a él y no se crea otra."""
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    assert svc.anadir_notificaciones_que_faltan(tramite).ok
    representante = _entidad('Gestoría S.L.', nif='B12312312')
    solicitud.representante_entidad_id = representante.id
    db.session.flush()

    res = svc.anadir_notificaciones_que_faltan(tramite)

    assert res.creadas == []
    notif = _notificar(tramite)[0].notificacion
    assert notif.entidad_id == representante.id
    assert notif.en_nombre_de_entidad_id == solicitud.entidad_id
    assert notif.dest_en_nombre_de_nombre == solicitud.entidad.nombre_completo
    assert notif.dest_en_nombre_de_nif == solicitud.entidad.nif


# ---------------------------------------------------------------------------
# Órgano ambiental en la resolución
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('con_fase_ambiental', [False, True])
def test_organo_ambiental_solo_con_fase_ambiental(con_usuario, arbol_aislado, con_fase_ambiental):
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    organo = _entidad('Servicio de Prevención Ambiental', rol_consultado=True)
    if con_fase_ambiental:
        fase = arbol_aislado.fase('COMPATIBILIDAD_AMBIENTAL', solicitud=solicitud)
        pedida = arbol_aislado.tramite(fase, 'SOLICITUD_COMPATIBILIDAD')
        assert svc.registrar_destinatario_tramite(pedida, entidad_id=organo.id).ok

    estado = dest_svc.estado_del_tramite(tramite)

    ambientales = [e.titular_id for e in estado.esperados if e.fuente == 'ORGANO_AMBIENTAL']
    assert ambientales == ([organo.id] if con_fase_ambiental else [])


# ---------------------------------------------------------------------------
# Invariante del trámite (§E)
# ---------------------------------------------------------------------------

def test_tramite_con_alguien_sin_notificar_no_esta_terminado(con_usuario, arbol_aislado):
    from app.services import estado_dominio as ed
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    assert svc.anadir_notificaciones_que_faltan(tramite).ok
    _hecha(arbol_aislado, _notificar(tramite)[0])
    assert tramite.finalizado

    _consultar(arbol_aislado, solicitud, _entidad('Organismo tardío', rol_consultado=True))

    assert not tramite.finalizado
    # Sus tareas están en FIN: el rojo es del propio trámite, la caja que falta.
    estados = [ed.estado_tarea(t) for t in tramite.tareas]
    assert set(estados) == {'FIN'}
    assert ed.estado_tramite(tramite, estados) == ('PENDIENTE_TRAMITAR', True)


def _resultado_fase(codigo='FAVORABLE'):
    from app.models.tipos_resultados_fases import TipoResultadoFase
    tipo = TipoResultadoFase.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el resultado de fase {codigo!r}'
    return tipo


def test_organismo_sin_notificar_bloquea_el_cierre_de_fase(con_usuario, arbol_aislado):
    """La cadena completa hasta el certificado de cierre (#956): un organismo
    sin notificar no es solo un trámite en rojo (ya probado arriba) — tiene que
    impedir de verdad `CERT_CIERRE_FASE`, o cerraría la fase con alguien sin
    notificar (zona de nulidad, art. 47.1.e LPACAP). Nadie lo probaba: el único
    test de "trámite sin terminar" de `test_956_cert_cierre_fase.py` usa un
    ELABORAR sin acabar, un camino de código distinto del de
    `destinatarios_notificacion.motivos()` que añadió #968."""
    from app.services import cert_cierre_fase, cert_cumplimiento_fase

    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    fase = tramite.fase
    fase.resultado_fase = _resultado_fase()
    assert svc.anadir_notificaciones_que_faltan(tramite).ok
    _hecha(arbol_aislado, _notificar(tramite)[0])
    db.session.flush()
    assert cert_cumplimiento_fase.emitir(fase).emitido

    _consultar(arbol_aislado, solicitud, _entidad('Organismo tardío', rol_consultado=True))
    assert not tramite.finalizado

    informe = cert_cierre_fase.revisar(fase)
    assert not informe.limpio

    emision = cert_cierre_fase.emitir(fase)
    assert not emision.emitido


def test_sobrante_tras_quitar_el_organismo(con_usuario, arbol_aislado):
    solicitud, tramite = _notificacion_resolucion(arbol_aislado)
    oe = _consultar(arbol_aislado, solicitud, _entidad('Organismo retirado', rol_consultado=True))
    assert svc.anadir_notificaciones_que_faltan(tramite).ok
    for tarea in _notificar(tramite):
        _hecha(arbol_aislado, tarea)
    assert tramite.finalizado

    db.session.delete(oe)
    db.session.flush()

    estado = dest_svc.estado_del_tramite(tramite)
    assert [t.notificacion.fuente for t in estado.sobran] == ['ORGANISMOS_CONSULTADOS']
    assert not tramite.finalizado


def test_escape_sin_destinatario_cubre_su_fuente(con_usuario, arbol_aislado):
    """Una NOTIFICAR que avanzó sin destinatario por escape (§B) ocupa el sitio
    de su fuente: si no, el trámite no podría terminarse nunca."""
    from app.services import bitacora as bitacora_svc
    from app.services.notificaciones import ACCION_SIN_DESTINATARIO
    tramite = arbol_aislado.tramite_sin_destinatario()
    tarea = arbol_aislado.notificar_sin_destinatario(tramite, 'BOLETIN')
    assert [f.fuente for f in dest_svc.estado_del_tramite(tramite).faltan] == ['BOLETIN']

    bitacora_svc.registrar(con_usuario.id, 'ALTERAR', 'tareas', tarea.id,
                           detalle={'accion': ACCION_SIN_DESTINATARIO, 'escape': True})
    db.session.flush()

    assert dest_svc.estado_del_tramite(tramite).completo


# ---------------------------------------------------------------------------
# Elección del usuario (§L)
# ---------------------------------------------------------------------------

def test_eleccion_en_notificar_sin_elaborar_queda_en_el_tramite(con_usuario, arbol_aislado):
    from app.models.tramites_destinatario import TramiteDestinatario
    tramite = arbol_aislado.tramite_sin_destinatario()
    boja = _entidad('Boletín Oficial de Prueba', rol_publicador=True)
    res = svc.crear_tarea(tramite, db.session.query(TipoTarea).filter_by(codigo='NOTIFICAR').one(),
                          justificacion='test #968')
    tarea = db.session.get(Tarea, res.ids[0])
    assert not tarea.notificacion.tiene_destinatario        # nadie lo eligió aún

    assert svc.fijar_destinatario(tarea, entidad_id=boja.id).ok

    assert TramiteDestinatario.query.filter_by(tramite_id=tramite.id).one().entidad_id == boja.id
    assert tarea.notificacion.entidad_id == boja.id
    assert dest_svc.estado_del_tramite(tramite).faltan == []


def test_con_elaborar_se_elige_al_elaborar_no_en_la_notificar(con_usuario, arbol_aislado):
    solicitud = arbol_aislado.solicitud_propia()
    tramite = arbol_aislado.tramite(arbol_aislado.fase('INFORMACION_PUBLICA', solicitud=solicitud),
                                    'TABLON_AYUNTAMIENTOS')
    ayto = _entidad('Ayuntamiento de Prueba', rol_publicador=True)
    tarea = arbol_aislado.notificar_sin_destinatario(tramite, 'AYUNTAMIENTO')

    res = svc.fijar_destinatario(tarea, entidad_id=ayto.id)

    assert not res.ok
    assert tramite.destinatario_elegido is None


# ---------------------------------------------------------------------------
# Escritos (§H)
# ---------------------------------------------------------------------------

def test_escrito_con_representante_va_al_solicitante_en_su_sede(con_usuario, arbol_aislado):
    """#989 (§K): el oficio va al solicitante, a su sede en la solicitud, aunque
    la notificación la reciba su representante. Evita imprimir en el oficio la
    dirección de la gestora o de otra sede."""
    from app.services.escritos import variables_destinatario
    solicitud = arbol_aislado.solicitud_propia()
    representante = _entidad('Gestoría Escritos S.L.', nif='B45645645')
    _direccion(representante, 'Calle de la Gestoría 5', titular=True)
    sede = _direccion(solicitud.entidad, 'Avda. de la Borbolla 5', titular=True)
    solicitud.representante_entidad_id = representante.id
    solicitud.direccion_notificacion_id = sede.id
    db.session.flush()
    tramite = arbol_aislado.tramite(arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud),
                                    'COMUNICACION_INICIO_ADMISION')

    ctx = variables_destinatario(arbol_aislado.tarea(tramite, 'ELABORAR'))

    assert ctx['destinatario_nombre'] == solicitud.entidad.nombre_completo
    assert ctx['destinatario_nif'] == solicitud.entidad.nif
    assert ctx['destinatario_dir']['calle'] == 'Avda. de la Borbolla 5'
    assert ctx['destinatario_en_nombre_de'] is None
    assert ctx['destinatario_representante'] == 'Gestoría Escritos S.L.'


def test_separata_a_su_organismo(con_usuario, arbol_aislado):
    from app.models.tramites_organismos import TramiteOrganismo
    from app.services.escritos import variables_destinatario
    solicitud = arbol_aislado.solicitud_propia()
    organismo = _entidad('Diputación de Prueba', rol_consultado=True)
    oe = _consultar(arbol_aislado, solicitud, organismo)
    tramite = arbol_aislado.tramite(oe.fase, 'CONSULTA_SEPARATA')
    db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
    db.session.flush()

    ctx = variables_destinatario(arbol_aislado.tarea(tramite, 'ELABORAR'))

    assert ctx['destinatario_nombre'] == 'Diputación de Prueba'
    assert ctx['destinatario_en_nombre_de'] is None


def test_resolucion_sin_destinatario(con_usuario, arbol_aislado):
    from app.services.escritos import variables_destinatario
    solicitud = arbol_aislado.solicitud_propia()
    tramite = arbol_aislado.tramite(arbol_aislado.fase('RESOLUCION', solicitud=solicitud),
                                    'ELABORACION')

    assert dest_svc.destinatario_del_tramite(tramite).aplica is False
    assert set(variables_destinatario(arbol_aislado.tarea(tramite, 'ELABORAR')).values()) == {None}


@pytest.fixture
def elaborar_sin_destinatario(app, expediente_seed):
    """ELABORAR del anuncio en el BOP sin boletín elegido, commiteada (las
    rutas no pasan por `app_ctx`, #836), y su limpieza."""
    from app.models.fases import Fase
    from app.models.solicitudes import Solicitud
    from tests.conftest import ArbolESFTT
    with app.app_context():
        arbol = ArbolESFTT(db)
        solicitud = (Solicitud.query.filter_by(expediente_id=expediente_seed)
                     .order_by(Solicitud.id).first())
        assert solicitud is not None, 'la semilla debe traer una solicitud en el expediente'
        fase = arbol.fase('INFORMACION_PUBLICA', solicitud=solicitud)
        tarea = arbol.tarea(arbol.tramite(fase, 'ANUNCIO_BOP'), 'ELABORAR')
        db.session.commit()
        fase_id, tarea_id = fase.id, tarea.id
    yield tarea_id
    with app.app_context():
        db.session.rollback()
        Fase.query.filter_by(id=fase_id).delete()
        db.session.commit()


def test_escrito_bloqueado_sin_destinatario_elegido(usuario_supervisor, app,
                                                    elaborar_sin_destinatario):
    from app.models.plantillas import Plantilla
    with app.app_context():
        plantilla = Plantilla.query.order_by(Plantilla.id).first()
        assert plantilla is not None, 'la semilla debe traer una plantilla'
        plantilla_id = plantilla.id

    r = usuario_supervisor.post('/api/escritos/generar', json={
        'plantilla_id': plantilla_id, 'tarea_id': elaborar_sin_destinatario})

    assert r.status_code == 422
    assert r.get_json()['elegir_destinatario']['fuente'] == 'BOLETIN'
    with app.app_context():
        assert db.session.get(Tarea, elaborar_sin_destinatario).vinculos_documento == []


# ---------------------------------------------------------------------------
# Rendimiento (§M)
# ---------------------------------------------------------------------------

def test_calculo_por_solicitud_no_por_tramite(con_usuario, arbol_aislado):
    """Preguntar `finalizado` a todos los trámites cuesta lo mismo con uno que
    con cuatro: las tablas se cargan una vez por solicitud."""
    from app.models.tramites_organismos import TramiteOrganismo

    def montar(n):
        # Separatas: su fuente (el organismo del trámite) sí lee una tabla.
        solicitud = arbol_aislado.solicitud_propia()
        tramites = []
        for i in range(n):
            organismo = _entidad(f'Organismo {n}-{i}', rol_consultado=True)
            oe = _consultar(arbol_aislado, solicitud, organismo)
            tramite = arbol_aislado.tramite(oe.fase, 'CONSULTA_SEPARATA')
            db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
            tarea = arbol_aislado.notificar_hecha(tramite)
            tarea.notificacion.fuente = 'ORGANISMO_DEL_TRAMITE'
            tarea.notificacion.entidad_id = organismo.id
            db.session.flush()
            tramites.append(tramite)
        for tramite in tramites:            # el árbol ya cargado, como al pintarlo
            for tarea in tramite.tareas:
                _ = tarea.notificacion, tarea.vinculos_documento, tarea.tipo_tarea
        return tramites

    def medir(tramites):
        db.session.info.pop('bddat_destinatarios_notificacion', None)
        return contar_consultas(lambda: [t.finalizado for t in tramites])

    assert medir(montar(1)) == medir(montar(4))
