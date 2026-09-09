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
    """Un DOC_PROYECTO del pool con su fecha administrativa."""
    from app.services.reloj_simulado import hoy

    return arbol.documento(expediente_id, CODIGO_PROYECTO, f'885-{sufijo}',
                           fecha=hoy() - timedelta(days=dias_atras))


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
    """Sin cronología no hay tramos, y sin tramos no hay versiones.

    Defensa en profundidad: el listener del modelo (bloque D) ya impide que un
    DOC_PROYECTO sin fecha llegue a la BD, pero el servicio no da por hecho que le
    llegue uno ya escrito — en memoria la fecha se puede haber vaciado.
    """
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    doc = _proyecto(arbol_esftt, sol.expediente_id, 'sin-fecha')
    fecha = doc.fecha_administrativa
    doc.fecha_administrativa = None

    with pytest.raises(ValueError, match='fecha administrativa'):
        declarar_reformado(doc, 'VOLUNTARIO', usuario_id=usuario_id)

    doc.fecha_administrativa = fecha   # el teardown aún tiene que poder escribir


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

def _orden_de(expediente_id, *documentos):
    """El orden de los cortes del test dentro del expediente.

    Filtrado a propósito: `solicitud_nueva()` reutiliza el primer expediente de la
    base, que puede traer cortes de la semilla o de otro test. Lo que se comprueba
    es la posición relativa, que es lo que define las versiones.
    """
    from app.services.reformados import reformados_de
    mios = {doc.id for doc in documentos}
    return [r.documento_id for r in reformados_de(expediente_id) if r.documento_id in mios]


def test_los_cortes_se_ordenan_por_fecha_no_por_alta(app_ctx, arbol_esftt, usuario_id):
    """El técnico puede subir el reformado antiguo después: manda la fecha."""
    from app.services.reformados import declarar_reformado, ultimo_reformado

    sol = arbol_esftt.solicitud_nueva()
    reciente = _proyecto(arbol_esftt, sol.expediente_id, 'reciente', dias_atras=0)
    antiguo = _proyecto(arbol_esftt, sol.expediente_id, 'antiguo', dias_atras=60)

    declarar_reformado(reciente, 'VOLUNTARIO', usuario_id=usuario_id)
    declarar_reformado(antiguo, 'VOLUNTARIO', usuario_id=usuario_id)

    assert _orden_de(sol.expediente_id, antiguo, reciente) == [antiguo.id, reciente.id]
    # Con fecha de hoy y el id más alto del expediente, el reciente es el último
    # aunque el expediente arrastre cortes previos.
    assert ultimo_reformado(sol.expediente_id).documento_id == reciente.id


def test_misma_fecha_desempata_el_id(app_ctx, arbol_esftt, usuario_id):
    from app.services.reformados import declarar_reformado

    sol = arbol_esftt.solicitud_nueva()
    primero = _proyecto(arbol_esftt, sol.expediente_id, 'mismo-dia-1', dias_atras=10)
    segundo = _proyecto(arbol_esftt, sol.expediente_id, 'mismo-dia-2', dias_atras=10)

    declarar_reformado(segundo, 'VOLUNTARIO', usuario_id=usuario_id)
    declarar_reformado(primero, 'VOLUNTARIO', usuario_id=usuario_id)

    assert _orden_de(sol.expediente_id, primero, segundo) == [primero.id, segundo.id]


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

    # El expediente recién fabricado sí está limpio: ahí la lista es exacta.
    assert [r.documento_id for r in reformados_de(otro.expediente_id)] == [doc_otro.id]
    assert doc_otro.id not in _orden_de(uno.expediente_id, doc_uno, doc_otro)


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


# ---------------------------------------------------------------------------
# D) La fecha administrativa, obligatoria para DOC_PROYECTO
# ---------------------------------------------------------------------------

def test_un_doc_proyecto_sin_fecha_no_llega_a_la_bd(app_ctx, arbol_esftt):
    """El listener corre en el flush, así que cubre las cuatro puertas del pool,
    los scripts y el shell — igual que el validador de fecha futura (#824)."""
    from app import db

    sol = arbol_esftt.solicitud_nueva()
    with pytest.raises(ValueError, match='fecha administrativa'):
        arbol_esftt.documento(sol.expediente_id, CODIGO_PROYECTO, '885-listener')
    db.session.rollback()


def test_reclasificar_a_proyecto_exige_la_fecha(app_ctx, arbol_esftt):
    """La puerta lateral: un documento ya en el pool que cambia de tipo."""
    from app import db
    from app.models.tipos_documentos import TipoDocumento

    sol = arbol_esftt.solicitud_nueva()
    doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', '885-reclasifica')
    assert doc.fecha_administrativa is None

    tipo_proyecto = TipoDocumento.query.filter_by(codigo=CODIGO_PROYECTO).first()
    assert tipo_proyecto is not None, 'la semilla debe traer el TipoDocumento DOC_PROYECTO'
    doc.tipo_doc_id = tipo_proyecto.id

    with pytest.raises(ValueError, match='fecha administrativa'):
        db.session.flush()
    db.session.rollback()


