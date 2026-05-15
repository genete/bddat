"""
Tests issue #393 — Alegante.as_contexto_cb() y ContextoRecepcionAlegacion.

Bloques:
  A) Alegante.as_contexto_cb()  — stubs, sin BD ni app context.
  B) ContextoRecepcionAlegacion.get_contexto() — stubs.
"""
from unittest.mock import MagicMock


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _alegante(tipo='particular', nombre='Juan García', nif='12345678A', entidad=None):
    """Stub de Alegante con as_contexto_cb() delegando al método real."""
    from app.models.alegantes import Alegante
    a = MagicMock()
    a.tipo_interesado = tipo
    a.nombre = nombre
    a.nif = nif
    a.entidad = entidad
    a.as_contexto_cb = lambda: Alegante.as_contexto_cb(a)
    return a


def _entidad(nombre_completo='Ayuntamiento de Málaga', nif='P2900900B'):
    e = MagicMock()
    e.nombre_completo = nombre_completo
    e.nif = nif
    return e


def _tramite_con_alegante(alegante=None):
    t = MagicMock()
    t.alegante = alegante
    return t


def _tarea_con_tramite(tramite):
    t = MagicMock()
    t.tramite = tramite
    return t


# ──────────────────────────────────────────────────────────────────────────────
# A) Alegante.as_contexto_cb()
# ──────────────────────────────────────────────────────────────────────────────

class TestAleganteAsContextoCb:

    def test_campos_ocasional(self):
        a = _alegante(tipo='particular', nombre='Juan García', nif='12345678A')
        ctx = a.as_contexto_cb()
        assert ctx['alegante_nombre'] == 'Juan García'
        assert ctx['alegante_nif'] == '12345678A'
        assert ctx['alegante_tipo_interesado'] == 'particular'

    def test_entidad_tiene_prioridad_sobre_campos_locales(self):
        ent = _entidad(nombre_completo='Ayuntamiento de Málaga', nif='P2900900B')
        a = _alegante(nombre='nombre_local', nif='nif_local', entidad=ent)
        ctx = a.as_contexto_cb()
        assert ctx['alegante_nombre'] == 'Ayuntamiento de Málaga'
        assert ctx['alegante_nif'] == 'P2900900B'

    def test_nif_none_permitido(self):
        a = _alegante(nombre='Sin NIF', nif=None)
        ctx = a.as_contexto_cb()
        assert ctx['alegante_nif'] is None

    def test_tipo_interesado_pasa_sin_transformacion(self):
        for tipo in ('particular', 'administracion', 'asociacion', 'empresa'):
            a = _alegante(tipo=tipo)
            assert a.as_contexto_cb()['alegante_tipo_interesado'] == tipo


# ──────────────────────────────────────────────────────────────────────────────
# B) ContextoRecepcionAlegacion.get_contexto()
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoRecepcionAlegacion:

    def test_sin_tarea_devuelve_vacio(self):
        from app.services.context_builders.recepcion_alegacion import ContextoRecepcionAlegacion
        cb = ContextoRecepcionAlegacion(MagicMock(), MagicMock(), tarea=None)
        assert cb.get_contexto() == {}

    def test_tramite_sin_alegante_devuelve_vacio(self):
        from app.services.context_builders.recepcion_alegacion import ContextoRecepcionAlegacion
        tarea = _tarea_con_tramite(_tramite_con_alegante(alegante=None))
        cb = ContextoRecepcionAlegacion(MagicMock(), MagicMock(), tarea=tarea)
        assert cb.get_contexto() == {}

    def test_con_alegante_ocasional_campos_correctos(self):
        from app.services.context_builders.recepcion_alegacion import ContextoRecepcionAlegacion
        a = _alegante(tipo='particular', nombre='María López', nif='87654321B')
        tarea = _tarea_con_tramite(_tramite_con_alegante(alegante=a))
        cb = ContextoRecepcionAlegacion(MagicMock(), MagicMock(), tarea=tarea)
        ctx = cb.get_contexto()
        assert ctx['alegante_nombre'] == 'María López'
        assert ctx['alegante_nif'] == '87654321B'
        assert ctx['alegante_tipo_interesado'] == 'particular'

    def test_con_alegante_vinculado_a_entidad(self):
        from app.services.context_builders.recepcion_alegacion import ContextoRecepcionAlegacion
        ent = _entidad(nombre_completo='Endesa S.A.', nif='A28023430')
        a = _alegante(tipo='empresa', nombre='ignorar', nif='ignorar', entidad=ent)
        tarea = _tarea_con_tramite(_tramite_con_alegante(alegante=a))
        cb = ContextoRecepcionAlegacion(MagicMock(), MagicMock(), tarea=tarea)
        ctx = cb.get_contexto()
        assert ctx['alegante_nombre'] == 'Endesa S.A.'
        assert ctx['alegante_nif'] == 'A28023430'
