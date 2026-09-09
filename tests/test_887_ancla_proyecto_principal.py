"""Tests #887 — el ancla del proyecto principal y su regla de motor (ADR-044 §D).

Cinco bloques:
  A) El ancla: anclar, mover el ancla y desanclar, cada acto con su bitácora.
  B) La bifurcación de la ingesta (§C): la rama la decide el estado del ancla, no el
     cliente, así que en un lote el primer DOC_PROYECTO puede anclar y el siguiente
     ya se encuentra la otra pregunta.
  C) La regla de motor: bloquea seguir la solicitud sin ancla, deja pasar el propio
     análisis, y no bloquea al expediente heredado.
  D) La guarda del pool sobre el documento anclado.
  E) La divergencia entre el checklist y el ancla, que el JSON del checklist declara.

Las variables se comprueban contra el registry real (`_REGISTRY`), como en #780,
pero aquí con BD: son variables de dato y lo que hay que probar es que leen el campo.
"""
from datetime import timedelta

import pytest


CODIGO_PROYECTO = 'DOC_PROYECTO'


@pytest.fixture
def usuario_id():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    return usuario.id


def _proyecto_doc(arbol, expediente_id, sufijo, *, dias_atras=30):
    from app.services.reloj_simulado import hoy
    return arbol.documento(expediente_id, CODIGO_PROYECTO, f'887-{sufijo}',
                           fecha=hoy() - timedelta(days=dias_atras))


def _variable(nombre):
    import app.services.variables.dato  # noqa: F401
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get(nombre)
    assert fn is not None, f'Variable {nombre!r} no registrada'
    return fn


def _anotaciones(proyecto_id):
    from app.models.bitacora import Bitacora
    return (Bitacora.query
            .filter_by(tabla='proyectos', registro_id=proyecto_id,
                       columna='documento_principal_id')
            .all())


# ---------------------------------------------------------------------------
# A) El ancla
# ---------------------------------------------------------------------------

def test_anclar_deja_el_documento_como_proyecto_y_lo_anota(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import anclar_principal

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'alta')

    proyecto = anclar_principal(doc, usuario_id=usuario_id)

    assert proyecto.documento_principal_id == doc.id
    assert doc.anclado_como_proyecto_principal == [proyecto]
    anotacion = _anotaciones(proyecto.id)[-1]
    assert anotacion.detalle['a'] == doc.id


def test_anclar_otro_documento_mueve_el_ancla(app_ctx, arbol_esftt, usuario_id):
    """El gesto que corrige un anclaje equivocado y el que resuelve la divergencia
    del checklist: no hay que desanclar antes, el ancla se mueve y queda el rastro."""
    from app.services.reformados import anclar_principal

    sol = arbol_esftt.solicitud_nueva()
    primero = _proyecto_doc(arbol_esftt, sol.expediente_id, 'mueve-1')
    segundo = _proyecto_doc(arbol_esftt, sol.expediente_id, 'mueve-2')

    proyecto = anclar_principal(primero, usuario_id=usuario_id)
    anclar_principal(segundo, usuario_id=usuario_id)

    assert proyecto.documento_principal_id == segundo.id
    ultima = _anotaciones(proyecto.id)[-1]
    assert (ultima.detalle['de'], ultima.detalle['a']) == (primero.id, segundo.id)


def test_solo_un_doc_proyecto_puede_ser_el_principal(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import anclar_principal

    sol = arbol_esftt.solicitud_nueva()
    otro = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', '887-no-proyecto')

    with pytest.raises(ValueError, match='clasificado como proyecto'):
        anclar_principal(otro, usuario_id=usuario_id)


def test_desanclar_deja_el_proyecto_sin_documento(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import anclar_principal, desanclar_principal

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'desancla')
    proyecto = anclar_principal(doc, usuario_id=usuario_id)

    desanclar_principal(proyecto, usuario_id=usuario_id)

    assert proyecto.documento_principal_id is None
    assert _anotaciones(proyecto.id)[-1].operacion == 'BORRAR'


def test_dejar_de_ser_proyecto_suelta_el_ancla(app_ctx, arbol_esftt, usuario_id):
    """Cambiar el tipo es desmarcar por la puerta de atrás: un proyecto no puede
    materializarse en un documento que ya no es el proyecto."""
    from app import db
    from app.models.tipos_documentos import TipoDocumento
    from app.services.reformados import anclar_principal, sincronizar_principal

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'cambia-tipo')
    proyecto = anclar_principal(doc, usuario_id=usuario_id)

    doc.tipo_doc_id = TipoDocumento.query.filter_by(codigo='MODELO_SOLICITUD').first().id
    db.session.flush()
    db.session.expire(doc, ['tipo_doc'])
    sincronizar_principal(doc, es_principal=True, usuario_id=usuario_id)

    assert proyecto.documento_principal_id is None


# ---------------------------------------------------------------------------
# B) La bifurcación de la ingesta
# ---------------------------------------------------------------------------

