"""Tests #885 — el corte que parte el proyecto en versiones (ADR-044 §C).

Tres bloques:
  A) `declarar_reformado`: lo que acepta, lo que rechaza y el rastro que deja en
     bitácora — declarar un reformado obliga a rehacer fases preceptivas, así que
     es un acto con consecuencias.
  B) El orden de los cortes: manda `fecha_administrativa` y el `id` desempata. De
     ahí sale qué versión es la vigente y cuál es el único corte reversible.
  C) La guarda del pool: el documento que abre corte deja de ser borrable.

Las fechas se derivan del reloj del sistema (`hoy()`), no de `date.today()`: bajo
`app_ctx` el reloj puede estar simulado (#820) y el modelo rechaza las futuras.
"""
from datetime import timedelta

import pytest


CODIGO_PROYECTO = 'DOC_PROYECTO'


@pytest.fixture
def usuario_id():
    """Cualquier usuario real: la bitácora tiene FK a `usuarios`."""
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    assert usuario is not None, 'la semilla debe traer al menos un usuario'
    return usuario.id


def _proyecto(arbol, expediente_id, sufijo, *, dias_atras=30):
    """Un DOC_PROYECTO del pool con fecha administrativa."""
    from app import db
    from app.services.reloj_simulado import hoy

    doc = arbol.documento(expediente_id, CODIGO_PROYECTO, f'885-{sufijo}')
    doc.fecha_administrativa = hoy() - timedelta(days=dias_atras)
    db.session.flush()
    return doc


def _entradas_bitacora(reformado_id):
    from app.models.bitacora import Bitacora
    return Bitacora.query.filter_by(
        tabla='reformados_proyecto', registro_id=reformado_id).all()


# ---------------------------------------------------------------------------
# A) Alta del corte
# ---------------------------------------------------------------------------

def test_declarar_crea_el_corte_y_lo_anota_en_bitacora(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'alta')

    reformado = declarar_reformado(doc, 'REQUERIDO', usuario_id=usuario_id)

    assert reformado.documento_id == doc.id
    assert reformado.origen == 'REQUERIDO'
    assert doc.reformado_proyecto is reformado

    anotaciones = _entradas_bitacora(reformado.id)
    assert len(anotaciones) == 1, 'declarar un reformado deja exactamente una entrada'
    assert anotaciones[0].operacion == 'CREAR'
    assert anotaciones[0].detalle['origen'] == 'REQUERIDO'


def test_declarar_rechaza_lo_que_no_es_proyecto(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    otro = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', '885-no-proyecto')

    with pytest.raises(ValueError, match='clasificado como proyecto'):
        declarar_reformado(otro, 'VOLUNTARIO', usuario_id=usuario_id)


def test_declarar_exige_fecha_administrativa(app_ctx, arbol_esftt, usuario_id):
    """Sin cronología no hay tramos, y sin tramos no hay versiones."""
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = arbol_esftt.documento(sol.expediente_id, CODIGO_PROYECTO, '885-sin-fecha')
    assert doc.fecha_administrativa is None

    with pytest.raises(ValueError, match='fecha administrativa'):
        declarar_reformado(doc, 'VOLUNTARIO', usuario_id=usuario_id)


def test_declarar_rechaza_origen_desconocido(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'origen-raro')

    with pytest.raises(ValueError, match='Origen de reformado desconocido'):
        declarar_reformado(doc, 'DE_OFICIO', usuario_id=usuario_id)


def test_un_documento_no_abre_dos_cortes(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'duplicado')
    declarar_reformado(doc, 'VOLUNTARIO', usuario_id=usuario_id)

    with pytest.raises(ValueError, match='ya abre un reformado'):
        declarar_reformado(doc, 'VOLUNTARIO', usuario_id=usuario_id)


# ---------------------------------------------------------------------------
# B) El orden de los cortes
# ---------------------------------------------------------------------------

def test_los_cortes_se_ordenan_por_fecha_no_por_alta(app_ctx, arbol_esftt, usuario_id):
    """El técnico puede subir el reformado antiguo después: manda la fecha."""
    from app.services.reformados import declarar_reformado, reformados_de, ultimo_reformado

    sol = arbol_esftt.solicitud_nueva()
    reciente = _proyecto(arbol_esftt, sol.expediente_id, 'reciente', dias_atras=5)
    antiguo = _proyecto(arbol_esftt, sol.expediente_id, 'antiguo', dias_atras=60)

    declarar_reformado(reciente, 'VOLUNTARIO', usuario_id=usuario_id)
    declarar_reformado(antiguo, 'VOLUNTARIO', usuario_id=usuario_id)

    orden = [r.documento_id for r in reformados_de(sol.expediente_id)]
    assert orden == [antiguo.id, reciente.id]
    assert ultimo_reformado(sol.expediente_id).documento_id == reciente.id


def test_misma_fecha_desempata_el_id(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado, reformados_de

    sol = arbol_esftt.solicitud_nueva()
    primero = _proyecto(arbol_esftt, sol.expediente_id, 'mismo-dia-1', dias_atras=10)
    segundo = _proyecto(arbol_esftt, sol.expediente_id, 'mismo-dia-2', dias_atras=10)

    declarar_reformado(segundo, 'VOLUNTARIO', usuario_id=usuario_id)
    declarar_reformado(primero, 'VOLUNTARIO', usuario_id=usuario_id)

    orden = [r.documento_id for r in reformados_de(sol.expediente_id)]
    assert orden == [primero.id, segundo.id]


def test_los_cortes_no_se_mezclan_entre_expedientes(app_ctx, arbol_aislado, usuario_id):
    """`solicitud_propia()` fabrica su propio expediente: `solicitud_nueva()`
    reutiliza el primero de la base y las dos caerían en el mismo pool."""
    from app.services.reformados import declarar_reformado, reformados_de

    uno = arbol_aislado.solicitud_nueva()
    otro = arbol_aislado.solicitud_propia()
    assert uno.expediente_id != otro.expediente_id
    doc_uno = _proyecto(arbol_aislado, uno.expediente_id, 'exp-uno')
    doc_otro = _proyecto(arbol_aislado, otro.expediente_id, 'exp-otro')
    declarar_reformado(doc_uno, 'VOLUNTARIO', usuario_id=usuario_id)
    declarar_reformado(doc_otro, 'VOLUNTARIO', usuario_id=usuario_id)

    assert [r.documento_id for r in reformados_de(uno.expediente_id)] == [doc_uno.id]
    assert [r.documento_id for r in reformados_de(otro.expediente_id)] == [doc_otro.id]


# ---------------------------------------------------------------------------
# C) La guarda del pool
# ---------------------------------------------------------------------------

def test_el_documento_que_abre_corte_no_es_borrable(app_ctx, arbol_esftt, usuario_id):
    """La guarda se construye solo con backrefs (#838): el corte es uno más."""
    from app.modules.expedientes.routes import _documento_es_referenciado
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'guarda')
    assert _documento_es_referenciado(doc) is False

    declarar_reformado(doc, 'VOLUNTARIO', usuario_id=usuario_id)

    assert _documento_es_referenciado(doc) is True


def test_un_doc_proyecto_sin_corte_sigue_siendo_borrable(app_ctx, arbol_esftt):
    """Consecuencia aceptada de retirar `documentos_proyecto` (ADR-044 §B)."""
    from app.modules.expedientes.routes import _documento_es_referenciado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'sin-corte')

    assert _documento_es_referenciado(doc) is False
