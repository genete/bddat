"""
Tests issue #788 — `catalogo_plazos` solo admite los niveles que portan fecha.

Un plazo necesita fecha de inicio. Desde #788 solo hay dos portadores de fecha
administrativa: la Solicitud (`documento_solicitud_id`) y la Tarea
(`documentos_tarea`, ADR-010) — Fase y Trámite son taxonomía ESFTT, no figuras
jurídicas, ninguna norma les fija plazo propio.

Historia del nivel de las filas:
  - #788: SOLICITUD y TAREA.
  - ADR-048 (#892) reabrió FASE, acotada a fases finalizadoras
    (`RESOLUCION_DUP`/AAP/AAC).
  - #931 la volvió a cerrar —el plazo de resolver es del acto (#930), no de la
    fase que lo resuelve, que ni existe mientras corre— y renombró SOLICITUD a
    ACTO, que es lo que esas filas eran: el plazo de cada tipo atómico. Con
    ello se retiraron el bloque F de esta suite (el plazo de fase) y el control
    de que el plazo de la solicitud recorría sus suspensiones.

Bloques:
  A) Niveles         — TRAMITE, FASE y el nombre viejo SOLICITUD no compilan
                       camino ni tocan BD; TAREA y ACTO sí.
  B) tipo_documento  — predicado de candidatura y filtro al resolver la fecha.
  C) Suspensiones    — la tarea no calcula suspensiones: solo el plazo de
                       resolver es suspendible.
  D) Trámite → tarea — `Tramite.tarea_espera` baja al ESPERAR_PLAZO (#778: es
                       navegación del árbol, no interfaz del servicio de plazos).
  E) Con BD          — solo filas ACTO y TAREA, y el CheckConstraint lo impide.
"""
from datetime import date
from types import SimpleNamespace
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
    # Explícitos para que no salgan MagicMock (truthy): estos tests miden niveles
    # y candidatura de fila, no el cumplimiento ni la suspensión (#778).
    e.campo_fecha_cumplimiento = None
    e.suspende_plazo_solicitud = False
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
# A) Niveles sin fila: Trámite, Fase y el nombre viejo SOLICITUD
# ---------------------------------------------------------------------------

# TRAMITE no porta fecha administrativa, sin excepción (#788). FASE se retiró en
# #931 (el plazo de resolver es del acto, no de la fase que lo resuelve).
# SOLICITUD es el nombre que tuvo el nivel ACTO hasta #931: que siga compilando
# dejaría a medias el renombrado.
_NIVELES_SIN_FILA = ['TRAMITE', 'FASE', 'SOLICITUD']


class TestNivelesSinPlazo:

    @pytest.mark.parametrize('nivel', _NIVELES_SIN_FILA)
    def test_nivel_sin_fila_no_compila_camino(self, nivel):
        """La firma lo sigue aceptando —los consumidores despachan por
        duck-typing— pero no hay longitud de camino que le corresponda."""
        from app.services.plazos import compilar_camino
        assert compilar_camino(MagicMock(), nivel) is None

    @pytest.mark.parametrize('nivel', _NIVELES_SIN_FILA)
    def test_no_se_consulta_el_catalogo_para_un_nivel_sin_fila(self, nivel):
        """Sale antes de tocar BD: no es un catálogo vacío, es que no aplica."""
        from app.services.plazos import _seleccionar_catalogo

        with patch('app.models.catalogo_plazos.CatalogoPlazo') as MockCP:
            resultado = _seleccionar_catalogo(MagicMock(), nivel, {})

        assert resultado is None
        MockCP.query.options.assert_not_called()

    def test_tarea_y_acto_si_compilan_camino(self):
        """Control: los niveles con plazo sí producen camino, y de la
        longitud que les toca. El del acto lleva su tipo atómico aunque la
        solicitud sea una combinación (#930)."""
        from app.services.actos_solicitud import ActoSolicitud
        from app.services.plazos import compilar_camino

        tarea = _tarea()
        assert compilar_camino(tarea, 'TAREA') == (
            'Distribucion/AAP/INFORMACION_PUBLICA/ANUNCIO_BOP/ESPERAR_PLAZO'
        )

        solicitud = MagicMock()
        solicitud.tipo_solicitud = MagicMock(siglas='AAP+AAC')
        solicitud.expediente.tipo_expediente = MagicMock(tipo='Distribucion')
        acto = ActoSolicitud(solicitud=solicitud, siglas='AAC')
        assert compilar_camino(acto, 'ACTO') == 'Distribucion/AAC'

    def test_los_ancestros_de_una_tarea_siguen_saliendo(self):
        """No regresión de #931 (D7): renombrar el nivel de la FILA no toca el
        del NODO. Una tarea sigue escribiendo la solicitud y la fase de su
        ascendencia; si no, las filas TAREA con fase concreta (las de
        ELABORAR en ANALISIS_SOLICITUD, la de SOLICITUD_INFORME en
        CONSULTA_MINISTERIO) dejarían de casar sin ningún error."""
        from app.services.plazos import compilar_camino

        camino = compilar_camino(_tarea(siglas='AAP+AAC', fase_codigo='CONSULTA_MINISTERIO',
                                        tramite_codigo='SOLICITUD_INFORME'), 'TAREA')
        assert camino.split('/')[1:3] == ['AAP+AAC', 'CONSULTA_MINISTERIO']
        assert '?' not in camino


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
# C) Las suspensiones son del plazo de resolver, y de ningún otro
# ---------------------------------------------------------------------------

