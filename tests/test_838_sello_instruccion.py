"""
Tests #838 — el sello de la instrucción y el acto que lo retira (ADR-043 §F).

Con SQL real (fixture `arbol_esftt`, #715) y `fs_tmp` (#674): las pruebas que
consolidan y deshacen generan PDFs de verdad, que no deben caer en el servidor de
ficheros de desarrollo ni borrarse de él.

Cinco bloques:
  A) El sello al CREAR: con el certificado emitido no se abre una fase de instrucción
     nueva; la finalizadora sigue siendo cosa del motor.
  B) El sello al REABRIR: el mismo acto por el otro extremo, con el orden entre las
     dos puertas de `_check_reabrir` cuando ambas aplican.
  C) Deshacer: sus precondiciones, lo que borra, y que el sello cae después.
  D) El relato: el certificado siguiente hace constar el anterior, en `relato` y no
     entre los actos salvados — deshacer no es forzar un bloqueo.
  E) La guarda del pool sobre las tres anclas de solicitud.
"""
import os

import pytest
from flask_login import login_user


@pytest.fixture(autouse=True)
def _fs_tmp(fs_tmp):
    """FILESYSTEM_BASE al tmp del test — aquí se emiten y se borran PDFs reales."""
    pass


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _cerrar(arbol, fase):
    """`Fase.finalizada` es exactamente `documento_resultado_id NOT NULL`."""
    from app import db
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'cierre-838-{fase.id}')
    fase.documento_resultado_id = doc.id
    db.session.flush()
    return fase


def _cumplir_requisitos(arbol, solicitud):
    """Sin esto la tasa del art. 45.1 deja al motor bloqueando y ningún informe sale
    limpio — correcto, pero impide llegar a la consolidación (igual que en #827)."""
    from app import db
    from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
    for req in RequisitoDocumental.query.filter(RequisitoDocumental.activo.is_(True)).all():
        doc = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD',
                              f'req838-{req.id}-sol-{solicitud.id}')
        db.session.add(DocumentoRequisito(requisito_id=req.id, solicitud_id=solicitud.id,
                                          documento_id=doc.id))
    db.session.flush()


def _certificada(arbol, app_ctx, *, codigo_fase='ANALISIS_SOLICITUD'):
    """Solicitud con su instrucción cerrada y el CERT_FIN_INSTRUCCION ya consolidado.

    Se emite de verdad, no se simula con la FK a pelo: lo que este módulo prueba es
    justamente el par emitir/deshacer, y un ancla puesta a mano no tendría ni
    `CertificadoFase` ni PDF que borrar.
    """
    from app.services.cert_fin_instruccion import consolidar
    sol = arbol.solicitud_nueva()
    _cerrar(arbol, arbol.fase(codigo_fase, solicitud=sol))
    _cumplir_requisitos(arbol, sol)
    with app_ctx.test_request_context():
        login_user(_usuario())
        res = consolidar(sol)
    if not res.consolidado:
        pytest.skip('La revisión no salió limpia en esta BD: '
                    f'{[l for b in res.informe.pendientes for l in b.pendiente]}')
    return sol


def _deshacer(solicitud, app_ctx, justificacion='La instrucción no había terminado'):
    from app.services.cert_fin_instruccion import deshacer
    with app_ctx.test_request_context():
        login_user(_usuario())
        return deshacer(solicitud, justificacion=justificacion)


# ---------------------------------------------------------------------------
# A) El sello al crear una fase de instrucción
# ---------------------------------------------------------------------------

