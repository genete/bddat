"""#1007 (ADR-050 §B, §G) — el módulo de contenido y el adaptador del almacén.

Fallo silencioso que evita: que una subida deje el almacén y `ficheros` sin acuerdo
(copias del mismo contenido, documentos a medias, un contenido dañado dado por bueno), o
que un almacén que no contesta agote los workers de la aplicación sin que salga ningún
error.

Contra la BD de tests y un almacén real en un temporal (`almacen_tmp`): la conexión
aparte con que el módulo escribe `ficheros` escapa al SAVEPOINT de `app_ctx`, y esa
fixture borra las filas al terminar. Los `Documento` que devuelve `subir` no se añaden a
la sesión: aquí solo importa a qué contenido apuntan.
"""
import hashlib
import io
import threading
import time
import zipfile

import pytest
from sqlalchemy import text

from app import db
from app.models.bitacora import Bitacora
from app.models.certificados import Certificado
from app.services.almacenamiento.adaptador import AdaptadorAlmacen, AlmacenNoDisponible
from app.services.almacenamiento.contenido import (
    VIA_REGENERACION, ContenidoNoUtilizable, EntradaSubida, SustitucionBloqueada,
    cambiar_contenido, comprobar_para_vincular, leer, servir_descarga, subir,
    sustituir_con_motivo,
)
from app.services.almacenamiento.formatos import FormatoNoAdmitido


def _pdf(texto):
    return b'%PDF-1.4 ' + texto.encode()


def _odt():
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_STORED) as z:
        z.writestr('mimetype', b'application/vnd.oasis.opendocument.text')
        z.writestr('content.xml', b'<x/>')
    return memoria.getvalue()


def _entrada(contenido, nombre='informe.pdf'):
    # expediente_id y tipo_doc_id no se persisten: el documento no llega a la sesión.
    return EntradaSubida(io.BytesIO(contenido), nombre, {'expediente_id': 1, 'tipo_doc_id': 1})


def _sha(contenido):
    return hashlib.sha256(contenido).hexdigest()


def _filas(contenido):
    with db.engine.connect() as conexion:
        return conexion.execute(
            text('SELECT ref, estado FROM public.ficheros WHERE contenido_sha256 = :h'),
            {'h': _sha(contenido)},
        ).fetchall()


def _estado(contenido):
    filas = _filas(contenido)
    assert len(filas) == 1, f'debería haber una fila en ficheros, hay {len(filas)}'
    return filas[0].estado


def _ruta_en_el_almacen(almacen_tmp, contenido):
    ref = _sha(contenido)      # con esta librería la ref es el SHA-256: se sabe dónde queda
    return almacen_tmp.almacen / 'sha256' / ref[:2] / ref[2:4] / ref


@pytest.fixture
def envios(monkeypatch):
    """Lo que se envía al almacén: el SHA-256 de cada `escribir`."""
    llamadas = []
    original = AdaptadorAlmacen.escribir

    def espia(self, flujo, contenido_sha256):
        llamadas.append(contenido_sha256)
        return original(self, flujo, contenido_sha256)

    monkeypatch.setattr(AdaptadorAlmacen, 'escribir', espia)
    return llamadas


# --- subir ------------------------------------------------------------------------

def test_subir_dos_veces_el_mismo_contenido_reutiliza_la_fila_y_no_reenvia(app_ctx, almacen_tmp, envios):
    """Fallo silencioso que evita: el almacén guarda copias del mismo contenido y el aviso
    de «ya existe» (N077) deja de salir."""
    contenido = _pdf('mismo contenido')

    primero = subir([_entrada(contenido)])[0]
    segundo = subir([_entrada(contenido, 'con otro nombre.pdf')])[0]

    assert primero.fichero_ref == segundo.fichero_ref
    assert len(_filas(contenido)) == 1
    assert envios == [_sha(contenido)], 'la segunda subida no debe enviar nada al almacén'
    assert segundo.nombre_fichero == 'con otro nombre.pdf', 'el nombre es del documento, no del contenido'


def test_dos_subidas_simultaneas_del_mismo_contenido_comparten_la_fila(app, app_ctx, almacen_tmp, monkeypatch):
    """Fallo silencioso que evita: la segunda subida simultánea falla con una clave
    duplicada, o crea una segunda fila para el mismo contenido.

    La barrera sostiene a las dos subidas justo después de comprobar que la fila no existe
    y antes de que ninguna la inserte: el choque ocurre siempre, no por azar."""
    contenido = _pdf('contenido a la vez')
    barrera = threading.Barrier(2, timeout=15)
    original = AdaptadorAlmacen.escribir

    def esperando(self, flujo, contenido_sha256):
        barrera.wait()
        return original(self, flujo, contenido_sha256)

    monkeypatch.setattr(AdaptadorAlmacen, 'escribir', esperando)
    refs, errores = [], []

    def subida():
        try:
            with app.app_context():
                refs.append(subir([_entrada(contenido)])[0].fichero_ref)
        except BaseException as exc:
            errores.append(exc)

    hilos = [threading.Thread(target=subida) for _ in range(2)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=30)

    assert not errores, errores
    assert len(refs) == 2 and len(set(refs)) == 1
    assert len(_filas(contenido)) == 1


