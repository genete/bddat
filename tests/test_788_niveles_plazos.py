"""
Tests issue #788 — `catalogo_plazos` solo admite los niveles que portan fecha.

Un plazo necesita fecha de inicio, y en BDDAT solo hay dos portadores de fecha
administrativa: la Solicitud (`documento_solicitud_id`) y la Tarea
(`documentos_tarea`, ADR-010). Fase y Trámite son taxonomía ESFTT, no figuras
jurídicas: ninguna norma les fija plazo propio.

Bloques:
  A) Niveles         — FASE y TRAMITE devuelven SIN_PLAZO sin tocar BD.
  B) tipo_documento  — predicado de candidatura y filtro al resolver la fecha.
  C) Suspensiones    — solo se calculan en el nivel SOLICITUD.
  D) Trámite → tarea — obtener_estado_plazo_espera baja al ESPERAR_PLAZO.
  E) Con BD          — la tabla no tiene filas de FASE/TRAMITE y el
                       CheckConstraint impide volver a ponerlas.
"""
from datetime import date
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
           tramite_codigo='ANUNCIO_BOP', fase_codigo='INFORMACION_PUBLICA',
           siglas='AAP', tipo_expediente='Distribucion'):
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


def _entrada(camino, campo_fecha, orden=10, entrada_id=1,
             plazo_valor=30, plazo_unidad='DIAS_NATURALES'):
    e = MagicMock()
    e.id = entrada_id
    e.orden = orden
    e.camino = camino
    e.campo_fecha = campo_fecha
    e.condiciones = []
    e.plazo_valor = plazo_valor
    e.plazo_unidad = plazo_unidad
    e.efecto_plazo.codigo = 'NINGUNO'
    return e


def _catalogo_mockeado(entradas):
    """Context manager compuesto: la query de catalogo_plazos devuelve `entradas`."""
    from contextlib import ExitStack

    stack = ExitStack()
    mock_cp = stack.enter_context(patch('app.models.catalogo_plazos.CatalogoPlazo'))
    stack.enter_context(patch('app.models.condiciones_plazo.CondicionPlazo'))
    stack.enter_context(patch('app.services.plazos.joinedload', return_value=MagicMock()))
    mock_cp.query.options.return_value.filter_by.return_value\
           .order_by.return_value.all.return_value = list(entradas)
    return stack


# ---------------------------------------------------------------------------
# A) Fase y Trámite no tienen plazo
# ---------------------------------------------------------------------------

class TestNivelesSinPlazo:

    @pytest.mark.parametrize('nivel', ['FASE', 'TRAMITE'])
    def test_nivel_sin_fecha_devuelve_sin_plazo(self, nivel):
        """La firma los sigue aceptando —los consumidores despachan por
        duck-typing— pero no hay camino que compilar para ellos."""
        from app.services.plazos import compilar_camino
        assert compilar_camino(MagicMock(), nivel) is None

    @pytest.mark.parametrize('nivel', ['FASE', 'TRAMITE'])
    def test_no_se_consulta_el_catalogo(self, nivel):
        """Sale antes de tocar BD: no es un catálogo vacío, es que no aplica."""
        from app.services.plazos import _seleccionar_catalogo

        with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP:
            resultado = _seleccionar_catalogo(MagicMock(), nivel, {})

        assert resultado is None
        MockCP.query.options.assert_not_called()

    def test_tarea_y_solicitud_si_compilan_camino(self):
        """Control: los dos niveles con plazo sí producen camino, y de la
        longitud que les toca."""
        from app.services.plazos import compilar_camino

        tarea = _tarea()
        assert compilar_camino(tarea, 'TAREA') == (
            'Distribucion/AAP/INFORMACION_PUBLICA/ANUNCIO_BOP/ESPERAR_PLAZO'
        )

        solicitud = MagicMock()
        solicitud.tipo_solicitud = MagicMock(siglas='AAP')
        solicitud.expediente.tipo_expediente = MagicMock(tipo='Distribucion')
        assert compilar_camino(solicitud, 'SOLICITUD') == 'Distribucion/AAP'


# ---------------------------------------------------------------------------
# B) tipo_documento — desempate de dos tareas del mismo tipo en un trámite
# ---------------------------------------------------------------------------
#
# Un ANUNCIO_* tiene DOS tareas ESPERAR_PLAZO: la que aguarda a que salga la
# publicación y la de los 30 días de exposición. Comparten camino, así que sin
# `tipo_documento` la fila se aplicaría a la primera que aparece.

