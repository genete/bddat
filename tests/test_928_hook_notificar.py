"""
Tests #928 (N1, 928c) — el acto de notificar sin fechas en la fila: hook de
`editar_tarea`, RECHAZADA y sede en el resto del sistema.

  - Hook (§6): crea la fila con cualquiera de los seis justificantes con canal,
    siempre con `resultado = NULL` (D2); SEDE y ANUNCIO_PUBLICADO no la crean;
    desvincular el último justificante la borra si no hay resultado y la
    conserva si lo hay (D16); avisa —y deja bitácora— del rol incoherente con el
    tipo y de canales distintos (D17).
  - RECHAZADA y sede (§7): `Tramite.finalizado`, `_check_crear_esperar_plazo`.
  - Contrato de NOTIFICAR (§8): `_check_finalizar_tarea`, radar de huérfanos.
  - PDF polivalente (§9): el mismo fichero como DISPOSICION y como NOTIFICA.
  - Sin N+1 en el árbol con varias NOTIFICAR (#907).

BD de tests con rollback por SAVEPOINT (app_ctx) + fs_tmp para el movimiento
físico de `mover_a_esftt`. Los endpoints HTTP están en test_928_api_notificar.py.
"""
import pytest
from sqlalchemy import event, text

from app import db
from app.models.documentos import Documento
from app.models.notificaciones import Notificacion
from app.models.tipos_documentos import TipoDocumento
from app.services import mutaciones_arbol as svc


@pytest.fixture
def con_usuario(app_ctx):
    """Petición con usuario autenticado: la bitácora (avisos del hook, D17;
    desvincular un documento crítico, #738) necesita `current_user` real."""
    from flask_login import login_user
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    with app_ctx.test_request_context():
        login_user(usuario)
        yield usuario


def _hoy():
    from app.services.reloj_simulado import hoy
    return hoy()


def _tarea_notificar(arbol, codigo_tramite='NOTIFICACION'):
    fase = arbol.fase('ANALISIS_SOLICITUD', solicitud=arbol.solicitud_propia())
    tramite = arbol.tramite(fase, codigo_tramite)
    return arbol.tarea(tramite, 'NOTIFICAR')


def _doc(tarea, codigo, fs_tmp, nombre=None, contenido=b'%PDF-1.4 justificante'):
    """Documento del pool con fichero real (mover_a_esftt lo mueve al vincular)."""
    tipo = TipoDocumento.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el tipo de documento {codigo}'
    nombre = nombre or f'{codigo.lower()}-{tarea.id}.pdf'
    (fs_tmp / nombre).write_bytes(contenido)
    doc = Documento(expediente_id=tarea.tramite.fase.solicitud.expediente_id, url=nombre,
                    tipo_doc_id=tipo.id, asunto='#928c test', fecha_administrativa=_hoy())
    db.session.add(doc)
    db.session.flush()
    return doc


def _guardar(tarea, consumidos=(), producido=None):
    return svc.editar_tarea(
        tarea, documentos_consumidos_ids=[d.id for d in consumidos],
        documento_producido_id=producido.id if producido else None, notas=None)


def _fila(tarea):
    return Notificacion.query.filter_by(tarea_id=tarea.id).first()


# ---------------------------------------------------------------------------
# Hook: creación de la fila
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('codigo,rol,canal', [
    ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO', 'NOTIFICA'),
    ('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO', 'POSTAL'),
    ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', 'NOTIFICA'),
    ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', 'POSTAL'),
    ('JUSTIFICANTE_BANDEJA', 'PRODUCIDO', 'BANDEJA'),
    ('JUSTIFICANTE_SIR', 'PRODUCIDO', 'SIR'),
])
def test_hook_crea_fila_sin_resultado_con_cada_tipo_con_canal(
        con_usuario, arbol_aislado, fs_tmp, codigo, rol, canal):
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, codigo, fs_tmp)

    res = _guardar(tarea, consumidos=[doc] if rol == 'CONSUMIDO' else [],
                   producido=doc if rol == 'PRODUCIDO' else None)

    assert res.ok is True, res.error
    assert res.advertencia is None
    notif = _fila(tarea)
    assert notif is not None
    assert notif.canal == canal
    assert notif.resultado is None
    assert notif.numero_intento == 1
    # documento_id sigue al PRODUCIDO; un previo consumido no lo fija.
    assert notif.documento_id == (doc.id if rol == 'PRODUCIDO' else None)


