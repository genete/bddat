"""Tests de #996 (N6, ADR-049 §F) — CERT_CIERRE_SOLICITUD y el estado por acto.

El certificado que cuenta cómo terminó la solicitud: se emite solo con cada acto
resuelto en su fase cerrada con su certificado, guarda una foto fija (resumen del
plazo por acto y copia de los certificados de cierre de las fases), y se retira con
justificación. De paso, el estado de la solicitud se decide por acto (D6) y en una
solicitud resuelta y notificada no se abren fases nuevas (asunto 2 de #996).

Fallo silencioso que evita: un certificado de cierre que omite un acto, se emite con
uno sin resolver, invierte el veredicto del plazo o cambia después de emitido, y una
solicitud que se da por resuelta y firme con un acto todavía sin resolver.

Con SQL real (`arbol_aislado`) y los servicios y las rutas llamados dentro de
`test_request_context`, como `test_947` y `test_956`.
"""
from contextlib import contextmanager
from datetime import date

import pytest
from flask import session
from flask_login import login_user

_CODIGO = 'CERT_CIERRE_SOLICITUD'
_F1 = date(2025, 3, 3)
_F2 = date(2025, 3, 10)
_PRESENTADA = date(2025, 1, 7)


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


def _solicitud(arbol, siglas, *, presentada=_PRESENTADA):
    """Solicitud de un expediente recién dado de alta, del tipo `siglas`."""
    from app.models.tipos_solicitudes import TipoSolicitud
    solicitud = arbol.solicitud_propia()
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el TipoSolicitud {siglas!r}'
    solicitud.tipo_solicitud = tipo
    solicitud.documento_solicitud.fecha_administrativa = presentada
    arbol.db.session.flush()
    return solicitud


def _fase_notificada(arbol, solicitud, codigo='RESOLUCION'):
    """Fase de resolución con su NOTIFICACION › NOTIFICAR al solicitante completa
    (puesta a disposición y lectura en Notifica) y resultado favorable."""
    from app.models.tipos_resultados_fases import TipoResultadoFase
    fase = arbol.fase(codigo, solicitud=solicitud)
    tarea = arbol.tarea(arbol.tramite(fase, 'NOTIFICACION'), 'NOTIFICAR')
    exp_id = solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'996-{tarea.id}-r'),
                   'CONSUMIDO')
    arbol.vincular(tarea, arbol.documento(exp_id, 'JUSTIFICANTE_NOTIFICA_DISPOSICION',
                                          f'996-{tarea.id}-d', fecha=_F1), 'CONSUMIDO')
    arbol.vincular(tarea, arbol.documento(exp_id, 'JUSTIFICANTE_NOTIFICA',
                                          f'996-{tarea.id}-j', fecha=_F2), 'PRODUCIDO')
    arbol.notificacion(tarea, resultado='CORRECTA', canal='NOTIFICA')
    favorable = TipoResultadoFase.query.filter_by(codigo='FAVORABLE').first()
    assert favorable is not None, 'la semilla debe traer el resultado FAVORABLE'
    fase.resultado_fase = favorable
    arbol.db.session.flush()
    arbol.db.session.expire(fase, ['tramites'])
    arbol.db.session.expire(tarea)
    return fase


def _cerrar(app_ctx, fase):
    """La fase cerrada como en el circuito real: cumplimiento y cierre certificados."""
    from app.services import cert_cierre_fase, cert_cumplimiento_fase
    with _peticion(app_ctx):
        assert cert_cumplimiento_fase.emitir(fase).emitido
        res = cert_cierre_fase.emitir(fase, confirmacion='cerrar finalizadora')
    assert res.emitido, res.error or [b.pendiente for b in res.informe.pendientes]
    return fase


def _resuelta(app_ctx, arbol, siglas='AAP', **kwargs):
    """Solicitud resuelta: su RESOLUCION, notificada y cerrada con su certificado."""
    solicitud = _solicitud(arbol, siglas, **kwargs)
    _cerrar(app_ctx, _fase_notificada(arbol, solicitud))
    return solicitud


