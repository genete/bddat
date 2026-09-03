"""
Tests #827 — la bisagra instrucción/resolución (ADR-043).

Con SQL real (fixture `arbol_esftt`, #715) y `fs_tmp` (#674): el emisor genera un
PDF de verdad, que no debe caer en el servidor de ficheros de desarrollo.

Cuatro bloques:
  A) El invariante del emisor (§E) y sus dos precisiones de #827 — cuenta solo las
     fases de instrucción, y la lista vacía no vale por vacuidad.
  B) El emisor: ancla, snapshot con `fase_id` NULL, PDF en disco, idempotencia.
  C) La bisagra completa: la regla del art. 82.1 bloquea CREAR la finalizadora
     antes de emitir y deja de bloquear después.
  D) El bucle de la auditoría congelada: el snapshot NO sale bloqueado por la
     propia regla que el certificado levanta.
"""
import os

import pytest
from flask_login import login_user


@pytest.fixture(autouse=True)
def _fs_tmp(fs_tmp):
    """FILESYSTEM_BASE al tmp del test — este módulo emite certificados reales."""
    pass


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


def _tipo_fase(codigo):
    from app.models.tipos_fases import TipoFase
    fila = TipoFase.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'TipoFase {codigo!r} no está en el catálogo de esta BD')
    return fila


def _cerrar(arbol, fase):
    """Formaliza el cierre de `fase` con un documento cualquiera del expediente —
    `Fase.finalizada` es exactamente `documento_resultado_id NOT NULL`."""
    from app import db
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'cierre-fase-{fase.id}')
    fase.documento_resultado_id = doc.id
    db.session.flush()
    return fase


def _emitir(arbol, solicitud, app_ctx):
    from app.services.cert_fin_instruccion import emitir_cert_fin_instruccion
    with app_ctx.test_request_context():
        login_user(_usuario())
        return emitir_cert_fin_instruccion(solicitud)


# ---------------------------------------------------------------------------
# A) El invariante del emisor (ADR-043 §E)
# ---------------------------------------------------------------------------

class TestInvarianteEmitir:

    def test_sin_ninguna_fase_bloquea(self, arbol_esftt):
        """Vacuidad: `all([])` es True y certificaría una instrucción inexistente —
        mismo agujero que #723 tapó en `Tramite.finalizado`."""
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()

        res = check_invariante('EMITIR', 'SOLICITUD', sol.id,
                               tipo_codigo='CERT_FIN_INSTRUCCION')

        assert res is not None
        assert res.puede_escapar is False
        assert 'no tiene ninguna fase de instrucción' in res.norma_compilada

    def test_fase_de_instruccion_abierta_bloquea_nombrandola(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)

        res = check_invariante('EMITIR', 'SOLICITUD', sol.id,
                               tipo_codigo='CERT_FIN_INSTRUCCION')

        assert res is not None
        assert res.puede_escapar is False
        assert 'Análisis de Solicitud' in res.norma_compilada

    def test_planificada_tambien_cuenta(self, arbol_esftt):
        """§E: cuentan las planificadas — una fase creada es una fase que alguien
        decidió necesaria; si sobra se borra, si hace falta se termina."""
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))
        planificada = arbol_esftt.fase('CONSULTAS', solicitud=sol)
        assert planificada.estado == 'PLANIFICADA'

        res = check_invariante('EMITIR', 'SOLICITUD', sol.id,
                               tipo_codigo='CERT_FIN_INSTRUCCION')

        assert res is not None
        assert 'Consultas a Organismos' in res.norma_compilada

    def test_finalizadora_abierta_no_bloquea(self, arbol_esftt):
        """Precisión de #827 sobre la letra de §E: contar también la finalizadora
        dejaría el certificado inemitible para siempre en cuanto alguien abriera la
        resolución con la vía de escape que §A admite. Es el caso real de AT-15,
        donde la fase RESOLUCION se creó con la instrucción sin cerrar."""
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))
        arbol_esftt.fase('RESOLUCION', solicitud=sol)

        assert check_invariante('EMITIR', 'SOLICITUD', sol.id,
                                tipo_codigo='CERT_FIN_INSTRUCCION') is None

    def test_resultado_desfavorable_no_impide_certificar(self, arbol_esftt):
        """§B: un desfavorable o un desistimiento cierran la instrucción igual que
        un favorable. Lo que se exige es que estén finalizadas, no cómo."""
        from app import db
        from app.models.tipos_resultados_fases import TipoResultadoFase
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()
        fase = _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))
        desfavorable = TipoResultadoFase.query.filter_by(codigo='DESFAVORABLE').first()
        fase.resultado_fase_id = desfavorable.id
        db.session.flush()

        assert check_invariante('EMITIR', 'SOLICITUD', sol.id,
                                tipo_codigo='CERT_FIN_INSTRUCCION') is None

    def test_sin_tipo_codigo_o_con_otro_sujeto_no_evalua(self, arbol_esftt):
        from app.services.invariantes_esftt import check_invariante

        sol = arbol_esftt.solicitud_nueva()

        assert check_invariante('EMITIR', 'SOLICITUD', sol.id) is None
        assert check_invariante('EMITIR', 'FASE', sol.id,
                                tipo_codigo='CERT_FIN_INSTRUCCION') is None


