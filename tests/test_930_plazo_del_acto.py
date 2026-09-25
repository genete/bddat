"""#930 (N2 de ADR-049): el plazo de resolver es del acto; su cumplimiento se
calcula de la notificación al titular.

Bloques:
  A) El acto y la fase que lo resuelve (`actos_solicitud`, fuente única, D4).
  B) `informe_instruccion.codigos_fase_finalizadora` derivada de los actos.
  C) Catálogo de fases: `es_finalizadora` == `FASES_RESOLUTORAS`.
  D) El cumplimiento del acto: `documento_cumplimiento_fase` y
     `ActoSolicitud.documento_cumplimiento`; la convención de D2 en catálogo.
  E) La rama `calculado` de `plazos._resolver_campo_fecha` (D5).
  F) El plazo del acto: `obtener_estado_plazo_acto` y `plazos_de_la_solicitud`
     sobre las filas reales del catálogo (D11).
  G) Rendimiento: sobre el árbol ya cargado, solo catálogo e inhábiles (D14).
  H) Tras la migración `930_plazo_acto_calculado`: el catálogo real y el
     cumplimiento de extremo a extremo (D6, D7).

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
        llegara (dato heredado), no cuenta. Sobre el cálculo puro: la lectura
        del sello (#947) no es lo que se prueba aquí."""
        from types import SimpleNamespace as N
        from app.services.notificaciones import (
            calcular_documento_cumplimiento_fase as documento_cumplimiento_fase,
        )

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


# ---------------------------------------------------------------------------
# E) La rama `calculado` (D5)
# ---------------------------------------------------------------------------

class TestRamaCalculado:

    def test_propiedad_calculada_da_la_fecha_de_su_documento(self):
        from types import SimpleNamespace as N
        from app.services.plazos import _resolver_campo_fecha
        elemento = N(documento_cumplimiento=N(fecha_administrativa=_F1))
        assert _resolver_campo_fecha(elemento, {'calculado': 'documento_cumplimiento'}) == _F1

    def test_sobre_un_acto_real(self, arbol_aislado):
        from app.services.plazos import _resolver_campo_fecha
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', _F2, 'CONSUMIDO')])
        acto = _acto(solicitud, 'AAP')
        assert _resolver_campo_fecha(acto, {'calculado': 'documento_cumplimiento'}) == _F2

    def test_nombre_desconocido_none_y_aviso_sin_tocar_el_dato(self, caplog):
        """Aunque el elemento tenga un atributo con ese nombre: no se hace
        `getattr` con lo que no está en la lista cerrada. Y el señalador no se
        «cura»: es una lectura."""
        import logging
        from types import SimpleNamespace as N
        from app.services.plazos import _resolver_campo_fecha
        elemento = N(documento_solicitud=N(fecha_administrativa=_F1))
        senalador = {'calculado': 'documento_solicitud'}
        with caplog.at_level(logging.WARNING, logger='app.services.plazos'):
            assert _resolver_campo_fecha(elemento, senalador) is None
        assert senalador == {'calculado': 'documento_solicitud'}
        assert any('documento_solicitud' in r.getMessage() and 'desconocida' in r.getMessage()
                   for r in caplog.records)

    def test_elemento_sin_la_propiedad(self, arbol_aislado):
        from app.services.plazos import _resolver_campo_fecha
        solicitud = arbol_aislado.solicitud_propia()
        fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        tarea = arbol_aislado.tarea(arbol_aislado.tramite(fase, 'ANALISIS_DOCUMENTAL'),
                                    'ANALIZAR')
        for elemento in (solicitud, tarea):
            assert _resolver_campo_fecha(elemento, {'calculado': 'documento_cumplimiento'}) is None

    def test_fk_y_rol_siguen_igual(self, arbol_aislado):
        """Incluida la subida a `elemento.solicitud`, que es la que usa el acto
        para su disparo."""
        from app.services.plazos import _resolver_campo_fecha
        solicitud = arbol_aislado.solicitud_propia()
        fecha_solicitud = solicitud.documento_solicitud.fecha_administrativa
        fk = {'fk': 'documento_solicitud_id'}
        assert _resolver_campo_fecha(solicitud, fk) == fecha_solicitud
        assert _resolver_campo_fecha(_acto(solicitud, 'AAP'), fk) == fecha_solicitud

        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        tarea = _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_POSTAL', _F3, 'PRODUCIDO')])
        assert _resolver_campo_fecha(tarea, {'rol': 'PRODUCIDO'}) == _F3


