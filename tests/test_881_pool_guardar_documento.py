"""
Tests #881 — el formulario de edición del inspector del pool: `POST .../documentos/<id>/guardar`
y las rutas de fragmento que lo acompañan (ADR-023, ADR-053 §E).

Fallo silencioso que evita: que pulsar «Guardar» en el inspector de un documento del pool, sin
haber tocado nada, cambie datos sin que nadie lo vea (el ancla del proyecto o el corte de un
reformado retirados, el documento sin su marca de prioritario); que lo que el usuario desmarca
no se desmarque y la pantalla diga «guardado»; o que una URL con el id de otro expediente
muestre o edite un documento que no es de ese expediente.

El núcleo de la edición (`_aplicar_edicion_documento`) ya lo cubren `test_885` (el corte), `test_824`
(la fecha futura) y `test_928` (el 422) por la ruta JSON. Lo que no cubría nadie es lo que esa ruta
no tiene: la traducción del formulario HTML a ese núcleo (`_datos_del_formulario_documento`, con
su centinela y sus marcadores) y el alcance por expediente de las tres rutas nuevas.

El «sin tocar nada» no se escribe a mano: se lee del fragmento real lo que enviaría un navegador
(los controles con su valor de partida, sin los deshabilitados ni las casillas desmarcadas) y se
envía a la `data-action` del propio formulario. Así el test se rompe si el fragmento y la ruta
dejan de entenderse, que es lo que no se ve desde ninguno de los dos lados.

BD de tests con rollback por SAVEPOINT (`arbol_aislado`, que trae `almacen_tmp`).
"""
import pytest
from lxml import html as lxml_html

from app import db
from app.models.documentos import Documento
from app.models.reformados_proyecto import ReformadoProyecto
from app.services.reloj_simulado import hoy


def _expediente_con_proyecto_anclado(arbol):
    """Un expediente propio con su proyecto identificado (el estado normal de uno en tramitación)."""
    expediente_id = arbol.solicitud_propia().expediente_id
    ancla = arbol.anclar_proyecto(expediente_id)
    return expediente_id, ancla


def _envio_del_navegador(fragmento):
    """`(action, datos)` de lo que mandaría el navegador al pulsar «Guardar» con el fragmento tal
    como llega: cada control con su valor de partida, menos los deshabilitados (por sí mismos o por
    un `<fieldset disabled>`) y las casillas desmarcadas, que no viajan."""
    raiz = lxml_html.fragment_fromstring(fragmento, create_parent='div')
    formularios = raiz.xpath('.//form[@data-inspector-form]')
    assert len(formularios) == 1, 'el fragmento de edición lleva un único formulario del inspector'
    form = formularios[0]
    datos = {}
    for control in form.xpath('.//input | .//select | .//textarea'):
        nombre = control.get('name')
        if (not nombre or control.get('disabled') is not None
                or control.xpath('ancestor::fieldset[@disabled]')):
            continue
        if control.tag == 'select':
            elegida = control.xpath('.//option[@selected]') or control.xpath('.//option[1]')
            datos[nombre] = elegida[0].get('value')
        elif control.tag == 'textarea':
            datos[nombre] = control.text or ''
        elif control.get('type') == 'checkbox':
            if control.get('checked') is not None:
                datos[nombre] = control.get('value', 'on')
        else:
            datos[nombre] = control.get('value', '')
    return form.get('data-action'), datos


def _estado(doc_id):
    """Lo que hay en la BD, no lo que tiene el objeto en memoria."""
    db.session.expire_all()
    doc = db.session.get(Documento, doc_id)
    corte = ReformadoProyecto.query.filter_by(documento_id=doc_id).first()
    return {
        'tipo_doc_id': doc.tipo_doc_id,
        'fecha_administrativa': doc.fecha_administrativa,
        'asunto': doc.asunto,
        'observaciones': doc.observaciones,
        'prioridad': doc.prioridad,
        'anclado': bool(doc.anclado_como_proyecto_principal),
        'origen_del_corte': corte.origen if corte is not None else None,
    }


def _con_texto(doc, **campos):
    """Rellena los campos de texto y la prioridad, para que 'conservar' se vea."""
    for campo, valor in campos.items():
        setattr(doc, campo, valor)
    db.session.flush()
    return doc


# ---------------------------------------------------------------------------
# Guardar sin tocar nada no cambia nada
# ---------------------------------------------------------------------------

def _caso_ordinario(arbol):
    """Un documento sin controles de proyecto, prioritario y con todos los textos rellenos."""
    expediente_id, _ = _expediente_con_proyecto_anclado(arbol)
    doc = arbol.documento(expediente_id, 'MODELO_SOLICITUD', 'ordinario', fecha=hoy())
    return expediente_id, _con_texto(doc, asunto='Asunto de partida', observaciones='Notas de partida',
                                     prioridad=1)


def _caso_proyecto_anclado(arbol):
    """El proyecto principal: el control del ancla existe y viene marcado."""
    expediente_id, ancla = _expediente_con_proyecto_anclado(arbol)
    return expediente_id, _con_texto(ancla, asunto='El proyecto', prioridad=1)


def _caso_ultimo_reformado(arbol):
    """El último reformado: el control del corte existe, viene marcado y se puede tocar."""
    expediente_id, _ = _expediente_con_proyecto_anclado(arbol)
    corte = arbol.reformado(expediente_id, origen='REQUERIDO')
    return expediente_id, _con_texto(db.session.get(Documento, corte.documento_id), asunto='Reformado')


