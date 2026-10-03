"""Librería del almacén (ADR-050 §B, #1007 PR 1): lo que decide al escribir y su independencia.

Fallo silencioso que evita: que el almacén guarde un contenido distinto del que
se le pidió guardar (truncado, en el disco equivocado o dañado sin reparación
posible) devolviendo una ref que parece buena, o que deje de poder usarse sin
BDDAT para reconstruir los expedientes.

Sin BD ni app: la librería no sabe nada de BDDAT, y sus tests tampoco.
"""
import ast
import hashlib
import io
import os
import sys
import threading
from pathlib import Path

import pytest

import almacen
from almacen import AlmacenDisco, Comprobacion, ComprobacionFallida, NoDisponible

RAIZ_REPO = Path(__file__).resolve().parent.parent
CONTENIDO = b'%PDF-1.4 contenido de prueba del almacen'
REF = hashlib.sha256(CONTENIDO).hexdigest()


@pytest.fixture
def almacen_disco(tmp_path):
    almacen.inicializar(str(tmp_path))
    return AlmacenDisco(str(tmp_path))


def _ficheros_bajo(ruta):
    return sorted(p.name for p in Path(ruta).rglob('*') if p.is_file())


def test_escribir_rechaza_contenido_que_no_coincide_con_su_comprobacion(almacen_disco, tmp_path):
    """Fallo silencioso que evita: un envío cortado a mitad deja en el almacén un
    contenido truncado con una ref que parece buena."""
    truncado = io.BytesIO(CONTENIDO[:10])

    with pytest.raises(ComprobacionFallida):
        almacen_disco.escribir(truncado, Comprobacion('sha256', REF))

    assert _ficheros_bajo(tmp_path / 'sha256') == []
    assert _ficheros_bajo(tmp_path / '.tmp') == []


def test_sin_marca_responde_no_disponible_y_no_crea_nada(tmp_path):
    """Fallo silencioso que evita: con la carpeta de red sin montar, el almacén
    escribe en el disco local que queda debajo (fuera de la copia de seguridad),
    o se toma por vacío y un contenido sano pasa por ausente."""
    sin_montar = AlmacenDisco(str(tmp_path))

    with pytest.raises(NoDisponible):
        sin_montar.existe(REF)
    with pytest.raises(NoDisponible):
        sin_montar.escribir(io.BytesIO(CONTENIDO))

    assert list(tmp_path.iterdir()) == []


def test_volver_a_escribir_repara_un_contenido_danado(almacen_disco):
    """Fallo silencioso que evita: subir otra vez el original no repara un
    contenido dañado (ADR-050 §G), porque se reutiliza el fichero que ya estaba."""
    almacen_disco.escribir(io.BytesIO(CONTENIDO))
    ruta = Path(almacen_disco.raiz) / 'sha256' / REF[:2] / REF[2:4] / REF
    ruta.write_bytes(b'bytes estropeados')

    assert almacen_disco.escribir(io.BytesIO(CONTENIDO)) == REF
    with almacen_disco.leer(REF) as f:
        assert f.read() == CONTENIDO


def test_dos_escrituras_simultaneas_del_mismo_contenido_terminan_las_dos_bien(almacen_disco):
    """Fallo silencioso que evita: en Windows, dos subidas del mismo contenido a la vez
    hacían fallar a una con «almacén no disponible» (acceso denegado al renombrar sobre el
    fichero que la otra estaba colocando), un falso aviso de almacén caído.

    Varias rondas con una barrera: sin el reintento del renombrado, falla casi siempre."""
    for ronda in range(30):
        contenido = CONTENIDO + str(ronda).encode()
        barrera = threading.Barrier(2, timeout=10)
        refs, errores = [], []

        def escribe():
            barrera.wait()
            try:
                refs.append(almacen_disco.escribir(io.BytesIO(contenido)))
            except BaseException as exc:
                errores.append(exc)

        hilos = [threading.Thread(target=escribe) for _ in range(2)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        assert not errores, f'ronda {ronda}: {errores}'
        assert refs == [hashlib.sha256(contenido).hexdigest()] * 2


def _imports(fichero):
    for nodo in ast.walk(ast.parse(fichero.read_text(encoding='utf-8'))):
        if isinstance(nodo, ast.Import):
            yield from (a.name.split('.')[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            yield nodo.module.split('.')[0]


@pytest.mark.parametrize('paquete, ademas', [
    ('almacen', set()),
    # El exportador lee el almacén con su librería (ADR-050 §H), que a su vez solo usa
    # la biblioteca estándar: la reconstrucción sigue sin necesitar nada de BDDAT.
    ('exportador', {'almacen', 'exportador'}),
])
def test_solo_importa_la_biblioteca_estandar(paquete, ademas):
    """Fallo silencioso que evita: la reconstrucción de los expedientes sin BDDAT
    deja de funcionar, y solo se descubre el día que hace falta; o el contrato del
    almacén se acopla a BDDAT sin que se vea."""
    ajenos = {
        f'{fichero.relative_to(RAIZ_REPO).as_posix()}: {modulo}'
        for fichero in (RAIZ_REPO / paquete).rglob('*.py')
        for modulo in _imports(fichero)
        if modulo not in sys.stdlib_module_names and modulo != '__future__' and modulo not in ademas
    }
    assert not ajenos, f'Imports fuera de la biblioteca estándar: {sorted(ajenos)}'
