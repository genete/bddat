"""
Tests #1037 — marcas de edicto del trámite: PATCH .../nodo/tramite/<id> con
`notificaciones_edicto` (ADR-052 §A y §G).

Fallo silencioso que evita: que las notificaciones que el usuario marcó para ir por
edicto desaparezcan sin aviso al guardar el trámite con un cuerpo sin esa clave (el
edicto se crearía sin ellas o la guarda de creación bloquearía sin que se entienda por
qué), o que se pueda quitar una marca cuando el anuncio ya está remitido al BOE y el
interesado quede fuera de un anuncio ya publicado sin que nada lo señale.

No había otro fichero que pruebe `editar_nodo`/`editar_tramite`: `test_832` declara que
no ve la API JSON y `test_967` solo toca la ruta de hijos. Se entra por la ruta, que es
donde llega el dato (REGLAS_DESARROLLO §Guardas).

BD de tests con rollback por SAVEPOINT (`arbol_aislado`, que trae `almacen_tmp`).
"""
from app import db
from app.models.documentos_tarea import DocumentoTarea
from app.models.notificaciones import Notificacion
from app.services.reloj_simulado import hoy


def _fase_y_tramite(arbol):
    fase = arbol.fase('RESOLUCION_DUP', solicitud=arbol.solicitud_propia())
    return fase, arbol.tramite(fase, 'NOTIFICACION')


def _notificar_a_propietario(arbol, tramite, nombre):
    """Una NOTIFICAR cuya fuente admite edicto (el builder las crea del solicitante)."""
    ta = arbol.tarea(tramite, 'NOTIFICAR')
    ta.notificacion.fuente = 'PROPIETARIOS_DUP'
    ta.notificacion.dest_nombre = nombre
    db.session.flush()
    return ta


def _marcada(tarea):
    """Lo que hay en la BD, no lo que tiene el objeto en memoria."""
    db.session.expire_all()
    return Notificacion.query.filter_by(tarea_id=tarea.id).one().va_por_edicto


def _patch_tramite(cliente, expediente_id, tramite, cuerpo):
    return cliente.patch(f'/api/expedientes/{expediente_id}/nodo/tramite/{tramite.id}', json=cuerpo)


def test_un_guardado_sin_la_clave_no_desmarca(arbol_aislado, usuario_supervisor):
    """Marcar, y luego guardar el trámite con un cuerpo que solo trae `observaciones`
    (un borrador sin la tarjeta de marcas): la marca se conserva y la observación se guarda."""
    fase, tramite = _fase_y_tramite(arbol_aislado)
    expediente_id = fase.solicitud.expediente_id
    ta = _notificar_a_propietario(arbol_aislado, tramite, 'Propietario A')

    r = _patch_tramite(usuario_supervisor, expediente_id, tramite, {'notificaciones_edicto': [ta.id]})
    assert r.status_code == 200, r.get_json()
    assert _marcada(ta)

    r = _patch_tramite(usuario_supervisor, expediente_id, tramite, {'observaciones': 'solo esto'})
    assert r.status_code == 200, r.get_json()
    assert _marcada(ta), 'un cuerpo sin la clave `notificaciones_edicto` borró la marca (#832)'
    db.session.refresh(tramite)
    assert tramite.observaciones == 'solo esto'


def test_la_marca_se_quita_antes_de_la_remision_y_no_despues(arbol_aislado, usuario_supervisor):
    """Una notificación recogida por un edictal se puede quitar mientras la remisión al BOE
    no tenga su justificante; con él vinculado, el conjunto del anuncio queda fijo."""
    fase, tramite = _fase_y_tramite(arbol_aislado)
    expediente_id = fase.solicitud.expediente_id
    ta = _notificar_a_propietario(arbol_aislado, tramite, 'Propietario A')
    edictal = arbol_aislado.tramite(fase, 'NOTIFICACION_EDICTAL')
    remision = arbol_aislado.tarea(edictal, 'NOTIFICAR')

    def recoger():
        db.session.expire_all()
        notif = Notificacion.query.filter_by(tarea_id=ta.id).one()
        notif.va_por_edicto = True
        notif.tramite_edictal_id = edictal.id
        db.session.flush()

    # Antes de la remisión: se quita, y deja de estar recogida.
    recoger()
    r = _patch_tramite(usuario_supervisor, expediente_id, tramite, {'notificaciones_edicto': []})
    assert r.status_code == 200, r.get_json()
    assert not _marcada(ta)
    assert Notificacion.query.filter_by(tarea_id=ta.id).one().tramite_edictal_id is None

    # La remisión sale (su justificante queda vinculado): ya no se quita.
    recoger()
    justificante = arbol_aislado.documento(
        fase.solicitud.expediente_id, 'JUSTIFICANTE_EDICTO', 'remision-edicto', fecha=hoy())
    db.session.add(DocumentoTarea(tarea_id=remision.id, documento_id=justificante.id, rol='PRODUCIDO'))
    db.session.flush()

    r = _patch_tramite(usuario_supervisor, expediente_id, tramite, {'notificaciones_edicto': []})
    assert r.status_code == 422, r.get_json()
    assert 'remitido' in r.get_json()['error']
    assert _marcada(ta), 'se quitó la marca con el anuncio ya remitido al BOE'


