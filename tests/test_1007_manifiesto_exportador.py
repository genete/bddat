"""#1007 PR 2 (ADR-050 §H, N009) — manifiesto y exportador: reconstruir las carpetas sin BDDAT.

Fallo silencioso que evita: N009 roto sin que nada lo use hasta la fase 2b. El manifiesto
y el exportador solo se usan de verdad el día que se pierde la BD; si dejan de reconstruir
bien (un documento fuera de su carpeta, un fichero dañado entregado como bueno, los
manifiestos escritos donde nadie los busca), nada lo nota hasta entonces.

El vínculo con la tarea se crea como fila de `documentos_tarea`, que es lo que es vincular
(ADR-050 §C): lo que se prueba es el manifiesto y el exportador, no la vía de vincular.
"""
import hashlib
import io

import pytest

import almacen
import exportador
from app import db
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services.almacenamiento.contenido import EntradaSubida, subir
from app.services.almacenamiento.manifiestos import (
    MARCA, ManifiestosNoDisponibles, escribir,
)
from app.services.reloj_simulado import hoy
from app.services.rutas_esftt import ruta_esftt_documento

INFORME = b'%PDF-1.4 informe tecnico de la prueba de punta a punta'
PLANO = b'%PDF-1.4 plano suelto, sin tarea'


def test_subir_vincular_rehacer_y_exportar_deja_los_mismos_bytes_en_su_carpeta(
        arbol_aislado, almacen_tmp, tmp_path):
    """Fallo silencioso que evita: la reconstrucción sin BDDAT deja un documento fuera de
    su carpeta ESFTT, con otros bytes, o no encuentra el manifiesto, y solo se descubre el
    día que hace falta."""
    tarea = arbol_aislado.tarea_propia('ANALIZAR')
    expediente = tarea.tramite.fase.solicitud.expediente
    tipo = TipoDocumento.query.filter_by(codigo='DOC_PROYECTO').first()
    assert tipo is not None, "la semilla debe traer el TipoDocumento 'DOC_PROYECTO'"
    datos = {'expediente_id': expediente.id, 'tipo_doc_id': tipo.id, 'fecha_administrativa': hoy()}

    vinculado, suelto = subir([
        EntradaSubida(io.BytesIO(INFORME), 'Informe técnico.pdf', datos),
        EntradaSubida(io.BytesIO(PLANO), 'plano.pdf', datos),
    ])
    enlace = Documento(**datos, url='https://sede.example/anuncio.pdf')
    db.session.add_all([vinculado, suelto, enlace])
    db.session.flush()
    arbol_aislado.vincular(tarea, vinculado, 'CONSUMIDO')

    escribir(expediente)
    n = expediente.numero_at
    manifiesto = exportador.cargar(str(almacen_tmp.manifiestos / f'{n // 1000:03d}' / f'AT-{n}.json'))
    destino = tmp_path / 'destino'
    informe = exportador.exportar(manifiesto, str(destino), almacen.AlmacenDisco(str(almacen_tmp.almacen)))

    assert (destino / ruta_esftt_documento(tarea) / 'Informe técnico.pdf').read_bytes() == INFORME
    assert (destino / f'AT-{n}' / 'pool' / 'plano.pdf').read_bytes() == PLANO
    assert exportador.Linea(enlace.id, 'https://sede.example/anuncio.pdf') in informe.enlaces


def test_un_contenido_danado_no_sale_con_su_nombre_y_figura_en_el_informe(tmp_path):
    """Fallo silencioso que evita: una reconstrucción entrega un fichero corrupto como si
    fuera el bueno.

    Sin BD: el exportador no la necesita, y su test tampoco."""
    raiz = tmp_path / 'almacen'
    almacen.inicializar(str(raiz))
    disco = almacen.AlmacenDisco(str(raiz))
    contenido = b'%PDF-1.4 resolucion'
    ref = disco.escribir(io.BytesIO(contenido))
    (raiz / 'sha256' / ref[:2] / ref[2:4] / ref).write_bytes(b'bytes estropeados')
    manifiesto = {'formato': exportador.FORMATO, 'expediente': 'AT-1', 'documentos': [{
        'id': 7, 'nombre': 'resolucion.pdf', 'carpeta': 'AT-1/pool', 'ref': ref,
        'contenido_sha256': hashlib.sha256(contenido).hexdigest(), 'url': None,
    }]}

    informe = exportador.exportar(manifiesto, str(tmp_path / 'destino'), disco)

    assert [p for p in (tmp_path / 'destino').rglob('*') if p.is_file()] == []
    assert [linea.id for linea in informe.incidencias] == [7]


def test_sin_marca_no_se_escribe_ningun_manifiesto(alta_propia, almacen_tmp):
    """Fallo silencioso que evita: con el share sin montar, los manifiestos se escriben en
    el disco local que queda debajo, fuera de la copia de seguridad, y los del share
    envejecen sin que nadie lo note."""
    (almacen_tmp.manifiestos / MARCA).unlink()

    with pytest.raises(ManifiestosNoDisponibles):
        escribir(alta_propia.expediente)

    assert list(almacen_tmp.manifiestos.iterdir()) == []
