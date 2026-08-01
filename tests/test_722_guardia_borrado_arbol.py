"""
Tests #722 — guardia viva del borrado del árbol ESFTT.

Monta el árbol de verdad en BD (mismo patrón que test_717/test_714: app_ctx
con rollback por SAVEPOINT) porque check_invariante consulta relaciones
reales (Tarea.notificacion, Tarea.vinculos_documento, Tramite.tareas...).

Ejes que cubren:
  - TAREA: bloquea si tiene Notificacion (evidencia comunicada, nuevo en
    #722) o documentos vinculados (ya existía en _check_borrar pero nunca
    estaba conectado a ningún camino vivo).
  - TRAMITE/FASE/SOLICITUD: bloquea si tiene hijos — política hoja a hoja:
    #722 retira la cascada manual que hacía mutaciones_arbol.py, así que la
    única forma de vaciar un nivel es borrar sus hijos uno a uno.
  - Ninguno de los bloqueos anteriores es bypasseable con `justificacion`
    (a diferencia de los bloqueos del motor de reglas).
  - Camino limpio (sin hijos, sin evidencia) permite borrar en cada nivel.
"""
from datetime import date

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _fase_con_tramite_y_tarea(codigo_tipo_tramite, codigo_tipo_tarea):
    """Monta Fase → Trámite → Tarea sobre la primera solicitud de la BD de desarrollo.

    Devuelve (solicitud, fase, tramite, tarea).
    """
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
    db.session.add(fase)
    db.session.flush()

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=_tipo(TipoTramite, codigo_tipo_tramite).id)
    db.session.add(tramite)
    db.session.flush()

    tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=_tipo(TipoTarea, codigo_tipo_tarea).id)
    db.session.add(tarea)
    db.session.flush()

    return solicitud, fase, tramite, tarea


def _solicitud_vacia():
    """Nueva Solicitud sin fases, sobre el mismo expediente/entidad/tipo que la primera de la BD."""
    from app import db
    from app.models.solicitudes import Solicitud

    base = Solicitud.query.first()
    if base is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    nueva = Solicitud(expediente_id=base.expediente_id, entidad_id=base.entidad_id,
                      tipo_solicitud_id=base.tipo_solicitud_id)
    db.session.add(nueva)
    db.session.flush()
    return nueva


# ---------------------------------------------------------------------------
# TAREA — evidencia notificada y documentos vinculados
# ---------------------------------------------------------------------------

class TestBorrarTarea:

    def test_con_notificacion_bloqueado_y_no_escapable(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.notificaciones import Notificacion
        from app import db

        _, _, _, tarea = _fase_con_tramite_y_tarea('REQUERIMIENTO_SUBSANACION', 'NOTIFICAR')
        db.session.add(Notificacion(tarea_id=tarea.id, canal='NOTIFICA',
                                    fecha_puesta_disposicion=date.today()))
        db.session.flush()

        res = svc.borrar_tarea(tarea)
        assert not res.ok
        assert res.bloqueo is not None
        assert 'evidencia' in res.bloqueo.norma_compilada

        # Puerta cerrada: ni con justificación se salta (a diferencia del motor).
        res_forzado = svc.borrar_tarea(tarea, justificacion='lo necesito igualmente')
        assert not res_forzado.ok
        assert res_forzado.bloqueo is not None

        from app.models.tareas import Tarea
        assert Tarea.query.get(tarea.id) is not None

    def test_con_documento_vinculado_bloqueado(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.tipos_documentos import TipoDocumento
        from app import db

        solicitud, _, _, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        tipo_doc = TipoDocumento.query.first()
        if tipo_doc is None:
            pytest.skip('No hay tipos de documento en la BD de desarrollo')
        doc = Documento(expediente_id=solicitud.expediente_id, tipo_doc_id=tipo_doc.id,
                        url='bddat://test-722/doc')
        db.session.add(doc)
        db.session.flush()
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()

        res = svc.borrar_tarea(tarea)
        assert not res.ok
        assert 'documentos asignados' in res.bloqueo.norma_compilada

    def test_sin_evidencia_ni_documentos_permitido(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.tareas import Tarea

        _, _, _, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        tarea_id = tarea.id

        res = svc.borrar_tarea(tarea)
        assert res.ok
        assert res.bloqueo is None
        assert Tarea.query.get(tarea_id) is None


# ---------------------------------------------------------------------------
# TRAMITE / FASE / SOLICITUD — hoja a hoja
# ---------------------------------------------------------------------------

class TestBorrarTramite:

    def test_con_tareas_bloqueado(self, app_ctx):
        from app.services import mutaciones_arbol as svc

        _, _, tramite, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')

        res = svc.borrar_tramite(tramite)
        assert not res.ok
        assert 'Bórrelas primero' in res.bloqueo.norma_compilada

    def test_vacio_permitido(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.tramites import Tramite

        _, _, tramite, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        tramite_id = tramite.id
        assert svc.borrar_tarea(tarea).ok  # deja el trámite sin hijos

        res = svc.borrar_tramite(tramite)
        assert res.ok
        assert Tramite.query.get(tramite_id) is None


class TestBorrarFase:

    def test_con_tramites_bloqueado(self, app_ctx):
        from app.services import mutaciones_arbol as svc

        _, fase, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')

        res = svc.borrar_fase(fase)
        assert not res.ok
        assert 'Bórrelos primero' in res.bloqueo.norma_compilada

    def test_vacia_permitido(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.fases import Fase

        _, fase, tramite, tarea = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')
        fase_id = fase.id
        assert svc.borrar_tarea(tarea).ok
        assert svc.borrar_tramite(tramite).ok

        res = svc.borrar_fase(fase)
        assert res.ok
        assert Fase.query.get(fase_id) is None


class TestBorrarSolicitud:

    def test_con_fases_bloqueado(self, app_ctx):
        from app.services import mutaciones_arbol as svc

        solicitud, _, _, _ = _fase_con_tramite_y_tarea('ANALISIS_DOCUMENTAL', 'ANALIZAR')

        res = svc.borrar_solicitud(solicitud)
        assert not res.ok
        assert 'Bórrelas primero' in res.bloqueo.norma_compilada

    def test_vacia_permitido(self, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.solicitudes import Solicitud

        nueva = _solicitud_vacia()
        nueva_id = nueva.id

        res = svc.borrar_solicitud(nueva)
        assert res.ok
        assert Solicitud.query.get(nueva_id) is None
