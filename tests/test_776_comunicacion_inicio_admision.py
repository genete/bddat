"""
Tests issue #776 — ContextoComunicacionInicioAdmision.

Desde #931 (N2b de ADR-049) el plazo que el escrito comunica es el de cada ACTO
de la solicitud, no uno de la solicitud: `actos` es siempre una lista (D2).

Bloques:
  A) get_contexto() con stubs (MagicMock), sin BD ni app context —
     `plazos_de_la_solicitud` se mockea con `EstadoPlazoActo` reales para no
     depender de catalogo_plazos.
  B) Con BD: una solicitud real contra el catálogo real (#931).
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _documento_solicitud(fecha_administrativa=None):
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    return doc


def _solicitud(id=1, documento_solicitud=None):
    s = MagicMock()
    s.id = id
    s.documento_solicitud = documento_solicitud
    return s


def _fase(solicitud=None):
    f = MagicMock()
    f.solicitud = solicitud
    return f


def _tramite(fase=None):
    t = MagicMock()
    t.fase = fase
    return t


def _tarea(tramite=None):
    t = MagicMock()
    t.tramite = tramite
    return t


def _cb(tarea):
    from app.services.context_builders.contexto_comunicacion_inicio_admision import (
        ContextoComunicacionInicioAdmision,
    )
    return ContextoComunicacionInicioAdmision(MagicMock(), MagicMock(), tarea=tarea)


def _plazo(acto='AAP', estado='EN_PLAZO', plazo_valor=3, plazo_unidad='MESES',
           norma_origen='Art. 128 RD 1955/2000',
           efecto_nombre='Silencio administrativo desestimatorio'):
    """El plazo de un acto tal como lo devuelve `plazos_de_la_solicitud`.

    SIN_PLAZO sale sin metadatos de catálogo, igual que en el servicio.
    """
    from app.services.plazos import EstadoPlazoActo
    if estado == 'SIN_PLAZO':
        return EstadoPlazoActo(estado='SIN_PLAZO', efecto='NINGUNO', fecha_limite=None,
                               dias_restantes=None, acto=acto,
                               fase_resolutora='RESOLUCION', fase_resolutora_id=None)
    return EstadoPlazoActo(estado=estado, efecto='SILENCIO_DESESTIMATORIO',
                           fecha_limite=date(2026, 4, 15), dias_restantes=40,
                           plazo_valor=plazo_valor, plazo_unidad=plazo_unidad,
                           norma_origen=norma_origen, efecto_nombre=efecto_nombre,
                           acto=acto, fase_resolutora='RESOLUCION', fase_resolutora_id=None)


def _contexto(plazos, documento_solicitud=None):
    """get_contexto() de una solicitud con esos plazos por acto."""
    if documento_solicitud is None:
        documento_solicitud = _documento_solicitud(date(2026, 1, 15))
    tarea = _tarea(_tramite(_fase(_solicitud(documento_solicitud=documento_solicitud))))
    with patch('app.services.plazos.plazos_de_la_solicitud', return_value=plazos):
        return _cb(tarea).get_contexto()


# ──────────────────────────────────────────────────────────────────────────────
# A) Sin BD
# ──────────────────────────────────────────────────────────────────────────────

class TestContextoComunicacionInicioAdmision:

    def test_sin_tarea_devuelve_vacio(self):
        cb = _cb(tarea=None)
        assert cb.get_contexto() == {}

    def test_sin_fase_devuelve_vacio(self):
        tarea = _tarea(_tramite(fase=None))
        assert _cb(tarea).get_contexto() == {}

    def test_sin_solicitud_devuelve_vacio(self):
        tarea = _tarea(_tramite(_fase(solicitud=None)))
        assert _cb(tarea).get_contexto() == {}

    def test_un_acto_es_una_lista_de_uno(self):
        """Contrato uniforme (D2): nunca un valor suelto. La frase única la
        decide la plantilla con `{%p if actos|length == 1 %}`."""
        ctx = _contexto([_plazo()])

        assert ctx['actos'] == [{
            'nombre': 'AAP',
            'plazo_maximo_resolucion': 3,
            'unidad_plazo': 'meses',
            'norma_plazo': 'Art. 128 RD 1955/2000',
            'efecto_silencio': 'Silencio administrativo desestimatorio',
        }]
        assert ctx['fecha_recepcion_solicitud'] == '15/01/2026'

    def test_varios_actos_cada_uno_con_su_plazo(self):
        """AAP+AAC+DUP: tres plazos, en el orden de los actos — la DUP con sus
        6 meses, no con los 3 de la combinación que retiró #931."""
        ctx = _contexto([
            _plazo('AAP', norma_origen='Art. 128 RD 1955/2000'),
            _plazo('AAC', norma_origen='Art. 131.7 RD 1955/2000'),
            _plazo('DUP', plazo_valor=6, norma_origen='Art. 148.1 RD 1955/2000'),
        ])

        assert [(a['nombre'], a['plazo_maximo_resolucion'], a['norma_plazo'])
                for a in ctx['actos']] == [
            ('AAP', 3, 'Art. 128 RD 1955/2000'),
            ('AAC', 3, 'Art. 131.7 RD 1955/2000'),
            ('DUP', 6, 'Art. 148.1 RD 1955/2000'),
        ]

    def test_acto_sin_plazo_queda_fuera(self):
        """El escrito no informa de un plazo que no existe."""
        ctx = _contexto([_plazo('AAP'), _plazo('INTERESADO', estado='SIN_PLAZO')])
        assert [a['nombre'] for a in ctx['actos']] == ['AAP']

    def test_ningun_acto_con_plazo_lista_vacia(self):
        """#347: degradado sin excepción; la fecha no depende del plazo."""
        ctx = _contexto([_plazo('INTERESADO', estado='SIN_PLAZO')])
        assert ctx['actos'] == []
        assert ctx['fecha_recepcion_solicitud'] == '15/01/2026'

    def test_unidad_dias_habiles_legible(self):
        ctx = _contexto([_plazo(plazo_valor=10, plazo_unidad='DIAS_HABILES')])
        assert ctx['actos'][0]['plazo_maximo_resolucion'] == 10
        assert ctx['actos'][0]['unidad_plazo'] == 'días hábiles'

    def test_ya_no_hay_campos_sueltos_del_plazo(self):
        """Los cuatro tokens de antes de #931 desaparecen del nivel raíz: una
        plantilla vieja no debe creer que siguen llegando."""
        ctx = _contexto([_plazo()])
        assert set(ctx) == {'actos', 'fecha_recepcion_solicitud'}

    def test_degradado_sin_documento_solicitud(self):
        """#347: sin documento_solicitud -> fecha None, sin excepción."""
        tarea = _tarea(_tramite(_fase(_solicitud(documento_solicitud=None))))
        with patch('app.services.plazos.plazos_de_la_solicitud', return_value=[_plazo()]):
            ctx = _cb(tarea).get_contexto()

        assert ctx['fecha_recepcion_solicitud'] is None
        assert ctx['actos'][0]['plazo_maximo_resolucion'] == 3

    def test_degradado_documento_solicitud_sin_fecha_administrativa(self):
        ctx = _contexto([_plazo()], documento_solicitud=_documento_solicitud(None))
        assert ctx['fecha_recepcion_solicitud'] is None

    def test_el_manifiesto_ofrece_los_campos_que_se_entregan(self):
        """El panel de plantillas enseña al supervisor `TOKENS`: tiene que
        coincidir con lo que `get_contexto` entrega de verdad."""
        from app.services.context_builders.contexto_comunicacion_inicio_admision import (
            ContextoComunicacionInicioAdmision,
        )
        tokens = {t['campo']: t for t in ContextoComunicacionInicioAdmision.TOKENS}
        ctx = _contexto([_plazo()])

        assert set(tokens) == set(ctx)
        assert tokens['actos']['tipo'] == 'tabla'
        assert {c['campo'] for c in tokens['actos']['columnas']} == set(ctx['actos'][0])