def _caso_reformado_con_versiones_posteriores(arbol):
    """Un reformado que ya no es el último (ADR-044 §C): se enseña pero no se toca, y el formulario
    no puede declarar nada sobre él."""
    expediente_id, _ = _expediente_con_proyecto_anclado(arbol)
    primero = arbol.reformado(expediente_id, origen='VOLUNTARIO', sufijo='reformado-1')
    arbol.reformado(expediente_id, origen='REQUERIDO', sufijo='reformado-2')
    return expediente_id, _con_texto(db.session.get(Documento, primero.documento_id), asunto='Intermedio')


@pytest.mark.parametrize('caso', [
    _caso_ordinario,
    _caso_proyecto_anclado,
    _caso_ultimo_reformado,
    _caso_reformado_con_versiones_posteriores,
], ids=['ordinario', 'proyecto_anclado', 'ultimo_reformado', 'reformado_con_versiones_posteriores'])
def test_guardar_sin_tocar_nada_no_cambia_nada(arbol_aislado, usuario_supervisor, caso):
    expediente_id, doc = caso(arbol_aislado)
    doc_id = doc.id
    antes = _estado(doc_id)

    r = usuario_supervisor.get(f'/expedientes/{expediente_id}/documentos/{doc_id}/editar-fragmento')
    assert r.status_code == 200
    action, datos = _envio_del_navegador(r.get_data(as_text=True))
    r = usuario_supervisor.post(action, data=datos)

    assert r.status_code == 200, r.get_json()
    assert _estado(doc_id) == antes, f'guardar sin tocar nada cambió el documento; el formulario envió {datos}'


# ---------------------------------------------------------------------------
# Lo que el formulario declara se aplica; lo que no menciona se conserva (#832)
# ---------------------------------------------------------------------------

def _guardar(cliente, expediente_id, doc_id, datos):
    return cliente.post(f'/expedientes/{expediente_id}/documentos/{doc_id}/guardar', data=datos)


def test_una_casilla_desmarcada_solo_cuenta_si_el_formulario_es_completo(arbol_aislado, usuario_supervisor):
    """Con el centinela, la ausencia de «Prioritario» es «desmarcada»; sin él, es «no lo menciona»."""
    expediente_id, doc = _caso_ordinario(arbol_aislado)
    doc_id = doc.id

    r = _guardar(usuario_supervisor, expediente_id, doc_id, {'asunto': 'Solo el asunto'})
    assert r.status_code == 200, r.get_json()
    assert _estado(doc_id)['prioridad'] == 1, 'un cuerpo sin centinela desmarcó el prioritario (#832)'

    r = _guardar(usuario_supervisor, expediente_id, doc_id, {'_form_completo': '1', 'asunto': 'Solo el asunto'})
    assert r.status_code == 200, r.get_json()
    assert _estado(doc_id)['prioridad'] == 0, 'desmarcar «Prioritario» en el formulario no se guardó'


def test_lo_ausente_se_conserva_y_lo_vacio_se_vacia(arbol_aislado, usuario_supervisor):
    expediente_id, doc = _caso_ordinario(arbol_aislado)
    doc_id = doc.id

    r = _guardar(usuario_supervisor, expediente_id, doc_id, {'observaciones': ''})

    assert r.status_code == 200, r.get_json()
    estado = _estado(doc_id)
    assert estado['observaciones'] is None, 'un campo presente y vacío no se vació'
    assert estado['asunto'] == 'Asunto de partida', 'un campo ausente se borró (#832)'


def test_desmarcar_el_ancla_con_su_marcador_la_retira_y_sin_el_no(arbol_aislado, usuario_supervisor):
    """El marcador `principal_activo` es lo que dice «el control existía y esta es la respuesta»:
    sin él, que la casilla no viaje no significa nada."""
    expediente_id, doc = _caso_proyecto_anclado(arbol_aislado)
    doc_id = doc.id

    r = _guardar(usuario_supervisor, expediente_id, doc_id, {'asunto': 'Sin marcador'})
    assert r.status_code == 200, r.get_json()
    assert _estado(doc_id)['anclado'], 'un cuerpo sin el marcador retiró el ancla del proyecto'

    r = _guardar(usuario_supervisor, expediente_id, doc_id, {'principal_activo': '1'})
    assert r.status_code == 200, r.get_json()
    assert not _estado(doc_id)['anclado'], 'desmarcar el ancla en el formulario no la retiró'


# ---------------------------------------------------------------------------
# Un documento solo se alcanza por su expediente
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('metodo, ruta', [
    ('get', 'fragmento'),
    ('get', 'editar-fragmento'),
    ('post', 'guardar'),
], ids=['fragmento', 'editar-fragmento', 'guardar'])
def test_un_documento_no_se_alcanza_por_otro_expediente(arbol_aislado, usuario_supervisor, metodo, ruta):
    """El usuario tiene acceso a los dos expedientes: lo que falla aquí es la pertenencia del
    documento, no el permiso."""
    expediente_a = arbol_aislado.solicitud_propia().expediente_id
    expediente_b, doc = _caso_ordinario(arbol_aislado)
    doc_id = doc.id
    antes = _estado(doc_id)
    assert expediente_a != expediente_b

    url = f'/expedientes/{expediente_a}/documentos/{doc_id}/{ruta}'
    if metodo == 'get':
        r = usuario_supervisor.get(url)
    else:
        r = usuario_supervisor.post(url, data={'_form_completo': '1', 'asunto': 'Desde otro expediente'})

    assert r.status_code == 404
    assert _estado(doc_id) == antes
