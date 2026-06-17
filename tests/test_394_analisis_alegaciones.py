"""
Tests issue #394 — ContextoAnalisisAlegaciones.

Bloques:
  A) get_contexto() sin datos
  B) get_contexto() con una alegación (sin respuesta del titular)
  C) get_contexto() con una alegación (con respuesta del titular)
  D) get_contexto() con múltiples alegaciones — resumen_clasificacion
  E) Alegante con entidad enlazada (entidad_id) — nombre y nif de entidad
"""
from datetime import date
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _alegante(tipo='particular', nombre='Juan García', nif='12345678A', entidad=None):
    from app.models.alegantes import Alegante
    a = MagicMock()
    a.tipo_interesado = tipo
    a.nombre = nombre
    a.nif = nif
    a.entidad = entidad
    a.as_contexto_cb = lambda: Alegante.as_contexto_cb(a)
    return a


def _entidad(nombre_completo='Endesa S.A.', nif='A28023430'):
    e = MagicMock()
    e.nombre_completo = nombre_completo
    e.nif = nif
    return e


def _tipo_tarea(codigo):
    t = MagicMock()
    t.codigo = codigo
    return t


def _tarea(codigo, documento_usado=None, documento_producido=None):
    t = MagicMock()
    t.tipo_tarea = _tipo_tarea(codigo)
    # Vínculos N:M (ADR-010): el documento de entrada se expone como lista
    t.documentos_consumidos = [documento_usado] if documento_usado is not None else []
    t.documento_producido = documento_producido
    return t


def _doc(asunto=None, fecha=None):
    d = MagicMock()
    d.asunto = asunto
    d.fecha_administrativa = fecha
    return d


def _tramite_recepcion(alegante, tareas=None):
    t = MagicMock()
    t.tipo_tramite = MagicMock()
    t.tipo_tramite.codigo = 'RECEPCION_ALEGACION'
    t.alegante = alegante
    t.tareas = tareas or []
    return t


def _tramite_otro():
    t = MagicMock()
    t.tipo_tramite = MagicMock()
    t.tipo_tramite.codigo = 'OTRO_TRAMITE'
    t.alegante = None
    return t


def _solicitud(tramites_por_fase):
    """tramites_por_fase: lista de listas de trámites, uno por fase."""
    fases = []
    for tramites in tramites_por_fase:
        fase = MagicMock()
        fase.tramites = tramites
        fases.append(fase)
    s = MagicMock()
    s.fases = fases
    return s


def _tarea_cb(solicitud):
    """Stub de Tarea que permite navegar hasta la solicitud dada."""
    tramite = MagicMock()
    tramite.fase = MagicMock()
    tramite.fase.solicitud = solicitud
    tarea = MagicMock()
    tarea.tramite = tramite
    return tarea


def _cb(solicitud):
    from app.services.context_builders.contexto_analisis_alegaciones import ContextoAnalisisAlegaciones
    return ContextoAnalisisAlegaciones(MagicMock(), MagicMock(), tarea=_tarea_cb(solicitud))


# ──────────────────────────────────────────────────────────────────────────────
# A) Sin datos
# ──────────────────────────────────────────────────────────────────────────────

