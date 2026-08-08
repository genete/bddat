"""
Tests de `_check_cierre_desfavorable` — #765.

El caso simétrico e inverso al de #419/#711: hasta ahora `_check_cierre_fase`
cortaba en seco con `codigo_resultado == 'DESFAVORABLE'` y no comprobaba nada,
así que se podía cerrar una fase DESFAVORABLE aunque el diagnóstico vigente
fuese favorable.

Con SQL real (fixture `arbol_esftt`, #715) — nada de mocks de `db.session`.

Ejes que cubren:
  - Vigencia: mismo criterio de #711 (dentro de la cadena de subsanación manda
    el último; fuera, los diagnósticos son paralelos y basta uno desfavorable
    para respaldar el cierre).
  - Qué respalda: solo `desfavorable`; `condicionado` no.
  - `consumido` no se mira en este sentido (requerido y no subsanado).
  - Sin diagnósticos vigentes no hay nada que contradecir: no bloquea.
  - Integración por `editar_fase`: forzable con justificación y rastro en
    bitácora, igual que la rama de #723.
"""
import pytest
from flask_login import login_user


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _bitacora_ultima(tabla, registro_id, operacion='ALTERAR'):
    from app.models.bitacora import Bitacora
    return (
        Bitacora.query
        .filter_by(tabla=tabla, registro_id=registro_id, operacion=operacion)
        .order_by(Bitacora.id.desc())
        .first()
    )


def _montar_fase(arbol, codigo_fase, specs):
    """Monta una fase nueva con un trámite por spec y devuelve (fase, tareas_analizar).

    `specs`: lista de (codigo_tramite, resultado_diagnostico, consumido) —
    mismo contrato que el helper de test_711, apoyado en el builder `ArbolESFTT`:
      - resultado_diagnostico None → el trámite no produce diagnóstico
      - consumido True → una tarea ELABORAR del mismo trámite vincula ese
        documento como CONSUMIDO (el requerimiento que se apoya en él)
    """
    from app import db
    from app.models.diagnosticos import Diagnostico

    fase = arbol.fase(codigo_fase)
    expediente_id = fase.solicitud.expediente_id

    tareas_analizar = []
    for codigo_tramite, resultado, consumido in specs:
        tramite = arbol.tramite(fase, codigo_tramite)
        tarea = arbol.tarea(tramite, 'ANALIZAR')
        tareas_analizar.append(tarea)

        if resultado is None:
            continue

        doc = arbol.documento(expediente_id, 'DIAGNOSTICO', f'765-{tarea.id}')
        db.session.add(Diagnostico(documento_id=doc.id, resultado=resultado, defectos=[]))
        arbol.vincular(tarea, doc, 'PRODUCIDO')

        if consumido:
            arbol.vincular(arbol.tarea(tramite, 'ELABORAR'), doc, 'CONSUMIDO')
        db.session.flush()

    return fase, tareas_analizar


# ---------------------------------------------------------------------------
# A) Cadena de subsanación — manda el último diagnóstico
# ---------------------------------------------------------------------------

class TestCadenaSubsanacion:

    def test_ultima_vuelta_favorable_bloquea_el_cierre_desfavorable(self, arbol_esftt):
        """El caso del issue: se subsanó bien y aun así se cierra DESFAVORABLE."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'DESFAVORABLE')
        assert resultado is not None
        assert resultado.permitido is False
        assert resultado.puede_escapar is True
        assert 'no está respaldado' in resultado.norma_compilada

    def test_ultima_vuelta_desfavorable_no_bloquea(self, arbol_esftt):
        """Defectos que persisten tras la subsanación: el cierre desfavorable es coherente."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'desfavorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None

    def test_desfavorable_consumido_sigue_respaldando(self, arbol_esftt):
        """Requerido y no subsanado: el desfavorable está CONSUMIDO por el ELABORAR
        del requerimiento y sigue siendo el último de la cadena — respalda el cierre
        sin fricción (criterio acordado: en este sentido `consumido` no se mira)."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', True),
        ])

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None

    def test_unico_diagnostico_favorable_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'favorable', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'DESFAVORABLE')
        assert resultado is not None
        assert 'el único diagnóstico vigente' in resultado.norma_compilada

    def test_condicionado_no_respalda_el_cierre_desfavorable(self, arbol_esftt):
        """Un condicionado es un favorable con condiciones: si el técnico entiende
        que son incumplibles, ese juicio debe quedar justificado (bloqueo forzable)."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'condicionado', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'DESFAVORABLE')
        assert resultado is not None
        assert 'condicionado' in resultado.norma_compilada


