"""
Tests issue #173 — _obtener_suspensiones: inferencia de intervalos de suspensión
(art. 22 LPACAP) desde el árbol documental de una Solicitud.

Reescrito en #788. Lo que cambia respecto de la versión anterior:

  - El ámbito es la SOLICITUD, no «el elemento evaluado». El art. 22 suspende «el
    plazo máximo legal para resolver un procedimiento y notificar la resolución»,
    que es el de la solicitud y ninguno más. Antes la función buscaba alrededor
    del elemento por duck-typing: la Solicitud salía siempre vacía (no tiene
    `.tramites`) y un Trámite se encontraba a SÍ MISMO entre sus hermanos.
  - Los dos extremos salen del mismo ESPERAR_PLAZO del trámite suspensor: el
    consumido abre, el producido cierra. Ya no se busca el NOTIFICAR hermano ni
    se encadenan tres tentativas de cierre.
  - Los intervalos se FUNDEN. Un reloj no se para dos veces.
  - El cómputo es (A, B]: la norma habla de lo que «medie entre» dos actos, que
    es una diferencia, no un recuento inclusivo.

Bloques:
  A) _obtener_suspensiones  — sin BD (mocks).
  B) Fusión de intervalos.
  C) Integración con _aplicar_suspensiones — la fecha_limite se extiende bien.
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
    return tr


def _fase(tramites):
    fase = MagicMock()
    fase.tramites = tramites
    return fase


def _solicitud(fases):
    sol = MagicMock()
    sol.fases = fases
    return sol


def _espera(inicio=None, fin=None):
    """ESPERAR_PLAZO con el justificante que abre y la respuesta que cierra."""
    return _tarea(
        'ESPERAR_PLAZO',
        doc_usado=_doc(inicio) if inicio else None,
        doc_producido=_doc(fin) if fin else None,
    )


HOY = date(2026, 5, 13)


# ---------------------------------------------------------------------------
# A) Tests unitarios de _obtener_suspensiones
# ---------------------------------------------------------------------------

class TestObtenerSuspensiones:

    def test_solicitud_sin_tramites_suspension(self):
        """Solicitud con solo trámites no suspensivos → lista vacía."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('ELABORACION', [])
        assert _obtener_suspensiones(_solicitud([_fase([tr])])) == []

    def test_tramite_sin_espera(self):
        """REQUERIMIENTO_SUBSANACION sin ESPERAR_PLAZO instanciado → vacío."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [
            _tarea('ELABORAR', doc_producido=_doc(date(2026, 3, 1))),
        ])
        assert _obtener_suspensiones(_solicitud([_fase([tr])])) == []

    def test_espera_sin_justificante(self):
        """ESPERAR_PLAZO sin documento consumido → sin fecha de inicio → vacío.

        Es el trámite preparado pero aún no notificado: no hay nada que suspender.
        """
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [_espera()])
        assert _obtener_suspensiones(_solicitud([_fase([tr])])) == []

    def test_requerimiento_subsanacion_sin_respuesta(self):
        """Notificado y sin contestar → suspensión abierta, marcada como tal."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [_espera(inicio=date(2026, 3, 10))])
        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_solicitud([_fase([tr])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 3, 10)
        assert resultado[0]['fecha_fin'] == HOY
        assert resultado[0]['abierto'] is True

    def test_requerimiento_subsanacion_con_respuesta(self):
        """Contestado → intervalo cerrado por el producido de su propia espera."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('REQUERIMIENTO_SUBSANACION', [
            _espera(inicio=date(2026, 3, 10), fin=date(2026, 3, 20)),
        ])
        resultado = _obtener_suspensiones(_solicitud([_fase([tr])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 3, 10)
        assert resultado[0]['fecha_fin'] == date(2026, 3, 20)
        assert resultado[0]['abierto'] is False

    def test_consulta_separata_con_respuesta(self):
        """CONSULTA_SEPARATA contestada → intervalo cerrado."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('CONSULTA_SEPARATA', [
            _espera(inicio=date(2026, 1, 15), fin=date(2026, 2, 20)),
        ])
        resultado = _obtener_suspensiones(_solicitud([_fase([tr])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 1, 15)
        assert resultado[0]['fecha_fin'] == date(2026, 2, 20)

    def test_solicitud_informe_sin_recepcion(self):
        """SOLICITUD_INFORME pedido sin recibir → suspensión abierta."""
        from app.services.plazos import _obtener_suspensiones
        tr = _tramite('SOLICITUD_INFORME', [_espera(inicio=date(2026, 2, 1))])
        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(_solicitud([_fase([tr])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == HOY
        assert resultado[0]['abierto'] is True

    def test_solicitud_informe_con_recepcion_hermano(self):
        """Receptor formalizado aparte: RECEPCION_INFORME posterior cierra."""
        from app.services.plazos import _obtener_suspensiones
        trigger = _tramite('SOLICITUD_INFORME', [_espera(inicio=date(2026, 2, 1))],
                           tramite_id=10)
        recepcion = _tramite('RECEPCION_INFORME',
                             [_tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 5)))],
                             tramite_id=15)

        resultado = _obtener_suspensiones(_solicitud([_fase([trigger, recepcion])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 2, 1)
        assert resultado[0]['fecha_fin'] == date(2026, 3, 5)
        assert resultado[0]['abierto'] is False

    def test_solicitud_compatibilidad_con_recepcion_dictamen(self):
        """SOLICITUD_COMPATIBILIDAD + RECEPCION_DICTAMEN posterior → cierre."""
        from app.services.plazos import _obtener_suspensiones
        trigger = _tramite('SOLICITUD_COMPATIBILIDAD', [_espera(inicio=date(2026, 1, 10))],
                           tramite_id=5)
        dictamen = _tramite('RECEPCION_DICTAMEN',
                            [_tarea('ANALIZAR', doc_usado=_doc(date(2026, 4, 8)))],
                            tramite_id=20)

        resultado = _obtener_suspensiones(_solicitud([_fase([trigger, dictamen])]))
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == date(2026, 4, 8)

    def test_hermano_anterior_ignorado(self):
        """Un RECEPCION_INFORME con id MENOR que el trigger no cierra nada."""
        from app.services.plazos import _obtener_suspensiones
        recepcion_anterior = _tramite('RECEPCION_INFORME',
                                      [_tarea('ANALIZAR', doc_usado=_doc(date(2026, 1, 1)))],
                                      tramite_id=5)
        trigger = _tramite('SOLICITUD_INFORME', [_espera(inicio=date(2026, 2, 1))],
                           tramite_id=10)

        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(
                _solicitud([_fase([recepcion_anterior, trigger])])
            )
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == HOY

    def test_rescate_por_hermano_acotado_a_la_fase(self):
        """#788: un RECEPCION_INFORME de OTRA fase no cierra la suspensión.

        Sin el acotado, el recorrido de la solicitud entera dejaba que cualquier
        recepción posterior del expediente cerrase una petición que no era suya.
        """
        from app.services.plazos import _obtener_suspensiones
        trigger = _tramite('SOLICITUD_INFORME', [_espera(inicio=date(2026, 2, 1))],
                           tramite_id=10)
        recepcion_ajena = _tramite('RECEPCION_INFORME',
                                   [_tarea('ANALIZAR', doc_usado=_doc(date(2026, 3, 5)))],
                                   tramite_id=15)

        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(
                _solicitud([_fase([trigger]), _fase([recepcion_ajena])])
            )
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == HOY, (
            'La recepción de otra fase no debe cerrar esta suspensión'
        )

    def test_recorre_todas_las_fases_de_la_solicitud(self):
        """Los disparadores viven en fases distintas de la finalizadora.

        Es justo el motivo por el que la inferencia estaba muerta: evaluada sobre
        la fase RESOLUCION, cuyos trámites son ELABORACION / NOTIFICACION /
        PUBLICACION, nunca encontraba ninguna causa.
        """
        from app.services.plazos import _obtener_suspensiones
        requerimiento = _tramite('REQUERIMIENTO_SUBSANACION',
                                 [_espera(inicio=date(2026, 1, 10), fin=date(2026, 1, 20))],
                                 tramite_id=1)
        separata = _tramite('CONSULTA_SEPARATA',
                            [_espera(inicio=date(2026, 3, 5), fin=date(2026, 3, 25))],
                            tramite_id=2)
        resolucion = _tramite('ELABORACION', [], tramite_id=3)

        resultado = _obtener_suspensiones(_solicitud([
            _fase([requerimiento]), _fase([separata]), _fase([resolucion]),
        ]))
        assert len(resultado) == 2
        assert [i['fecha_inicio'] for i in resultado] == [date(2026, 1, 10), date(2026, 3, 5)]


# ---------------------------------------------------------------------------
# B) Fusión de intervalos — un reloj no se para dos veces
# ---------------------------------------------------------------------------

class TestFusionIntervalos:

    def test_disjuntos_no_se_funden(self):
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 1, 10), 'abierto': False},
            {'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 2, 10), 'abierto': False},
        ])
        assert len(resultado) == 2

    def test_solapados_se_funden(self):
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 2, 15), 'abierto': False},
            {'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 3, 1), 'abierto': False},
        ])
        assert resultado == [
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 3, 1), 'abierto': False},
        ]

    def test_contiguos_se_funden(self):
        """Entre el cierre de uno y el día siguiente no corre plazo ninguno."""
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 1, 31), 'abierto': False},
            {'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 2, 10), 'abierto': False},
        ])
        assert len(resultado) == 1
        assert resultado[0]['fecha_fin'] == date(2026, 2, 10)

    def test_contenido_no_alarga_el_bloque(self):
        """Un intervalo dentro de otro no debe acortar el fin del que lo contiene."""
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 6, 1), 'abierto': False},
            {'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 3, 1), 'abierto': False},
        ])
        assert resultado == [
            {'fecha_inicio': date(2026, 1, 1), 'fecha_fin': date(2026, 6, 1), 'abierto': False},
        ]

    def test_cerrado_y_abierto_se_funden_juntos(self):
        """Caso del documento de diseño: separata cerrada + requerimiento vivo.

        Separata notificada el 1-feb y contestada el 1-abr; requerimiento
        notificado el 1-mar y sin contestar. En dos bolsas separadas serían
        2 + 2 = 4 meses; la verdad es la unión: 1-feb → hoy. Y el plazo lleva
        parado de forma continua desde el 1-feb, aunque la causa viva sea del
        1-mar.
        """
        from app.services.plazos import _fusionar_intervalos
        resultado = _fusionar_intervalos([
            {'fecha_inicio': date(2026, 2, 1), 'fecha_fin': date(2026, 4, 1), 'abierto': False},
            {'fecha_inicio': date(2026, 3, 1), 'fecha_fin': HOY, 'abierto': True},
        ])
        assert len(resultado) == 1
        assert resultado[0]['fecha_inicio'] == date(2026, 2, 1)
        assert resultado[0]['fecha_fin'] == HOY
        assert resultado[0]['abierto'] is True

    def test_fusion_en_el_recorrido_real(self):
        """La fusión no es solo del helper: _obtener_suspensiones ya la aplica."""
        from app.services.plazos import _obtener_suspensiones
        separata = _tramite('CONSULTA_SEPARATA',
                            [_espera(inicio=date(2026, 2, 1), fin=date(2026, 4, 1))],
                            tramite_id=1)
        requerimiento = _tramite('REQUERIMIENTO_SUBSANACION',
                                 [_espera(inicio=date(2026, 3, 1))],
                                 tramite_id=2)
        with patch('app.services.plazos._hoy', return_value=HOY):
            resultado = _obtener_suspensiones(
                _solicitud([_fase([separata]), _fase([requerimiento])])
            )
        assert len(resultado) == 1, f'Esperado un solo bloque fusionado: {resultado}'
        assert resultado[0]['fecha_inicio'] == date(2026, 2, 1)
        assert resultado[0]['abierto'] is True