def test_una_subida_de_varios_que_falla_en_el_ultimo_no_deja_documentos_y_al_reintentar_no_reenvia(
        app_ctx, almacen_tmp, envios, monkeypatch):
    """Fallo silencioso que evita: documentos a medias en el expediente, o un reintento que
    vuelve a enviar al almacén lo que ya estaba."""
    contenidos = [_pdf('uno'), _pdf('dos'), _pdf('tres')]
    espia = AdaptadorAlmacen.escribir

    def cae_en_el_tercero(self, flujo, contenido_sha256):
        if contenido_sha256 == _sha(contenidos[2]):
            raise AlmacenNoDisponible('simulado')
        return espia(self, flujo, contenido_sha256)

    monkeypatch.setattr(AdaptadorAlmacen, 'escribir', cae_en_el_tercero)
    with pytest.raises(AlmacenNoDisponible):
        subir([_entrada(c, f'{i}.pdf') for i, c in enumerate(contenidos)])

    assert len(_filas(contenidos[0])) == 1 and len(_filas(contenidos[1])) == 1
    assert _filas(contenidos[2]) == []
    assert not [o for o in db.session.new], 'una subida fallida no deja nada pendiente en la sesión'

    monkeypatch.setattr(AdaptadorAlmacen, 'escribir', espia)     # el almacén se recupera
    envios.clear()
    documentos = subir([_entrada(c, f'{i}.pdf') for i, c in enumerate(contenidos)])

    assert envios == [_sha(contenidos[2])], 'al reintentar solo se envía lo que faltaba'
    assert len({d.fichero_ref for d in documentos}) == 3


def test_un_fichero_rechazado_en_una_subida_no_envia_ninguno(app_ctx, almacen_tmp, envios):
    """Fallo silencioso que evita: el primer fichero se envía y se registra antes de rechazar
    el segundo, y queda en el almacén un contenido que nadie referencia."""
    bueno = _pdf('bueno')

    with pytest.raises(FormatoNoAdmitido, match='malo.pdf'):
        subir([_entrada(bueno), _entrada(b'<html><script>alert(1)</script></html>', 'malo.pdf')])

    assert envios == []
    assert _filas(bueno) == []


# --- leer y comprobar ----------------------------------------------------------------

def test_un_contenido_danado_no_se_usa_y_volver_a_subir_el_original_lo_repara(app_ctx, almacen_tmp):
    """Fallo silencioso que evita: un contenido dañado se da por bueno y sostiene un acto, o
    subir otra vez el original no lo repara porque se reutiliza la fila."""
    contenido = _pdf('contenido sano')
    documento = subir([_entrada(contenido)])[0]
    _ruta_en_el_almacen(almacen_tmp, contenido).write_bytes(b'bytes estropeados')

    with pytest.raises(ContenidoNoUtilizable, match='dañado'):
        leer(documento)
    assert _estado(contenido) == 'CORRUPTO'
    with pytest.raises(ContenidoNoUtilizable):
        comprobar_para_vincular(documento)

    subir([_entrada(contenido)])

    assert _estado(contenido) == 'OK'
    assert leer(documento).datos == contenido
    comprobar_para_vincular(documento)


def test_un_contenido_ausente_no_se_vincula_ni_se_lee(app_ctx, almacen_tmp):
    """Fallo silencioso que evita: se vincula un documento sin contenido y sostiene un acto."""
    para_vincular, para_leer = _pdf('se vincula'), _pdf('se lee')
    doc_vincular = subir([_entrada(para_vincular)])[0]
    doc_leer = subir([_entrada(para_leer)])[0]
    _ruta_en_el_almacen(almacen_tmp, para_vincular).unlink()
    _ruta_en_el_almacen(almacen_tmp, para_leer).unlink()

    with pytest.raises(ContenidoNoUtilizable, match='no está en el almacén'):
        comprobar_para_vincular(doc_vincular)
    assert _estado(para_vincular) == 'AUSENTE'
    with pytest.raises(ContenidoNoUtilizable, match='no está en el almacén'):
        leer(doc_leer)
    assert _estado(para_leer) == 'AUSENTE'