class TestSuspensionSoloEnElPlazoDeResolver:

    def test_nivel_tarea_no_calcula_suspensiones(self):
        """Art. 22: se suspende «el plazo máximo legal para resolver un
        procedimiento y notificar la resolución». Los plazos de nivel TAREA son
        de un tercero, del interesado o períodos que han de transcurrir."""
        from app.services.plazos import obtener_estado_plazo_tarea

        tarea = _tarea(consumidos=[_doc(date(2026, 1, 12))])
        entrada = _entrada('ANY/ANY/ANY/ANUNCIO_BOP/ESPERAR_PLAZO', {'rol': 'CONSUMIDO'},
                           plazo_valor=20, plazo_unidad='DIAS_HABILES')

        with _catalogo_mockeado([entrada]), \
             patch('app.services.plazos._hoy', return_value=date(2026, 1, 20)), \
             patch('app.services.plazos._obtener_inhabiles_bd', return_value=frozenset()), \
             patch('app.services.plazos._causas_suspension') as mock_susp:
            resultado = obtener_estado_plazo_tarea(tarea)

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
        from app.services.plazos import obtener_estado_plazo_tarea

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
            resultado = obtener_estado_plazo_tarea(espera)

        assert resultado.estado == 'VENCIDO'
        assert resultado.fecha_limite == date(2026, 2, 23)   # 12 ene + 30 hábiles

# ---------------------------------------------------------------------------
# D) Los consumidores de nivel trámite bajan a la tarea
# ---------------------------------------------------------------------------

class TestBajarDelTramiteASuEspera:
    """Desde #778 esto NO es una entrada del servicio de plazos, sino navegación
    del árbol: `Tramite.tarea_espera`. Una función «plazo de un trámite»
    reintroduciría por la puerta de atrás el nivel que #788 eliminó.

    La property es pura —solo mira `self.tareas`— así que se invoca sobre un stub
    en vez de montar instancias ORM con sesión.
    """

    def _tarea_espera(self, tareas):
        from app.models.tramites import Tramite
        return Tramite.tarea_espera.fget(SimpleNamespace(tareas=tareas))

    def test_devuelve_la_espera_del_tramite(self):
        espera = _tarea(tramite_codigo='CONSULTA_TRASLADO_TITULAR',
                        consumidos=[_doc(date(2026, 1, 12))])
        assert self._tarea_espera([_tarea(codigo='NOTIFICAR'), espera]) is espera

    def test_tramite_sin_espera_devuelve_none(self):
        assert self._tarea_espera([_tarea(codigo='ELABORAR')]) is None

    def test_tramite_sin_tareas_devuelve_none(self):
        assert self._tarea_espera([]) is None


# ---------------------------------------------------------------------------
# E) Con BD — el estado de la tabla y la salvaguarda que lo mantiene
# ---------------------------------------------------------------------------

