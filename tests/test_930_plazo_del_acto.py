"""#930 (N2 de ADR-049): el plazo de resolver es del acto; su cumplimiento se
calcula de la notificación al titular.

Bloques:
  A) El acto y la fase que lo resuelve (`actos_solicitud`, fuente única, D4).
  B) `informe_instruccion.codigos_fase_finalizadora` derivada de los actos.
  C) Catálogo de fases: `es_finalizadora` == `FASES_RESOLUTORAS`.
  D) El cumplimiento del acto: `documento_cumplimiento_fase` y
     `ActoSolicitud.documento_cumplimiento`; la convención de D2 en catálogo.

Fechas fijas y en el pasado: el modelo rechaza la fecha administrativa futura
(#824) y bajo `app_ctx` «hoy» puede ser el reloj simulado.
"""
from datetime import date

import pytest


def _sol(siglas, fases=()):
    """Solicitud mínima para el mapa: tipo, sus actos (con la misma propiedad
    del modelo, no una copia) y las fases que constan en el árbol."""
    from types import SimpleNamespace
    from app.models.solicitudes import Solicitud

    class _Sol:
        tipos_simples = Solicitud.tipos_simples

        def __init__(self):
            self.tipo_solicitud = SimpleNamespace(siglas=siglas) if siglas else None
            self.fases = [SimpleNamespace(tipo_fase=SimpleNamespace(codigo=c)) for c in fases]

    return _Sol()


# ---------------------------------------------------------------------------
# A) El acto y la fase que lo resuelve
# ---------------------------------------------------------------------------

class TestActos:

    @pytest.mark.parametrize('siglas, actos', [
        ('AAP', ['AAP']),
        ('AAP+AAC', ['AAP', 'AAC']),
        ('AAP+AAC+DUP', ['AAP', 'AAC', 'DUP']),
        ('AE_DEFINITIVA+AAT', ['AE_DEFINITIVA', 'AAT']),
        ('DUP', ['DUP']),
        ('INTERESADO', ['INTERESADO']),
        (None, []),
    ])
    def test_un_acto_por_tipo_atomico(self, siglas, actos):
        from app.services.actos_solicitud import actos_de
        sol = _sol(siglas)
        resultado = actos_de(sol)
        assert [a.siglas for a in resultado] == actos
        assert all(a.solicitud is sol for a in resultado)

    @pytest.mark.parametrize('siglas, acto, fases, esperada', [
        ('DUP', 'DUP', (), 'RESOLUCION_DUP'),
        ('INTERESADO', 'INTERESADO', (), 'RECONOCIMIENTO_INTERESADO'),
        ('AAT', 'AAT', (), 'RESOLUCION'),
        ('AE_DEFINITIVA+AAT', 'AE_DEFINITIVA', (), 'RESOLUCION'),
        ('RECURSO', 'RECURSO', (), 'RESOLUCION'),
        # Conjunta: sin elección todavía
        ('AAP+AAC', 'AAP', (), 'RESOLUCION'),
        ('AAP+AAC', 'AAC', ('RESOLUCION',), 'RESOLUCION'),
        ('AAP+AAC+DUP', 'DUP', ('RESOLUCION_AAP',), 'RESOLUCION_DUP'),
        # Partida: basta con que conste una de las dos
        ('AAP+AAC', 'AAP', ('RESOLUCION_AAP', 'RESOLUCION_AAC'), 'RESOLUCION_AAP'),
        ('AAP+AAC', 'AAC', ('RESOLUCION_AAP',), 'RESOLUCION_AAC'),
        ('AAP+AAC+DUP', 'AAP', ('RESOLUCION_AAC',), 'RESOLUCION_AAP'),
        # La partida solo cabe en las solicitudes que piden AAP y AAC a la vez
        ('AAP+DUP', 'AAP', ('RESOLUCION_AAP',), 'RESOLUCION'),
        ('AAP', 'AAP', ('RESOLUCION_AAP',), 'RESOLUCION'),
    ])
    def test_fase_resolutora(self, siglas, acto, fases, esperada):
        from app.services.actos_solicitud import fase_resolutora
        assert fase_resolutora(_sol(siglas, fases), acto) == esperada

    def test_toda_fase_emitible_esta_en_fases_resolutoras(self):
        """`FASES_RESOLUTORAS` es lo que el guardián compara con el catálogo:
        si el mapa pudiera emitir un código que no está ahí, el guardián no lo
        vería."""
        from app.services import actos_solicitud as m
        emitibles = (set(m._FASE_DE_ACTO.values()) | set(m._FASE_DE_ACTO_PARTIDA.values())
                     | {m._FASE_POR_DEFECTO})
        assert emitibles == m.FASES_RESOLUTORAS


