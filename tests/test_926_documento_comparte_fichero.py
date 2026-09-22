"""
Tests #926 — dos `Documento` que comparten fichero (duplicado exacto, ADR-032 §4)
no deben dejar al otro sin fichero cuando `mover_a_esftt`/`mover_a_pool`
(`app/services/rutas_esftt.py`, ADR-032 §3) mueven uno de los dos.

Documento real y persistido (a diferencia de test_667 Parte 1, que usa objetos
transitorios): el arreglo comprueba en BD si OTRO `Documento` sigue apuntando al
mismo origen antes de borrarlo, así que hace falta que esa fila exista de verdad.
Mismo patrón que test_667 Parte 2 (app_ctx + fs_tmp, ArbolESFTT, tarea/documento
reales).
"""
import hashlib
import os

import pytest

from app import db
from app.models.documentos import Documento
from app.services.rutas_esftt import mover_a_esftt, mover_a_pool
from tests.conftest import ArbolESFTT
from tests.test_667_mover_documento_esftt import _tarea_real


def _pool_duplicado(expediente, fs_tmp, contenido=b'contenido #926 compartido'):
    """Escribe un fichero en AT-N/pool/ y crea DOS `Documento` reales que
    comparten hash_md5 y url apuntando a él (duplicado exacto, ADR-032 §4,
    tal como los deja de verdad `ingestar_en_pool` — ver test_666)."""
    hash_md5 = hashlib.md5(contenido).hexdigest()
    prefijo = hash_md5[:8]
    nombre = f'{prefijo}_compartido.pdf'
    pool_dir = fs_tmp / f'AT-{expediente.numero_at}' / 'pool'
    pool_dir.mkdir(parents=True, exist_ok=True)
    (pool_dir / nombre).write_bytes(contenido)
    url = f'AT-{expediente.numero_at}/pool/{nombre}'

    doc_1 = Documento(expediente_id=expediente.id, url=url, hash_md5=hash_md5,
                       asunto='#926 test — duplicado 1')
    doc_2 = Documento(expediente_id=expediente.id, url=url, hash_md5=hash_md5,
                       asunto='#926 test — duplicado 2')
    db.session.add_all([doc_1, doc_2])
    db.session.flush()
    return doc_1, doc_2


def _tarea_hermana(tarea, codigo_tarea='ANALIZAR', codigo_fase='ANALISIS_SOLICITUD',
                    codigo_tramite='ANALISIS_DOCUMENTAL'):
    """Segunda tarea en la MISMA solicitud que `tarea` (mismo expediente, para
    poder vincular el mismo Documento a las dos)."""
    builder = ArbolESFTT(db)
    solicitud = tarea.tramite.fase.solicitud
    fase = builder.fase(codigo_fase, solicitud=solicitud)
    tramite = builder.tramite(fase, codigo_tramite)
    return builder.tarea(tramite, codigo_tarea)


class TestMoverAEsfttDocumentoCompartido:

    def test_vincular_ambos_a_la_misma_tarea_no_pierde_el_fichero(self, app_ctx, fs_tmp):
        tarea = _tarea_real()
        expediente = tarea.tramite.fase.solicitud.expediente
        doc_1, doc_2 = _pool_duplicado(expediente, fs_tmp)

        assert mover_a_esftt(doc_1, tarea) is True
        assert (fs_tmp / doc_1.url).exists()

        # Antes del arreglo: doc_1 se lleva por delante el origen del pool y esto
        # revienta con FileNotFoundError (#926) porque doc_2 sigue apuntando ahí.
        assert mover_a_esftt(doc_2, tarea) is True
        assert (fs_tmp / doc_2.url).exists()
        assert (fs_tmp / doc_1.url).exists()

    def test_vincular_a_tareas_distintas_borra_el_origen_solo_cuando_sale_el_segundo(
        self, app_ctx, fs_tmp,
    ):
        tarea_1 = _tarea_real()
        tarea_2 = _tarea_hermana(tarea_1)
        expediente = tarea_1.tramite.fase.solicitud.expediente
        doc_1, doc_2 = _pool_duplicado(expediente, fs_tmp)
        origen_abs = fs_tmp / doc_1.url

        assert mover_a_esftt(doc_1, tarea_1) is True
        assert origen_abs.exists()  # doc_2 todavía lo necesita

        assert mover_a_esftt(doc_2, tarea_2) is True
        assert not origen_abs.exists()  # ya no queda nadie que lo necesite

        assert (fs_tmp / doc_1.url).exists()
        assert (fs_tmp / doc_2.url).exists()
        assert doc_1.url != doc_2.url  # tareas distintas -> carpetas ESFTT distintas


class TestMoverAPoolDocumentoCompartido:

    @pytest.mark.parametrize('orden', [(0, 1), (1, 0)])
    def test_desvincular_en_cualquier_orden_no_deja_sin_fichero(self, app_ctx, fs_tmp, orden):
        tarea = _tarea_real()
        expediente = tarea.tramite.fase.solicitud.expediente
        docs = _pool_duplicado(expediente, fs_tmp)
        for doc in docs:
            assert mover_a_esftt(doc, tarea) is True
        assert docs[0].url == docs[1].url  # comparten fichero también en ESFTT

        primero, segundo = docs[orden[0]], docs[orden[1]]

        assert mover_a_pool(primero, expediente) is True
        assert (fs_tmp / segundo.url).exists()  # el otro sigue teniendo su fichero

        assert mover_a_pool(segundo, expediente) is True
        assert (fs_tmp / primero.url).exists()
        assert (fs_tmp / segundo.url).exists()