class TestPredicadoTipoDocumento:

    CAMINO = 'ANY/ANY/ANY/ANUNCIO_BOP/ESPERAR_PLAZO'

    def _entrada_exposicion(self):
        return _entrada(
            self.CAMINO,
            {'rol': 'CONSUMIDO', 'tipo_documento': 'ANUNCIO_PUBLICADO'},
        )

    def test_espera_de_exposicion_selecciona_la_fila(self):
        """La segunda espera consume el ANUNCIO_PUBLICADO → es su fila."""
        from app.services.plazos import _seleccionar_catalogo

        entrada = self._entrada_exposicion()
        tarea = _tarea(consumidos=[_doc(date(2026, 3, 2), 'ANUNCIO_PUBLICADO')])

        with _catalogo_mockeado([entrada]):
            assert _seleccionar_catalogo(tarea, 'TAREA', {}) is entrada

    def test_espera_de_publicacion_no_es_candidata(self):
        """La primera espera no tiene ese vínculo → la fila no le aplica.

        Antes de #788 ganaba igual, porque la candidatura se decidía solo por
        camino, y al fallar la resolución de la fecha el servicio devolvía
        SIN_PLAZO sin probar otra fila. Quedaba muda para las dos.
        """
        from app.services.plazos import _seleccionar_catalogo

        tarea = _tarea(consumidos=[_doc(date(2026, 3, 2), 'OFICIO_PUBLICAR_BOLETIN')])

        with _catalogo_mockeado([self._entrada_exposicion()]):
            assert _seleccionar_catalogo(tarea, 'TAREA', {}) is None

    def test_sin_vinculos_no_es_candidata(self):
        from app.services.plazos import _seleccionar_catalogo

        with _catalogo_mockeado([self._entrada_exposicion()]):
            assert _seleccionar_catalogo(_tarea(), 'TAREA', {}) is None

    def test_fila_sin_tipo_declarado_sigue_siendo_candidata(self):
        """`tipo_documento` es opcional: la espera de CONSULTA_SEPARATA consume
        un justificante polimórfico (BANDEJA / NOTIFICA / POSTAL / SIR) y no se
        puede nombrar un tipo, ni hace falta — esa espera es única en su trámite.
        """
        from app.services.plazos import _seleccionar_catalogo

        entrada = _entrada('ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO',
                           {'rol': 'CONSUMIDO'})
        tarea = _tarea(tramite_codigo='CONSULTA_SEPARATA', fase_codigo='CONSULTAS',
                       consumidos=[_doc(date(2026, 3, 2), 'JUSTIFICANTE_SIR')])

        with _catalogo_mockeado([entrada]):
            assert _seleccionar_catalogo(tarea, 'TAREA', {}) is entrada

    def test_resolver_fecha_toma_el_documento_del_tipo_declarado(self):
        """Con varios consumidos, la fecha sale del que declara la fila."""
        from app.services.plazos import _resolver_campo_fecha

        tarea = _tarea(consumidos=[
            _doc(date(2026, 1, 5), 'OFICIO_PUBLICAR_BOLETIN'),
            _doc(date(2026, 3, 2), 'ANUNCIO_PUBLICADO'),
        ])
        fecha = _resolver_campo_fecha(
            tarea, {'rol': 'CONSUMIDO', 'tipo_documento': 'ANUNCIO_PUBLICADO'}
        )
        assert fecha == date(2026, 3, 2)

    def test_resolver_fecha_rol_producido_con_tipo(self):
        """El caso retroactivo del tablón (#416): la fecha la trae el certificado
        que el ayuntamiento devuelve al final, con rol PRODUCIDO."""
        from app.services.plazos import _resolver_campo_fecha

        tarea = _tarea(tramite_codigo='TABLON_AYUNTAMIENTOS',
                       producido=_doc(date(2026, 2, 10), 'CERT_PLAZO_TABLON'))
        fecha = _resolver_campo_fecha(
            tarea, {'rol': 'PRODUCIDO', 'tipo_documento': 'CERT_PLAZO_TABLON'}
        )
        assert fecha == date(2026, 2, 10)

    def test_resolver_fecha_tipo_que_no_casa_devuelve_none(self):
        from app.services.plazos import _resolver_campo_fecha

        tarea = _tarea(consumidos=[_doc(date(2026, 1, 5), 'OFICIO_PUBLICAR_BOLETIN')])
        assert _resolver_campo_fecha(
            tarea, {'rol': 'CONSUMIDO', 'tipo_documento': 'ANUNCIO_PUBLICADO'}
        ) is None