# ---------------------------------------------------------------------------
# B) Fuera de la cadena — diagnósticos paralelos
# ---------------------------------------------------------------------------

class TestDiagnosticosParalelos:

    def test_un_organismo_desfavorable_respalda_aunque_otro_sea_favorable(self, arbol_esftt):
        """Espejo del test de #711: los diagnósticos de CONSULTAS son paralelos y
        ninguno supera a otro, así que basta uno desfavorable para sostener el cierre."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'CONSULTAS', [
            ('CONSULTA_SEPARATA', 'desfavorable', False),
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None

    def test_todos_los_organismos_favorables_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'CONSULTAS', [
            ('CONSULTA_SEPARATA', 'favorable', False),
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'DESFAVORABLE')
        assert resultado is not None
        assert 'ninguno de los 2 diagnósticos vigentes' in resultado.norma_compilada


# ---------------------------------------------------------------------------
# C) Sin diagnósticos vigentes no hay nada que contradecir
# ---------------------------------------------------------------------------

class TestSinDiagnosticos:

    def test_fase_sin_diagnosticos_no_bloquea(self, arbol_esftt):
        """La mayoría de fases no producen diagnóstico (RESOLUCION entre ellas):
        el check no debe alcanzarlas — es la asimetría de `_check_cierre_fase`,
        no el guardián general de RESOLUCION."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', None, False),
        ])

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None

    def test_fase_vacia_no_bloquea(self, arbol_esftt):
        from app.services.invariantes_esftt import _check_cierre_fase

        fase = arbol_esftt.fase('RESOLUCION')

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None


# ---------------------------------------------------------------------------
# D) Otros resultados de fase siguen por la rama de #419/#711
# ---------------------------------------------------------------------------

class TestOtrosResultados:

    def test_desistida_con_favorable_vigente_no_bloquea(self, arbol_esftt):
        """El guardián nuevo es solo para DESFAVORABLE: DESISTIDA/ARCHIVADA/NO_PROCEDE
        no expresan juicio sobre el análisis y siguen evaluándose como antes."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'favorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'DESISTIDA') is None


# ---------------------------------------------------------------------------
# E) Integración por editar_fase — forzable con justificación y bitácora
# ---------------------------------------------------------------------------

class TestCierreForzable:

    def _fase_lista(self, arbol_esftt):
        """Fase con la cadena subsanada favorable y el trámite completo, para que
        el bloqueo que se pruebe sea el de #765 y no el de completitud (#723)."""
        fase, _ = _montar_fase(arbol_esftt, 'ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', False),
        ])
        return fase

    def test_bloquea_sin_justificacion(self, arbol_esftt):
        from app.services import mutaciones_arbol as svc
        from app.models.tipos_resultados_fases import TipoResultadoFase

        fase = self._fase_lista(arbol_esftt)
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                    'CERT_FIN_INSTRUCCION', 'cierre-765')
        desfavorable = _tipo(TipoResultadoFase, 'DESFAVORABLE')

        res = svc.editar_fase(fase, resultado_fase_id=desfavorable.id,
                              documento_resultado_id=doc.id,
                              observaciones=None, justificacion=None)

        assert res.ok is False
        assert res.bloqueo.puede_escapar is True
        assert 'no está respaldado' in res.bloqueo.norma_compilada

    def test_se_fuerza_y_registra_bitacora(self, arbol_esftt, app_ctx):
        from app.services import mutaciones_arbol as svc
        from app.models.tipos_resultados_fases import TipoResultadoFase

        usuario = _usuario()
        fase = self._fase_lista(arbol_esftt)
        doc = arbol_esftt.documento(fase.solicitud.expediente_id,
                                    'CERT_FIN_INSTRUCCION', 'cierre-765-forzado')
        desfavorable = _tipo(TipoResultadoFase, 'DESFAVORABLE')

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.editar_fase(fase, resultado_fase_id=desfavorable.id,
                                  documento_resultado_id=doc.id, observaciones=None,
                                  justificacion='El informe posterior desmiente el diagnóstico')

        assert res.ok is True
        assert fase.resultado_fase_id == desfavorable.id

        entrada = _bitacora_ultima('fases', fase.id)
        assert entrada is not None
        assert entrada.detalle['escape'] is True
        assert entrada.detalle['justificacion'] == 'El informe posterior desmiente el diagnóstico'