# ---------------------------------------------------------------------------
# B) codigos_fase_finalizadora derivada de los actos (refactor puro, D4)
# ---------------------------------------------------------------------------

# Lo que devolvía `codigos_fase_finalizadora` ANTES del refactor, en estado por
# defecto (sin fases en el árbol). Escrito a mano, no derivado del mapa nuevo:
# es la red que dice que el refactor no cambió nada.
_INFORME_HOY = {
    'AAP': ['RESOLUCION'],
    'AAC': ['RESOLUCION'],
    'DUP': ['RESOLUCION_DUP'],
    'AAP+AAC': ['RESOLUCION'],
    'AAP+AAC+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAC+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAP+DUP': ['RESOLUCION', 'RESOLUCION_DUP'],
    'AAT': ['RESOLUCION'],
    'AE_PROVISIONAL': ['RESOLUCION'],
    'AE_DEFINITIVA': ['RESOLUCION'],
    'AE_DEFINITIVA+AAT': ['RESOLUCION'],
    'CIERRE': ['RESOLUCION'],
    'INTERESADO': ['RECONOCIMIENTO_INTERESADO'],
    'AMPLIACION_PLAZO': ['RESOLUCION'],
    'CORRECCION_ERRORES': ['RESOLUCION'],
    'DESISTIMIENTO': ['RESOLUCION'],
    'OTRO': ['RESOLUCION'],
    'RADNE': ['RESOLUCION'],
    'RAIPEE_DEFINITIVA': ['RESOLUCION'],
    'RAIPEE_PREVIA': ['RESOLUCION'],
    'RECURSO': ['RESOLUCION'],
    'RENUNCIA': ['RESOLUCION'],
}


class TestCodigosFaseFinalizadora:

    def test_la_tabla_cubre_todo_el_catalogo_de_tipos(self, app_ctx):
        """Un tipo de solicitud nuevo obliga a decir aquí qué fase lo resuelve."""
        from app.models.tipos_solicitudes import TipoSolicitud
        siglas = {t.siglas for t in TipoSolicitud.query.all()}
        assert siglas == set(_INFORME_HOY)

    @pytest.mark.parametrize('siglas', sorted(_INFORME_HOY))
    def test_estado_por_defecto_igual_que_antes(self, siglas):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        assert codigos_fase_finalizadora(_sol(siglas)) == _INFORME_HOY[siglas]

    def test_sin_tipo_resolucion(self):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        assert codigos_fase_finalizadora(_sol(None)) == ['RESOLUCION']

    @pytest.mark.parametrize('siglas, esperada', [
        ('AAP+AAC', ['RESOLUCION_AAP', 'RESOLUCION_AAC']),
        ('AAP+AAC+DUP', ['RESOLUCION_AAP', 'RESOLUCION_AAC', 'RESOLUCION_DUP']),
    ])
    def test_partida_completa(self, siglas, esperada):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol(siglas, ('ANALISIS_SOLICITUD', 'RESOLUCION_AAP', 'RESOLUCION_AAC'))
        assert codigos_fase_finalizadora(sol) == esperada

    def test_partida_a_medias_audita_tambien_la_que_falta(self):
        """Único cambio de comportamiento del refactor (D4): antes solo
        `[RESOLUCION_AAP]`. Inocuo: las reglas CREAR de RESOLUCION_AAC son las
        mismas que las de RESOLUCION_AAP."""
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol('AAP+AAC', ('RESOLUCION_AAP',))
        assert codigos_fase_finalizadora(sol) == ['RESOLUCION_AAP', 'RESOLUCION_AAC']

    def test_aap_dup_no_se_parte_aunque_conste_resolucion_aap(self):
        from app.services.informe_instruccion import codigos_fase_finalizadora
        sol = _sol('AAP+DUP', ('RESOLUCION_AAP',))
        assert codigos_fase_finalizadora(sol) == ['RESOLUCION', 'RESOLUCION_DUP']

    def test_con_solicitud_real_partida(self, arbol_aislado):
        """Lo mismo sobre filas reales: el mapa lee `solicitud.fases` del ORM."""
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.informe_instruccion import codigos_fase_finalizadora

        solicitud = arbol_aislado.solicitud_propia()
        tipo = TipoSolicitud.query.filter_by(siglas='AAP+AAC+DUP').first()
        assert tipo is not None, "la semilla debe traer el tipo 'AAP+AAC+DUP'"
        solicitud.tipo_solicitud = tipo
        assert codigos_fase_finalizadora(solicitud) == ['RESOLUCION', 'RESOLUCION_DUP']

        arbol_aislado.fase('RESOLUCION_AAC', solicitud=solicitud)
        assert codigos_fase_finalizadora(solicitud) == [
            'RESOLUCION_AAP', 'RESOLUCION_AAC', 'RESOLUCION_DUP']


