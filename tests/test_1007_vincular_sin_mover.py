"""#1007 (ADR-050 §C, §G) — vincular un documento es solo una fila, y exige que su contenido esté.

Fallo silencioso que evita: se vincula a una tarea un documento cuyo contenido no está en el
almacén (ausente o dañado) y sostiene un acto —un justificante, un diagnóstico— sin que nada lo
detecte hasta que alguien intenta abrirlo.

Cada camino que añade un vínculo tiene que comprobarlo: `editar_tarea` (la Despensa, y los
hooks de notificar y de #717) y `sincronizar_consumido_documental` (casar un requisito). El
documento es un fichero real del almacén temporal al que se le quita el contenido.
"""
import io

import pytest
from unittest.mock import patch

from app import db
from app.services import mutaciones_arbol as svc
from app.services.almacenamiento.contenido import (
    ContenidoNoUtilizable, EntradaSubida, subir,
)


def _documento_sin_contenido(almacen_tmp, expediente_id):
    """Un documento subido de verdad, al que luego se le quita el contenido del almacén."""
    import hashlib

    contenido = b'%PDF-1.4 contenido que va a faltar #1007'
    doc = subir([EntradaSubida(io.BytesIO(contenido), 'perdido.pdf',
                               {'expediente_id': expediente_id, 'tipo_doc_id': 1})])[0]
    db.session.add(doc)
    db.session.flush()
    ref = hashlib.sha256(contenido).hexdigest()      # con esta librería la ref es el SHA-256
    (almacen_tmp.almacen / 'sha256' / ref[:2] / ref[2:4] / ref).unlink()
    return doc


def test_editar_tarea_no_vincula_un_contenido_ausente(app_ctx, fs_tmp, almacen_tmp):
    from tests.conftest import ArbolESFTT

    tarea = ArbolESFTT(db).tarea_propia('ANALIZAR')
    doc = _documento_sin_contenido(almacen_tmp, tarea.tramite.fase.solicitud.expediente_id)

    resultado = svc.editar_tarea(tarea, documentos_consumidos_ids=[doc.id],
                                 documento_producido_id=None, notas=None)

    assert resultado.ok is False
    assert 'no está en el almacén' in resultado.error


def test_sincronizar_consumido_no_vincula_un_contenido_ausente(app_ctx, fs_tmp, almacen_tmp):
    from tests.conftest import ArbolESFTT

    tarea = ArbolESFTT(db).tarea_propia('ANALIZAR')
    doc = _documento_sin_contenido(almacen_tmp, tarea.tramite.fase.solicitud.expediente_id)

    with patch('app.services.mutaciones_arbol.build', return_value=(None, {})), \
         patch('app.services.mutaciones_arbol.evaluar_requisitos',
               return_value={'items': [{'documento': doc}], 'error': False}):
        with pytest.raises(ContenidoNoUtilizable, match='no está en el almacén'):
            svc.sincronizar_consumido_documental(tarea)

    assert not [v for v in tarea.vinculos_documento if v.documento_id == doc.id]