def _recogida_por(tarea):
    """(marcada, trámite edictal que la recogió) tal como está en la BD."""
    db.session.expire_all()
    notif = Notificacion.query.filter_by(tarea_id=tarea.id).one()
    return notif.va_por_edicto, notif.tramite_edictal_id


def _crear_edictal(cliente, expediente_id, fase):
    from app.models.tipos_tramites import TipoTramite
    tipo = TipoTramite.query.filter_by(codigo='NOTIFICACION_EDICTAL').one()
    r = cliente.post(f'/api/expedientes/{expediente_id}/nodo/fase/{fase.id}/hijos',
                     json={'tipo_id': tipo.id})
    assert r.status_code == 201, r.get_json()
    return r.get_json()['ids'][0]


def test_cada_edicto_recoge_solo_lo_que_no_era_de_otro_y_de_su_fase(arbol_aislado, usuario_supervisor):
    """Fallo silencioso que evita: que un segundo edicto reasigne las notificaciones que ya
    eran de otro, o que tome marcas de otra fase, y cambie sin aviso el conjunto de un
    anuncio ya redactado.

    Primer edicto: recoge A y B, no C. Segundo, en la misma fase: solo C. Un edicto en otra
    fase de la misma solicitud recoge su D y deja la E marcada de la primera sin recoger."""
    cl = usuario_supervisor
    fase, tramite = _fase_y_tramite(arbol_aislado)
    expediente_id = fase.solicitud.expediente_id
    a, b, c, e = (_notificar_a_propietario(arbol_aislado, tramite, n) for n in 'ABCE')

    _patch_tramite(cl, expediente_id, tramite, {'notificaciones_edicto': [a.id, b.id]})
    e1 = _crear_edictal(cl, expediente_id, fase)
    assert _recogida_por(a) == (True, e1) and _recogida_por(b) == (True, e1)
    assert _recogida_por(c) == (False, None)

    _patch_tramite(cl, expediente_id, tramite, {'notificaciones_edicto': [a.id, b.id, c.id]})
    e2 = _crear_edictal(cl, expediente_id, fase)
    assert _recogida_por(c) == (True, e2)
    assert _recogida_por(a) == (True, e1), 'el segundo edicto se llevó lo que era del primero'

    # E, marcada en la primera fase y sin recoger; D, en otra fase de la misma solicitud.
    _patch_tramite(cl, expediente_id, tramite, {'notificaciones_edicto': [a.id, b.id, c.id, e.id]})
    otra_fase = arbol_aislado.fase('RESOLUCION_AAP', solicitud=fase.solicitud)
    otro_tramite = arbol_aislado.tramite(otra_fase, 'NOTIFICACION')
    d = _notificar_a_propietario(arbol_aislado, otro_tramite, 'D')
    _patch_tramite(cl, expediente_id, otro_tramite, {'notificaciones_edicto': [d.id]})
    e3 = _crear_edictal(cl, expediente_id, otra_fase)
    assert _recogida_por(d) == (True, e3)
    assert _recogida_por(e) == (True, None), 'un edicto de otra fase recogió una marca ajena'


def test_el_anuncio_identifica_a_cada_interesado_solo_por_documento_o_por_nombre(arbol_aislado):
    """Fallo silencioso que evita: que el anuncio del BOE publique el nombre de un afectado
    junto a su documento completo, que la DA 7.ª LOPDGDD prohíbe en las notificaciones por
    anuncios del art. 44, sin que nada falle al generarlo.

    Con documento sale el documento completo; sin él, el nombre; ninguno con las dos cosas, y
    el mismo interesado en dos notificaciones sale una vez."""
    from app.services.context_builders.contexto_anuncio_edictal import ContextoAnuncioEdictal

    fase, tramite = _fase_y_tramite(arbol_aislado)
    edictal = arbol_aislado.tramite(fase, 'NOTIFICACION_EDICTAL')
    elaborar = arbol_aislado.tarea(edictal, 'ELABORAR')
    for nombre, documento in (('Ana Pérez', 'A1111111A'), ('Beatriz Gómez', None),
                              ('Ana P.', 'A1111111A')):
        ta = _notificar_a_propietario(arbol_aislado, tramite, nombre)
        ta.notificacion.dest_nif = documento
        ta.notificacion.va_por_edicto = True
        ta.notificacion.tramite_edictal_id = edictal.id
    db.session.flush()

    contexto = ContextoAnuncioEdictal(fase.solicitud.expediente, db.session, tarea=elaborar).get_contexto()

    assert contexto == {'interesados_edicto': ['A1111111A', 'Beatriz Gómez']}
    assert not any('Ana' in identificacion for identificacion in contexto['interesados_edicto']), \
        'el anuncio publicaría el nombre junto al documento completo (DA 7.ª LOPDGDD)'