# ---------------------------------------------------------------------------
# C) Catálogo de fases: las finalizadoras son exactamente las del mapa
# ---------------------------------------------------------------------------

class TestCatalogoDeFases:

    def test_es_finalizadora_igual_a_fases_resolutoras(self, app_ctx):
        """En los dos sentidos: una finalizadora que el mapa no conoce se
        auditaría contra otra fase y ningún acto mediría su plazo contra ella;
        un código del mapa que no es finalizadora no cerraría nada."""
        from app.models.tipos_fases import TipoFase
        from app.services.actos_solicitud import FASES_RESOLUTORAS
        finalizadoras = {t.codigo for t in TipoFase.query.filter_by(es_finalizadora=True).all()}
        assert finalizadoras == FASES_RESOLUTORAS

    def test_el_guardian_de_arranque_no_avisa(self, app_ctx):
        from app.checks.catalogo_requerido import _validar_finalizadoras_con_regla
        assert _validar_finalizadoras_con_regla() == []

    def test_toda_finalizadora_tiene_notificacion_con_notificar(self, app_ctx):
        """Convención de D2: la NOTIFICAR del titular es la del trámite
        NOTIFICACION. Si una finalizadora nueva no lo tuviera, el plazo de su
        acto quedaría VENCIDO para siempre sin que nada lo explicara."""
        from app.models.fases_tramites import FaseTramite
        from app.models.tipos_fases import TipoFase
        from app.models.tramites_tareas import TramiteTarea
        from app.services.notificaciones import TRAMITE_NOTIFICACION_TITULAR

        sin_convencion = []
        for tf in TipoFase.query.filter_by(es_finalizadora=True).all():
            tramites = {ft.tipo_tramite.codigo: ft.tipo_tramite
                        for ft in FaseTramite.query.filter_by(tipo_fase_id=tf.id).all()}
            tramite = tramites.get(TRAMITE_NOTIFICACION_TITULAR)
            tareas = ({tt.tipo_tarea.codigo for tt in
                       TramiteTarea.query.filter_by(tipo_tramite_id=tramite.id).all()}
                      if tramite else set())
            if 'NOTIFICAR' not in tareas:
                sin_convencion.append(tf.codigo)
        assert sin_convencion == []


# ---------------------------------------------------------------------------
# D) El cumplimiento del acto
# ---------------------------------------------------------------------------

_F1 = date(2025, 3, 3)
_F2 = date(2025, 3, 10)
_F3 = date(2025, 3, 17)