# ---------------------------------------------------------------------------
# F) El plazo del acto (filas reales del catálogo, «hoy» fijado)
# ---------------------------------------------------------------------------

# Escrito de solicitud un martes. Los límites caen en día hábil sin festivo
# nacional ni andaluz, así que no hay prórroga que calcular: +1 mes → vie
# 4-abr, +3 meses → mié 4-jun, +6 meses → jue 4-sep.
_DISPARO = date(2025, 3, 4)
_LIMITE_1M = date(2025, 4, 4)
_LIMITE_3M = date(2025, 6, 4)
_LIMITE_6M = date(2025, 9, 4)


@pytest.fixture
def hoy_fijo(monkeypatch):
    """Fija el «hoy» del motor de plazos; devuelve el setter para moverlo."""
    def fijar(dia):
        monkeypatch.setattr('app.services.plazos._hoy', lambda: dia)
    return fijar


def _solicitud_desde(arbol, siglas, disparo=_DISPARO):
    solicitud = _con_tipo(arbol.solicitud_propia(), siglas)
    solicitud.documento_solicitud.fecha_administrativa = disparo
    arbol.db.session.flush()
    return solicitud


def _por_acto(plazos):
    return {p.acto: p for p in plazos}


class TestPlazoDelActo:

    def test_el_plazo_corre_durante_la_instruccion(self, arbol_aislado, hoy_fijo):
        """Sin fase resolutora todavía: el plazo existe y corre (H5)."""
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)

        hoy_fijo(date(2025, 4, 1))
        (aap,) = plazos_de_la_solicitud(solicitud)
        assert (aap.acto, aap.estado) == ('AAP', 'EN_PLAZO')
        assert aap.fecha_disparo == _DISPARO and aap.fecha_limite == _LIMITE_3M
        assert aap.fecha_cumplimiento is None
        assert (aap.fase_resolutora, aap.fase_resolutora_id) == ('RESOLUCION', None)

        hoy_fijo(date(2025, 6, 2))
        assert plazos_de_la_solicitud(solicitud)[0].estado == 'PROXIMO_VENCER'

    def test_sin_fase_y_pasado_el_limite_vencido(self, arbol_aislado, hoy_fijo):
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        hoy_fijo(date(2025, 7, 1))
        (aap,) = plazos_de_la_solicitud(solicitud)
        assert aap.estado == 'VENCIDO' and aap.dias_restantes < 0

    def test_el_estado_no_se_guarda(self, arbol_aislado, hoy_fijo):
        """Se calcula en cada lectura: cambia «hoy» y cambia el estado, sin
        nada que invalidar."""
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        hoy_fijo(date(2025, 4, 1))
        assert plazos_de_la_solicitud(solicitud)[0].estado == 'EN_PLAZO'
        hoy_fijo(date(2025, 7, 1))
        assert plazos_de_la_solicitud(solicitud)[0].estado == 'VENCIDO'

    def test_cada_acto_con_su_plazo(self, arbol_aislado, hoy_fijo):
        """El defecto de la v1: la DUP no se mide contra los 3 meses de la AAC,
        ni la AAT contra el mes de la AE."""
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))

        aac_dup = _por_acto(plazos_de_la_solicitud(
            _solicitud_desde(arbol_aislado, 'AAC+DUP')))
        assert aac_dup['AAC'].fecha_limite == _LIMITE_3M
        assert aac_dup['DUP'].fecha_limite == _LIMITE_6M
        assert (aac_dup['AAC'].fase_resolutora, aac_dup['DUP'].fase_resolutora) == (
            'RESOLUCION', 'RESOLUCION_DUP')

        ae_aat = plazos_de_la_solicitud(_solicitud_desde(arbol_aislado, 'AE_DEFINITIVA+AAT'))
        assert [(p.acto, p.plazo_valor, p.plazo_unidad, p.fecha_limite) for p in ae_aat] == [
            ('AE_DEFINITIVA', 1, 'MESES', _LIMITE_1M),
            ('AAT', 3, 'MESES', _LIMITE_3M),
        ]

    def test_acto_sin_fila_sin_plazo(self, arbol_aislado, hoy_fijo):
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        (interesado,) = plazos_de_la_solicitud(_solicitud_desde(arbol_aislado, 'INTERESADO'))
        assert (interesado.acto, interesado.estado) == ('INTERESADO', 'SIN_PLAZO')
        assert interesado.fase_resolutora == 'RECONOCIMIENTO_INTERESADO'
        assert interesado.fecha_limite is None

    def _requerimiento(self, arbol, solicitud, notificado, contestado=None):
        """Requerimiento de subsanación con su espera: notificado (CONSUMIDO) y,
        si se pasa fecha, contestado (PRODUCIDO)."""
        fase = arbol.fase('ANALISIS_SOLICITUD', solicitud=solicitud)
        espera = arbol.tarea(arbol.tramite(fase, 'REQUERIMIENTO_SUBSANACION'), 'ESPERAR_PLAZO')
        arbol.vincular(espera, arbol.documento(
            solicitud.expediente_id, 'JUSTIFICANTE_NOTIFICA', f'796-req-{espera.id}',
            fecha=notificado), 'CONSUMIDO')
        if contestado is not None:
            arbol.vincular(espera, arbol.documento(
                solicitud.expediente_id, 'JUSTIFICANTE_NOTIFICA', f'796-resp-{espera.id}',
                fecha=contestado), 'PRODUCIDO')
        return espera

    def test_el_requerimiento_vivo_suspende_todos_los_actos(self, arbol_aislado, hoy_fijo):
        """Art. 22.1.a (#796): el requerimiento cuelga de ANALISIS_SOLICITUD, fase
        de la solicitud entera, así que empuja el plazo de cada acto. Entre el
        20-mar (notificación) y hoy, 1-abr, median 8 días hábiles."""
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAP+AAC+DUP')
        self._requerimiento(arbol_aislado, solicitud, date(2025, 3, 20))

        plazos = _por_acto(plazos_de_la_solicitud(solicitud))
        for acto in ('AAP', 'AAC', 'DUP'):
            p = plazos[acto]
            assert p.suspendido is True
            assert p.suspendido_desde == date(2025, 3, 20)
            assert p.dias_suspendidos == 8
            assert p.fecha_limite > p.fecha_limite_sin_suspender
        assert plazos['AAP'].fecha_limite_sin_suspender == _LIMITE_3M
        assert plazos['AAP'].fecha_limite == date(2025, 6, 16)   # 8 hábiles después
        assert plazos['DUP'].fecha_limite_sin_suspender == _LIMITE_6M

    def test_el_requerimiento_contestado_deja_de_suspender_pero_cuenta(
            self, arbol_aislado, hoy_fijo):
        """Contestado el 25-mar el reloj vuelve a correr (`suspendido` es
        «ahora»), pero los 3 días hábiles parados ya empujaron el límite."""
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        self._requerimiento(arbol_aislado, solicitud, date(2025, 3, 20), date(2025, 3, 25))

        (aap,) = plazos_de_la_solicitud(solicitud)
        assert aap.suspendido is False and aap.suspendido_desde is None
        assert aap.dias_suspendidos == 3
        assert aap.fecha_limite > aap.fecha_limite_sin_suspender == _LIMITE_3M

    def test_sin_requerimiento_no_hay_suspension(self, arbol_aislado, hoy_fijo):
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAP+AAC+DUP')
        for p in plazos_de_la_solicitud(solicitud):
            assert p.suspendido is False and p.dias_suspendidos == 0
            assert p.fecha_limite_sin_suspender == p.fecha_limite

    def test_la_separata_no_suspende(self, arbol_aislado, hoy_fijo):
        """Art. 22.1.d (#796): exige acuerdo y dos comunicaciones que no se hacen;
        contar esa suspensión escondería un plazo vencido. La migración 796 apagó
        la marca en el catálogo y la separata ya no es causa."""
        from app.services.plazos import _causas_suspension, plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        fase = arbol_aislado.fase('CONSULTAS', solicitud=solicitud)
        espera = arbol_aislado.tarea(
            arbol_aislado.tramite(fase, 'CONSULTA_SEPARATA'), 'ESPERAR_PLAZO')
        arbol_aislado.vincular(espera, arbol_aislado.documento(
            solicitud.expediente_id, 'JUSTIFICANTE_NOTIFICA', f'796-sep-{espera.id}',
            fecha=date(2025, 3, 20)), 'CONSUMIDO')

        assert _causas_suspension(solicitud) == []
        (aap,) = plazos_de_la_solicitud(solicitud)
        assert aap.suspendido is False and aap.dias_suspendidos == 0
        assert aap.fecha_limite == _LIMITE_3M

    def test_fase_resolutora_id_cuando_existe(self, arbol_aislado, hoy_fijo):
        from app.services.plazos import plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAP+AAC+DUP')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        plazos = _por_acto(plazos_de_la_solicitud(solicitud))
        assert plazos['AAP'].fase_resolutora_id == fase.id
        assert plazos['AAC'].fase_resolutora_id == fase.id
        assert plazos['DUP'].fase_resolutora_id is None

    def test_un_acto_suelto_igual_que_en_la_lista(self, arbol_aislado, hoy_fijo):
        from app.services.actos_solicitud import actos_de
        from app.services.plazos import obtener_estado_plazo_acto, plazos_de_la_solicitud
        hoy_fijo(date(2025, 4, 1))
        solicitud = _solicitud_desde(arbol_aislado, 'AAC+DUP')
        assert [obtener_estado_plazo_acto(a) for a in actos_de(solicitud)] == \
            plazos_de_la_solicitud(solicitud)

    def test_camino_del_acto(self, arbol_aislado):
        """El camino del acto es el de su solicitud con el tipo atómico en lugar
        de la combinación; desde #931 lo compila `compilar_camino` con el nivel
        ACTO (antes, `_camino_acto` sobre el nivel SOLICITUD)."""
        from app.services.plazos import compilar_camino
        solicitud = _con_tipo(arbol_aislado.solicitud_propia(), 'AAP+AAC')
        expediente = solicitud.expediente.tipo_expediente.tipo
        assert compilar_camino(_acto(solicitud, 'AAC'), 'ACTO') == f'{expediente}/AAC'

    def test_sin_solicitud_lista_vacia(self):
        from app.services.plazos import plazos_de_la_solicitud
        assert plazos_de_la_solicitud(None) == []


