"""
Tests #367 — servicio sugerencia_documento.py, endpoint HTTP asociado, y
extensión de pool_subir_documento con 'documentos' en la respuesta.

Servicio en aislamiento: arbol_esftt (SAVEPOINT, sin HTTP) para los casos con
catálogo real — mismo patrón que TestCandidatas en
test_smoke_seguimiento_y_huerfanos.py (sugerencia_subida() es el gemelo
inverso de tareas_candidatas()). Los casos de borde (ambigüedad, catálogo
vacío) se mockean: requieren estados de catálogo (dos filas del mismo tipo
exacto para el mismo tipo de tarea) que no existen en la BD real de
desarrollo a propósito — el catálogo real está diseñado sin ambigüedad.

Endpoint HTTP: BD real + limpieza manual en finally (mismo patrón que
TestEndpointsHuerfanoHTTP en test_smoke_seguimiento_y_huerfanos.py) —
combinar app_ctx con cliente HTTP no es seguro en este proyecto.

pool_subir_documento: mismo patrón que TestEndpointSubirDocumento en
test_666_ingesta_multipart.py (FILESYSTEM_BASE a tmp_path, limpieza por
marcador en el asunto).
"""
import io
import json
from unittest.mock import MagicMock, patch

import pytest


def _fila_catalogo_exacta(rol):
    """Primera fila `rol` con tipo_documento_id exacto (no polimórfico), cuyo
    rol hermano (mismo tipo_tramite_id/orden_tarea) no aporta un segundo tipo
    exacto DISTINTO. Necesario porque una tarea recién creada tiene ambos
    roles (ENTRADA y SALIDA) disponibles a la vez — `ejecutada` y
    `documento_producido` se derivan los dos del mismo vínculo PRODUCIDO
    (app/models/tareas.py), así que nunca hay un estado real con solo uno de
    los dos roles cerrado sin el otro. Si el hermano espera un tipo distinto,
    la sugerencia es ambigua a propósito (no se puede adivinar cuál de los
    dos se está subiendo) — mismo comportamiento verificado aparte en
    TestSugerenciaSubidaCasosBorde.test_ambiguo_dos_tipos_exactos_no_sugiere.
    Skip si el catálogo de esta BD no tiene ninguna fila sin esa ambigüedad.
    """
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    rol_hermano = 'SALIDA' if rol == 'ENTRADA' else 'ENTRADA'
    candidatas = TramiteTareaDocumento.query.filter(
        TramiteTareaDocumento.rol == rol,
        TramiteTareaDocumento.tipo_documento_id.isnot(None),
    ).all()
    for fila in candidatas:
        hermana = TramiteTareaDocumento.query.filter_by(
            tipo_tramite_id=fila.tipo_tramite_id, orden_tarea=fila.orden_tarea, rol=rol_hermano,
        ).first()
        if hermana is not None and hermana.tipo_documento_id is not None \
                and hermana.tipo_documento_id != fila.tipo_documento_id:
            continue  # rol hermano exacto y distinto -> ambiguo para tarea recién creada
        slot = TramiteTarea.query.filter_by(
            tipo_tramite_id=fila.tipo_tramite_id, orden=fila.orden_tarea).first()
        if slot is None:
            continue
        tipo_tramite = TipoTramite.query.get(fila.tipo_tramite_id)
        tipo_tarea = TipoTarea.query.get(slot.tipo_tarea_id)
        return tipo_tramite.codigo, tipo_tarea.codigo, fila.tipo_documento_id
    pytest.skip(f'No hay fila {rol!r} sin ambigüedad de rol hermano en tramites_tareas_documentos')


# ── sugerencia_subida() — casos con catálogo real (arbol_esftt) ─────────────

