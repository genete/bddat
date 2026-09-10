"""Tests #895 — fases.reformado_id, el nodo de versión del árbol y la regla de §F
(ADR-044, R3).

Cinco bloques:
  A) La variable `version_ya_cubierta`: cuándo dispara y cuándo no.
  B) La regla de motor BLOQUEAR CREAR ANY/ANY/ANY, de punta a punta.
  C) `crear_fase` engancha la fase a la versión vigente.
  D) El payload del árbol: la clave `versiones` de `_serializar_solicitud`.
  E) Las guardas de reversión del reformado con fases enganchadas.
"""
import pytest
from flask_login import login_user
from sqlalchemy.exc import IntegrityError


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _solicitud_de(arbol, siglas='AAP'):
    from app import db
    from app.models.tipos_solicitudes import TipoSolicitud
    sol = arbol.solicitud_nueva()
    tipo = TipoSolicitud.query.filter_by(siglas=siglas).first()
    assert tipo is not None, f'la semilla debe traer el TipoSolicitud {siglas}'
    sol.tipo_solicitud_id = tipo.id
    db.session.flush()
    return sol


def _tipo_fase(codigo):
    from app.models.tipos_fases import TipoFase
    tipo = TipoFase.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el TipoFase {codigo}'
    return tipo


def _puede_avanzar(arbol, solicitud):
    """Satisface las reglas que #895 no prueba (ancla #887, tasa #582) para poder
    ejercitar crear_fase() sin justificación y aislar el bloqueo de §F."""
    from app import db
    from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
    arbol.anclar_proyecto(solicitud.expediente_id, sufijo='895-avanza')
    for req in RequisitoDocumental.query.filter(RequisitoDocumental.activo.is_(True)).all():
        doc = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD',
                              f'895-{req.id}-sol-{solicitud.id}')
        db.session.add(DocumentoRequisito(requisito_id=req.id, solicitud_id=solicitud.id,
                                          documento_id=doc.id))
    db.session.flush()


def _crear_fase(solicitud, tipo_fase, app_ctx, **kwargs):
    from app.services import mutaciones_arbol as svc
    with app_ctx.test_request_context():
        login_user(_usuario())
        return svc.crear_fase(solicitud, tipo_fase, **kwargs)


# ---------------------------------------------------------------------------
# A) La variable version_ya_cubierta
# ---------------------------------------------------------------------------

def _variable():
    from app.services.variables import _REGISTRY
    fn = _REGISTRY.get('version_ya_cubierta')
    assert fn is not None, "Variable 'version_ya_cubierta' no registrada"
    return fn


def _ctx_crear_fase(solicitud, tipo_fase):
    from app.services.assembler import ExpedienteContext
    return ExpedienteContext(solicitud.expediente, {'solicitud': solicitud, 'tipo_fase': tipo_fase})