# ---------------------------------------------------------------------------
# G) Rendimiento (D14; precedente #907)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('sellos', [(), ('cumplimiento',), ('cumplimiento', 'cierre')],
                         ids=['calculado', 'sellado', 'cerrada'])
def test_plazos_sobre_el_arbol_cargado_solo_catalogo_e_inhabiles(
        arbol_aislado, hoy_fijo, sellos):
    """Sobre el árbol cargado como lo carga `construir_arbol` (expediente con
    su tipo + `opciones_solicitud()`), los plazos de los actos —incluido
    recorrer la finalizadora notificada hasta el justificante y buscar las
    causas de suspensión (#796) por todo el árbol— cuestan tres sentencias: el
    catálogo de los actos, el de las tareas (las causas) y el calendario, cada
    uno una vez para todos los actos.

    También con el `CERT_CUMPLIMIENTO_FASE` emitido (#947): el certificado viene
    en la carga del árbol y el documento que cita, entre los vínculos de su
    tarea, así que leer el sello no añade ninguna. Y con la fase cerrada por su
    `CERT_CIERRE_FASE` (#956): el backref de la fase trae las dos filas, y el
    filtro por tipo es en memoria.

    Se reproduce la carga en vez de llamar a `construir_arbol` porque este
    devuelve un dict y suelta los objetos: el mapa de identidad es débil y
    todo se volvería a cargar en perezoso, cosa que no pasará cuando #922
    pinte las barras dentro del propio árbol. `expunge_all` por lo mismo que
    en #928: una petición real parte de una sesión limpia."""
    from sqlalchemy.orm import joinedload

    from app import db
    from app.models.expedientes import Expediente
    from app.models.solicitudes import Solicitud
    from app.services.arbol_expediente import opciones_solicitud
    from app.services.plazos import plazos_de_la_solicitud
    from tests.conftest import contar_consultas

    hoy_fijo(date(2025, 4, 1))
    solicitud = _solicitud_desde(arbol_aislado, 'AAP+AAC+DUP')
    fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
    tarea = _notificar(arbol_aislado, fase, 'NOTIFICACION', [
        ('JUSTIFICANTE_NOTIFICA_DISPOSICION', date(2025, 3, 20), 'CONSUMIDO'),
        ('JUSTIFICANTE_NOTIFICA', date(2025, 3, 24), 'PRODUCIDO'),
    ])
    if 'cumplimiento' in sellos:
        _sellar(arbol_aislado, fase, tarea)
    if 'cierre' in sellos:
        _cerrar_con_certificado(arbol_aislado, fase)
    expediente_id = solicitud.expediente_id

    def cargar_arbol():
        db.session.flush()
        db.session.expunge_all()
        expediente = (Expediente.query.options(joinedload(Expediente.tipo_expediente))
                      .get(expediente_id))
        solicitudes = (Solicitud.query.filter_by(expediente_id=expediente_id)
                       .options(*opciones_solicitud()).all())
        return expediente, solicitudes

    def arbol_y_plazos():
        _expediente, solicitudes = cargar_arbol()
        (sol,) = solicitudes
        plazos = plazos_de_la_solicitud(sol)
        assert [p.acto for p in plazos] == ['AAP', 'AAC', 'DUP']
        assert plazos[0].fecha_cumplimiento == date(2025, 3, 20)

    assert contar_consultas(arbol_y_plazos) - contar_consultas(cargar_arbol) == 3