def _emitir(app_ctx, solicitud):
    from app.services import cert_cierre_solicitud
    with _peticion(app_ctx):
        return cert_cierre_solicitud.emitir(solicitud)


def _retirar(app_ctx, solicitud, justificacion):
    from app.services import cert_cierre_solicitud
    with _peticion(app_ctx):
        return cert_cierre_solicitud.retirar(solicitud, justificacion=justificacion)


def _certificado(certificado_id):
    from app import db
    from app.models.certificados import Certificado
    return db.session.get(Certificado, certificado_id)


# ---------------------------------------------------------------------------
# Emitir
# ---------------------------------------------------------------------------

def test_emite_con_una_fase_que_resuelve_dos_actos(app_ctx, arbol_aislado):
    """AAP+AAC resueltas juntas en una RESOLUCION: el certificado nace sin fecha
    propia, con su tipo, anclado a la solicitud y sin `solicitud_id` ni `fase_id`, y
    cuenta los dos actos y copia el certificado de cierre de la fase tal cual.

    Fallo silencioso que evita: la constancia de cierre omite un acto o no queda
    anclada en la solicitud, y nadie lo ve hasta que otra solicitud la necesita.
    """
    from app.services import sellos
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP+AAC')
    cierre_fase = sellos.certificado_cierre(solicitud.fases[0])

    res = _emitir(app_ctx, solicitud)

    assert res.emitido and not res.ya_emitido, res.error or res.informe.pendientes
    certificado = _certificado(res.certificado_id)
    assert certificado.tipo == _CODIGO
    assert (certificado.solicitud_id, certificado.fase_id) == (None, None)
    documento = certificado.documento
    assert documento.fecha_administrativa is None
    assert documento.url == f'bddat://certificados/{certificado.id}'
    assert solicitud.documento_cierre_id == documento.id
    actos = certificado.datos['actos']
    assert [a['acto'] for a in actos] == ['AAP', 'AAC']
    assert {a['veredicto'] for a in actos} == {'EN_PLAZO'}
    (copia,) = certificado.datos['fases']
    assert copia['certificado_id'] == cierre_fase.id
    assert copia['datos'] == cierre_fase.datos
    assert _emitir(app_ctx, solicitud).certificado_id == certificado.id


@pytest.mark.parametrize('caso', ['fase_sin_crear', 'cerrada_sin_certificado'])
def test_no_emite_con_un_acto_sin_resolver(app_ctx, arbol_aislado, caso):
    """Una AAC+DUP con la RESOLUCION cerrada y sin RESOLUCION_DUP, o una fase de
    resolución cerrada como antes de #956 (con un documento, sin su certificado):
    informe con lo que falta, nada creado, y la puerta cerrada también dice que no.

    Fallo silencioso que evita: se emite un certificado de cierre de una solicitud
    con un acto sin resolver.
    """
    from app.models.documentos import Documento
    from app.services.invariantes_esftt import check_invariante
    if caso == 'fase_sin_crear':
        solicitud = _resuelta(app_ctx, arbol_aislado, 'AAC+DUP')
        esperado = 'Falta crear la fase'
    else:
        solicitud = _solicitud(arbol_aislado, 'AAP')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        fase.documento_resultado_id = arbol_aislado.documento(
            solicitud.expediente_id, 'RESOLUCION', '996-cerrada-a-mano').id
        arbol_aislado.db.session.flush()
        esperado = 'sin certificado de cierre'
    antes = Documento.query.filter_by(expediente_id=solicitud.expediente_id).count()

    res = _emitir(app_ctx, solicitud)

    assert not res.emitido and res.error is None and res.bloqueo is None
    assert any(esperado in p for p in res.informe.pendientes), res.informe.pendientes
    assert solicitud.documento_cierre_id is None
    assert Documento.query.filter_by(expediente_id=solicitud.expediente_id).count() == antes
    bloqueo = check_invariante('EMITIR', 'SOLICITUD', solicitud.id, tipo_codigo=_CODIGO)
    assert bloqueo is not None and bloqueo.puede_escapar is False