# ---------------------------------------------------------------------------
# B) El emisor
# ---------------------------------------------------------------------------

class TestEmisor:

    def test_ancla_snapshot_y_pdf(self, arbol_esftt, app_ctx):
        from app.models.certificados_fase import CertificadoFase
        from app.models.documentos import Documento

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        res = _emitir(arbol_esftt, sol, app_ctx)

        assert res.ok is True, res.error
        assert sol.documento_fin_instruccion_id == res.ids[0]

        doc = Documento.query.get(res.ids[0])
        assert doc.tipo_doc.codigo == 'CERT_FIN_INSTRUCCION'
        assert doc.tipo_contenido == 'application/pdf'
        # La url quedó relativa a FILESYSTEM_BASE (ADR-032), no en el placeholder.
        assert not doc.url.startswith('bddat://')
        assert doc.url.endswith('.pdf')

        cert = CertificadoFase.query.filter_by(
            expediente_id=sol.expediente_id, tipo_cert='CERT_FIN_INSTRUCCION'
        ).order_by(CertificadoFase.id.desc()).first()
        # ADR-043 §D: no cuelga de ninguna fase — certifica la instrucción completa.
        assert cert.fase_id is None
        assert os.path.isfile(cert.ruta_pdf)
        assert os.path.getsize(cert.ruta_pdf) > 0

    def test_no_se_reemite(self, arbol_esftt, app_ctx):
        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        primero = _emitir(arbol_esftt, sol, app_ctx)
        segundo = _emitir(arbol_esftt, sol, app_ctx)

        assert primero.ok is True
        assert segundo.ok is False
        assert 'ya está emitido' in segundo.error
        assert sol.documento_fin_instruccion_id == primero.ids[0]

    def test_bloqueado_no_deja_documento_suelto(self, arbol_esftt, app_ctx):
        """La puerta cerrada se comprueba ANTES de crear nada: un intento fallido no
        deja un Documento huérfano en el pool ni un PDF en disco."""
        from app.models.documentos import Documento

        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)  # abierta
        docs_antes = Documento.query.filter_by(expediente_id=sol.expediente_id).count()

        res = _emitir(arbol_esftt, sol, app_ctx)

        assert res.ok is False
        assert res.bloqueo is not None
        assert res.bloqueo.puede_escapar is False
        assert sol.documento_fin_instruccion_id is None
        assert Documento.query.filter_by(
            expediente_id=sol.expediente_id).count() == docs_antes

    def test_fase_finalizadora_por_tipo_de_solicitud(self, app_ctx):
        """El sujeto contra el que se audita sale del tipo de solicitud: la
        solicitud INTERESADO resuelve por RECONOCIMIENTO_INTERESADO (ADR-043 §C)."""
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.cert_fin_instruccion import codigo_fase_finalizadora

        class _SolFake:
            def __init__(self, tipo):
                self.tipo_solicitud = tipo

        interesado = TipoSolicitud.query.filter_by(siglas='INTERESADO').first()
        aap = TipoSolicitud.query.filter_by(siglas='AAP').first()
        if interesado is None or aap is None:
            pytest.skip('Catálogo de tipos_solicitudes incompleto en esta BD')

        assert codigo_fase_finalizadora(_SolFake(interesado)) == 'RECONOCIMIENTO_INTERESADO'
        assert codigo_fase_finalizadora(_SolFake(aap)) == 'RESOLUCION'
        assert codigo_fase_finalizadora(_SolFake(None)) == 'RESOLUCION'


# ---------------------------------------------------------------------------
# C) La bisagra: la regla del art. 82.1 antes y después de emitir
# ---------------------------------------------------------------------------