class TestVariable:

    def test_sin_fases_previas_no_choca(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()
        fn = _variable()

        assert fn(_ctx_crear_fase(sol, _tipo_fase('CONSULTAS'))) is False

    def test_repite_tipo_sin_reformado_bloquea(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('CONSULTAS', solicitud=sol)
        fn = _variable()

        assert fn(_ctx_crear_fase(sol, _tipo_fase('CONSULTAS'))) is True

    def test_distinto_tipo_no_choca(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('CONSULTAS', solicitud=sol)
        fn = _variable()

        assert fn(_ctx_crear_fase(sol, _tipo_fase('INFORMACION_PUBLICA'))) is False

    def test_con_reformado_nuevo_permite(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('CONSULTAS', solicitud=sol)   # versión inicial (reformado_id NULL)
        arbol_esftt.reformado(sol.expediente_id)        # versión vigente cambia
        fn = _variable()

        assert fn(_ctx_crear_fase(sol, _tipo_fase('CONSULTAS'))) is False

    def test_no_dispara_con_fase_existente_en_contexto(self, app_ctx, arbol_esftt):
        """Crear trámite (u otro contexto con fase ya resuelta): ctx.fase no es
        None, así que la variable no evalúa el choque de versión."""
        from app.services.assembler import ExpedienteContext
        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        arbol_esftt.fase('CONSULTAS', solicitud=sol)   # ya hay dos del mismo tipo
        fn = _variable()

        ctx = ExpedienteContext(sol.expediente, fase)   # objeto existente, no dict de CREAR
        assert fn(ctx) is False


# ---------------------------------------------------------------------------
# B) La regla de motor, de punta a punta
# ---------------------------------------------------------------------------

def _reglas_895(solicitud, tipo_fase):
    from app.services.assembler import auditar_multi
    resultado = auditar_multi('CREAR', solicitud.expediente,
                              {'solicitud': solicitud, 'tipo_fase': tipo_fase})
    return [r for r in resultado.reglas_evaluadas
            if 'ya está cubierta' in (r.descripcion or '') and r.disparada]


class TestRegla:

    def test_bloquea_repetir_fase_sin_reformado(self, app_ctx, arbol_esftt):
        sol = _solicitud_de(arbol_esftt)
        arbol_esftt.fase('CONSULTAS', solicitud=sol)

        disparadas = _reglas_895(sol, _tipo_fase('CONSULTAS'))

        assert len(disparadas) == 1
        assert disparadas[0].efecto == 'BLOQUEAR'

    def test_con_reformado_la_regla_no_dispara(self, app_ctx, arbol_esftt):
        sol = _solicitud_de(arbol_esftt)
        arbol_esftt.fase('CONSULTAS', solicitud=sol)
        arbol_esftt.reformado(sol.expediente_id)

        assert not _reglas_895(sol, _tipo_fase('CONSULTAS'))

    def test_primera_fase_del_tipo_no_dispara(self, app_ctx, arbol_esftt):
        sol = _solicitud_de(arbol_esftt)

        assert not _reglas_895(sol, _tipo_fase('CONSULTAS'))

    def test_no_dispara_al_crear_tramite(self, app_ctx, arbol_esftt):
        """El dict de crear_tramite ({'fase', 'tipo_tramite'}, sin 'solicitud') también
        compila 3 segmentos —la regla SÍ casa por sujeto—, pero no dispara: la
        protección real es la propia variable (`ctx.fase is not None` → False),
        no la longitud del camino."""
        from app.services.assembler import auditar_multi
        from app.models.tipos_tramites import TipoTramite
        sol = _solicitud_de(arbol_esftt)
        fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        arbol_esftt.fase('CONSULTAS', solicitud=sol)   # dos del mismo tipo ya
        tipo_tramite = TipoTramite.query.first()
        assert tipo_tramite is not None

        resultado = auditar_multi('CREAR', sol.expediente,
                                  {'fase': fase, 'tipo_tramite': tipo_tramite})

        assert not [r for r in resultado.reglas_evaluadas
                   if 'ya está cubierta' in (r.descripcion or '') and r.disparada]

    def test_bloquea_de_punta_a_punta_via_crear_fase(self, app_ctx, arbol_esftt):
        sol = _solicitud_de(arbol_esftt)
        _puede_avanzar(arbol_esftt, sol)
        consultas = _tipo_fase('CONSULTAS')
        primera = _crear_fase(sol, consultas, app_ctx)
        assert primera.ok is True, primera.error

        segunda = _crear_fase(sol, consultas, app_ctx)

        assert segunda.ok is False
        assert 'ya está cubierta' in (segunda.bloqueo.motivo or segunda.bloqueo.norma_compilada)

    def test_con_reformado_crear_fase_vuelve_a_permitir(self, app_ctx, arbol_esftt):
        sol = _solicitud_de(arbol_esftt)
        _puede_avanzar(arbol_esftt, sol)
        consultas = _tipo_fase('CONSULTAS')
        primera = _crear_fase(sol, consultas, app_ctx)
        assert primera.ok is True, primera.error
        arbol_esftt.reformado(sol.expediente_id)

        segunda = _crear_fase(sol, consultas, app_ctx)

        assert segunda.ok is True, segunda.error


# ---------------------------------------------------------------------------
# C) crear_fase engancha la versión vigente
# ---------------------------------------------------------------------------

class TestCrearFaseEnganchaVersion:

    def test_sin_reformado_queda_en_null(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()

        res = _crear_fase(sol, _tipo_fase('CONSULTAS'), app_ctx, justificacion='setup 895')

        assert res.ok is True, res.error
        from app.models.fases import Fase
        fase = Fase.query.get(res.ids[0])
        assert fase.reformado_id is None

    def test_con_reformado_la_hereda(self, app_ctx, arbol_esftt):
        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)

        res = _crear_fase(sol, _tipo_fase('CONSULTAS'), app_ctx, justificacion='setup 895')

        assert res.ok is True, res.error
        from app.models.fases import Fase
        fase = Fase.query.get(res.ids[0])
        assert fase.reformado_id == reformado.id

    def test_dos_reformados_hereda_el_ultimo(self, app_ctx, arbol_esftt):
        from datetime import timedelta
        from app.services.reloj_simulado import hoy
        from app.models.reformados_proyecto import ReformadoProyecto
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        primero = arbol_esftt.documento(sol.expediente_id, 'DOC_PROYECTO', 'primero-895',
                                        fecha=hoy() - timedelta(days=5))
        db.session.add(ReformadoProyecto(documento_id=primero.id, origen='VOLUNTARIO'))
        db.session.flush()
        segundo = arbol_esftt.reformado(sol.expediente_id, sufijo='segundo')   # fecha = hoy()

        res = _crear_fase(sol, _tipo_fase('CONSULTAS'), app_ctx, justificacion='setup 895')

        assert res.ok is True, res.error
        from app.models.fases import Fase
        fase = Fase.query.get(res.ids[0])
        assert fase.reformado_id == segundo.id


# ---------------------------------------------------------------------------
# D) El payload del árbol
# ---------------------------------------------------------------------------

class TestPayloadArbol:

    def test_sin_reformados_versiones_vacio(self, app_ctx, arbol_esftt):
        from app.services.arbol_expediente import _serializar_solicitud
        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('CONSULTAS', solicitud=sol)

        data = _serializar_solicitud(sol)

        assert data['versiones'] == []
        assert len(data['fases']) == 1   # solicitud.fases se queda intacta

    def test_con_reformado_agrupa_las_fases_por_version(self, app_ctx, arbol_esftt):
        from app import db
        from app.services.arbol_expediente import _serializar_solicitud, ID_VERSION_INICIAL_BASE
        sol = arbol_esftt.solicitud_nueva()
        inicial = arbol_esftt.fase('INFORMACION_PUBLICA', solicitud=sol)
        reformado = arbol_esftt.reformado(sol.expediente_id)
        posterior = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        posterior.reformado_id = reformado.id
        db.session.flush()

        data = _serializar_solicitud(sol)

        assert len(data['fases']) == 2                       # sigue intacta
        assert len(data['versiones']) == 2
        v_inicial = next(v for v in data['versiones'] if v['id'] == ID_VERSION_INICIAL_BASE + sol.id)
        v_reformado = next(v for v in data['versiones'] if v['id'] == reformado.id)
        assert v_inicial['fase_ids'] == [inicial.id]
        assert v_reformado['fase_ids'] == [posterior.id]
        assert v_inicial['etiqueta'] == 'PROYECTO'
        assert 'REFORMADO DE PROYECTO' in v_reformado['etiqueta']
        # Orden: la inicial siempre primero.
        assert [v['id'] for v in data['versiones']] == [ID_VERSION_INICIAL_BASE + sol.id, reformado.id]

    def test_etiqueta_inicial_con_ancla_lleva_fecha(self, app_ctx, arbol_esftt):
        from app import db
        from app.services.arbol_expediente import _serializar_solicitud
        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('INFORMACION_PUBLICA', solicitud=sol)
        arbol_esftt.anclar_proyecto(sol.expediente_id, sufijo='895-etiqueta')
        reformado = arbol_esftt.reformado(sol.expediente_id)
        posterior = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        posterior.reformado_id = reformado.id
        db.session.flush()

        data = _serializar_solicitud(sol)
        v_inicial = next(v for v in data['versiones'] if v['id'] != reformado.id)
        assert 'PROYECTO de fecha' in v_inicial['etiqueta']


# ---------------------------------------------------------------------------
# E) Las guardas de reversión
# ---------------------------------------------------------------------------

class TestGuardasReversion:

    def test_revertir_niega_si_hay_fases_enganchadas(self, app_ctx, arbol_esftt):
        from app.services.reformados import revertir_reformado
        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        fase.reformado_id = reformado.id
        from app import db
        db.session.flush()

        with pytest.raises(ValueError, match='tiene fases creadas'):
            revertir_reformado(reformado.documento, usuario_id=_usuario().id)

    def test_revertir_funciona_sin_fases(self, app_ctx, arbol_esftt):
        from app.services.reformados import revertir_reformado
        from app.models.reformados_proyecto import ReformadoProyecto
        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        documento = reformado.documento
        reformado_id = reformado.id

        revertir_reformado(documento, usuario_id=_usuario().id)

        # Consulta fresca: el backref en memoria no se sincroniza solo tras un
        # delete directo del hijo (solo se actualizaría reasignando el atributo).
        assert ReformadoProyecto.query.get(reformado_id) is None

    def test_motivo_del_pool_nombra_las_fases(self, app_ctx, arbol_esftt):
        from app.modules.expedientes.routes import _motivo_ancla
        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        fase.reformado_id = reformado.id
        from app import db
        db.session.flush()

        motivo = _motivo_ancla(reformado.documento)

        assert motivo is not None
        assert f'#{fase.id}' in motivo

    def test_passive_deletes_deja_que_la_bd_niegue_el_borrado(self, app_ctx, arbol_esftt):
        """Defensa en profundidad (#895 §1): si alguien se salta revertir_reformado
        y borra la fila directamente, el ORM no debe anular la FK en silencio
        (SET NULL) — passive_deletes=True deja que la BD aplique el RESTRICT real."""
        from app import db
        sol = arbol_esftt.solicitud_nueva()
        reformado = arbol_esftt.reformado(sol.expediente_id)
        fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        fase.reformado_id = reformado.id
        db.session.flush()

        db.session.delete(reformado)
        with pytest.raises(IntegrityError):
            db.session.flush()
        db.session.rollback()
