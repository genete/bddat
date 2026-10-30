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