class TestSugerenciaSubidaCatalogoReal:

    def test_coincidencia_exacta_entrada_sugiere_tipo_y_asunto(self, arbol_esftt):
        from app.services.sugerencia_documento import sugerencia_subida
        from app.models.tipos_documentos import TipoDocumento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo_exacta('ENTRADA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)

        resultado = sugerencia_subida(tarea)
        tipo_doc = TipoDocumento.query.get(tipo_doc_id)
        assert resultado['tipo_doc_id'] == tipo_doc_id
        assert resultado['asunto'] == f'{tipo_doc.nombre} - {tramite.tipo_tramite.nombre}'

    def test_coincidencia_exacta_salida_sugiere_tipo_y_asunto(self, arbol_esftt):
        from app.services.sugerencia_documento import sugerencia_subida
        from app.models.tipos_documentos import TipoDocumento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo_exacta('SALIDA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)

        resultado = sugerencia_subida(tarea)
        tipo_doc = TipoDocumento.query.get(tipo_doc_id)
        assert resultado['tipo_doc_id'] == tipo_doc_id
        assert resultado['asunto'] == f'{tipo_doc.nombre} - {tramite.tipo_tramite.nombre}'

    def test_rol_ya_ocupado_no_sugiere(self, arbol_esftt):
        """Tarea con documento ya PRODUCIDO: ejecutada=True y documento_producido
        no es None -> ningún rol disponible, sin sugerencia (misma regla de
        exclusión por seguridad que tareas_candidatas(), ADR-038 §4)."""
        from app.services.sugerencia_documento import sugerencia_subida
        from app.models.documentos import Documento

        codigo_tramite, codigo_tarea, tipo_doc_id = _fila_catalogo_exacta('SALIDA')
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        tramite = arbol_esftt.tramite(fase, codigo_tramite)
        tarea = arbol_esftt.tarea(tramite, codigo_tarea)
        expediente_id = tarea.tramite.fase.solicitud.expediente_id

        producido = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_doc_id,
                               url='bddat://test-367/ya-producido')
        arbol_esftt.db.session.add(producido)
        arbol_esftt.db.session.flush()
        arbol_esftt.vincular(tarea, producido, 'PRODUCIDO')

        resultado = sugerencia_subida(tarea)
        assert resultado == {'tipo_doc_id': None, 'asunto': None}


# ── sugerencia_subida() — casos de borde, mockeados ──────────────────────────
# (ambigüedad y catálogo vacío no son reproducibles con el catálogo real: está
# diseñado a propósito sin tipo de tarea repetido con tipos exactos distintos)

def _tarea_mock(*, ejecutada=False, documento_producido=None):
    tarea = MagicMock()
    tarea.tramite.tipo_tramite_id = 1
    tarea.tipo_tarea_id = 2
    tarea.ejecutada = ejecutada
    tarea.documento_producido = documento_producido
    tarea.tramite.tipo_tramite.nombre = 'Trámite de prueba'
    return tarea


def _run(ordenes, catalogo_filas, tarea=None):
    from app.services.sugerencia_documento import sugerencia_subida

    tarea = tarea or _tarea_mock()

    mock_tt_query = MagicMock()
    mock_tt_query.filter_by.return_value.all.return_value = [MagicMock(orden=o) for o in ordenes]

    mock_ttd_query = MagicMock()
    cadena = (mock_ttd_query.filter.return_value.filter.return_value
              .filter.return_value.filter.return_value)
    cadena.all.return_value = catalogo_filas

    with patch('app.services.sugerencia_documento.TramiteTarea') as MockTT, \
         patch('app.services.sugerencia_documento.TramiteTareaDocumento') as MockTTD:
        MockTT.query = mock_tt_query
        MockTTD.query = mock_ttd_query
        return sugerencia_subida(tarea)


class TestSugerenciaSubidaCasosBorde:

    def test_catalogo_sin_filas_para_este_tramite_tarea_no_sugiere(self):
        """Sin fila en tramites_tareas para (tipo_tramite, tipo_tarea): el
        formulario queda en blanco, igual que hoy en el pool — nunca bloquea."""
        assert _run(ordenes=[], catalogo_filas=[]) == {'tipo_doc_id': None, 'asunto': None}

    def test_rol_ejecutada_y_producido_sin_roles_disponibles_no_sugiere(self):
        tarea = _tarea_mock(ejecutada=True, documento_producido=MagicMock())
        assert _run(ordenes=[1], catalogo_filas=[MagicMock(tipo_documento_id=10)], tarea=tarea) == \
            {'tipo_doc_id': None, 'asunto': None}

    def test_ambiguo_dos_tipos_exactos_no_sugiere(self):
        """Caso conocido de ADR-038 §4 (tipo de tarea repetido en el mismo
        trámite, p.ej. doble ESPERAR_PLAZO): dos slots resuelven al mismo
        tipo_tarea_id pero con tipo_documento_id distinto -> ambiguo, nunca
        se sugiere algo incorrecto."""
        fila_a = MagicMock(tipo_documento_id=10)
        fila_b = MagicMock(tipo_documento_id=20)
        assert _run(ordenes=[1, 2], catalogo_filas=[fila_a, fila_b]) == {'tipo_doc_id': None, 'asunto': None}

    def test_tipo_doc_inexistente_no_sugiere(self):
        """tipo_documento_id apunta a una fila que ya no existe en
        tipos_documentos (dato inconsistente) -> degrada a sin sugerencia,
        nunca lanza excepción."""
        fila = MagicMock(tipo_documento_id=999)
        with patch('app.services.sugerencia_documento.TipoDocumento') as MockTD:
            MockTD.query.get.return_value = None
            assert _run(ordenes=[1], catalogo_filas=[fila]) == {'tipo_doc_id': None, 'asunto': None}


# ── Endpoint HTTP GET .../nodo/tarea/<id>/sugerencia_documento ──────────────

class TestEndpointSugerenciaDocumento:

    def _montar_tarea(self, app, rol_catalogo):
        """Fase/Trámite/Tarea reales (BD de desarrollo), commiteados. Devuelve
        (expediente_id, fase_id, tarea_id, tipo_doc_id)."""
        from app import db
        from app.models.solicitudes import Solicitud
        from app.models.fases import Fase
        from app.models.tramites import Tramite
        from app.models.tareas import Tarea
        from app.models.tipos_fases import TipoFase
        from app.models.tramites_tareas_documentos import TramiteTareaDocumento
        from app.models.tramites_tareas import TramiteTarea

        with app.app_context():
            # Mismo criterio de no-ambigüedad que _fila_catalogo_exacta():
            # una tarea recién creada tiene ENTRADA y SALIDA disponibles a la
            # vez, así que el rol hermano no debe aportar un tipo exacto
            # distinto o la sugerencia sería ambigua a propósito.
            rol_hermano = 'SALIDA' if rol_catalogo == 'ENTRADA' else 'ENTRADA'
            fila = None
            slot = None
            for candidata in TramiteTareaDocumento.query.filter(
                TramiteTareaDocumento.rol == rol_catalogo,
                TramiteTareaDocumento.tipo_documento_id.isnot(None),
            ).all():
                hermana = TramiteTareaDocumento.query.filter_by(
                    tipo_tramite_id=candidata.tipo_tramite_id,
                    orden_tarea=candidata.orden_tarea, rol=rol_hermano,
                ).first()
                if hermana is not None and hermana.tipo_documento_id is not None \
                        and hermana.tipo_documento_id != candidata.tipo_documento_id:
                    continue
                candidata_slot = TramiteTarea.query.filter_by(
                    tipo_tramite_id=candidata.tipo_tramite_id, orden=candidata.orden_tarea).first()
                if candidata_slot is None:
                    continue
                fila, slot = candidata, candidata_slot
                break
            if fila is None:
                pytest.skip(f'No hay fila {rol_catalogo!r} sin ambigüedad de rol hermano en tramites_tareas_documentos')

            solicitud = Solicitud.query.first()
            if solicitud is None:
                pytest.skip('No hay solicitudes en la BD de desarrollo')
            tipo_fase = TipoFase.query.first()
            if tipo_fase is None:
                pytest.skip('No hay tipos de fase en el catálogo')

            fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo_fase.id)
            db.session.add(fase)
            db.session.flush()
            tramite = Tramite(fase_id=fase.id, tipo_tramite_id=fila.tipo_tramite_id)
            db.session.add(tramite)
            db.session.flush()
            tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=slot.tipo_tarea_id)
            db.session.add(tarea)
            db.session.flush()
            db.session.commit()
            return solicitud.expediente_id, fase.id, tarea.id, fila.tipo_documento_id

    def _limpiar(self, app, fase_id):
        from app import db
        from app.models.fases import Fase
        with app.app_context():
            db.session.rollback()
            # CASCADE en tramite_id/tarea_id (ADR-010) se lleva Tramite/Tarea al borrar la Fase.
            Fase.query.filter_by(id=fase_id).delete()
            db.session.commit()

    def test_devuelve_sugerencia_con_catalogo_exacto(self, usuario_tramitador, app):
        exp_id, fase_id, tarea_id, tipo_doc_id = self._montar_tarea(app, 'ENTRADA')
        try:
            r = usuario_tramitador.get(f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_id}/sugerencia_documento')
            assert r.status_code == 200
            data = r.get_json()
            assert data['tipo_doc_id'] == tipo_doc_id
            assert data['asunto']
        finally:
            self._limpiar(app, fase_id)

    def test_tarea_ajena_al_expediente_404(self, usuario_tramitador, app):
        exp_id, fase_id, tarea_id, _ = self._montar_tarea(app, 'ENTRADA')
        try:
            with app.app_context():
                from app.models.expedientes import Expediente
                otro = Expediente.query.filter(Expediente.id != exp_id).first()
                if otro is None:
                    pytest.skip('Solo hay un expediente en la BD de desarrollo')
                otro_id = otro.id
            r = usuario_tramitador.get(f'/api/expedientes/{otro_id}/nodo/tarea/{tarea_id}/sugerencia_documento')
            assert r.status_code == 404
        finally:
            self._limpiar(app, fase_id)


