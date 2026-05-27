"""
Tests issue #173 — _obtener_suspensiones: inferencia de intervalos de suspensión
desde el árbol documental de una Fase o Trámite.

Bloques:
  A) _obtener_suspensiones  — sin BD (mocks).
  B) Integración con _aplicar_suspensiones — la fecha_limite se extiende correctamente.
"""
from datetime import date
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers de construcción de mocks
# ---------------------------------------------------------------------------

def _doc(fecha_administrativa):
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    return doc


def _tarea(codigo_tipo, doc_usado=None, doc_producido=None):
    t = MagicMock()
    t.tipo_tarea = MagicMock()
    t.tipo_tarea.codigo = codigo_tipo
    # Vínculos N:M (ADR-010): el documento de entrada se expone como lista
    t.documentos_consumidos = [doc_usado] if doc_usado is not None else []
    t.documento_producido = doc_producido
    return t


def _tramite(codigo_tipo, tareas, tramite_id=1):
    tr = MagicMock()
    tr.id = tramite_id
    tr.tipo_tramite = MagicMock()
    tr.tipo_tramite.codigo = codigo_tipo
    tr.tareas = tareas
    tr.tramites = None   # los Trámites no tienen atributo tramites
    return tr


def _fase(tramites):
    fase = MagicMock()
    fase.tramites = tramites
    return fase


HOY = date(2026, 5, 13)


# ---------------------------------------------------------------------------
# A) Tests unitarios de _obtener_suspensiones
# ---------------------------------------------------------------------------

class TestObtenerSuspensiones:

    def test_fase_sin_tramites_suspension(self):
        """Fase con solo trámites no suspensivos → lista vacía."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('ELABORACION', [])
        assert _obtener_suspensiones(_fase([tr])) == []

    def test_tramite_no_notificado(self):
        """REQUERIMIENTO_SUBSANACION sin NOTIFICAR ejecutado → sin fecha_inicio → vacío."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [
            _tarea('ELABORAR', doc_producido=_doc(date(2026, 3, 1))),
        ])
        assert _obtener_suspensiones(_fase([tr])) == []

    def test_notificar_sin_documento(self):
        """NOTIFICAR sin documento_producido → no se puede extraer fecha_inicio → vacío."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=None)
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [notif])
        assert _obtener_suspensiones(_fase([tr])) == []

    def test_requerimiento_subsanacion_sin_respuesta(self):
        """REQUERIMIENTO_SUBSANACION notificado sin ANALIZAR → suspensión activa (fecha_fin=hoy)."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 3, 10)))
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [notif])
        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_fase([tr]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 3, 10)
        assert resultado[0]['fecha_fin'] == HOY

    def test_requerimiento_subsanacion_con_respuesta(self):
        """REQUERIMIENTO_SUBSANACION con ANALIZAR ejecutado → intervalo cerrado."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 3, 10)))
        anal = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 20)))
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [notif, anal])
        resultado = _obtener_suspensiones(_fase([tr]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 3, 10)
        assert resultado[0]['fecha_fin'] == date(2026, 3, 20)

    def test_consulta_separata_con_analizar(self):
        """CONSULTA_SEPARATA con ANALIZAR ejecutado → intervalo cerrado."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 1, 15)))
        anal = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 2, 20)))
        tr = _tramite('CONSULTA_SEPARATA', [notif, anal])
        resultado = _obtener_suspensiones(_fase([tr]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 1, 15)
        assert resultado[0]['fecha_fin'] == date(2026, 2, 20)

    def test_solicitud_informe_sin_recepcion(self):
        """SOLICITUD_INFORME notificado sin RECEPCION_INFORME → suspensión activa."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 2, 1)))
        esperar = _tarea('ESPERAR_PLAZO', doc_producido=None)
        tr = _tramite('SOLICITUD_INFORME', [notif, esperar])
        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_fase([tr]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 2, 1)
        assert resultado[0]['fecha_fin'] == HOY

    def test_solicitud_informe_con_documento_producido_esperar(self):
        """SOLICITUD_INFORME con ESPERAR_PLAZO.documento_producido (ADR-004) → cierre inline."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 2, 1)))
        esperar = _tarea('ESPERAR_PLAZO', doc_producido=_doc(date(2026, 3, 5)))
        tr = _tramite('SOLICITUD_INFORME', [notif, esperar])
        resultado = _obtener_suspensiones(_fase([tr]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == date(2026, 3, 5)

    def test_solicitud_informe_con_recepcion_hermano(self):
        """SOLICITUD_INFORME + RECEPCION_INFORME hermano posterior con ANALIZAR → cierre vía hermano."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 2, 1)))
        esperar = _tarea('ESPERAR_PLAZO', doc_producido=None)
        trigger = _tramite('SOLICITUD_INFORME', [notif, esperar], tramite_id=10)

        anal_rec = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 5)))
        recepcion = _tramite('RECEPCION_INFORME', [anal_rec], tramite_id=15)

        resultado = _obtener_suspensiones(_fase([trigger, recepcion]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 2, 1)
        assert resultado[0]['fecha_fin'] == date(2026, 3, 5)

    def test_solicitud_compatibilidad_con_recepcion_dictamen(self):
        """SOLICITUD_COMPATIBILIDAD + RECEPCION_DICTAMEN posterior → cierre vía hermano."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 1, 10)))
        esperar = _tarea('ESPERAR_PLAZO', doc_producido=None)
        trigger = _tramite('SOLICITUD_COMPATIBILIDAD', [notif, esperar], tramite_id=5)

        anal_dic = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 4, 8)))
        dictamen = _tramite('RECEPCION_DICTAMEN', [anal_dic], tramite_id=20)

        resultado = _obtener_suspensiones(_fase([trigger, dictamen]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 1, 10)
        assert resultado[0]['fecha_fin'] == date(2026, 4, 8)

    def test_hermano_anterior_ignorado(self):
        """Un RECEPCION_INFORME con id MENOR que el trigger no cierra la suspensión."""
        from app.services.plazos import _obtener_suspensiones
        anal_anterior = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 1, 1)))
        recepcion_anterior = _tramite('RECEPCION_INFORME', [anal_anterior], tramite_id=5)

        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 2, 1)))
        trigger = _tramite('SOLICITUD_INFORME', [notif], tramite_id=10)

        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_fase([recepcion_anterior, trigger]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == HOY  # el hermano anterior no cuenta

    def test_multiples_suspensiones(self):
        """Fase con dos trámites de suspensión → dos intervalos."""
        from app.services.plazos import _obtener_suspensiones
        notif1 = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 1, 10)))
        tr1 = _tramite('SOLICITUD_INFORME', [notif1], tramite_id=1)

        notif2 = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 2, 5)))
        anal2 = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 1)))
        tr2 = _tramite('CONSULTA_SEPARATA', [notif2, anal2], tramite_id=2)

        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_fase([tr1, tr2]))
        assert len(resultado) == 2
        assert resultado[1]['fecha_fin'] == date(2026, 3, 1)  # CONSULTA_SEPARATA cerrada

    def test_elemento_tramite_usa_tramites_de_su_fase(self):
        """Elemento es un Trámite → navega a su Fase y usa todos los hermanos."""
        from app.services.plazos import _obtener_suspensiones
        notif = _tarea('NOTIFICAR', doc_producido=_doc(date(2026, 3, 1)))
        anal = _tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 15)))
        trigger = _tramite('REQUERIMIENTO_SUBSANACION', [notif, anal], tramite_id=5)
        fase = _fase([trigger])
        trigger.fase = fase
        trigger.tramites = None  # el Trámite no tiene atributo tramites propio

        resultado = _obtener_suspensiones(trigger)
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == date(2026, 3, 15)

    def test_elemento_sin_tramites_ni_fase(self):
        """Elemento sin tramites ni tipo_tramite → lista vacía sin excepción."""
        from app.services.plazos import _obtener_suspensiones
        tarea = MagicMock(spec=[])  # spec vacío → AttributeError en cualquier acceso
        assert _obtener_suspensiones(tarea) == []