def _notificar(arbol, fase, codigo_tramite, justificantes, tramite=None):
    """NOTIFICAR en `codigo_tramite` de `fase` con sus justificantes
    `[(tipo_doc, fecha, rol)]`. Devuelve la tarea."""
    tramite = tramite or arbol.tramite(fase, codigo_tramite)
    tarea = arbol.tarea(tramite, 'NOTIFICAR')
    exp_id = fase.solicitud.expediente_id
    arbol.vincular(tarea, arbol.documento(exp_id, 'RESOLUCION', f'930-{tarea.id}-res'),
                   'CONSUMIDO')
    for i, (tipo, fecha, rol) in enumerate(justificantes):
        arbol.vincular(tarea, arbol.documento(exp_id, tipo, f'930-{tarea.id}-{i}', fecha=fecha),
                       rol)
    return tarea


def _con_tipo(solicitud, siglas):
    from app.models.tipos_solicitudes import TipoSolicitud
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el tipo de solicitud {siglas!r}'
    solicitud.tipo_solicitud = tipo
    return solicitud


def _acto(solicitud, siglas):
    from app.services.actos_solicitud import actos_de
    return next(a for a in actos_de(solicitud) if a.siglas == siglas)


class TestCumplimiento:

    def test_fase_aun_no_creada(self, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        assert _acto(solicitud, 'AAP').documento_cumplimiento is None

    def test_fase_sin_notificacion(self, arbol_aislado):
        from app.services.notificaciones import documento_cumplimiento_fase
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        arbol_aislado.tramite(fase, 'ELABORACION')
        assert documento_cumplimiento_fase(fase) is None
        assert _acto(solicitud, 'AAP').documento_cumplimiento is None

    def test_notifica_cumple_con_la_puesta_a_disposicion(self, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        tarea = _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO'),
            ('JUSTIFICANTE_NOTIFICA', _F2, 'PRODUCIDO'),
        ])
        doc = _acto(solicitud, 'AAP').documento_cumplimiento
        assert doc is not None and doc.fecha_administrativa == _F1
        assert doc.tipo_doc.codigo == 'JUSTIFICANTE_NOTIFICA_DISPOSICION'
        assert any(v.documento is doc for v in tarea.vinculos_documento)

    def test_postal_cumple_con_el_primer_intento(self, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_POSTAL_1ER', _F1, 'CONSUMIDO'),
            ('JUSTIFICANTE_POSTAL', _F2, 'PRODUCIDO'),
        ])
        doc = _acto(solicitud, 'AAP').documento_cumplimiento
        assert doc.tipo_doc.codigo == 'JUSTIFICANTE_POSTAL_1ER'

    @pytest.mark.parametrize('tipo', ['JUSTIFICANTE_BANDEJA', 'JUSTIFICANTE_SIR'])
    def test_bandeja_y_sir_no_son_cumplimiento(self, arbol_aislado, tipo):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [(tipo, _F1, 'PRODUCIDO')])
        assert _acto(solicitud, 'AAP').documento_cumplimiento is None

    def test_la_fase_no_finalizadora_no_cumple_nada(self, arbol_aislado):
        """Aunque tenga un trámite NOTIFICACION con su justificante."""
        from app.services.notificaciones import documento_cumplimiento_fase
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO')])
        assert documento_cumplimiento_fase(fase) is None

    def test_en_resolucion_dup_solo_cuenta_el_tramite_notificacion(self, arbol_aislado):
        """Las otras NOTIFICAR de RESOLUCION_DUP tienen su propio plazo de
        cursar (40.2), pero no cierran el de resolver, aunque sean anteriores."""
        solicitud = _con_tipo(arbol_aislado.solicitud_propia(), 'DUP')
        fase = arbol_aislado.fase('RESOLUCION_DUP', solicitud=solicitud)
        for codigo in ('NOTIFICACION_INTERESADOS', 'NOTIFICACION_ORGANISMOS',
                       'REQUERIMIENTO_RBDA_DEFINITIVA'):
            _notificar(arbol_aislado, fase, codigo, [
                ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO')])
        acto = _acto(solicitud, 'DUP')
        assert acto.documento_cumplimiento is None

        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_POSTAL_1ER', _F3, 'CONSUMIDO')])
        # El builder crea el trámite por FK: la colección ya leída no lo ve
        arbol_aislado.db.session.expire(fase, ['tramites'])
        assert acto.documento_cumplimiento.fecha_administrativa == _F3

    def test_varias_notificar_del_titular_gana_la_mas_antigua(self, arbol_aislado):
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        primera = _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_POSTAL_1ER', _F2, 'CONSUMIDO')])
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO')],
            tramite=primera.tramite)
        assert _acto(solicitud, 'AAP').documento_cumplimiento.fecha_administrativa == _F1

    def test_aap_y_aac_en_una_resolucion_reciben_el_mismo_documento(self, arbol_aislado):
        solicitud = _con_tipo(arbol_aislado.solicitud_propia(), 'AAP+AAC')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO')])
        aap = _acto(solicitud, 'AAP').documento_cumplimiento
        aac = _acto(solicitud, 'AAC').documento_cumplimiento
        assert aap is not None and aap is aac

    def test_partida_cada_acto_con_su_fase(self, arbol_aislado):
        solicitud = _con_tipo(arbol_aislado.solicitud_propia(), 'AAP+AAC')
        fase_aap = arbol_aislado.fase('RESOLUCION_AAP', solicitud=solicitud)
        _notificar(arbol_aislado, fase_aap, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F1, 'CONSUMIDO')])
        assert _acto(solicitud, 'AAP').documento_cumplimiento.fecha_administrativa == _F1
        # La AAC ya va a RESOLUCION_AAC, que aún no existe: sin cumplimiento
        assert _acto(solicitud, 'AAC').documento_cumplimiento is None

    def test_justificante_sin_fecha_se_ignora(self):
        """Desde N1 el modelo no admite un justificante de notificación sin
        fecha (TIPOS_FECHA_OBLIGATORIA), así que se prueba sin BD: si alguno
        llegara (dato heredado), no cuenta."""
        from types import SimpleNamespace as N
        from app.services.notificaciones import documento_cumplimiento_fase

        def _doc(id_, fecha):
            return N(id=id_, fecha_administrativa=fecha,
                     tipo_doc=N(codigo='JUSTIFICANTE_POSTAL_1ER'))

        con_fecha = _doc(2, _F2)
        tarea = N(tipo_tarea=N(codigo='NOTIFICAR'), vinculos_documento=[
            N(rol='CONSUMIDO', documento=_doc(1, None)),
            N(rol='CONSUMIDO', documento=con_fecha),
        ])
        tramite = N(tipo_tramite=N(codigo='NOTIFICACION'), tareas=[tarea])
        fase = N(tipo_fase=N(es_finalizadora=True), tramites=[tramite])
        assert documento_cumplimiento_fase(fase) is con_fecha