def test_la_ingesta_rechaza_el_proyecto_sin_fecha_antes_de_escribir(app_ctx, arbol_aislado):
    """La puerta que escribe pregunta antes de tocar el disco.

    El listener es la red final, pero salta en el flush —cuando el fichero ya está
    en el pool— y el rollback devuelve la fila sin borrar el fichero (es lo que
    documenta `ResultadoIngesta`). Sin la comprobación temprana, un proyecto sin
    fecha dejaba un huérfano en el pool.
    """
    import os

    from app.models.tipos_documentos import TipoDocumento
    from app.services.ingesta_pool import ingestar_en_pool
    from app.services.rutas_esftt import ruta_pool_documento

    expediente = arbol_aislado.solicitud_propia().expediente
    tipo = TipoDocumento.query.filter_by(codigo=CODIGO_PROYECTO).first()
    assert tipo is not None, 'la semilla debe traer el TipoDocumento DOC_PROYECTO'

    with pytest.raises(ValueError, match='fecha administrativa'):
        ingestar_en_pool(expediente, b'contenido', 'proyecto-885.pdf',
                         tipo_doc_id=tipo.id, fecha_administrativa=None)

    directorio = ruta_pool_documento(expediente)
    presentes = os.listdir(directorio) if os.path.isdir(directorio) else []
    assert not any('proyecto-885' in nombre for nombre in presentes), \
        'no debe quedar fichero huérfano en el pool'


def test_los_demas_tipos_siguen_admitiendo_fecha_vacia(app_ctx, arbol_esftt):
    """La columna sigue siendo nullable (#191): la exigencia es del tipo, no de todos."""
    sol = arbol_esftt.solicitud_nueva()
    doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', '885-sin-fecha-ok')

    assert doc.fecha_administrativa is None
    assert doc.id is not None


# ---------------------------------------------------------------------------
# E) Las puertas del pool: alta por ruta y sincronización al editar
# ---------------------------------------------------------------------------

@pytest.fixture
def puerta(app, usuario_admin, expediente_seed):
    """Cliente autenticado + helpers contra la puerta de URL externa del pool.

    Se usa esa puerta y no la multipart porque no toca el disco: lo que se prueba
    aquí es el contrato del payload —la marca y su origen—, que es el mismo en las
    tres puertas de alta.
    """
    from app import db
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    from app.services.reloj_simulado import hoy

    creados = []

    class Puerta:
        client = usuario_admin
        expediente_id = expediente_seed

        def tipo_id(self, codigo):
            with app.app_context():
                tipo = TipoDocumento.query.filter_by(codigo=codigo).first()
                assert tipo is not None, f'la semilla debe traer el TipoDocumento {codigo}'
                return tipo.id

        def alta(self, **payload):
            datos = {
                'url': f'https://example.org/885/{len(creados)}',
                'fecha_administrativa': (hoy() - timedelta(days=20)).isoformat(),
            }
            datos.update(payload)
            respuesta = self.client.post(
                f'/expedientes/{self.expediente_id}/documentos/url-externa', json=datos)
            assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
            with app.app_context():
                doc = (Documento.query.filter_by(url=datos['url'])
                       .order_by(Documento.id.desc()).first())
            assert doc is not None, 'el alta debe haber creado el documento'
            creados.append(doc.id)
            return doc.id

        def editar(self, doc_id, **payload):
            return self.client.post(
                f'/expedientes/{self.expediente_id}/documentos/{doc_id}/editar',
                json=payload)

        def corte(self, doc_id):
            from app.models.reformados_proyecto import ReformadoProyecto
            with app.app_context():
                return ReformadoProyecto.query.filter_by(documento_id=doc_id).first()

    yield Puerta()

    # Estos tests no corren bajo `app_ctx`: escriben de verdad y hay que recoger.
    with app.app_context():
        for doc_id in creados:
            doc = db.session.get(Documento, doc_id)
            if doc is not None:
                db.session.delete(doc)
        db.session.commit()


def test_la_puerta_declara_el_corte_si_viene_marcado(puerta):
    doc_id = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO),
                         abre_reformado=True, origen_reformado='REQUERIDO')

    corte = puerta.corte(doc_id)
    assert corte is not None
    assert corte.origen == 'REQUERIDO'


def test_la_puerta_ignora_la_marca_si_el_tipo_no_es_proyecto(puerta):
    """El control solo existe mientras el tipo elegido es DOC_PROYECTO: una marca
    sobre otro tipo no es la declaración de nadie."""
    doc_id = puerta.alta(tipo_doc_id=puerta.tipo_id('MODELO_SOLICITUD'),
                         abre_reformado=True)

    assert puerta.corte(doc_id) is None


def test_desmarcar_al_editar_retira_el_corte(puerta):
    doc_id = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO), abre_reformado=True)
    assert puerta.corte(doc_id) is not None

    respuesta = puerta.editar(doc_id, abre_reformado=False)

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert puerta.corte(doc_id) is None


def test_editar_sin_hablar_del_corte_no_lo_toca(puerta):
    """Clave ausente conserva: guardar el asunto no borra el reformado."""
    doc_id = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO), abre_reformado=True)

    respuesta = puerta.editar(doc_id, asunto='Reformado de la línea aérea')

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert puerta.corte(doc_id) is not None


def test_cambiar_el_tipo_retira_el_corte(puerta):
    """Dejar de ser proyecto es desmarcar por la puerta de atrás."""
    doc_id = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO), abre_reformado=True)

    respuesta = puerta.editar(doc_id, tipo_doc_id=puerta.tipo_id('MODELO_SOLICITUD'))

    assert respuesta.status_code == 200, respuesta.get_data(as_text=True)
    assert puerta.corte(doc_id) is None


def test_solo_se_revierte_el_ultimo_corte(puerta):
    """Quitar uno intermedio fundiría dos tramos: la puerta lo rechaza."""
    primero = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO), abre_reformado=True)
    segundo = puerta.alta(tipo_doc_id=puerta.tipo_id(CODIGO_PROYECTO), abre_reformado=True)

    respuesta = puerta.editar(primero, abre_reformado=False)

    assert respuesta.status_code == 500
    assert 'último reformado' in respuesta.get_json()['error']
    assert puerta.corte(primero) is not None
    assert puerta.corte(segundo) is not None