# ---------------------------------------------------------------------------
# C) Las suspensiones son del plazo de la solicitud, y de ningún otro
# ---------------------------------------------------------------------------

class TestSuspensionSoloEnSolicitud:

    def test_nivel_tarea_no_calcula_suspensiones(self):
        """Art. 22: se suspende «el plazo máximo legal para resolver un
        procedimiento y notificar la resolución». Los plazos de nivel TAREA son
        de un tercero, del interesado o períodos que han de transcurrir."""
        from app.services.plazos import obtener_estado_plazo

        tarea = _tarea(consumidos=[_doc(date(2026, 1, 12))])
        entrada = _entrada('ANY/ANY/ANY/ANUNCIO_BOP/ESPERAR_PLAZO', {'rol': 'CONSUMIDO'},
                           plazo_valor=20, plazo_unidad='DIAS_HABILES')

        with _catalogo_mockeado([entrada]), \
             patch('app.services.plazos._hoy', return_value=date(2026, 1, 20)), \
             patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()), \
             patch('app.services.plazos._obtener_suspensiones') as mock_susp:
            resultado = obtener_estado_plazo(tarea, 'TAREA')

        mock_susp.assert_not_called()
        assert resultado.fecha_limite == date(2026, 2, 9)   # 20 hábiles, sin extender

    def test_la_separata_ya_no_se_suspende_a_si_misma(self):
        """No-regresión del defecto vivo hasta #788.

        Evaluada a nivel TRAMITE, `_obtener_suspensiones` subía a la fase y
        recorría los hermanos — y CONSULTA_SEPARATA es ella misma causa del
        art. 22. Cada separata se suspendía a sí misma: el intervalo era
        [notificación, hoy], que es exactamente su propio plazo, así que la
        fecha límite retrocedía un día hábil por cada día hábil transcurrido y
        no vencía nunca.
        """
        from app.services.plazos import obtener_estado_plazo

        notificacion = date(2026, 1, 12)
        espera = _tarea(tramite_codigo='CONSULTA_SEPARATA', fase_codigo='CONSULTAS',
                        consumidos=[_doc(notificacion)])
        entrada = _entrada('ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO',
                           {'rol': 'CONSUMIDO'},
                           plazo_valor=30, plazo_unidad='DIAS_HABILES')

        # Muy posterior al vencimiento: sin la corrección, la suspensión crecía
        # al mismo ritmo que el tiempo y el estado nunca llegaba a VENCIDO.
        with _catalogo_mockeado([entrada]), \
             patch('app.services.plazos._hoy', return_value=date(2026, 6, 1)), \
             patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()):
            resultado = obtener_estado_plazo(espera, 'TAREA')

        assert resultado.estado == 'VENCIDO'
        assert resultado.fecha_limite == date(2026, 2, 23)   # 12 ene + 30 hábiles

    def test_nivel_solicitud_si_calcula_suspensiones(self):
        """Control: en el nivel que sí tiene plazo suspendible, se recorre."""
        from app.services.plazos import obtener_estado_plazo

        solicitud = MagicMock()
        solicitud.tipo_solicitud = MagicMock(siglas='AAP')
        solicitud.expediente.tipo_expediente = MagicMock(tipo='Distribucion')
        solicitud.documento_solicitud = _doc(date(2026, 1, 12))
        solicitud.fases = []
        entrada = _entrada('ANY/AAP', {'fk': 'documento_solicitud_id'},
                           plazo_valor=20, plazo_unidad='DIAS_HABILES')

        with _catalogo_mockeado([entrada]), \
             patch('app.services.plazos._hoy', return_value=date(2026, 1, 20)), \
             patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()), \
             patch('app.services.plazos._obtener_suspensiones', return_value=[]) as mock_susp:
            obtener_estado_plazo(solicitud, 'SOLICITUD')

        mock_susp.assert_called_once_with(solicitud)