class TestNotificarDelTitular:

    def test_la_notificar_del_tramite_notificacion_de_una_finalizadora(self, arbol_aislado):
        from app.services.notificaciones import es_notificar_del_titular
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        tramite = arbol_aislado.tramite(fase, 'NOTIFICACION')
        assert es_notificar_del_titular(arbol_aislado.tarea(tramite, 'NOTIFICAR')) is True
        # Otra tarea en el mismo trámite no es «la notificación»
        assert es_notificar_del_titular(arbol_aislado.tarea(tramite, 'ELABORAR')) is False

    @pytest.mark.parametrize('codigo_fase, codigo_tramite', [
        ('RESOLUCION_DUP', 'NOTIFICACION_INTERESADOS'),
        ('RESOLUCION_DUP', 'NOTIFICACION_ORGANISMOS'),
        ('RESOLUCION_DUP', 'REQUERIMIENTO_RBDA_DEFINITIVA'),
        ('ANALISIS_SOLICITUD', 'REQUERIMIENTO_SUBSANACION'),
        ('ANALISIS_SOLICITUD', 'NOTIFICACION'),
    ])
    def test_las_demas_no(self, arbol_aislado, codigo_fase, codigo_tramite):
        from app.services.notificaciones import es_notificar_del_titular
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase(codigo_fase, solicitud=solicitud)
        tarea = arbol_aislado.tarea(arbol_aislado.tramite(fase, codigo_tramite), 'NOTIFICAR')
        assert es_notificar_del_titular(tarea) is False