class TestSelloAlCrear:

    def test_con_certificado_no_se_abre_otra_fase_de_instruccion(self, arbol_esftt, app_ctx):
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)

        res = check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='CONSULTAS')

        assert res is not None
        assert res.nivel == 'BLOQUEAR'
        assert 'certificada como terminada' in res.norma_compilada

    def test_es_puerta_cerrada(self, arbol_esftt, app_ctx):
        """No admite justificación: la ley no abre una excepción, señala otra vía."""
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)

        res = check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='CONSULTAS')

        assert res.puede_escapar is False

    def test_el_mensaje_nombra_las_dos_vias(self, arbol_esftt, app_ctx):
        """ADR-043 §F: un check que señala la salida es ayuda, uno que solo prohíbe
        es obstáculo. Las dos vías son el art. 87 y deshacer el certificado."""
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)

        mensaje = check_invariante('CREAR', 'FASE', sol.id,
                                   tipo_codigo='CONSULTAS').norma_compilada

        assert 'art. 87' in mensaje.lower()
        assert 'deshaga el certificado' in mensaje.lower()

    def test_la_fase_finalizadora_no_la_mira_el_sello(self, arbol_esftt, app_ctx):
        """La gobiernan las dos reglas del art. 82.1, que piden justo lo contrario
        —que el certificado conste—: mirarla aquí sería contradecirlas."""
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)

        assert check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='RESOLUCION') is None

    def test_sin_certificado_no_sella(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante
        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        assert check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='CONSULTAS') is None

    def test_el_servicio_bloquea_tambien_con_justificacion(self, arbol_esftt, app_ctx):
        """El invariante va delante del motor en `crear_fase`, y `justificacion` solo
        salta al motor: la puerta cerrada no se fuerza."""
        from app.models.fases import Fase
        from app.services import mutaciones_arbol as svc
        from app.models.tipos_fases import TipoFase
        sol = _certificada(arbol_esftt, app_ctx)
        tipo = TipoFase.query.filter_by(codigo='CONSULTAS').first()
        if tipo is None:
            pytest.skip("TipoFase 'CONSULTAS' no está en el catálogo de esta BD")
        antes = Fase.query.filter_by(solicitud_id=sol.id).count()

        with app_ctx.test_request_context():
            login_user(_usuario())
            res = svc.crear_fase(sol, tipo, justificacion='lo necesito igualmente')

        assert res.ok is False
        assert res.bloqueo is not None and res.bloqueo.puede_escapar is False
        assert Fase.query.filter_by(solicitud_id=sol.id).count() == antes

    def test_el_ambito_es_la_solicitud_no_el_expediente(self, arbol_esftt, app_ctx):
        """El sello se lee de la FK propia (§D). Con dos solicitudes en el mismo
        expediente, el certificado de una no sella la otra."""
        from app.services.invariantes_esftt import check_invariante
        certificada = _certificada(arbol_esftt, app_ctx)
        otra = arbol_esftt.solicitud_nueva()
        assert otra.expediente_id == certificada.expediente_id

        assert check_invariante('CREAR', 'FASE', otra.id, tipo_codigo='CONSULTAS') is None


# ---------------------------------------------------------------------------
# B) El sello al reabrir — el mismo acto por el otro extremo
# ---------------------------------------------------------------------------