class TestBisagra:

    def test_regla_bloquea_antes_y_deja_pasar_despues(self, arbol_esftt, app_ctx):
        """Se mira la regla del art. 82.1 en concreto, no `permitido` global: otras
        reglas del catálogo (la tasa del art. 45.1, p. ej.) pueden seguir bloqueando
        por su cuenta, y eso es correcto — el certificado levanta la suya, no las
        demás."""
        from app.services.assembler import auditar_multi, evaluar_multi

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))
        objeto = {'solicitud': sol, 'tipo_fase': _tipo_fase('RESOLUCION')}

        def _regla_821(auditoria):
            reglas = [r for r in auditoria.reglas_evaluadas
                      if 'certificado de fin de instrucción' in (r.descripcion or '')]
            assert reglas, 'la regla del art. 82.1 debe casar con el sujeto RESOLUCION'
            return reglas

        antes = _regla_821(auditar_multi('CREAR', sol.expediente, objeto=objeto))
        assert all(r.disparada for r in antes)
        assert all(not r.neutralizada for r in antes)

        # Y es la que gana en `evaluar`: prioridad 5, por delante de las 36/37/38.
        bloqueo = evaluar_multi('CREAR', sol.expediente, objeto=objeto)
        assert bloqueo.permitido is False
        assert 'certificado de fin de instrucción' in (bloqueo.motivo or bloqueo.norma_compilada)
        # Contenido normativo, no invariante: escapable con justificación (ADR-043 §B).
        assert bloqueo.puede_escapar is True

        assert _emitir(arbol_esftt, sol, app_ctx).ok is True

        despues = _regla_821(auditar_multi('CREAR', sol.expediente, objeto=objeto))
        assert all(not r.disparada for r in despues)

    def test_variable_es_de_la_solicitud_no_del_expediente(self, arbol_esftt, app_ctx):
        """ADR-043 §C/§D: el ámbito es la solicitud. Con dos solicitudes en el mismo
        expediente, el certificado de la primera no vale para la segunda — que es
        exactamente lo que hace mal `cert_fin_ip_consultas._buscar_existente`."""
        from app.services.assembler import build

        primera = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=primera))
        assert _emitir(arbol_esftt, primera, app_ctx).ok is True

        segunda = arbol_esftt.solicitud_nueva()
        assert segunda.expediente_id == primera.expediente_id, (
            'solicitud_nueva debe colgar del mismo expediente para que este test valga')

        _, vars_primera = build(primera.expediente, objeto=primera)
        _, vars_segunda = build(segunda.expediente, objeto=segunda)

        assert vars_primera['solicitud_tiene_cert_fin_instruccion'] is True
        assert vars_segunda['solicitud_tiene_cert_fin_instruccion'] is False


# ---------------------------------------------------------------------------
# D) El bucle de la auditoría congelada (hallazgo de #827)
# ---------------------------------------------------------------------------

class TestSnapshotSinBucle:

    def test_la_regla_del_821_no_sale_disparada_en_el_snapshot(self, arbol_esftt, app_ctx):
        """El certificado se ancla ANTES de auditar. Si se auditara antes, la regla
        del art. 82.1 dispararía —el certificado aún no consta— y el snapshot
        declararía bloqueada la resolución por falta del certificado que lo lleva.
        """
        from app.models.certificados_fase import CertificadoFase

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        assert _emitir(arbol_esftt, sol, app_ctx).ok is True

        cert = CertificadoFase.query.filter_by(
            expediente_id=sol.expediente_id, tipo_cert='CERT_FIN_INSTRUCCION'
        ).order_by(CertificadoFase.id.desc()).first()

        del_821 = [r for r in cert.reglas_evaluadas
                   if 'certificado de fin de instrucción' in (r.get('descripcion') or '')]
        assert del_821, 'la regla del art. 82.1 debe constar entre las evaluadas'
        assert all(r['disparada'] is False for r in del_821)
        # Y consta con su norma citada, que es lo que las 36/37/38 no tienen.
        assert all('82.1' in (r.get('norma_compilada') or '') for r in del_821)

    def test_variables_ctx_recoge_el_certificado_ya_anclado(self, arbol_esftt, app_ctx):
        from app.models.certificados_fase import CertificadoFase

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        assert _emitir(arbol_esftt, sol, app_ctx).ok is True

        cert = CertificadoFase.query.filter_by(
            expediente_id=sol.expediente_id, tipo_cert='CERT_FIN_INSTRUCCION'
        ).order_by(CertificadoFase.id.desc()).first()

        assert cert.variables_ctx['solicitud_tiene_cert_fin_instruccion'] is True
        assert cert.sujeto.endswith('/RESOLUCION')