def test_un_almacen_sin_montar_no_marca_los_contenidos_como_ausentes(app_ctx, almacen_tmp):
    """Fallo silencioso que evita: con el almacén desmontado, todos los contenidos se marcan
    AUSENTE y se dan por perdidos cuando solo faltaba volver a montar la carpeta."""
    contenido = _pdf('el almacen se cae')
    documento = subir([_entrada(contenido)])[0]
    marca = almacen_tmp.almacen / 'ALMACEN.txt'
    oculta = marca.with_name('ALMACEN.oculta')
    marca.rename(oculta)
    try:
        with pytest.raises(AlmacenNoDisponible):
            leer(documento)
        with pytest.raises(AlmacenNoDisponible):
            comprobar_para_vincular(documento)
    finally:
        oculta.rename(marca)

    assert _estado(contenido) == 'OK'
    assert leer(documento).datos == contenido


# --- servir la descarga --------------------------------------------------------------

def test_la_descarga_lleva_las_cabeceras_de_seguridad_y_marca_el_contenido_danado(app, app_ctx, almacen_tmp):
    """Fallo silencioso que evita: un fichero se sirve sin `nosniff` ni `sandbox` y el
    navegador lo interpreta como algo ejecutable; o un contenido dañado se sirve una y otra
    vez sin que nada lo marque."""
    contenido = _pdf('informe de la descarga')
    pdf = subir([_entrada(contenido, 'Informe técnico.pdf')])[0]
    odt = subir([_entrada(_odt(), 'memoria.odt')])[0]

    with app.test_request_context():
        respuesta = servir_descarga(pdf)
        cabeceras = respuesta.headers
        assert cabeceras['X-Content-Type-Options'] == 'nosniff'
        assert cabeceras['Content-Security-Policy'] == 'sandbox'
        assert cabeceras['Content-Type'] == 'application/pdf'
        assert cabeceras['Content-Disposition'].startswith('inline;')
        assert "filename*=UTF-8''Informe%20t%C3%A9cnico.pdf" in cabeceras['Content-Disposition']
        assert respuesta.get_data() == contenido
        assert servir_descarga(odt).headers['Content-Disposition'].startswith('attachment;')

    _ruta_en_el_almacen(almacen_tmp, contenido).write_bytes(b'x' * len(contenido))
    with app.test_request_context():
        servir_descarga(pdf).get_data()
    assert _estado(contenido) == 'CORRUPTO'


# --- cambiar el contenido de un documento y copiarlo ---------------------------------------

def _documento(expediente_id, contenido, nombre='informe.pdf'):
    """Un documento de verdad en la sesión: la bitácora y la copia necesitan su `id`."""
    entrada = EntradaSubida(io.BytesIO(contenido), nombre, {'expediente_id': expediente_id, 'tipo_doc_id': 1})
    documento = subir([entrada])[0]
    db.session.add(documento)
    db.session.flush()
    return documento


def _cambios_en_bitacora(documento):
    return (Bitacora.query
            .filter_by(tabla='documentos', registro_id=documento.id, columna='fichero_ref')
            .order_by(Bitacora.id).all())


def test_cambiar_el_contenido_anota_en_la_bitacora_los_dos_hashes(
        app_ctx, almacen_tmp, expediente_seed, primer_usuario_id):
    """Fallo silencioso que evita: un documento que citan vínculos y certificados cambia de
    contenido y nada deja rastro de cuál era. Vale para todos los llamadores: la bitácora
    la escribe la función, no quien la llama."""
    antes, despues = _pdf('borrador generado'), _pdf('borrador regenerado')
    documento = _documento(expediente_seed, antes)

    cambiado = cambiar_contenido(
        documento, io.BytesIO(despues), via=VIA_REGENERACION, usuario_id=primer_usuario_id)

    assert cambiado is True
    assert leer(documento).datos == despues
    entradas = _cambios_en_bitacora(documento)
    assert len(entradas) == 1
    assert (entradas[0].usuario_id, entradas[0].operacion) == (primer_usuario_id, 'ALTERAR')
    assert entradas[0].detalle == {
        'via': 'REGENERACION', 'sha256_anterior': _sha(antes), 'sha256_nuevo': _sha(despues)}


# --- sustituir con motivo (ADR-050 §F) -------------------------------------------------------