class TestSelloAlReabrir:

    def test_una_fase_de_instruccion_cerrada_no_se_reabre(self, arbol_esftt, app_ctx):
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)
        fase = sol.fases[0]

        res = check_invariante('REABRIR', 'FASE', fase.id)

        assert res is not None
        assert 'certificada como terminada' in res.norma_compilada
        assert res.puede_escapar is False

    def test_la_finalizadora_si_se_reabre(self, arbol_esftt, app_ctx):
        """No desmiente el certificado —lo que ocurre dentro de la resolución es
        posterior a él— y es el primer paso del rebobinado que permite deshacerlo."""
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)
        resolucion = _cerrar(arbol_esftt, arbol_esftt.fase('RESOLUCION', solicitud=sol))

        assert check_invariante('REABRIR', 'FASE', resolucion.id) is None

    def test_sin_certificado_se_reabre(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante
        sol = arbol_esftt.solicitud_nueva()
        fase = _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        assert check_invariante('REABRIR', 'FASE', fase.id) is None

    def test_la_resolucion_firme_manda_sobre_el_sello(self, arbol_esftt, app_ctx):
        """Cuando aplican las dos puertas, gana la de #720: con la resolución
        notificada no hay nada que hacer dentro de este flujo, mientras que el sello
        sí tiene salida. Decirle «deshaga el certificado» a quien ya notificó sería
        mandarle por un camino que no le corresponde."""
        from datetime import date
        from app import db
        from app.models.notificaciones import Notificacion
        from app.services.invariantes_esftt import check_invariante

        sol = _certificada(arbol_esftt, app_ctx)
        fase_instruccion = sol.fases[0]
        fase_fin = arbol_esftt.fase('RESOLUCION', solicitud=sol)
        tramite = arbol_esftt.tramite(fase_fin, 'ELABORACION')
        tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
        db.session.add(Notificacion(tarea_id=tarea.id, canal='NOTIFICA',
                                    fecha_puesta_disposicion=date.today()))
        db.session.flush()
        _cerrar(arbol_esftt, fase_fin)
        assert sol.estado.startswith('RESUELTA')

        res = check_invariante('REABRIR', 'FASE', fase_instruccion.id)

        assert res is not None
        assert 'resolución es firme' in res.norma_compilada
        assert 'certificada como terminada' not in res.norma_compilada


# ---------------------------------------------------------------------------
# C) Deshacer el sello
# ---------------------------------------------------------------------------

class TestDeshacer:

    def test_exige_justificacion(self, arbol_esftt, app_ctx):
        sol = _certificada(arbol_esftt, app_ctx)

        res = _deshacer(sol, app_ctx, justificacion='   ')

        assert res.ok is False
        assert 'justificación' in res.error
        assert sol.documento_fin_instruccion_id is not None

    def test_sin_certificado_no_hay_nada_que_deshacer(self, arbol_esftt, app_ctx):
        sol = arbol_esftt.solicitud_nueva()

        res = _deshacer(sol, app_ctx)

        assert res.ok is False
        assert 'no tiene certificado' in res.error

    def test_con_fase_finalizadora_es_puerta_cerrada(self, arbol_esftt, app_ctx):
        """Espejo de la puerta de emisión: aquella exige que no quede abierta ninguna
        fase de instrucción, esta que no exista ninguna de las que el certificado
        habilitó. El rebobinado es previo y lo hace el técnico paso a paso."""
        sol = _certificada(arbol_esftt, app_ctx)
        arbol_esftt.fase('RESOLUCION', solicitud=sol)

        res = _deshacer(sol, app_ctx)

        assert res.ok is False
        assert res.bloqueo is not None and res.bloqueo.puede_escapar is False
        assert 'Resolución' in res.bloqueo.norma_compilada
        assert sol.documento_fin_instruccion_id is not None

    def test_borra_ancla_certificado_documento_y_pdf(self, arbol_esftt, app_ctx):
        from app.models.certificados_fase import CertificadoFase
        from app.models.documentos import Documento

        sol = _certificada(arbol_esftt, app_ctx)
        doc_id = sol.documento_fin_instruccion_id
        cert = CertificadoFase.query.filter_by(documento_id=doc_id).first()
        assert cert is not None and os.path.isfile(cert.ruta_pdf)
        cert_id, ruta = cert.id, cert.ruta_pdf

        res = _deshacer(sol, app_ctx)

        assert res.ok is True
        assert (res.documento_id, res.certificado_id) == (doc_id, cert_id)
        assert sol.documento_fin_instruccion_id is None
        assert Documento.query.get(doc_id) is None
        assert CertificadoFase.query.get(cert_id) is None
        assert not os.path.isfile(ruta)

    def test_el_sello_cae(self, arbol_esftt, app_ctx):
        """Lo que demuestra que el acto sirve para algo: vuelve a haber instrucción."""
        from app.services.invariantes_esftt import check_invariante
        sol = _certificada(arbol_esftt, app_ctx)
        fase = sol.fases[0]
        assert check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='CONSULTAS') is not None

        _deshacer(sol, app_ctx)

        assert check_invariante('CREAR', 'FASE', sol.id, tipo_codigo='CONSULTAS') is None
        assert check_invariante('REABRIR', 'FASE', fase.id) is None

    def test_queda_en_bitacora_y_no_como_escape(self, arbol_esftt, app_ctx):
        """`escape: True` significa «se forzó un bloqueo del motor» en todo el
        sistema, y `_relato_escapes` lo da por supuesto al redactar. Aquí no se
        fuerza nada: la puerta se abre porque sus condiciones se cumplen."""
        from app.models.bitacora import Bitacora
        from app.services.cert_fin_instruccion import ACCION_DESHACER

        sol = _certificada(arbol_esftt, app_ctx)
        doc_id = sol.documento_fin_instruccion_id

        _deshacer(sol, app_ctx, justificacion='faltaba la ronda de consultas')

        fila = (Bitacora.query
                .filter_by(tabla='solicitudes', registro_id=sol.id, operacion='ALTERAR')
                .order_by(Bitacora.id.desc()).first())
        assert fila is not None
        assert fila.detalle['accion'] == ACCION_DESHACER
        assert fila.detalle['justificacion'] == 'faltaba la ronda de consultas'
        assert fila.detalle['documento_id'] == doc_id
        assert 'escape' not in fila.detalle

    def test_se_puede_volver_a_certificar(self, arbol_esftt, app_ctx):
        """El ancla queda libre: era el problema que §E describía del certificado
        emitido con pendientes, y que deshacer resuelve."""
        from app.services.cert_fin_instruccion import consolidar
        sol = _certificada(arbol_esftt, app_ctx)
        primero = sol.documento_fin_instruccion_id

        _deshacer(sol, app_ctx)
        with app_ctx.test_request_context():
            login_user(_usuario())
            res = consolidar(sol)

        assert res.consolidado is True
        assert res.documento_id != primero
        assert sol.documento_fin_instruccion_id == res.documento_id

    def test_certificado_antiguo_sin_vuelta_al_documento(self, arbol_esftt, app_ctx):
        """`CertificadoFase.documento_id` se añadió en la migración 827b: los
        emitidos antes lo tienen a NULL. Se parte del ancla, que existe desde el
        principio y es la que define de quién es el certificado (§D)."""
        from app import db
        from app.models.certificados_fase import CertificadoFase
        from app.models.documentos import Documento

        sol = _certificada(arbol_esftt, app_ctx)
        doc_id = sol.documento_fin_instruccion_id
        cert = CertificadoFase.query.filter_by(documento_id=doc_id).first()
        cert.documento_id = None          # como quedó el 901 de AT-15
        db.session.flush()

        res = _deshacer(sol, app_ctx)

        assert res.ok is True
        assert res.certificado_id is None
        assert sol.documento_fin_instruccion_id is None
        assert Documento.query.get(doc_id) is None