@pytest.mark.parametrize('codigo,rol', [
    ('JUSTIFICANTE_SEDE', 'CONSUMIDO'),
    ('ANUNCIO_PUBLICADO', 'PRODUCIDO'),
])
def test_hook_sede_y_anuncio_no_crean_fila(con_usuario, arbol_aislado, fs_tmp, codigo, rol):
    """La sede no es una notificación; el edicto es de #568 (D15)."""
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, codigo, fs_tmp)

    res = _guardar(tarea, consumidos=[doc] if rol == 'CONSUMIDO' else [],
                   producido=doc if rol == 'PRODUCIDO' else None)

    assert res.ok is True, res.error
    assert _fila(tarea) is None


def test_hook_previo_y_final_mismo_canal_una_sola_fila(con_usuario, arbol_aislado, fs_tmp):
    """Disposición (consumido) y justificante final (producido): el canal lo da
    el producido; la fila, una, con documento_id del producido."""
    tarea = _tarea_notificar(arbol_aislado)
    disposicion = _doc(tarea, 'JUSTIFICANTE_NOTIFICA_DISPOSICION', fs_tmp)
    assert _guardar(tarea, consumidos=[disposicion]).ok
    final = _doc(tarea, 'JUSTIFICANTE_NOTIFICA', fs_tmp)

    res = _guardar(tarea, consumidos=[disposicion], producido=final)

    assert res.ok is True, res.error
    assert res.advertencia is None
    assert Notificacion.query.filter_by(tarea_id=tarea.id).count() == 1
    assert _fila(tarea).documento_id == final.id


# ---------------------------------------------------------------------------
# Hook: desvincular (D16)
# ---------------------------------------------------------------------------

def test_desvincular_ultimo_justificante_sin_resultado_borra_la_fila(
        con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, 'JUSTIFICANTE_POSTAL_1ER', fs_tmp)
    assert _guardar(tarea, consumidos=[doc]).ok
    assert _fila(tarea) is not None

    res = _guardar(tarea)

    assert res.ok is True, res.error
    assert _fila(tarea) is None


def test_desvincular_ultimo_justificante_con_resultado_conserva_la_fila(
        con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, 'JUSTIFICANTE_POSTAL_1ER', fs_tmp)
    assert _guardar(tarea, consumidos=[doc]).ok
    notif = _fila(tarea)
    notif.resultado = 'INCORRECTA'
    db.session.flush()

    res = _guardar(tarea)

    assert res.ok is True, res.error
    assert _fila(tarea) is not None
    assert _fila(tarea).resultado == 'INCORRECTA'