def test_la_rama_la_decide_el_estado_del_ancla(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import (
        RAMA_PRINCIPAL, RAMA_REFORMADO, anclar_principal, rama_de_la_ingesta)

    sol = arbol_esftt.solicitud_nueva()
    expediente = sol.expediente
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'rama')

    assert rama_de_la_ingesta(expediente) == RAMA_PRINCIPAL
    anclar_principal(doc, usuario_id=usuario_id)
    assert rama_de_la_ingesta(expediente) == RAMA_REFORMADO


def test_en_la_rama_del_principal_la_marca_de_reformado_no_cuenta(app_ctx, arbol_esftt, usuario_id):
    """El control del reformado no existía en la interfaz: lo que llegue no es la
    declaración de nadie."""
    from app.services.reformados import declarar_desde_metadatos

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'rama-marca')

    declarar_desde_metadatos(doc, {'abre_reformado': True}, usuario_id=usuario_id)

    assert doc.reformado_proyecto is None
    assert sol.expediente.proyecto.documento_principal_id is None


def test_en_un_lote_el_primero_ancla_y_el_siguiente_ya_es_reformado(app_ctx, arbol_esftt, usuario_id):
    """Por esto no hay caso de «dos principales»: la rama la decide el estado del
    ancla en el momento de procesar cada documento."""
    from app.services.reformados import declarar_desde_metadatos

    sol = arbol_esftt.solicitud_nueva()
    primero = _proyecto_doc(arbol_esftt, sol.expediente_id, 'lote-1', dias_atras=20)
    segundo = _proyecto_doc(arbol_esftt, sol.expediente_id, 'lote-2', dias_atras=10)

    declarar_desde_metadatos(primero, {'es_principal': True}, usuario_id=usuario_id)
    # El segundo llega con la misma marca del front, pero el ancla ya existe.
    declarar_desde_metadatos(segundo, {'es_principal': True, 'abre_reformado': True,
                                       'origen_reformado': 'REQUERIDO'},
                             usuario_id=usuario_id)

    assert sol.expediente.proyecto.documento_principal_id == primero.id
    assert segundo.reformado_proyecto is not None
    assert segundo.reformado_proyecto.origen == 'REQUERIDO'


# ---------------------------------------------------------------------------
# C) La regla de motor
# ---------------------------------------------------------------------------

def _solicitud_de(arbol, siglas):
    from app import db
    from app.models.tipos_solicitudes import TipoSolicitud
    sol = arbol.solicitud_nueva()
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el TipoSolicitud {siglas}'
    sol.tipo_solicitud_id = tipo.id
    db.session.flush()
    return sol


def _reglas_del_ancla(solicitud, tipo_fase):
    """Las reglas de este issue que dispararon, de entre todas las que casaron.

    El objeto va como dict `{'solicitud', 'tipo_fase'}`, que es lo que le pasa
    `crear_fase` al motor: de ahí sale el tercer nivel del sujeto y la variable
    `tipo_sujeto_solicitado`.
    """
    from app.services.assembler import auditar_multi
    resultado = auditar_multi('CREAR', solicitud.expediente,
                              {'solicitud': solicitud, 'tipo_fase': tipo_fase})
    return [r for r in resultado.reglas_evaluadas
            if 'es el proyecto' in (r.descripcion or '') and r.disparada]


def test_la_variable_dice_si_falta_el_ancla(app_ctx, arbol_esftt, usuario_id):
    from app.services.assembler import ExpedienteContext
    from app.services.reformados import anclar_principal

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'variable')
    fn = _variable('proyecto_sin_principal')

    assert fn(ExpedienteContext(sol.expediente)) is True
    anclar_principal(doc, usuario_id=usuario_id)
    assert fn(ExpedienteContext(sol.expediente)) is False


def test_la_variable_del_heredado_trata_null_como_no_heredado(app_ctx, arbol_esftt):
    from app import db
    from app.services.assembler import ExpedienteContext

    sol = arbol_esftt.solicitud_nueva()
    expediente = sol.expediente
    fn = _variable('expediente_heredado')

    expediente.heredado = None
    db.session.flush()
    assert fn(ExpedienteContext(expediente)) is False

    expediente.heredado = True
    db.session.flush()
    assert fn(ExpedienteContext(expediente)) is True


@pytest.mark.parametrize('siglas, cita', [
    ('AAP', 'Art. 123.1'),       # la AAP sola: anteproyecto
    ('AAC', 'Art. 130.1'),       # la AAC sola: proyecto de ejecución
    ('AAP+AAC', 'Art. 130.1'),   # las dos juntas: manda el trámite más avanzado
])
def test_sin_ancla_bloquea_citando_la_norma_del_tramite_mas_avanzado(
        app_ctx, arbol_esftt, siglas, cita):
    """El caso combinado es el que obliga al reparto simple/multi.

    `evaluar_multi` recorre `tipos_simples` en orden y devuelve el **primer**
    BLOQUEAR, y ese orden pone 'AAP' antes que 'AAC'. Con una regla por sujeto sin
    condición, una AAP+AAC se bloquearía citando el anteproyecto del 123.1 cuando lo
    exigible ahí es el proyecto de ejecución del 130.1. Por eso la regla de la AAP
    lleva `solicitud_contiene_aac EQ false` y la de la AAC no lleva ninguna: cubre
    también las combinadas.
    """
    from app.models.tipos_fases import TipoFase
    from app import db

    sol = _solicitud_de(arbol_esftt, siglas)
    sol.expediente.heredado = False
    db.session.flush()
    consultas = TipoFase.query.filter_by(codigo='CONSULTAS').first()

    disparadas = _reglas_del_ancla(sol, consultas)

    assert len(disparadas) == 1, \
        f'una sola regla debe bloquear, con una sola cita: {[r.norma_compilada for r in disparadas]}'
    assert disparadas[0].efecto == 'BLOQUEAR'
    assert cita in disparadas[0].norma_compilada