# ---------------------------------------------------------------------------
# D) El certificado siguiente hace constar el anterior
# ---------------------------------------------------------------------------

class TestRelatoDeLaReversion:

    def test_el_informe_lo_relata(self, arbol_esftt, app_ctx):
        """Que se certificara el fin de la instrucción, se retirara y se volviera a
        instruir explica por qué el expediente tiene la forma que tiene, y quien
        redacta la resolución tiene el certificado delante por catálogo."""
        from app.services import informe_instruccion as inf
        sol = _certificada(arbol_esftt, app_ctx)
        _deshacer(sol, app_ctx, justificacion='faltaba consultar al Ayuntamiento')

        relato = ' '.join(inf.revisar(sol).bloques[0].relato)

        assert 'sin efecto un certificado de fin de instrucción anterior' in relato
        assert 'faltaba consultar al Ayuntamiento' in relato

    def test_va_en_el_relato_y_no_entre_los_actos_salvados(self, arbol_esftt, app_ctx):
        """Deshacer no es una desviación salvada bajo criterio: no se forzó ningún
        bloqueo. Es un hecho de la historia de esta instrucción."""
        from app.services import informe_instruccion as inf
        sol = _certificada(arbol_esftt, app_ctx)
        _deshacer(sol, app_ctx)

        informe = inf.revisar(sol)

        assert informe.salvados == []
        assert informe.limpio is True

    def test_sin_reversiones_no_dice_nada(self, arbol_esftt, app_ctx):
        from app.services import informe_instruccion as inf
        sol = _certificada(arbol_esftt, app_ctx)

        relato = ' '.join(inf.revisar(sol).bloques[0].relato)

        assert 'sin efecto' not in relato


# ---------------------------------------------------------------------------
# E) La guarda del pool sobre las tres anclas de solicitud
# ---------------------------------------------------------------------------

class TestGuardaDelPool:

    def test_el_certificado_anclado_no_se_borra_del_pool(self, arbol_esftt, app_ctx):
        """Ninguna de las tres referencias que la guarda ya miraba lo ve: no lo
        consume ninguna tarea mientras la fase que resuelve no exista."""
        from app.models.documentos import Documento
        from app.modules.expedientes.routes import _documento_es_referenciado

        sol = _certificada(arbol_esftt, app_ctx)
        doc = Documento.query.get(sol.documento_fin_instruccion_id)
        assert not doc.vinculos_tarea and doc.notificacion is None

        assert _documento_es_referenciado(doc) is True

    def test_el_motivo_nombra_la_solicitud_y_la_via(self, arbol_esftt, app_ctx):
        from app.models.documentos import Documento
        from app.modules.expedientes.routes import _motivo_ancla

        sol = _certificada(arbol_esftt, app_ctx)
        motivo = _motivo_ancla(Documento.query.get(sol.documento_fin_instruccion_id))

        assert f'#{sol.id}' in motivo
        assert 'deshaga el certificado' in motivo.lower()

    @pytest.mark.parametrize('campo', ['documento_solicitud_id', 'documento_cierre_id'])
    def test_las_otras_dos_anclas_tambien(self, arbol_esftt, campo):
        """Faltaban desde que se creó cada una (ADR-041 §D bis): la FK es NO ACTION,
        así que el borrado moría en IntegrityError en vez de decir quién lo usaba."""
        from app import db
        from app.modules.expedientes.routes import (_documento_es_referenciado,
                                                    _motivo_ancla)
        sol = arbol_esftt.solicitud_nueva()
        doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', f'ancla-{campo}')
        assert _documento_es_referenciado(doc) is False

        setattr(sol, campo, doc.id)
        db.session.flush()
        db.session.refresh(doc)

        assert _documento_es_referenciado(doc) is True
        assert f'#{sol.id}' in _motivo_ancla(doc)

    def test_un_documento_libre_sigue_siendo_borrable(self, arbol_esftt):
        from app.modules.expedientes.routes import (_documento_es_referenciado,
                                                    _motivo_ancla)
        sol = arbol_esftt.solicitud_nueva()
        doc = arbol_esftt.documento(sol.expediente_id, 'MODELO_SOLICITUD', 'suelto-838')

        assert _documento_es_referenciado(doc) is False
        assert _motivo_ancla(doc) is None