def _sellar(arbol, fase, tarea):
    """El certificado de cumplimiento a pelo, sin el servicio (que pide usuario
    para la bitácora): aquí solo importa que exista al cargar el árbol."""
    from app.models.certificados import Certificado
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    citado = next(v.documento for v in tarea.vinculos_documento
                  if v.documento.tipo_doc.codigo == 'JUSTIFICANTE_NOTIFICA_DISPOSICION')
    tipo = TipoDocumento.query.filter_by(codigo='CERT_CUMPLIMIENTO_FASE').first()
    assert tipo is not None, 'la migración 947 debe traer CERT_CUMPLIMIENTO_FASE'
    doc = Documento(expediente_id=fase.solicitud.expediente_id, tipo_doc_id=tipo.id,
                    url='bddat://certificados/0')
    arbol.db.session.add(doc)
    arbol.db.session.flush()
    from datetime import UTC, datetime
    arbol.db.session.add(Certificado(documento_id=doc.id, tipo='CERT_CUMPLIMIENTO_FASE',
                                     fase_id=fase.id, datos={'documento_id': citado.id},
                                     generado_en=datetime.now(UTC).replace(tzinfo=None)))
    arbol.db.session.flush()


def _cerrar_con_certificado(arbol, fase):
    """El certificado de cierre a pelo (#956), por el mismo motivo que `_sellar`:
    solo importa que la fase quede cerrada por él al cargar el árbol."""
    from datetime import UTC, datetime

    from app.models.certificados import Certificado
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    tipo = TipoDocumento.query.filter_by(codigo='CERT_CIERRE_FASE').first()
    assert tipo is not None, 'la migración 956 debe traer CERT_CIERRE_FASE'
    doc = Documento(expediente_id=fase.solicitud.expediente_id, tipo_doc_id=tipo.id,
                    url='bddat://certificados/0')
    arbol.db.session.add(doc)
    arbol.db.session.flush()
    arbol.db.session.add(Certificado(documento_id=doc.id, tipo='CERT_CIERRE_FASE',
                                     fase_id=fase.id, datos={'bloques': []},
                                     generado_en=datetime.now(UTC).replace(tzinfo=None)))
    fase.documento_resultado_id = doc.id
    arbol.db.session.flush()