# ---------------------------------------------------------------------------
# B) Integración: _aplicar_suspensiones extiende fecha_limite correctamente
# ---------------------------------------------------------------------------

class TestIntegracionSuspensionesEnPlazo:

    def test_suspension_activa_extiende_fecha_limite(self):
        """
        Plazo: 20 días hábiles desde 2026-01-12 → fecha_base = 2026-02-09.
        Suspensión activa: 2026-01-19 al 2026-01-26 = 6 días hábiles (lun–lun).
        Fecha efectiva: 2026-02-09 + 6 hábiles = 2026-02-17.
        """
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 12), 20, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 2, 9)

        suspensiones = [{'fecha_inicio': date(2026, 1, 19), 'fecha_fin': date(2026, 1, 26)}]
        fecha_efectiva = _aplicar_suspensiones(fecha_base, suspensiones, inhabiles)
        assert fecha_efectiva == date(2026, 2, 17)

    def test_sin_suspensiones_no_cambia_fecha(self):
        """Sin suspensiones, _aplicar_suspensiones devuelve la misma fecha."""
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 3, 1), 10, 'DIAS_HABILES', inhabiles)
        assert _aplicar_suspensiones(fecha_base, [], inhabiles) == fecha_base

    def test_dos_suspensiones_se_acumulan(self):
        """Dos suspensiones independientes acumulan sus días."""
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 5), 5, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 1, 12)  # 5 hábiles: 6,7,8,9,12

        suspensiones = [
            {'fecha_inicio': date(2026, 1, 8), 'fecha_fin': date(2026, 1, 8)},   # 1 día hábil
            {'fecha_inicio': date(2026, 1, 13), 'fecha_fin': date(2026, 1, 14)}, # 2 días hábiles
        ]
        fecha_efectiva = _aplicar_suspensiones(fecha_base, suspensiones, inhabiles)
        assert fecha_efectiva == date(2026, 1, 15)  # 2026-01-12 + 3 hábiles = jue 15