# ---------------------------------------------------------------------------
# F) Contrato del PATCH que consume el escape del inspector (#765)
# ---------------------------------------------------------------------------

class TestBypassEnPatchDeFase:
    """El Guardar del árbol reintenta con `bypass`+`justificacion` en el mismo
    PATCH del nodo (store.js, `guardar`). Ese contrato existía desde #723 pero
    solo estaba probado a nivel de servicio: aquí se fija la ruta, que es de lo
    que depende la vía de escape de la interfaz.

    Mismo patrón que test_616 para la creación: se mockea el servicio — lo que
    se prueba es el enrutado del body, no la mutación (cubierta arriba).
    """

    def _fase_id(self, app, expediente_seed):
        from app.models.fases import Fase
        from app.models.solicitudes import Solicitud
        with app.app_context():
            fase = (Fase.query.join(Solicitud, Fase.solicitud_id == Solicitud.id)
                    .filter(Solicitud.expediente_id == expediente_seed).first())
            if fase is None:
                pytest.skip('El expediente de la BD de desarrollo no tiene fases')
            return fase.id

    def test_patch_fase_propaga_justificacion(self, app, usuario_supervisor, expediente_seed):
        from unittest.mock import patch
        from app.services.mutaciones_arbol import ResultadoMutacion

        fase_id = self._fase_id(app, expediente_seed)
        with patch('app.routes.api_expedientes.svc.editar_fase') as mock_editar:
            mock_editar.return_value = ResultadoMutacion(ok=True)
            r = usuario_supervisor.patch(
                f'/api/expedientes/{expediente_seed}/nodo/fase/{fase_id}',
                json={'observaciones': 'x', 'bypass': True,
                      'justificacion': 'El diagnóstico ha quedado desfasado'})

        assert r.status_code == 200
        assert mock_editar.call_args.kwargs['justificacion'] == 'El diagnóstico ha quedado desfasado'

    def test_patch_fase_sin_bypass_no_justifica(self, app, usuario_supervisor, expediente_seed):
        from unittest.mock import patch
        from app.services.mutaciones_arbol import ResultadoMutacion

        fase_id = self._fase_id(app, expediente_seed)
        with patch('app.routes.api_expedientes.svc.editar_fase') as mock_editar:
            mock_editar.return_value = ResultadoMutacion(ok=True)
            r = usuario_supervisor.patch(
                f'/api/expedientes/{expediente_seed}/nodo/fase/{fase_id}',
                json={'observaciones': 'x'})

        assert r.status_code == 200
        assert mock_editar.call_args.kwargs['justificacion'] is None

    def test_patch_fase_bypass_sin_justificacion_400(self, app, usuario_supervisor, expediente_seed):
        """Guardarraíl de `leer_bypass`: forzar sin motivo no llega al servicio."""
        from unittest.mock import patch

        fase_id = self._fase_id(app, expediente_seed)
        with patch('app.routes.api_expedientes.svc.editar_fase') as mock_editar:
            r = usuario_supervisor.patch(
                f'/api/expedientes/{expediente_seed}/nodo/fase/{fase_id}',
                json={'observaciones': 'x', 'bypass': True})

        assert r.status_code == 400
        assert mock_editar.called is False