# ---------------------------------------------------------------------------
# C) Integración: _aplicar_suspensiones extiende fecha_limite correctamente
# ---------------------------------------------------------------------------

class TestIntegracionSuspensionesEnPlazo:

    def test_suspension_activa_extiende_fecha_limite(self):
        """
        Plazo: 20 días hábiles desde 2026-01-12 → fecha_base = 2026-02-09.
        Suspensión: lun 2026-01-19 al lun 2026-01-26. Contada como (A, B] son 5
        días hábiles —del 20 al 26, sin contar el día del acto—, no 6.
        Fecha efectiva: 2026-02-09 + 5 hábiles = 2026-02-16.
        """
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 12), 20, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 2, 9)

        suspensiones = [{'fecha_inicio': date(2026, 1, 19), 'fecha_fin': date(2026, 1, 26)}]
        fecha_efectiva = _aplicar_suspensiones(fecha_base, suspensiones, inhabiles)
        assert fecha_efectiva == date(2026, 2, 16)

    def test_sin_suspensiones_no_cambia_fecha(self):
        """Sin suspensiones, _aplicar_suspensiones devuelve la misma fecha."""
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 3, 1), 10, 'DIAS_HABILES', inhabiles)
        assert _aplicar_suspensiones(fecha_base, [], inhabiles) == fecha_base

    def test_cierre_el_mismo_dia_no_suma_nada(self):
        """(A, B] con A == B son cero días: no medió nada entre los dos actos."""
        from app.services.plazos import _aplicar_suspensiones

        fecha_base = date(2026, 1, 12)
        suspensiones = [{'fecha_inicio': date(2026, 1, 8), 'fecha_fin': date(2026, 1, 8)}]
        assert _aplicar_suspensiones(fecha_base, suspensiones, frozenset()) == fecha_base

    def test_bloques_disjuntos_acumulan_sus_dias(self):
        """Dos bloques que la fusión dejó separados suman por separado."""
        from app.services.plazos import _aplicar_suspensiones, calcular_fecha_fin

        inhabiles = frozenset()
        fecha_base = calcular_fecha_fin(date(2026, 1, 5), 5, 'DIAS_HABILES', inhabiles)
        assert fecha_base == date(2026, 1, 12)  # 5 hábiles: 6,7,8,9,12

        suspensiones = [
            {'fecha_inicio': date(2026, 1, 7), 'fecha_fin': date(2026, 1, 8)},   # (7,8]  → 1 hábil
            {'fecha_inicio': date(2026, 1, 13), 'fecha_fin': date(2026, 1, 15)}, # (13,15] → 2 hábiles
        ]
        fecha_efectiva = _aplicar_suspensiones(fecha_base, suspensiones, inhabiles)
        assert fecha_efectiva == date(2026, 1, 15)  # lun 12 + 3 hábiles = jue 15