def test_fuera_de_plazo_se_emite_y_lo_hace_constar(app_ctx, arbol_aislado):
    """Presentada en septiembre de 2024 y notificada en marzo de 2025, la AAP (3
    meses) se resolvió fuera de plazo: se emite igual, y el resumen lo dice con el
    efecto que da el catálogo.

    Fallo silencioso que evita: el veredicto del plazo queda invertido en un
    documento que no se recalcula.
    """
    from app.services.plazos import plazos_de_la_solicitud
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP', presentada=date(2024, 9, 2))
    (plazo,) = plazos_de_la_solicitud(solicitud)

    res = _emitir(app_ctx, solicitud)

    assert res.emitido, res.informe.pendientes
    (acto,) = _certificado(res.certificado_id).datos['actos']
    assert acto['veredicto'] == 'FUERA_DE_PLAZO'
    assert acto['efecto'] == (plazo.efecto_nombre or plazo.efecto)


def test_el_emitido_no_cambia_si_cambia_el_escrito_de_solicitud(app_ctx, arbol_aislado):
    """Tras emitir, corregir la fecha del escrito de solicitud cambia el plazo vivo
    pero no la vista del certificado emitido, que se lee de su foto fija.

    Fallo silencioso que evita: el certificado emitido cambia de contenido sin que
    conste.
    """
    from app.modules.expedientes.routes import cert_cierre_solicitud_vista
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP')
    assert _emitir(app_ctx, solicitud).emitido

    def html():
        with _peticion(app_ctx):
            return cert_cierre_solicitud_vista(solicitud.expediente_id, solicitud.id)

    assert '07/01/2025' in html()
    solicitud.documento_solicitud.fecha_administrativa = date(2025, 1, 20)
    arbol_aislado.db.session.flush()

    despues = html()
    assert '07/01/2025' in despues and '20/01/2025' not in despues


# ---------------------------------------------------------------------------
# Retirar (D4)
# ---------------------------------------------------------------------------

# Fallo silencioso que evita: retirar deja la solicitud apuntando a un documento
# borrado, o borra uno que otra solicitud consume.
def test_retirar_borra_vacia_el_ancla_y_el_siguiente_lo_relata(app_ctx, arbol_aislado):
    from app import db
    from app.models.bitacora import Bitacora
    from app.models.documentos import Documento
    from app.services.cert_cierre_solicitud import ACCION_RETIRAR
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP')
    emision = _emitir(app_ctx, solicitud)

    res = _retirar(app_ctx, solicitud, 'La fecha de presentación estaba mal')

    assert res.ok, res.error
    assert solicitud.documento_cierre_id is None
    assert db.session.get(Documento, emision.documento_id) is None
    assert _certificado(emision.certificado_id) is None
    entrada = (Bitacora.query.filter_by(tabla='solicitudes', registro_id=solicitud.id)
               .order_by(Bitacora.id.desc()).first())
    assert entrada.detalle['accion'] == ACCION_RETIRAR
    assert entrada.detalle['justificacion'] == 'La fecha de presentación estaba mal'

    siguiente = _emitir(app_ctx, solicitud)
    retiradas = _certificado(siguiente.certificado_id).datos['retiradas']
    assert any('«La fecha de presentación estaba mal»' in r for r in retiradas)


def test_retirar_bloqueado_si_una_tarea_lo_usa(app_ctx, arbol_aislado):
    from app.models.solicitudes import Solicitud
    from tests.conftest import documento_ancla_de_prueba
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP')
    emision = _emitir(app_ctx, solicitud)
    # Otra solicitud del expediente lo usa como entrada (#997, hoy a mano).
    otra = Solicitud(expediente_id=solicitud.expediente_id, entidad_id=solicitud.entidad_id,
                     tipo_solicitud_id=solicitud.tipo_solicitud_id,
                     documento_solicitud_id=documento_ancla_de_prueba(
                         solicitud.expediente_id).id)
    arbol_aislado.db.session.add(otra)
    arbol_aislado.db.session.flush()
    tarea = arbol_aislado.tarea(arbol_aislado.tramite(
        arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=otra), 'ANALISIS_DOCUMENTAL'),
        'ANALIZAR')
    arbol_aislado.vincular(tarea, solicitud.documento_cierre, 'CONSUMIDO')

    res = _retirar(app_ctx, solicitud, 'Ya no hace falta')

    assert not res.ok and 'vinculado' in res.error
    assert solicitud.documento_cierre_id == emision.documento_id
    assert _certificado(emision.certificado_id) is not None