# ---------------------------------------------------------------------------
# H) Tras la migración 930: catálogo real y cumplimiento de extremo a extremo
# ---------------------------------------------------------------------------

_CALCULADO = {'calculado': 'documento_cumplimiento'}
_ATOMICAS = {'ANY/AAP', 'ANY/AAC', 'ANY/DUP', 'ANY/AAT',
             'ANY/AE_PROVISIONAL', 'ANY/AE_DEFINITIVA', 'ANY/CIERRE'}


class TestCatalogoReal:

    def test_todo_calculado_esta_en_la_lista_cerrada(self, app_ctx):
        """La red de D5/D7 en lugar de un CHECK: cualquier `calculado` del
        catálogo, en cualquiera de los dos señaladores, es un nombre que la
        lectura sabe resolver."""
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.services.plazos import CALCULADOS
        fuera = [
            (fila.camino, senalador)
            for fila in CatalogoPlazo.query.all()
            for senalador in (fila.campo_fecha, fila.campo_fecha_cumplimiento)
            if senalador and 'calculado' in senalador
            and senalador['calculado'] not in CALCULADOS
        ]
        assert fuera == []

    def test_las_siete_filas_atomicas_se_cumplen_calculadas(self, app_ctx):
        """Tras #931 son las únicas filas del plazo de resolver, con nivel ACTO."""
        from app.models.catalogo_plazos import CatalogoPlazo
        filas = CatalogoPlazo.query.filter_by(tipo_elemento='ACTO').all()
        atomicas = {f.camino: f.campo_fecha_cumplimiento for f in filas}
        assert set(atomicas) == _ATOMICAS
        assert all(cc == _CALCULADO for cc in atomicas.values()), atomicas

    def test_sin_combinaciones_ni_fases_y_tareas_sin_cambio(self, app_ctx):
        """#931 retiró las 4 combinaciones y las 3 filas de fase que N2 había
        dejado sin tocar; las 14 de tarea siguen con su vínculo (13) o sin
        señalador (el tablón)."""
        from app.models.catalogo_plazos import CatalogoPlazo
        filas = CatalogoPlazo.query.all()
        assert [f.camino for f in filas if '+' in f.camino and f.tipo_elemento != 'TAREA'] == []
        assert {f.tipo_elemento for f in filas} == {'ACTO', 'TAREA'}

        tareas = [f for f in filas if f.tipo_elemento == 'TAREA']
        con_rol = [f for f in tareas if (f.campo_fecha_cumplimiento or {}).get('rol')]
        sin_senalador = [f for f in tareas if f.campo_fecha_cumplimiento is None]
        assert (len(tareas), len(con_rol), len(sin_senalador)) == (14, 13, 1)