class TestCatalogoEnBD:

    def test_solo_hay_filas_de_acto_y_de_tarea(self, app_ctx):
        """TRAMITE sin fecha administrativa, sin excepción (#788); FASE retirada
        en #931; SOLICITUD renombrada a ACTO en #931."""
        from app.models.catalogo_plazos import CatalogoPlazo
        residuales = (
            CatalogoPlazo.query
            .filter(CatalogoPlazo.tipo_elemento.notin_(['ACTO', 'TAREA']))
            .all()
        )
        assert residuales == [], (
            f'Filas en niveles sin plazo: '
            f'{[(e.id, e.tipo_elemento, e.camino) for e in residuales]}'
        )

    def test_la_hoja_de_una_fila_de_acto_es_atomica(self, app_ctx):
        """#931 (D10): el camino del acto lleva siempre su tipo atómico, así que
        una fila ACTO con una combinación no casaría nunca. El CRUD lo rechaza;
        esta es la salvaguarda a nivel de datos, porque el CRUD no cubre
        migraciones ni SQL suelto — y las combinaciones son justo las filas que
        #931 retiró."""
        from app.models.catalogo_plazos import CatalogoPlazo
        combinadas = [
            (f.id, f.camino)
            for f in CatalogoPlazo.query.filter_by(tipo_elemento='ACTO').all()
            if '+' in f.hoja
        ]
        assert combinadas == []

    def test_campo_fecha_usa_el_vocabulario_cerrado(self, app_ctx):
        """`via_tarea_tipo` era la indirección que bajaba de un trámite a su
        tarea. Con la fila en la tarea, sobra."""
        from app.models.catalogo_plazos import CatalogoPlazo
        for fila in CatalogoPlazo.query.filter_by(activo=True).all():
            cf = fila.campo_fecha or {}
            assert 'via_tarea_tipo' not in cf, f'Fila {fila.id} conserva via_tarea_tipo'
            claves = set(cf)
            if fila.tipo_elemento == 'ACTO':
                assert claves == {'fk'}, f'Fila {fila.id}: {cf}'
                assert cf['fk'] == 'documento_solicitud_id', f'Fila {fila.id}: {cf}'
            else:
                assert claves <= {'rol', 'tipo_documento'}, f'Fila {fila.id}: {cf}'
                assert cf.get('rol') in ('CONSUMIDO', 'PRODUCIDO'), f'Fila {fila.id}: {cf}'

    def test_longitud_del_camino_coincide_con_el_nivel(self, app_ctx):
        from app.models.catalogo_plazos import CatalogoPlazo
        esperado = {'ACTO': 2, 'TAREA': 5}
        for fila in CatalogoPlazo.query.filter_by(activo=True).all():
            segmentos = len((fila.camino or '').split('/'))
            assert segmentos == esperado[fila.tipo_elemento], (
                f'Fila {fila.id} ({fila.tipo_elemento}) tiene {segmentos} '
                f'segmentos: {fila.camino}'
            )

    @pytest.mark.parametrize('nivel,camino', [
        ('TRAMITE', 'ANY/ANY/ANY/TEST_788'),
        ('FASE', 'ANY/ANY/TEST_931'),
        ('SOLICITUD', 'ANY/TEST_931'),
    ])
    def test_constraint_rechaza_nivel_sin_fila(self, app_ctx, nivel, camino):
        """TRAMITE sigue prohibido sin excepción; FASE vuelve a estarlo desde
        #931; SOLICITUD es el nombre viejo de ACTO, y aceptarlo dejaría el
        renombrado a medias. El CRUD valida para dar error legible; el
        constraint cubre lo que escribe sin pasar por él — una migración de
        seed o un test, que son las dos vías por las que entraron los
        incidentes reales de esta tabla."""
        import sqlalchemy.exc
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo

        efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
        assert efecto is not None, 'Seed de efectos_plazo no encontrado'

        db.session.add(CatalogoPlazo(
            tipo_elemento=nivel,
            camino=camino,
            campo_fecha={'fk': 'documento_solicitud_id'},
            plazo_valor=1,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto.id,
        ))
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db.session.flush()

    def test_constraint_admite_nivel_acto(self, app_ctx):
        """Control positivo del nombre nuevo (#931)."""
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.efectos_plazo import EfectoPlazo

        efecto = EfectoPlazo.query.filter_by(codigo='NINGUNO').first()
        assert efecto is not None, 'Seed de efectos_plazo no encontrado'

        db.session.add(CatalogoPlazo(
            tipo_elemento='ACTO',
            camino='ANY/TEST_931',
            campo_fecha={'fk': 'documento_solicitud_id'},
            plazo_valor=1,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto.id,
        ))
        db.session.flush()   # no debe lanzar — app_ctx hace rollback al terminar