# ---------------------------------------------------------------------------
# El estado de la solicitud, por acto (D6), y no abrir fases en una firme
# ---------------------------------------------------------------------------

def test_aac_dup_sin_resolucion_dup_no_esta_resuelta(app_ctx, arbol_aislado):
    """AAC+DUP con la RESOLUCION cerrada y sin RESOLUCION_DUP: la solicitud sigue en
    trámite, cerrar esa fase no pidió la frase del cierre irreversible y la fase,
    aunque notificada, se puede reabrir.

    Fallo silencioso que evita: la solicitud se da por resuelta y firme con un acto
    sin resolver, y se bloquea la reapertura de sus fases.
    """
    from app.services import cert_cierre_fase, cert_cumplimiento_fase
    from app.services.invariantes_esftt import check_invariante
    solicitud = _solicitud(arbol_aislado, 'AAC+DUP')
    fase = _fase_notificada(arbol_aislado, solicitud)
    with _peticion(app_ctx):
        assert cert_cumplimiento_fase.emitir(fase).emitido
        assert cert_cierre_fase.revisar(fase).cierra_solicitud is False
        assert cert_cierre_fase.emitir(fase).emitido      # sin frase

    assert solicitud.estado == 'EN_TRAMITE'
    assert check_invariante('REABRIR', 'FASE', fase.id) is None


def test_en_una_solicitud_resuelta_y_notificada_no_se_crean_fases(app_ctx, arbol_aislado):
    """Ni con justificación. Con un acto aún sin su fase (D6) la solicitud no está
    resuelta, y esa fase sí se puede crear.

    Fallo silencioso que evita: una fase creada por error devuelve la solicitud
    resuelta a «en trámite», deja reabrir su resolución ya notificada y el
    certificado de cierre queda describiendo un cierre que ya no existe.
    """
    from app.models.tipos_fases import TipoFase
    from app.services import mutaciones_arbol
    from app.services.invariantes_esftt import check_invariante
    resuelta = _resuelta(app_ctx, arbol_aislado, 'AAP')
    assert resuelta.estado.startswith('RESUELTA')
    tipo = TipoFase.query.filter_by(codigo='RECONOCIMIENTO_INTERESADO').first()

    with _peticion(app_ctx):
        res = mutaciones_arbol.crear_fase(resuelta, tipo, justificacion='La necesito igual')

    assert not res.ok and res.bloqueo is not None and res.bloqueo.puede_escapar is False
    assert len(resuelta.fases) == 1 and resuelta.estado.startswith('RESUELTA')

    pendiente_dup = _resuelta(app_ctx, arbol_aislado, 'AAC+DUP')
    assert check_invariante('CREAR', 'FASE', pendiente_dup.id,
                            tipo_codigo='RESOLUCION_DUP') is None


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('metodo', ['POST', 'DELETE'])
def test_sin_gestionar_estructura_403(app_ctx, arbol_aislado, metodo):
    """Fallo silencioso que evita: un rol sin permiso emite o retira el certificado
    y no se ve desde el rol que sí lo tiene."""
    from app.routes.api_expedientes import (
        emitir_cert_cierre_solicitud_nodo, retirar_cert_cierre_solicitud_nodo,
    )
    solicitud = _resuelta(app_ctx, arbol_aislado, 'AAP')
    if metodo == 'DELETE':
        assert _emitir(app_ctx, solicitud).emitido
    ruta = (emitir_cert_cierre_solicitud_nodo if metodo == 'POST'
            else retirar_cert_cierre_solicitud_nodo)
    antes = solicitud.documento_cierre_id

    with _peticion(app_ctx, rol='ADMINISTRATIVO', method=metodo,
                   json={'justificacion': 'Sin permiso'}):
        status, _ = _respuesta(ruta(solicitud.expediente_id, solicitud.id))

    assert status == 403
    assert solicitud.documento_cierre_id == antes