# ── pool_subir_documento — respuesta extendida con 'documentos' (#367) ─────

@pytest.fixture(autouse=True)
def _limpiar_documentos_prueba_367(app):
    yield
    with app.app_context():
        from app import db
        from app.models.documentos import Documento
        Documento.query.filter(
            Documento.asunto.like('%#367 test%')
        ).delete(synchronize_session=False)
        db.session.commit()


@pytest.fixture
def _pool_tmp_367(app, tmp_path):
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


class TestPoolSubirDocumentoRespuestaExtendida:

    def test_respuesta_incluye_documentos_con_campos_esperados(
        self, usuario_supervisor, expediente_seed, _pool_tmp_367,
    ):
        metadatos = [{'tipo_doc_id': 1, 'asunto': '#367 test — respuesta extendida'}]
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={
                'ficheros': (io.BytesIO(b'contenido #367'), 'informe_367.pdf'),
                'metadatos': json.dumps(metadatos),
            },
            content_type='multipart/form-data',
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data['ok'] is True
        assert data['creados'] == 1
        assert len(data['documentos']) == 1
        doc = data['documentos'][0]
        assert set(doc.keys()) == {'id', 'nombre', 'tipo_doc', 'tipo_doc_codigo', 'fecha'}
        assert doc['nombre'].endswith('informe_367.pdf')

    def test_contrato_previo_ok_creados_se_mantiene(
        self, usuario_supervisor, expediente_seed, _pool_tmp_367,
    ):
        """Cambio aditivo: el único consumidor previo (pool_documentos.html)
        solo lee 'ok'/'creados' — deben seguir presentes y sin cambiar de forma."""
        metadatos = [{'tipo_doc_id': 1, 'asunto': '#367 test — contrato previo'}]
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={
                'ficheros': (io.BytesIO(b'contenido #367 v2'), 'informe_367_b.pdf'),
                'metadatos': json.dumps(metadatos),
            },
            content_type='multipart/form-data',
        )
        data = r.get_json()
        assert data['ok'] is True
        assert isinstance(data['creados'], int) and data['creados'] == 1