def test_desvincular_uno_de_dos_justificantes_conserva_la_fila(con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    disposicion = _doc(tarea, 'JUSTIFICANTE_NOTIFICA_DISPOSICION', fs_tmp)
    final = _doc(tarea, 'JUSTIFICANTE_NOTIFICA', fs_tmp)
    assert _guardar(tarea, consumidos=[disposicion], producido=final).ok

    res = _guardar(tarea, consumidos=[disposicion])

    assert res.ok is True, res.error
    notif = _fila(tarea)
    assert notif is not None
    assert notif.documento_id is None  # sigue al producido, que ya no hay


# ---------------------------------------------------------------------------
# Hook: avisos no bloqueantes con bitácora (D17)
# ---------------------------------------------------------------------------

def _ultima_advertencia_bitacora(tarea_id):
    return db.session.execute(text(
        "select detalle from bitacora where tabla='tareas' and registro_id=:tid "
        "and (detalle->>'advertencia')::boolean order by id desc limit 1"
    ), {'tid': tarea_id}).scalar()


def test_previo_vinculado_como_producido_avisa_y_deja_bitacora(con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, 'JUSTIFICANTE_NOTIFICA_DISPOSICION', fs_tmp)

    res = _guardar(tarea, producido=doc)

    assert res.ok is True, res.error
    assert res.advertencia is not None
    assert 'JUSTIFICANTE_NOTIFICA_DISPOSICION' in res.advertencia['motivo']
    assert 'consumido' in res.advertencia['motivo']
    detalle = _ultima_advertencia_bitacora(tarea.id)
    assert detalle is not None
    assert detalle['motivo'] == res.advertencia['motivo']
    assert 'sujeto' in detalle


def test_final_vinculado_como_consumido_avisa(con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, 'JUSTIFICANTE_SIR', fs_tmp)

    res = _guardar(tarea, consumidos=[doc])

    assert res.ok is True, res.error
    assert 'JUSTIFICANTE_SIR' in res.advertencia['motivo']
    assert 'producido' in res.advertencia['motivo']


def test_anuncio_consumido_no_avisa(con_usuario, arbol_aislado, fs_tmp):
    """La copia intermedia del anuncio se consume (#568): no es rol incoherente."""
    tarea = _tarea_notificar(arbol_aislado)
    doc = _doc(tarea, 'ANUNCIO_PUBLICADO', fs_tmp)

    res = _guardar(tarea, consumidos=[doc])

    assert res.ok is True, res.error
    assert res.advertencia is None


def test_canales_distintos_entre_previos_avisa(con_usuario, arbol_aislado, fs_tmp):
    tarea = _tarea_notificar(arbol_aislado)
    disposicion = _doc(tarea, 'JUSTIFICANTE_NOTIFICA_DISPOSICION', fs_tmp)
    primer_intento = _doc(tarea, 'JUSTIFICANTE_POSTAL_1ER', fs_tmp)

    res = _guardar(tarea, consumidos=[disposicion, primer_intento])

    assert res.ok is True, res.error
    assert 'canales distintos' in res.advertencia['motivo']
    assert _ultima_advertencia_bitacora(tarea.id) is not None


def test_cambio_de_postal_a_otro_canal_normaliza_el_intento(con_usuario, arbol_aislado, fs_tmp):
    """ck_notificaciones_intento_postal (D14): fuera de POSTAL, intento 1."""
    tarea = _tarea_notificar(arbol_aislado)
    primer_intento = _doc(tarea, 'JUSTIFICANTE_POSTAL_1ER', fs_tmp)
    assert _guardar(tarea, consumidos=[primer_intento]).ok
    notif = _fila(tarea)
    notif.numero_intento = 2
    db.session.flush()
    final = _doc(tarea, 'JUSTIFICANTE_NOTIFICA', fs_tmp)

    res = _guardar(tarea, consumidos=[primer_intento], producido=final)

    assert res.ok is True, res.error
    db.session.refresh(notif)
    assert notif.canal == 'NOTIFICA'
    assert notif.numero_intento == 1


# ---------------------------------------------------------------------------
# CHECKs de 928c
# ---------------------------------------------------------------------------

def test_check_intento_2_solo_en_postal(app_ctx, arbol_esftt):
    from sqlalchemy.exc import IntegrityError
    fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
    tarea = arbol_esftt.tarea(arbol_esftt.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    with pytest.raises(IntegrityError):
        with db.session.begin_nested():
            arbol_esftt.notificacion(tarea, canal='NOTIFICA', numero_intento=2)


def test_check_resultado_admite_rechazada(app_ctx, arbol_esftt):
    fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
    tarea = arbol_esftt.tarea(arbol_esftt.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    assert arbol_esftt.notificacion(tarea, resultado='RECHAZADA').id is not None


# ---------------------------------------------------------------------------
# RECHAZADA y sede en el resto del sistema (§7)
# ---------------------------------------------------------------------------

def _notificar_ejecutada(arbol, *, resultado, canal='NOTIFICA', sede=None, sede_justificacion=None):
    """NOTIFICAR con documento a notificar, justificante final y fila. `sede`:
    None (sin justificante de sede) o 'PUESTA' (JUSTIFICANTE_SEDE con fecha)."""
    fase = arbol.fase('ANALISIS_SOLICITUD')
    tramite = arbol.tramite(fase, 'NOTIFICACION')
    tarea = arbol.tarea(tramite, 'NOTIFICAR')
    exp_id = fase.solicitud.expediente_id
    final = 'JUSTIFICANTE_POSTAL' if canal == 'POSTAL' else 'JUSTIFICANTE_NOTIFICA'
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'{tarea.id}-res'), 'CONSUMIDO')
    arbol.vincular(tarea, arbol.documento(exp_id, final, f'{tarea.id}-fin', fecha=_hoy()), 'PRODUCIDO')
    if sede == 'PUESTA':
        arbol.vincular(tarea, arbol.documento(exp_id, 'JUSTIFICANTE_SEDE', f'{tarea.id}-sede',
                                              fecha=_hoy()), 'CONSUMIDO')
    arbol.notificacion(tarea, resultado=resultado, canal=canal,
                       sede_justificacion=sede_justificacion)
    db.session.expire(tarea)
    return tramite, tarea


@pytest.mark.parametrize('resultado,finalizado', [
    ('CORRECTA', True), ('RECHAZADA', True), ('INCORRECTA', False), (None, False),
])
def test_tramite_finalizado_segun_resultado(app_ctx, arbol_esftt, resultado, finalizado):
    tramite, _ = _notificar_ejecutada(arbol_esftt, resultado=resultado)
    assert tramite.finalizado is finalizado


@pytest.mark.parametrize('sede,justificacion,finalizado', [
    (None, None, False),            # PENDIENTE: impide finalizar (D4)
    ('PUESTA', None, True),
    (None, 'Destinatario sin acceso', True),  # JUSTIFICADA
])
def test_tramite_finalizado_postal_segun_sede(app_ctx, arbol_esftt, sede, justificacion, finalizado):
    tramite, _ = _notificar_ejecutada(arbol_esftt, resultado='CORRECTA', canal='POSTAL',
                                      sede=sede, sede_justificacion=justificacion)
    assert tramite.finalizado is finalizado


@pytest.mark.parametrize('resultado,bloquea', [
    ('CORRECTA', False), ('RECHAZADA', False), ('INCORRECTA', True),
])
def test_crear_esperar_plazo_segun_resultado(app_ctx, arbol_esftt, resultado, bloquea):
    from app.services.invariantes_esftt import _check_crear_esperar_plazo
    tramite, _ = _notificar_ejecutada(arbol_esftt, resultado=resultado)
    assert (_check_crear_esperar_plazo(tramite.id) is not None) is bloquea


def test_crear_esperar_plazo_no_espera_a_la_sede(app_ctx, arbol_esftt):
    """D18: la sede pendiente impide finalizar el trámite, no abrir la espera."""
    from app.services.invariantes_esftt import _check_crear_esperar_plazo
    tramite, _ = _notificar_ejecutada(arbol_esftt, resultado='CORRECTA', canal='POSTAL')
    assert tramite.finalizado is False
    assert _check_crear_esperar_plazo(tramite.id) is None


# ---------------------------------------------------------------------------
# Contrato de NOTIFICAR (§8)
# ---------------------------------------------------------------------------

def test_finalizar_tarea_con_solo_justificante_previo_bloquea(app_ctx, arbol_esftt):
    from app.services.invariantes_esftt import _check_finalizar_tarea
    fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
    tarea = arbol_esftt.tarea(arbol_esftt.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    exp_id = fase.solicitud.expediente_id
    arbol_esftt.vincular(tarea, arbol_esftt.documento(
        exp_id, 'JUSTIFICANTE_NOTIFICA_DISPOSICION', f'{tarea.id}-disp', fecha=_hoy()), 'CONSUMIDO')
    arbol_esftt.vincular(tarea, arbol_esftt.documento(
        exp_id, 'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-fin', fecha=_hoy()), 'PRODUCIDO')
    db.session.expire(tarea)

    res = _check_finalizar_tarea(tarea.id)

    assert res is not None
    assert 'documento de entrada' in res.norma_compilada


def test_huerfanos_ofrece_el_previo_aunque_la_tarea_este_ejecutada(app_ctx, arbol_esftt):
    """D10: el PDF polivalente puede subirse por segunda vez después del final."""
    from app.services.huerfanos import tareas_candidatas
    fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
    tarea = arbol_esftt.tarea(arbol_esftt.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    exp_id = fase.solicitud.expediente_id
    arbol_esftt.vincular(tarea, arbol_esftt.documento(
        exp_id, 'JUSTIFICANTE_NOTIFICA', f'{tarea.id}-fin', fecha=_hoy()), 'PRODUCIDO')
    previo = arbol_esftt.documento(exp_id, 'JUSTIFICANTE_NOTIFICA_DISPOSICION',
                                   f'{tarea.id}-disp', fecha=_hoy())
    otro = arbol_esftt.documento(exp_id, 'RESOLUCION', f'{tarea.id}-res')
    db.session.expire(tarea)

    candidatas_previo = [c for c in tareas_candidatas(previo) if c['tarea_id'] == tarea.id]
    candidatas_otro = [c for c in tareas_candidatas(otro) if c['tarea_id'] == tarea.id]

    assert any(c['rol'] == 'CONSUMIDO' for c in candidatas_previo)
    assert not any(c['rol'] == 'CONSUMIDO' for c in candidatas_otro)


# ---------------------------------------------------------------------------
# PDF polivalente (§9): un fichero, dos Documento, dos roles
# ---------------------------------------------------------------------------

def test_pdf_polivalente_ambos_ficheros_validos_y_cada_fecha_la_suya(
        con_usuario, arbol_aislado, fs_tmp):
    from datetime import timedelta
    from app.services.notificaciones import fecha_cumplimiento, fecha_efectos

    tarea = _tarea_notificar(arbol_aislado)
    exp_id = tarea.tramite.fase.solicitud.expediente_id
    (fs_tmp / 'polivalente.pdf').write_bytes(b'%PDF-1.4 polivalente')
    f_disp, f_efectos = _hoy() - timedelta(days=9), _hoy() - timedelta(days=2)
    tipos = {t.codigo: t.id for t in TipoDocumento.query.filter(TipoDocumento.codigo.in_(
        ['JUSTIFICANTE_NOTIFICA_DISPOSICION', 'JUSTIFICANTE_NOTIFICA'])).all()}
    disposicion = Documento(expediente_id=exp_id, url='polivalente.pdf', asunto='#928c test',
                            tipo_doc_id=tipos['JUSTIFICANTE_NOTIFICA_DISPOSICION'],
                            fecha_administrativa=f_disp)
    notifica = Documento(expediente_id=exp_id, url='polivalente.pdf', asunto='#928c test',
                         tipo_doc_id=tipos['JUSTIFICANTE_NOTIFICA'],
                         fecha_administrativa=f_efectos)
    db.session.add_all([disposicion, notifica])
    db.session.flush()

    assert _guardar(tarea, consumidos=[disposicion]).ok
    res = _guardar(tarea, consumidos=[disposicion], producido=notifica)
    assert res.ok is True, res.error
    _fila(tarea).resultado = 'CORRECTA'
    db.session.flush()
    db.session.expire_all()

    import os
    assert os.path.isfile(disposicion.ruta_absoluta())
    assert os.path.isfile(notifica.ruta_absoluta())
    assert fecha_cumplimiento(tarea).fecha == f_disp
    assert fecha_cumplimiento(tarea).documento.id == disposicion.id
    assert fecha_efectos(tarea).fecha == f_efectos
    assert fecha_efectos(tarea).documento.id == notifica.id


# ---------------------------------------------------------------------------
# Sin N+1 en el árbol (#907): el coste no crece con el número de NOTIFICAR
# ---------------------------------------------------------------------------

def _contar_consultas(funcion):
    contador = {'n': 0}

    def _uno(*_args, **_kwargs):
        contador['n'] += 1

    motor = db.engine
    event.listen(motor, 'before_cursor_execute', _uno)
    try:
        funcion()
    finally:
        event.remove(motor, 'before_cursor_execute', _uno)
    return contador['n']


def _anadir_notificar_completa(arbol, fase):
    tramite = arbol.tramite(fase, 'NOTIFICACION')
    tarea = arbol.tarea(tramite, 'NOTIFICAR')
    exp_id = fase.solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'{tarea.id}-res'), 'CONSUMIDO')
    arbol.vincular(tarea, arbol.documento(exp_id, 'JUSTIFICANTE_POSTAL_1ER', f'{tarea.id}-1er',
                                          fecha=_hoy()), 'CONSUMIDO')
    arbol.vincular(tarea, arbol.documento(exp_id, 'JUSTIFICANTE_POSTAL', f'{tarea.id}-fin',
                                          fecha=_hoy()), 'PRODUCIDO')
    arbol.notificacion(tarea, resultado='CORRECTA', canal='POSTAL', numero_intento=2)


@pytest.mark.parametrize('ruta', ['construir_arbol', 'construir_arbol_solicitud'])
def test_arbol_sin_consulta_extra_por_notificar(arbol_aislado, ruta):
    """`documentos_a_notificar`, `justificantes_previos` y `estado_sede` leen
    lo que `opciones_solicitud()` ya carga: ni una consulta más por NOTIFICAR.
    `expunge_all` y no `expire_all`: un objeto caducado sigue en el mapa de
    identidad y `.get()` lo refresca sin las opciones de carga — el N+1 sería
    del test, no de una petición real, que parte de una sesión limpia."""
    from app.services import arbol_expediente

    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
    fase_id, solicitud_id, expediente_id = fase.id, solicitud.id, solicitud.expediente_id
    _anadir_notificar_completa(arbol_aislado, fase)
    arg = expediente_id if ruta == 'construir_arbol' else solicitud_id

    def construir():
        db.session.flush()
        db.session.expunge_all()
        assert getattr(arbol_expediente, ruta)(arg) is not None

    con_una = _contar_consultas(construir)
    from app.models.fases import Fase
    fase = db.session.get(Fase, fase_id)
    for _ in range(3):
        _anadir_notificar_completa(arbol_aislado, fase)
    con_cuatro = _contar_consultas(construir)

    assert con_cuatro == con_una, (con_una, con_cuatro)
