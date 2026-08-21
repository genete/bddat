"""
Tests issue #778 — plazos y suspensiones se miden con el mismo mecanismo (ADR-041).

Un plazo produce cuatro fechas —disparo, vencimiento, cumplimiento y parada, la
primera de cumplimiento, vencimiento u hoy— y de ellas sale el estado. La misma
medida responde a «cómo va esta espera» y, aplicada a las tareas suspensoras de
una solicitud, al intervalo que hay que descontarle a su plazo.

Bloques:
  A) Los cuatro finales de una espera, con fechas fijas.
  B) El tope por construcción — el defecto que abrió este issue.
  C) El plazo de la solicitud: qué suspende, qué no, y la fusión en el recorrido.
  D) Con BD: el catálogo cumple los invariantes del rediseño.
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers de construcción de mocks
# ---------------------------------------------------------------------------

def _doc(fecha_administrativa=None, tipo_documento=None):
    doc = MagicMock()
    doc.fecha_administrativa = fecha_administrativa
    doc.tipo_doc = MagicMock(codigo=tipo_documento) if tipo_documento else None
    return doc


def _tarea(codigo='ESPERAR_PLAZO', consumidos=(), producido=None,
           tramite_codigo='REQUERIMIENTO_SUBSANACION',
           fase_codigo='ANALISIS_SOLICITUD', siglas='AAP',
           tipo_expediente='Distribucion'):
    """Tarea con ascendencia de strings reales, para que compile el camino."""
    t = MagicMock()
    t.tipo_tarea = MagicMock(codigo=codigo)
    t.documentos_consumidos = list(consumidos)
    t.documento_producido = producido
    t.tramite.tipo_tramite = MagicMock(codigo=tramite_codigo)
    t.tramite.fase.tipo_fase = MagicMock(codigo=fase_codigo)
    t.tramite.fase.solicitud.tipo_solicitud = MagicMock(siglas=siglas)
    t.tramite.fase.solicitud.expediente.tipo_expediente = MagicMock(tipo=tipo_expediente)
    return t


def _entrada(camino, campo_fecha, cumplimiento=None, suspende=False,
             plazo_valor=10, plazo_unidad='DIAS_HABILES', orden=10, entrada_id=1,
             efecto='SIN_EFECTO_AUTOMATICO'):
    e = MagicMock()
    e.id = entrada_id
    e.orden = orden
    e.camino = camino
    e.campo_fecha = campo_fecha
    e.campo_fecha_cumplimiento = cumplimiento
    e.suspende_plazo_solicitud = suspende
    e.condiciones = []
    e.plazo_valor = plazo_valor
    e.plazo_unidad = plazo_unidad
    e.efecto_plazo.codigo = efecto
    return e


def _entrada_subsanacion(**kwargs):
    """La del art. 68.1: 10 días hábiles, suspende, cierra con su producido."""
    kwargs.setdefault('cumplimiento', {'rol': 'PRODUCIDO'})
    kwargs.setdefault('suspende', True)
    return _entrada(
        'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO',
        {'rol': 'CONSUMIDO'},
        efecto='CADUCIDAD_PROCEDIMIENTO',
        **kwargs,
    )


def _entrada_solicitud(**kwargs):
    """El plazo para resolver y notificar de una AAP: 3 meses (art. 128)."""
    kwargs.setdefault('cumplimiento', {'fk': 'documento_cierre_id'})
    return _entrada(
        'ANY/AAP',
        {'fk': 'documento_solicitud_id'},
        plazo_valor=3, plazo_unidad='MESES',
        efecto='SILENCIO_DESESTIMATORIO',
        **kwargs,
    )


def _solicitud(disparo=None, cierre=None, tareas_por_fase=()):
    sol = MagicMock()
    sol.tipo_solicitud = MagicMock(siglas='AAP')
    sol.expediente.tipo_expediente = MagicMock(tipo='Distribucion')
    sol.documento_solicitud = _doc(disparo) if disparo else None
    sol.documento_cierre = _doc(cierre) if cierre else None
    fases = []
    for tareas in tareas_por_fase:
        tramites = {}
        for t in tareas:
            tramites.setdefault(id(t.tramite), t.tramite)
            t.tramite.tareas = [x for x in tareas if x.tramite is t.tramite]
        fase = MagicMock()
        fase.tramites = list(tramites.values())
        fases.append(fase)
    sol.fases = fases
    return sol


def _catalogo(por_nivel: dict):
    """Parchea la carga del catálogo: {'TAREA': [...], 'SOLICITUD': [...]}.

    Se parchea `_cargar_entradas` y no la query: el punto de corte es el que el
    servicio expone a propósito para poder medir muchas tareas con una sola
    consulta, y deja los tests legibles.
    """
    return patch(
        'app.services.plazos._cargar_entradas',
        side_effect=lambda nivel: list(por_nivel.get(nivel, [])),
    )


def _sin_bd(hoy):
    """Congela `hoy` y deja el calendario de inhábiles vacío (solo findes)."""
    return (
        patch('app.services.plazos._hoy', return_value=hoy),
        patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()),
    )


# ---------------------------------------------------------------------------
# A) Los cuatro finales de una espera
# ---------------------------------------------------------------------------
#
# Requerimiento de subsanación notificado el lunes 12-ene-2026, 10 días hábiles:
# vence el lunes 26-ene-2026.

NOTIFICACION = date(2026, 1, 12)
VENCIMIENTO = date(2026, 1, 26)


def _medir_espera(producido=None, hoy=date(2026, 1, 20)):
    from app.services.plazos import obtener_estado_plazo_tarea

    tarea = _tarea(consumidos=[_doc(NOTIFICACION)], producido=producido)
    congela_hoy, sin_inhabiles = _sin_bd(hoy)
    with _catalogo({'TAREA': [_entrada_subsanacion()]}), congela_hoy, sin_inhabiles:
        return obtener_estado_plazo_tarea(tarea)


class TestLosCuatroFinales:

    def test_el_vencimiento_sale_del_catalogo(self):
        assert _medir_espera().fecha_limite == VENCIMIENTO

    def test_contesta_a_tiempo(self):
        """Gana el cumplimiento: llegó lo que se esperaba, y con margen."""
        ep = _medir_espera(producido=_doc(date(2026, 1, 19)))
        assert ep.estado == 'CUMPLIDO'
        assert ep.fecha_cumplimiento == date(2026, 1, 19)
        assert ep.fecha_parada == date(2026, 1, 19)
        assert ep.cumplido_fuera_de_plazo is False
        assert ep.dias_restantes is None

    def test_contesta_tarde(self):
        """CUMPLIDO igualmente: «cumplido fuera de plazo» no es un valor del
        vocabulario, se lee comparando las dos fechas (ADR-041 §C)."""
        ep = _medir_espera(producido=_doc(date(2026, 2, 10)), hoy=date(2026, 2, 12))
        assert ep.estado == 'CUMPLIDO'
        assert ep.cumplido_fuera_de_plazo is True
        assert ep.fecha_parada == VENCIMIENTO, (
            'La parada nunca pasa del vencimiento: el plazo dejó de correr ahí, '
            'aunque la respuesta llegara después'
        )

    def test_no_contesta_y_aun_no_vence(self):
        ep = _medir_espera(hoy=date(2026, 1, 20))
        assert ep.estado == 'PROXIMO_VENCER'   # quedan 5 hábiles: 20,21,22,23,26
        assert ep.dias_restantes == 5
        assert ep.fecha_parada == date(2026, 1, 20), 'gana hoy: el plazo sigue corriendo'

    def test_no_contesta_y_ya_vencio(self):
        """El caso que este issue vino a arreglar."""
        ep = _medir_espera(hoy=date(2026, 3, 2))
        assert ep.estado == 'VENCIDO'
        assert ep.fecha_parada == VENCIMIENTO
        assert ep.dias_restantes < 0

    def test_en_plazo_holgado(self):
        ep = _medir_espera(hoy=date(2026, 1, 13))
        assert ep.estado == 'EN_PLAZO'

    def test_sin_disparo_no_hay_plazo(self):
        """Trámite preparado pero aún no notificado: no hay nada que medir."""
        from app.services.plazos import obtener_estado_plazo_tarea

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 1, 20))
        with _catalogo({'TAREA': [_entrada_subsanacion()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_tarea(_tarea())
        assert ep.estado == 'SIN_PLAZO'
        assert ep.fecha_limite is None

    def test_sin_senalador_de_cumplimiento_nunca_llega_a_cumplido(self):
        """El caso del tablón (#416): disparo y cierre son el mismo documento, la
        entrada se queda sin señalador y VENCIDO se lee como «se completó»."""
        from app.services.plazos import obtener_estado_plazo_tarea

        entrada = _entrada(
            'ANY/ANY/ANY/TABLON_AYUNTAMIENTOS/ESPERAR_PLAZO',
            {'rol': 'PRODUCIDO', 'tipo_documento': 'CERT_PLAZO_TABLON'},
            cumplimiento=None, plazo_valor=30, plazo_unidad='DIAS_NATURALES',
        )
        tarea = _tarea(tramite_codigo='TABLON_AYUNTAMIENTOS',
                       fase_codigo='INFORMACION_PUBLICA',
                       producido=_doc(date(2026, 1, 12), 'CERT_PLAZO_TABLON'))

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 3, 2))
        with _catalogo({'TAREA': [entrada]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_tarea(tarea)

        assert ep.estado == 'VENCIDO'
        assert ep.fecha_cumplimiento is None


# ---------------------------------------------------------------------------
# B) El tope existe por construcción
# ---------------------------------------------------------------------------

class TestTopePorConstruccion:

    def test_la_parada_no_pasa_del_vencimiento(self):
        """Sin respuesta, la parada se queda en el vencimiento pase el tiempo que
        pase. Antes de #778 el cierre se fijaba en «hoy» y se recalculaba cada
        día, así que la suspensión crecía indefinidamente."""
        paradas = {
            _medir_espera(hoy=VENCIMIENTO + timedelta(days=n)).fecha_parada
            for n in (1, 30, 365)
        }
        assert paradas == {VENCIMIENTO}

    def test_la_fecha_limite_de_la_solicitud_no_se_aleja(self):
        """No regresión del defecto de #778, medido donde dolía: un
        REQUERIMIENTO_SUBSANACION notificado y sin contestar mantiene la fecha
        límite de la solicitud, se calcule hoy o dentro de un año."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        limites = set()
        for dias in (0, 60, 365):
            espera = _tarea(consumidos=[_doc(NOTIFICACION)])
            solicitud = _solicitud(disparo=date(2026, 1, 2), tareas_por_fase=[[espera]])
            congela_hoy, sin_inhabiles = _sin_bd(date(2026, 2, 1) + timedelta(days=dias))
            with _catalogo({'TAREA': [_entrada_subsanacion()],
                            'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
                limites.add(obtener_estado_plazo_solicitud(solicitud).fecha_limite)

        assert len(limites) == 1, f'La fecha límite se mueve con el tiempo: {limites}'

    def test_la_solicitud_acaba_venciendo(self):
        """Y por tanto el silencio llega a producirse y el semáforo avisa."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        espera = _tarea(consumidos=[_doc(NOTIFICACION)])
        solicitud = _solicitud(disparo=date(2026, 1, 2), tareas_por_fase=[[espera]])
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 9, 1))
        with _catalogo({'TAREA': [_entrada_subsanacion()],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.estado == 'VENCIDO'
        assert ep.efecto == 'SILENCIO_DESESTIMATORIO'
        assert ep.suspendido is False, 'una espera vencida ya no para el reloj'


# ---------------------------------------------------------------------------
# C) El plazo de la solicitud
# ---------------------------------------------------------------------------

class TestPlazoDeLaSolicitud:

    def test_sin_causas_el_plazo_es_el_del_catalogo(self):
        from app.services.plazos import obtener_estado_plazo_solicitud

        solicitud = _solicitud(disparo=date(2026, 1, 12))
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 2, 2))
        with _catalogo({'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.fecha_limite == date(2026, 4, 13)   # 12-ene + 3 meses → dom 12 → lun 13
        assert ep.dias_suspendidos == 0
        assert ep.fecha_limite_sin_suspender == ep.fecha_limite

    def test_una_suspension_viva_empuja_y_se_declara(self):
        from app.services.plazos import obtener_estado_plazo_solicitud

        espera = _tarea(consumidos=[_doc(NOTIFICACION)])
        solicitud = _solicitud(disparo=date(2026, 1, 2), tareas_por_fase=[[espera]])
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 1, 20))
        with _catalogo({'TAREA': [_entrada_subsanacion()],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.suspendido is True
        assert ep.suspendido_desde == NOTIFICACION
        assert ep.dias_suspendidos == 6            # (12-ene, 20-ene] hábiles
        assert ep.fecha_limite > ep.fecha_limite_sin_suspender

    def test_un_plazo_que_no_suspende_no_empuja_nada(self):
        """La información pública y los traslados al peticionario (arts. 126 /
        127.3 RD 1955/2000) tienen plazo y NO suspenden: corren dentro del plazo
        de la solicitud y lo consumen."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        traslado = _tarea(tramite_codigo='CONSULTA_TRASLADO_TITULAR',
                          fase_codigo='CONSULTAS',
                          consumidos=[_doc(NOTIFICACION)])
        entrada = _entrada('ANY/ANY/ANY/CONSULTA_TRASLADO_TITULAR/ESPERAR_PLAZO',
                           {'rol': 'CONSUMIDO'}, cumplimiento={'rol': 'PRODUCIDO'},
                           suspende=False, plazo_valor=15)
        solicitud = _solicitud(disparo=date(2026, 1, 2), tareas_por_fase=[[traslado]])

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 1, 20))
        with _catalogo({'TAREA': [entrada],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.suspendido is False
        assert ep.dias_suspendidos == 0
        assert ep.fecha_limite == ep.fecha_limite_sin_suspender

    def test_un_plazo_sin_fila_no_suspende(self):
        """Corolario de ADR-041 §E: sin entrada en el catálogo no hay cómputo.

        Es el caso real de SOLICITUD_COMPATIBILIDAD, que estaba en la lista del
        código y nunca tuvo fila: el sistema lo pintaba como plazo no configurado
        y a la vez lo usaba para mover la fecha límite de la solicitud.
        """
        from app.services.plazos import obtener_estado_plazo_solicitud

        compatibilidad = _tarea(tramite_codigo='SOLICITUD_COMPATIBILIDAD',
                                fase_codigo='COMPATIBILIDAD_AMBIENTAL',
                                consumidos=[_doc(NOTIFICACION)])
        solicitud = _solicitud(disparo=date(2026, 1, 2),
                               tareas_por_fase=[[compatibilidad]])

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 1, 20))
        with _catalogo({'TAREA': [_entrada_subsanacion()],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.suspendido is False
        assert ep.dias_suspendidos == 0

    def test_causas_solapadas_se_cuentan_una_vez(self):
        """Separata contestada + requerimiento vivo que se solapan: la unión, no
        la suma. Un reloj no se para dos veces (art. 22, en singular)."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        separata = _tarea(tramite_codigo='CONSULTA_SEPARATA', fase_codigo='CONSULTAS',
                          consumidos=[_doc(date(2026, 2, 2))],
                          producido=_doc(date(2026, 3, 2)))
        requerimiento = _tarea(consumidos=[_doc(date(2026, 2, 16))])
        entrada_separata = _entrada(
            'ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO', {'rol': 'CONSUMIDO'},
            cumplimiento={'rol': 'PRODUCIDO'}, suspende=True,
            plazo_valor=30, entrada_id=2,
        )
        solicitud = _solicitud(disparo=date(2026, 1, 2),
                               tareas_por_fase=[[separata], [requerimiento]])

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 3, 10))
        with _catalogo({'TAREA': [_entrada_subsanacion(), entrada_separata],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        # Separata: (2-feb, 2-mar]. Requerimiento: (16-feb, 2-mar] — vence el 2-mar
        # (10 hábiles desde el 16-feb) y no llega a hoy. La unión es (2-feb, 2-mar]:
        # 20 días hábiles, no 20 + 10.
        assert ep.dias_suspendidos == 20
        assert ep.suspendido is False

    def test_suspendido_desde_es_el_inicio_del_bloque_continuo(self):
        """Puede ser anterior a la causa viva más antigua: lo que interesa es
        desde cuándo lleva el plazo parado sin interrupción."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        separata = _tarea(tramite_codigo='CONSULTA_SEPARATA', fase_codigo='CONSULTAS',
                          consumidos=[_doc(date(2026, 2, 2))],
                          producido=_doc(date(2026, 3, 2)))
        requerimiento = _tarea(consumidos=[_doc(date(2026, 2, 27))])
        entrada_separata = _entrada(
            'ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO', {'rol': 'CONSUMIDO'},
            cumplimiento={'rol': 'PRODUCIDO'}, suspende=True,
            plazo_valor=30, entrada_id=2,
        )
        solicitud = _solicitud(disparo=date(2026, 1, 2),
                               tareas_por_fase=[[separata], [requerimiento]])

        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 3, 5))
        with _catalogo({'TAREA': [_entrada_subsanacion(), entrada_separata],
                        'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.suspendido is True
        assert ep.suspendido_desde == date(2026, 2, 2)

    def test_la_solicitud_cerrada_esta_cumplida(self):
        """El plazo de la solicitud se cierra con el certificado que acredita la
        notificación a todos los interesados (art. 40.4), no con la resolución."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        solicitud = _solicitud(disparo=date(2026, 1, 12), cierre=date(2026, 3, 30))
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 5, 1))
        with _catalogo({'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.estado == 'CUMPLIDO'
        assert ep.cumplido_fuera_de_plazo is False

    def test_sin_certificado_de_cierre_la_solicitud_vence(self):
        """Consecuencia asumida en ADR-041 §D bis: CUMPLIDO depende de un acto de
        formalización, y sin él la solicitud se marca vencida aunque se resolviera
        a tiempo. Misma señal que una fase en PDTE_CIERRE."""
        from app.services.plazos import obtener_estado_plazo_solicitud

        solicitud = _solicitud(disparo=date(2026, 1, 12))
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 5, 1))
        with _catalogo({'SOLICITUD': [_entrada_solicitud()]}), congela_hoy, sin_inhabiles:
            ep = obtener_estado_plazo_solicitud(solicitud)

        assert ep.estado == 'VENCIDO'

    def test_la_tarea_no_calcula_suspensiones(self):
        """Art. 22: se suspende «el plazo máximo legal para resolver un
        procedimiento y notificar la resolución». Los plazos de nivel TAREA son de
        un tercero, del interesado o períodos que han de transcurrir (#788)."""
        from app.services.plazos import obtener_estado_plazo_tarea

        tarea = _tarea(consumidos=[_doc(NOTIFICACION)])
        congela_hoy, sin_inhabiles = _sin_bd(date(2026, 1, 20))
        with _catalogo({'TAREA': [_entrada_subsanacion()]}), congela_hoy, sin_inhabiles, \
             patch('app.services.plazos._causas_suspension') as mock_causas:
            ep = obtener_estado_plazo_tarea(tarea)

        mock_causas.assert_not_called()
        assert ep.fecha_limite == VENCIMIENTO

    def test_ninguna_fila_suspensora_evita_el_recorrido(self):
        """Atajo barato: si el catálogo no marca nada, no hay por qué recorrer el
        árbol entero de la solicitud."""
        from app.services.plazos import _causas_suspension

        espera = _tarea(consumidos=[_doc(NOTIFICACION)])
        solicitud = _solicitud(disparo=date(2026, 1, 2), tareas_por_fase=[[espera]])
        with _catalogo({'TAREA': [_entrada_subsanacion(suspende=False)]}):
            assert _causas_suspension(solicitud) == []


class TestConsumidoresLlamanBienAlServicio:
    """El `except Exception` defensivo de los consumidores oculta los errores de
    firma: el plazo degrada a None y la pantalla enseña «sin plazo» en vez de
    romperse. Es la protección correcta, pero deja pasar en silencio que un
    consumidor haya dejado de hablar con el servicio — que es el defecto que este
    issue vino a arreglar. Estos tests atan la llamada.
    """

    def test_la_cola_pide_el_plazo_solo_con_la_tarea(self):
        """`plazo_tarea` perdió su segundo parámetro en #785 (el catálogo se
        identifica por el camino SFTT, derivado de la propia tarea) y la cola
        siguió pasándole el trámite. El TypeError caía en el `except`, así que
        TODA espera se mostraba como «pendiente iniciar plazo» y el filtro por
        plazo no encontraba ninguna vencida."""
        from unittest.mock import MagicMock as MM
        import app.services.cola_administrativo as cola

        tarea = MM()
        tarea.tipo_tarea = MM(codigo='ESPERAR_PLAZO')
        tarea.ejecutada = False
        tarea.planificada = False

        with patch.object(cola, 'plazo_tarea',
                          return_value={'estado': 'VENCIDO'}) as mock_plazo:
            estado, plazo = cola._estado_y_plazo(tarea)

        mock_plazo.assert_called_once_with(tarea)
        assert plazo == {'estado': 'VENCIDO'}
        assert estado == 'PENDIENTE_ESTUDIO', (
            'Con el plazo vencido la cola debe ofrecer la tarea como trabajo '
            'que hacer, no como espera'
        )

    def test_la_cola_dice_que_el_plazo_vencio(self):
        from unittest.mock import MagicMock as MM
        from app.services.cola_administrativo import _mensaje_pendiente

        tarea = MM()
        tarea.tipo_tarea = MM(codigo='ESPERAR_PLAZO')
        assert _mensaje_pendiente(tarea, 'PENDIENTE_ESTUDIO') == 'plazo vencido — incorporar'
        assert _mensaje_pendiente(tarea, 'PENDIENTE_TRAMITAR') == 'pendiente iniciar plazo'

    def test_el_arbol_pide_el_plazo_solo_con_la_tarea(self):
        """Mismo contrato para el otro consumidor de `plazo_tarea` (el árbol y,
        a través de él, el inspector lazy de detalle_nodo)."""
        import inspect
        from app.services.arbol_expediente import plazo_tarea

        parametros = inspect.signature(plazo_tarea).parameters
        assert list(parametros) == ['tarea']


class TestAvisoTopeSuspension:
    """Art. 22.1.d: la suspensión «no podrá exceder en ningún caso de tres meses».

    El límite recae sobre la suspensión, no sobre el plazo concedido al
    informante, así que no se recorta el valor del catálogo ni se mete lógica en
    el cómputo: se avisa al dar de alta la entrada (ADR-041 §F).
    """

    def _aviso(self, unidad, valor, suspende=True):
        from app.modules.catalogo_plazos.routes import _aviso_tope_suspension
        from types import SimpleNamespace
        return _aviso_tope_suspension(SimpleNamespace(
            suspende_plazo_solicitud=suspende,
            plazo_unidad=unidad,
            plazo_valor=valor,
        ))

    @pytest.mark.parametrize('unidad,valor', [
        ('MESES', 6), ('ANOS', 1), ('DIAS_NATURALES', 120), ('DIAS_HABILES', 90),
    ])
    def test_avisa_si_pasa_de_tres_meses(self, unidad, valor):
        assert self._aviso(unidad, valor) is not None

    @pytest.mark.parametrize('unidad,valor', [
        ('MESES', 3), ('DIAS_NATURALES', 90), ('DIAS_HABILES', 10),
    ])
    def test_no_avisa_dentro_del_tope(self, unidad, valor):
        assert self._aviso(unidad, valor) is None

    def test_no_avisa_si_no_suspende(self):
        """Los 30 días de exposición de un anuncio no suspenden nada: corren
        dentro del plazo de la solicitud y lo consumen."""
        assert self._aviso('MESES', 6, suspende=False) is None


# ---------------------------------------------------------------------------
# D) Con BD — invariantes del catálogo tras el rediseño
# ---------------------------------------------------------------------------

class TestCatalogoEnBD:

    def test_solo_las_tareas_suspenden(self, app_ctx):
        from app.models.catalogo_plazos import CatalogoPlazo
        malas = (
            CatalogoPlazo.query
            .filter(CatalogoPlazo.suspende_plazo_solicitud.is_(True),
                    CatalogoPlazo.tipo_elemento != 'TAREA')
            .all()
        )
        assert malas == [], (
            'El art. 22 suspende el plazo de la solicitud: marcarla a ella '
            f'significaría que se suspende a sí misma. Filas: {[e.id for e in malas]}'
        )

    def test_constraint_rechaza_solicitud_suspensora(self, app_ctx):
        """El CRUD valida para dar error legible; el constraint cubre lo que
        escribe sin pasar por él — migraciones de seed y tests, que son por donde
        entraron los incidentes reales de esta tabla."""
        import sqlalchemy.exc
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo

        efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
        assert efecto is not None, 'Seed de efectos_plazo no encontrado'

        db.session.add(CatalogoPlazo(
            tipo_elemento='SOLICITUD',
            camino='ANY/TEST_778',
            campo_fecha={'fk': 'documento_solicitud_id'},
            plazo_valor=3,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto.id,
            suspende_plazo_solicitud=True,
        ))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db.session.flush()

    def test_cumplimiento_usa_el_vocabulario_cerrado(self, app_ctx):
        """Mismo vocabulario que el señalador de disparo: no hay un tercer
        portador de fecha al que apuntar."""
        from app.models.catalogo_plazos import CatalogoPlazo
        for fila in CatalogoPlazo.query.filter_by(activo=True).all():
            cf = fila.campo_fecha_cumplimiento
            if cf is None:
                continue
            claves = set(cf)
            if fila.tipo_elemento == 'SOLICITUD':
                assert claves == {'fk'}, f'Fila {fila.id}: {cf}'
                assert cf['fk'] == 'documento_cierre_id', f'Fila {fila.id}: {cf}'
            else:
                assert claves <= {'rol', 'tipo_documento'}, f'Fila {fila.id}: {cf}'
                assert cf.get('rol') in ('CONSUMIDO', 'PRODUCIDO'), f'Fila {fila.id}: {cf}'

    def test_el_tablon_sigue_sin_senalador_de_cumplimiento(self, app_ctx):
        """#416: allí disparo y cierre son el mismo documento. Si alguien le pone
        señalador, el certificado retroactivo pasaría a cerrar su propio plazo el
        día que empieza a contarlo."""
        from app.models.catalogo_plazos import CatalogoPlazo
        filas = (
            CatalogoPlazo.query
            .filter(CatalogoPlazo.camino.like('%/TABLON_AYUNTAMIENTOS/%'),
                    CatalogoPlazo.activo.is_(True))
            .all()
        )
        for fila in filas:
            assert fila.campo_fecha_cumplimiento is None, f'Fila {fila.id}'

    def test_las_esperas_pobladas_saben_cerrar(self, app_ctx):
        """Toda fila de nivel TAREA que no sea la del tablón declara con qué
        documento se cumple: si no, no puede alcanzar CUMPLIDO nunca."""
        from app.models.catalogo_plazos import CatalogoPlazo
        mudas = [
            f.id for f in CatalogoPlazo.query.filter_by(
                tipo_elemento='TAREA', activo=True).all()
            if f.campo_fecha_cumplimiento is None
            and 'TABLON_AYUNTAMIENTOS' not in (f.camino or '')
        ]
        assert mudas == [], f'Filas sin señalador de cumplimiento: {mudas}'