@pytest.mark.parametrize('sello', ['certificado', 'fase_cerrada'])
def test_sustituir_un_documento_sellado_se_rechaza_y_no_cambia_nada(
        app_ctx, arbol_aislado, primer_usuario_id, sello):
    """Fallo silencioso que evita: un documento que cita un certificado, o que cuelga de una
    fase cerrada, cambia de contenido y el sello deja de decir la verdad sin que nada lo avise."""
    solicitud = arbol_aislado.solicitud_propia()
    original = _pdf('el sellado')
    documento = _documento(solicitud.expediente_id, original)
    if sello == 'certificado':
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        certificado = arbol_aislado.documento(solicitud.expediente_id, 'CERT_CUMPLIMIENTO_FASE', 'sust-cert')
        db.session.add(Certificado(documento_id=certificado.id, tipo='CERT_CUMPLIMIENTO_FASE',
                                   fase_id=fase.id, datos={'documento_id': documento.id}))
        salida = 'deshaga el certificado'
    else:
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        tarea = arbol_aislado.tarea(arbol_aislado.tramite(fase, 'ANALISIS_DOCUMENTAL'), 'ELABORAR')
        arbol_aislado.vincular(tarea, documento, 'CONSUMIDO')       # antes de cerrar: cerrada, no se vincula
        cierre = arbol_aislado.documento(solicitud.expediente_id, 'RESOLUCION', 'sust-cierre')
        fase.documento_resultado_id = cierre.id
        salida = 'reabra antes la fase'
    db.session.flush()
    db.session.expire(documento, ['vinculos_tarea'])

    with pytest.raises(SustitucionBloqueada, match=salida):
        sustituir_con_motivo(documento, io.BytesIO(_pdf('el equivocado')), 'nuevo.pdf',
                             'subí el fichero equivocado', usuario_id=primer_usuario_id)

    assert leer(documento).datos == original
    assert documento.nombre_fichero == 'informe.pdf'
    assert _cambios_en_bitacora(documento) == []


def test_sustituir_permitido_deja_hash_y_nombre_anteriores_en_la_bitacora(
        app_ctx, arbol_aislado, primer_usuario_id):
    """Fallo silencioso que evita: una sustitución se hace sin rastro de cuál era el contenido
    y el nombre anteriores (el motivo, el hash y el nombre), y el expediente no puede explicar
    por qué el documento ya no es el que se subió."""
    solicitud = arbol_aislado.solicitud_propia()
    antes, despues = _pdf('el equivocado'), _pdf('el bueno')
    documento = _documento(solicitud.expediente_id, antes, nombre='equivocado.pdf')

    sustituir_con_motivo(documento, io.BytesIO(despues), 'bueno.pdf', '  subí el fichero equivocado ',
                         usuario_id=primer_usuario_id)
    db.session.flush()

    assert leer(documento).datos == despues
    assert documento.nombre_fichero == 'bueno.pdf'
    [entrada] = _cambios_en_bitacora(documento)
    assert (entrada.usuario_id, entrada.operacion) == (primer_usuario_id, 'ALTERAR')
    assert entrada.detalle == {
        'via': 'SUSTITUCION', 'motivo': 'subí el fichero equivocado',
        'sha256_anterior': _sha(antes), 'sha256_nuevo': _sha(despues),
        'nombre_anterior': 'equivocado.pdf', 'nombre_nuevo': 'bueno.pdf'}


# --- el adaptador ----------------------------------------------------------------------

class _AlmacenColgado:
    """Un almacén que no contesta hasta que se le deja."""

    def __init__(self):
        self.liberar = threading.Event()

    def comprobaciones_admitidas(self):
        return frozenset({'sha256'})

    def existe(self, ref):
        self.liberar.wait(timeout=30)
        return True


def test_un_almacen_colgado_hace_fallar_al_momento_y_no_acumula_hilos():
    """Fallo silencioso que evita: con el almacén colgado cada petición deja un hilo
    esperando, y la aplicación se queda sin workers sin que salga ningún error."""
    almacen = _AlmacenColgado()
    adaptador = AdaptadorAlmacen(almacen, tiempo_limite=0.2, simultaneas=1)
    try:
        with pytest.raises(AlmacenNoDisponible):
            adaptador.existe('x')                      # deja de esperar, pero el hilo sigue colgado
        hilos_con_el_colgado = threading.active_count()

        inicio = time.monotonic()
        with pytest.raises(AlmacenNoDisponible):
            adaptador.existe('x')                      # sin plaza: falla al momento
        assert time.monotonic() - inicio < 0.1
        assert threading.active_count() <= hilos_con_el_colgado, 'no debe crear un hilo más'
    finally:
        almacen.liberar.set()

    for _ in range(100):                               # el hilo termina y devuelve su plaza
        try:
            assert adaptador.existe('x') is True
            break
        except AlmacenNoDisponible:
            time.sleep(0.02)
    else:
        pytest.fail('el adaptador no recuperó la plaza al contestar el almacén')