# ---------------------------------------------------------------------------
# D) Los consumidores de nivel trámite bajan a la tarea
# ---------------------------------------------------------------------------

class TestEstadoPlazoEspera:

    def test_baja_del_tramite_a_su_espera(self):
        from app.services.plazos import obtener_estado_plazo_espera

        espera = _tarea(tramite_codigo='CONSULTA_TRASLADO_TITULAR',
                        consumidos=[_doc(date(2026, 1, 12))])
        tramite = MagicMock()
        tramite.tareas = [_tarea(codigo='NOTIFICAR'), espera]

        with patch('app.services.plazos.obtener_estado_plazo') as mock_estado:
            obtener_estado_plazo_espera(tramite)

        mock_estado.assert_called_once_with(espera, 'TAREA', variables={})

    def test_tramite_sin_espera_devuelve_sin_plazo(self):
        from app.services.plazos import obtener_estado_plazo_espera

        tramite = MagicMock()
        tramite.tareas = [_tarea(codigo='ELABORAR')]
        assert obtener_estado_plazo_espera(tramite).estado == 'SIN_PLAZO'

    def test_tramite_none_devuelve_sin_plazo(self):
        from app.services.plazos import obtener_estado_plazo_espera
        assert obtener_estado_plazo_espera(None).estado == 'SIN_PLAZO'


# ---------------------------------------------------------------------------
# E) Con BD — el estado de la tabla y la salvaguarda que lo mantiene
# ---------------------------------------------------------------------------

class TestCatalogoEnBD:

    def test_no_quedan_filas_de_fase_ni_de_tramite(self, app_ctx):
        from app.models.catalogo_plazos import CatalogoPlazo
        residuales = (
            CatalogoPlazo.query
            .filter(CatalogoPlazo.tipo_elemento.in_(['FASE', 'TRAMITE']))
            .all()
        )
        assert residuales == [], (
            f'Filas en niveles sin fecha: '
            f'{[(e.id, e.tipo_elemento, e.camino) for e in residuales]}'
        )

    def test_campo_fecha_usa_el_vocabulario_cerrado(self, app_ctx):
        """`via_tarea_tipo` era la indirección que bajaba de un trámite a su
        tarea. Con la fila en la tarea, sobra."""
        from app.models.catalogo_plazos import CatalogoPlazo
        for fila in CatalogoPlazo.query.filter_by(activo=True).all():
            cf = fila.campo_fecha or {}
            assert 'via_tarea_tipo' not in cf, f'Fila {fila.id} conserva via_tarea_tipo'
            claves = set(cf)
            if fila.tipo_elemento == 'SOLICITUD':
                assert claves == {'fk'}, f'Fila {fila.id}: {cf}'
                assert cf['fk'] == 'documento_solicitud_id', f'Fila {fila.id}: {cf}'
            else:
                assert claves <= {'rol', 'tipo_documento'}, f'Fila {fila.id}: {cf}'
                assert cf.get('rol') in ('CONSUMIDO', 'PRODUCIDO'), f'Fila {fila.id}: {cf}'

    def test_longitud_del_camino_coincide_con_el_nivel(self, app_ctx):
        from app.models.catalogo_plazos import CatalogoPlazo
        esperado = {'SOLICITUD': 2, 'TAREA': 5}
        for fila in CatalogoPlazo.query.filter_by(activo=True).all():
            segmentos = len((fila.camino or '').split('/'))
            assert segmentos == esperado[fila.tipo_elemento], (
                f'Fila {fila.id} ({fila.tipo_elemento}) tiene {segmentos} '
                f'segmentos: {fila.camino}'
            )

    def test_constraint_rechaza_nivel_fase(self, app_ctx):
        """El CRUD valida para dar error legible; el constraint cubre lo que
        escribe sin pasar por él — una migración de seed o un test, que son las
        dos vías por las que entraron los incidentes reales de esta tabla."""
        import sqlalchemy.exc
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo

        efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
        assert efecto is not None, 'Seed de efectos_plazo no encontrado'

        db.session.add(CatalogoPlazo(
            tipo_elemento='FASE',
            camino='ANY/ANY/TEST_788',
            campo_fecha={'fk': 'documento_resultado_id'},
            plazo_valor=1,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto.id,
        ))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db.session.flush()