def test_la_regla_deja_pasar_el_propio_analisis(app_ctx, arbol_esftt):
    """El análisis documental es donde la falta se detecta y se requiere."""
    from app.models.tipos_fases import TipoFase
    from app import db

    sol = _solicitud_de(arbol_esftt, 'AAP')
    sol.expediente.heredado = False
    db.session.flush()
    analisis = TipoFase.query.filter_by(codigo='ANALISIS_SOLICITUD').first()

    assert not _reglas_del_ancla(sol, analisis)


def test_con_el_ancla_puesta_la_regla_no_dispara(app_ctx, arbol_esftt, usuario_id):
    from app.models.tipos_fases import TipoFase
    from app import db
    from app.services.reformados import anclar_principal

    sol = _solicitud_de(arbol_esftt, 'AAP')
    sol.expediente.heredado = False
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'con-ancla')
    anclar_principal(doc, usuario_id=usuario_id)
    db.session.flush()
    consultas = TipoFase.query.filter_by(codigo='CONSULTAS').first()

    assert not _reglas_del_ancla(sol, consultas)


def test_el_expediente_heredado_queda_exento(app_ctx, arbol_esftt):
    """La excepción va en la regla y no como bypass manual: un expediente migrado
    nunca va a tener el dato."""
    from app.models.tipos_fases import TipoFase
    from app import db

    sol = _solicitud_de(arbol_esftt, 'AAP')
    sol.expediente.heredado = True
    db.session.flush()
    consultas = TipoFase.query.filter_by(codigo='CONSULTAS').first()

    assert not _reglas_del_ancla(sol, consultas)


# ---------------------------------------------------------------------------
# D) La guarda del pool
# ---------------------------------------------------------------------------

def test_el_documento_anclado_no_es_borrable(app_ctx, arbol_esftt, usuario_id):
    from app.modules.expedientes.routes import _documento_es_referenciado, _motivo_ancla
    from app.services.reformados import anclar_principal

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto_doc(arbol_esftt, sol.expediente_id, 'guarda')
    assert _documento_es_referenciado(doc) is False

    anclar_principal(doc, usuario_id=usuario_id)

    assert _documento_es_referenciado(doc) is True
    assert 'proyecto de la instalación' in _motivo_ancla(doc)


# ---------------------------------------------------------------------------
# E) La divergencia entre el checklist y el ancla
# ---------------------------------------------------------------------------

def test_el_checklist_declara_la_divergencia_con_el_ancla(app_ctx, arbol_aislado, usuario_id):
    """El requisito es por solicitud y el ancla por expediente: pueden discrepar, y
    el ancla es la fuente (ADR-044 §D). Avisa, no bloquea."""
    from app import db
    from app.models.requisitos_documentales import DocumentoRequisito, RequisitoDocumental
    from app.models.tipos_documentos import TipoDocumento
    from app.routes.api_expedientes import _checklist_documental_json
    from app.services.reformados import anclar_principal

    tarea = arbol_aislado.tarea_propia('ANALIZAR')
    solicitud = tarea.tramite.fase.solicitud
    expediente_id = solicitud.expediente_id

    requisito = (RequisitoDocumental.query
                 .join(TipoDocumento)
                 .filter(TipoDocumento.codigo == CODIGO_PROYECTO,
                         RequisitoDocumental.activo.is_(True))
                 .first())
    assert requisito is not None, 'la semilla debe traer el requisito del proyecto'

    anclado = _proyecto_doc(arbol_aislado, expediente_id, 'divergencia-anclado')
    otro = _proyecto_doc(arbol_aislado, expediente_id, 'divergencia-checklist')
    anclar_principal(anclado, usuario_id=usuario_id)
    db.session.add(DocumentoRequisito(requisito_id=requisito.id, solicitud_id=solicitud.id,
                                      documento_id=otro.id))
    db.session.flush()

    fila = next(it for it in _checklist_documental_json(tarea)
                if it['requisito_id'] == requisito.id)

    assert fila['divergencia_ancla']['documento_anclado']['id'] == anclado.id

    # Y con el mismo documento en las dos vías, no hay nada que avisar.
    anclar_principal(otro, usuario_id=usuario_id)
    fila = next(it for it in _checklist_documental_json(tarea)
                if it['requisito_id'] == requisito.id)
    assert 'divergencia_ancla' not in fila