class TestSinDatos:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.contexto_analisis_alegaciones import ContextoAnalisisAlegaciones
        cb = ContextoAnalisisAlegaciones(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_alegaciones_estructura_vacia(self):
        solicitud = _solicitud([[_tramite_otro()]])
        ctx = _cb(solicitud).get_contexto()
        assert ctx['num_alegaciones'] == 0
        assert ctx['alegaciones'] == []
        assert ctx['resumen_clasificacion'] == {}

    def test_tramite_sin_alegante_se_ignora(self):
        tramite = _tramite_recepcion(alegante=None)
        solicitud = _solicitud([[tramite]])
        ctx = _cb(solicitud).get_contexto()
        assert ctx['num_alegaciones'] == 0


# ──────────────────────────────────────────────────────────────────────────────
# B) Una alegación sin respuesta del titular
# ──────────────────────────────────────────────────────────────────────────────

class TestUnaAlegacionSinRespuesta:

    def _ctx(self):
        doc_alg = _doc(asunto='Alegación sobre trazado', fecha=date(2026, 3, 10))
        tareas = [_tarea('ANALIZAR', documento_usado=doc_alg)]
        tramite = _tramite_recepcion(_alegante(), tareas=tareas)
        return _cb(_solicitud([[tramite]])).get_contexto()

    def test_num_alegaciones(self):
        assert self._ctx()['num_alegaciones'] == 1

    def test_campos_alegante(self):
        a = self._ctx()['alegaciones'][0]
        assert a['alegante_nombre'] == 'Juan García'
        assert a['alegante_nif'] == '12345678A'
        assert a['alegante_tipo_interesado'] == 'particular'

    def test_campos_alegacion_doc(self):
        a = self._ctx()['alegaciones'][0]
        assert a['alegacion_asunto'] == 'Alegación sobre trazado'
        assert a['alegacion_fecha'] == '10/03/2026'

    def test_respuesta_titular_no_recibida(self):
        a = self._ctx()['alegaciones'][0]
        assert a['respuesta_titular_recibida'] is False
        assert a['respuesta_titular_asunto'] is None
        assert a['respuesta_titular_fecha'] is None

    def test_resumen_clasificacion(self):
        assert self._ctx()['resumen_clasificacion'] == {'particular': 1}


# ──────────────────────────────────────────────────────────────────────────────
# C) Una alegación con respuesta del titular
# ──────────────────────────────────────────────────────────────────────────────

class TestUnaAlegacionConRespuesta:

    def _ctx(self):
        doc_alg = _doc(asunto='Alegación sobre impacto visual', fecha=date(2026, 3, 5))
        doc_resp = _doc(asunto='Respuesta al alegante', fecha=date(2026, 4, 2))
        tareas = [
            _tarea('ANALIZAR', documento_usado=doc_alg),
            _tarea('ESPERAR_PLAZO', documento_producido=doc_resp),
        ]
        tramite = _tramite_recepcion(_alegante(tipo='asociacion'), tareas=tareas)
        return _cb(_solicitud([[tramite]])).get_contexto()

    def test_respuesta_titular_recibida(self):
        a = self._ctx()['alegaciones'][0]
        assert a['respuesta_titular_recibida'] is True

    def test_campos_respuesta_titular(self):
        a = self._ctx()['alegaciones'][0]
        assert a['respuesta_titular_asunto'] == 'Respuesta al alegante'
        assert a['respuesta_titular_fecha'] == '02/04/2026'

    def test_resumen_clasificacion(self):
        assert self._ctx()['resumen_clasificacion'] == {'asociacion': 1}


# ──────────────────────────────────────────────────────────────────────────────
# D) Múltiples alegaciones — resumen_clasificacion y num_alegaciones
# ──────────────────────────────────────────────────────────────────────────────

class TestMultiplesAlegaciones:

    def _ctx(self):
        t1 = _tramite_recepcion(_alegante(tipo='particular', nombre='Ana'))
        t2 = _tramite_recepcion(_alegante(tipo='particular', nombre='Luis'))
        t3 = _tramite_recepcion(_alegante(tipo='empresa', nombre='Iberdrola'))
        t4 = _tramite_recepcion(_alegante(tipo='administracion', nombre='Ayto. Sevilla'))
        solicitud = _solicitud([[t1, t2], [t3, t4]])
        return _cb(solicitud).get_contexto()

    def test_num_alegaciones(self):
        assert self._ctx()['num_alegaciones'] == 4

    def test_resumen_clasificacion(self):
        r = self._ctx()['resumen_clasificacion']
        assert r['particular'] == 2
        assert r['empresa'] == 1
        assert r['administracion'] == 1

    def test_longitud_lista_alegaciones(self):
        assert len(self._ctx()['alegaciones']) == 4

    def test_tramites_de_distinto_tipo_se_ignoran(self):
        t_alg = _tramite_recepcion(_alegante())
        t_otro = _tramite_otro()
        solicitud = _solicitud([[t_alg, t_otro]])
        ctx = _cb(solicitud).get_contexto()
        assert ctx['num_alegaciones'] == 1


# ──────────────────────────────────────────────────────────────────────────────
# E) Alegante con entidad enlazada — nombre y nif proceden de la entidad
# ──────────────────────────────────────────────────────────────────────────────

class TestAleganteConEntidad:

    def test_nombre_y_nif_de_entidad(self):
        ent = _entidad(nombre_completo='Endesa S.A.', nif='A28023430')
        alegante = _alegante(tipo='empresa', nombre='nombre_local', nif='nif_local', entidad=ent)
        tramite = _tramite_recepcion(alegante)
        ctx = _cb(_solicitud([[tramite]])).get_contexto()
        a = ctx['alegaciones'][0]
        assert a['alegante_nombre'] == 'Endesa S.A.'
        assert a['alegante_nif'] == 'A28023430'

    def test_campos_locales_cuando_sin_entidad(self):
        alegante = _alegante(tipo='particular', nombre='Pedro Ruiz', nif='11111111H')
        tramite = _tramite_recepcion(alegante)
        ctx = _cb(_solicitud([[tramite]])).get_contexto()
        a = ctx['alegaciones'][0]
        assert a['alegante_nombre'] == 'Pedro Ruiz'
        assert a['alegante_nif'] == '11111111H'