# ──────────────────────────────────────────────────────────────────────────────
# B) Con BD — solicitud y catálogo reales
# ──────────────────────────────────────────────────────────────────────────────

def test_solicitud_real_aac_dup(arbol_aislado):
    """Contra las filas reales: la AAC con sus 3 meses (art. 131.7) y la DUP
    con sus 6 (art. 148.1), en vez del único plazo de 3 meses que daba la fila
    de combinación `AAC+DUP`."""
    from app.models.tipos_solicitudes import TipoSolicitud

    solicitud = arbol_aislado.solicitud_propia()
    tipo = TipoSolicitud.query.filter_by(siglas='AAC+DUP').first()
    assert tipo is not None, "la semilla debe traer el tipo de solicitud 'AAC+DUP'"
    solicitud.tipo_solicitud = tipo
    solicitud.documento_solicitud.fecha_administrativa = date(2025, 3, 4)
    arbol_aislado.db.session.flush()

    tarea = _tarea(_tramite(_fase(solicitud)))
    ctx = _cb(tarea).get_contexto()

    assert [(a['nombre'], a['plazo_maximo_resolucion'], a['unidad_plazo'], a['norma_plazo'])
            for a in ctx['actos']] == [
        ('AAC', 3, 'meses', 'Art. 131.7 RD 1955/2000'),
        ('DUP', 6, 'meses', 'Art. 148.1 RD 1955/2000'),
    ]
    assert ctx['fecha_recepcion_solicitud'] == '04/03/2025'