class TestCumplimientoDeExtremoAExtremo:

    def test_la_aac_cumple_y_la_dup_sigue_en_plazo(self, arbol_aislado, hoy_fijo):
        """El caso que tumbó la v1: en AAC+DUP, notificada la RESOLUCION (la
        AAC) el mes 2 y sin resolver la DUP el mes 5, la AAC está cumplida en
        plazo y la DUP sigue corriendo contra sus 6 meses, no contra 3."""
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AAC+DUP')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', date(2025, 5, 5), 'CONSUMIDO')])

        hoy_fijo(date(2025, 8, 1))
        plazos = _por_acto(plazos_de_la_solicitud(solicitud))
        assert plazos['AAC'].estado == 'CUMPLIDO'
        assert plazos['AAC'].fecha_cumplimiento == date(2025, 5, 5)
        assert plazos['AAC'].cumplido_fuera_de_plazo is False
        assert plazos['AAC'].dias_restantes is None
        assert plazos['DUP'].estado == 'EN_PLAZO'
        assert plazos['DUP'].fecha_cumplimiento is None

    def test_notificada_tarde_cumplido_fuera_de_plazo(self, arbol_aislado, hoy_fijo):
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AAP')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_POSTAL_1ER', date(2025, 6, 20), 'CONSUMIDO')])

        hoy_fijo(date(2025, 7, 1))
        (aap,) = plazos_de_la_solicitud(solicitud)
        assert aap.estado == 'CUMPLIDO'
        assert aap.fecha_limite == _LIMITE_3M
        assert aap.cumplido_fuera_de_plazo is True

    def test_una_notificacion_cumple_dos_plazos_cada_uno_contra_el_suyo(
            self, arbol_aislado, hoy_fijo):
        """AE_DEFINITIVA+AAT resueltas en una RESOLUCION: el mismo documento
        cierra el mes de la AE (tarde) y los 3 meses de la AAT (a tiempo)."""
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'AE_DEFINITIVA+AAT')
        fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)
        _notificar(arbol_aislado, fase, 'NOTIFICACION', [
            ('JUSTIFICANTE_NOTIFICA_DISPOSICION', date(2025, 5, 5), 'CONSUMIDO')])

        hoy_fijo(date(2025, 7, 1))
        plazos = _por_acto(plazos_de_la_solicitud(solicitud))
        assert {p.estado for p in plazos.values()} == {'CUMPLIDO'}
        assert plazos['AE_DEFINITIVA'].cumplido_fuera_de_plazo is True
        assert plazos['AAT'].cumplido_fuera_de_plazo is False

    def test_sin_notificacion_al_titular_vencido_aunque_haya_otras(
            self, arbol_aislado, hoy_fijo):
        """La RESOLUCION_DUP con organismos e interesados notificados pero sin
        la notificación al titular: el plazo de la DUP no se cumple."""
        from app.services.plazos import plazos_de_la_solicitud
        solicitud = _solicitud_desde(arbol_aislado, 'DUP')
        fase = arbol_aislado.fase('RESOLUCION_DUP', solicitud=solicitud)
        for codigo in ('NOTIFICACION_ORGANISMOS', 'NOTIFICACION_INTERESADOS'):
            _notificar(arbol_aislado, fase, codigo, [
                ('JUSTIFICANTE_NOTIFICA_DISPOSICION', date(2025, 5, 5), 'CONSUMIDO')])

        hoy_fijo(date(2025, 10, 1))
        (dup,) = plazos_de_la_solicitud(solicitud)
        assert dup.estado == 'VENCIDO' and dup.fecha_cumplimiento is None
