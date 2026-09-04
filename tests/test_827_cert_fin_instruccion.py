"""
Tests #827 — la bisagra instrucción/resolución (ADR-043, §E reescrita).

Con SQL real (fixture `arbol_esftt`, #715) y `fs_tmp` (#674): la consolidación
genera un PDF de verdad, que no debe caer en el servidor de ficheros de desarrollo.

El gesto dejó de ser una puerta que concede o deniega y pasó a ser una revisión que
a veces se consolida, así que la mitad de estos tests cambió de premisa: «falta
algo» ya no es un bloqueo, es un informe con pendientes y sin efectos.

Cinco bloques:
  A) El invariante del emisor (§E) y sus dos precisiones — lo único que no cambió.
  B) El informe: las tres categorías, la prosa que sube ya redactada, los escapes
     relatados donde ocurrieron y las fechas derivadas de los documentos.
  C) La consolidación: con pendientes no se crea NADA; sin pendientes, certificado.
  D) La bisagra: la regla del art. 82.1 antes y después, y su ámbito por solicitud.
  E) El snapshot congelado, con el orden nuevo: la regla del 82.1 SÍ consta
     disparada —se evalúa antes de crear nada— y por eso viaja aparte para que el
     PDF la presente como satisfecha por el propio certificado.
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


def _cerrar(arbol, fase, fecha=None):
    """Formaliza el cierre de `fase` con un documento cualquiera del expediente —
    `Fase.finalizada` es exactamente `documento_resultado_id NOT NULL`. La fecha
    administrativa de ese documento es la que el informe deriva como fecha de
    cierre: las fases no guardan fecha propia (§2.bis DISEÑO_FECHAS_PLAZOS)."""
    from app import db
    doc = arbol.documento(fase.solicitud.expediente_id, 'MODELO_SOLICITUD',
                          f'cierre-fase-{fase.id}')
    if fecha is not None:
        doc.fecha_administrativa = fecha
    fase.documento_resultado_id = doc.id
    db.session.flush()
    return fase


def _escape(tabla, registro_id, *, operacion='ALTERAR', justificacion='porque sí',
            motivo=None, accion=None):
    """Registra en bitácora un escape sobre un nodo, como lo haría el forzado real."""
    from app import db
    from app.models.bitacora import Bitacora
    detalle = {'escape': True, 'justificacion': justificacion, 'sujeto': 'X/Y/Z'}
    if motivo:
        detalle['motivo'] = motivo
    if accion:
        detalle['accion'] = accion
    fila = Bitacora(usuario_id=_usuario().id, operacion=operacion, tabla=tabla,
                    registro_id=registro_id, detalle=detalle)
    db.session.add(fila)
    db.session.flush()
    return fila


def _cumplir_requisitos(arbol, solicitud):
    """Cubre los requisitos documentales activos de la solicitud.

    Sin esto, `tasa_impagada` (art. 45.1) deja al motor bloqueando la creación de la
    fase finalizadora y ningún informe sale limpio — que es correcto, pero impide
    probar el camino de la consolidación."""
    from app import db
    from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
    requisitos = RequisitoDocumental.query.filter(
        RequisitoDocumental.activo.is_(True)).all()
    for req in requisitos:
        doc = arbol.documento(solicitud.expediente_id, 'MODELO_SOLICITUD',
                              f'req-{req.id}-sol-{solicitud.id}')
        db.session.add(DocumentoRequisito(requisito_id=req.id,
                                          solicitud_id=solicitud.id,
                                          documento_id=doc.id))
    db.session.flush()


def _consolidar(solicitud, app_ctx):
    from app.services.cert_fin_instruccion import consolidar
    with app_ctx.test_request_context():
        login_user(_usuario())
        return consolidar(solicitud)


def _solicitud_certificable(arbol, *, codigo_fase='ANALISIS_SOLICITUD'):
    """Solicitud con una fase de instrucción cerrada y los requisitos cubiertos:
    el caso en que la revisión debe salir limpia."""
    sol = arbol.solicitud_nueva()
    _cerrar(arbol, arbol.fase(codigo_fase, solicitud=sol))
    _cumplir_requisitos(arbol, sol)
    return sol


def _pendientes(informe):
    """Todas las frases de pendiente del informe, aplanadas."""
    return [linea for b in informe.pendientes for linea in b.pendiente]


# ---------------------------------------------------------------------------
# A) El invariante del emisor (ADR-043 §E) — la puerta cerrada, que no cambia
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
# B) El informe (ADR-043 §E/§E bis)
# ---------------------------------------------------------------------------

class TestInforme:

    def test_solicitud_sin_fases_habla_de_si_misma(self, arbol_esftt):
        """El agujero de vacuidad que ningún bloque de fase puede cubrir: no hay
        nodos que hablen, así que lo dice la propia solicitud."""
        from app.services.informe_instruccion import PENDIENTE, revisar

        informe = revisar(arbol_esftt.solicitud_nueva())

        assert informe.limpio is False
        propio = informe.bloques[0]
        assert propio.categoria == PENDIENTE
        assert propio.nodo[0] == 'solicitud'
        assert 'no tiene ninguna fase de instrucción' in propio.pendiente[0]

    def test_fase_cerrada_relata_su_cierre_con_la_fecha_derivada(self, arbol_esftt):
        """Ni fases ni trámites guardan fecha propia: la del cierre sale del
        documento que lo formaliza."""
        from datetime import date

        from app.services.informe_instruccion import PASA, revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        _cerrar(arbol_esftt, fase, fecha=date(2026, 3, 17))

        informe = revisar(sol)

        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert bloque.categoria == PASA
        assert any('17/03/2026' in linea for linea in bloque.relato)
        assert any('Análisis de Solicitud' in linea for linea in bloque.relato)
        assert bloque.pendiente == ()

    def test_tramite_sin_tareas_es_pendiente_y_lo_dice_la_fase(self, arbol_esftt):
        """La prosa sube ya redactada: el trámite escribe su frase y la fase la
        recoge sin volver a componerla (§E bis)."""
        from app.services.informe_instruccion import PENDIENTE, revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')

        informe = revisar(sol)

        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert bloque.categoria == PENDIENTE
        assert any('no tiene ninguna tarea' in linea for linea in bloque.pendiente)
        assert informe.limpio is False

    def test_tarea_pendiente_sube_su_motivo_hasta_la_fase(self, arbol_esftt):
        """El motivo lo pone `estado_dominio`, no una redacción nueva: es el mismo
        vocabulario que el técnico ve en árbol y seguimiento (#558). Y la tarea se
        nombra en prosa: `TipoTarea.nombre` es una descripción de catálogo
        impresentable en una frase, y `abrev` es el código en mayúsculas."""
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)
        tramite = arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')
        arbol_esftt.tarea(tramite, 'ANALIZAR')

        informe = revisar(sol)

        lineas = _pendientes(informe)
        de_la_tarea = [l for l in lineas if 'Análisis técnico o jurídico' in l]
        assert de_la_tarea, f'la tarea debe nombrarse en prosa; salió: {lineas}'
        assert 'falta iniciar o completar una tarea' in de_la_tarea[0]
        # Y la fase la cita porque el trámite se la subió ya escrita (§E bis).
        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert any('Análisis técnico o jurídico' in l for l in bloque.pendiente)

    def test_escape_se_relata_donde_ocurrio_y_no_impide_certificar(self, arbol_esftt):
        """§E, categoría 2: el criterio motivado del tramitador es superior a la
        regla —para eso existe el escape— y por eso queda escrito y no escondido."""
        from app.services.informe_instruccion import SALVADO, revisar

        sol = _solicitud_certificable(arbol_esftt)
        fase = sol.fases[0]
        _escape('fases', fase.id, justificacion='cerrada con el informe verbal',
                motivo='El trámite "X" no está completo.')

        informe = revisar(sol)

        bloque = next(b for b in informe.bloques if b.nodo == ('fase', fase.id))
        assert bloque.categoria == SALVADO
        assert bloque.salvado, 'el escape debe relatarse en el bloque de su nodo'
        texto = bloque.salvado[0]
        assert 'cerrada con el informe verbal' in texto
        assert 'El trámite "X" no está completo' in texto
        # Y no impide: los pendientes no lo mencionan, y el informe sigue limpio.
        assert informe.limpio is True
        assert bloque.pendiente == ()

    def test_el_escape_no_se_repite_en_el_relato(self, arbol_esftt):
        """Tres registros distintos y sin solapamiento: si el escape estuviera
        además en `relato`, el PDF lo imprimiría dos veces."""
        from app.services.informe_instruccion import revisar

        sol = _solicitud_certificable(arbol_esftt)
        _escape('fases', sol.fases[0].id, justificacion='una razón concreta')

        informe = revisar(sol)

        relato = [linea for b in informe.bloques for linea in b.relato]
        assert not any('una razón concreta' in linea for linea in relato)
        assert any('una razón concreta' in linea
                   for b in informe.salvados for linea in b.salvado)

    def test_la_regla_del_821_no_cuenta_como_pendiente(self, arbol_esftt):
        """§E ter: es la única que este acto satisface, y esperar a que deje de
        disparar sola sería esperar a nunca."""
        from app.services.informe_instruccion import revisar

        sol = _solicitud_certificable(arbol_esftt)

        informe = revisar(sol)

        assert informe.reglas_del_acto, 'las reglas del art. 82.1 deben localizarse'
        assert not any('fin de instrucción' in linea for linea in _pendientes(informe))
        assert informe.limpio is True, f'pendientes inesperados: {_pendientes(informe)}'

    def test_una_regla_del_motor_bloqueante_es_un_pendiente_y_solo_uno(self, arbol_esftt):
        """La tasa del art. 45.1 impide certificar, y aparece UNA vez aunque
        `auditar_multi` audite una vez por tipo simple de la solicitud."""
        from app.services.informe_instruccion import revisar

        sol = arbol_esftt.solicitud_nueva()
        _cerrar(arbol_esftt, arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol))

        informe = revisar(sol)

        de_la_tasa = [linea for linea in _pendientes(informe) if 'tasa' in linea.lower()]
        if not de_la_tasa:
            pytest.skip('El catálogo de esta BD no tiene la regla de la tasa activa')
        assert len(de_la_tasa) == 1
        assert '45.1' in de_la_tasa[0]
        assert informe.limpio is False


# ---------------------------------------------------------------------------
# C) La consolidación (ADR-043 §E ter)
# ---------------------------------------------------------------------------

class TestConsolidacion:

    def test_con_pendientes_no_crea_nada(self, arbol_esftt, app_ctx):
        """El cambio de premisa de §E: que falte algo no es un error ni un bloqueo,
        y sobre todo no deja un certificado que diga «esto no está listo» ocupando
        el ancla de §D."""
        from app.models.certificados_fase import CertificadoFase
        from app.models.documentos import Documento

        sol = arbol_esftt.solicitud_nueva()
        arbol_esftt.fase('ANALISIS_SOLICITUD', solicitud=sol)   # abierta
        docs_antes = Documento.query.filter_by(expediente_id=sol.expediente_id).count()
        certs_antes = CertificadoFase.query.filter_by(
            expediente_id=sol.expediente_id).count()

        res = _consolidar(sol, app_ctx)

        assert res.consolidado is False
        assert res.error is None and res.bloqueo is None
        assert res.informe.limpio is False
        assert sol.documento_fin_instruccion_id is None
        assert Documento.query.filter_by(
            expediente_id=sol.expediente_id).count() == docs_antes
        assert CertificadoFase.query.filter_by(
            expediente_id=sol.expediente_id).count() == certs_antes

    def test_sin_pendientes_consolida_y_ancla(self, arbol_esftt, app_ctx):
        from app.models.certificados_fase import CertificadoFase
        from app.models.documentos import Documento

        sol = _solicitud_certificable(arbol_esftt)

        res = _consolidar(sol, app_ctx)

        assert res.consolidado is True, f'pendientes: {_pendientes(res.informe)}'
        assert sol.documento_fin_instruccion_id == res.documento_id

        doc = Documento.query.get(res.documento_id)
        assert doc.tipo_doc.codigo == 'CERT_FIN_INSTRUCCION'
        assert doc.tipo_contenido == 'application/pdf'
        # La url es relativa a FILESYSTEM_BASE (ADR-032) y definitiva desde el
        # principio: ya no hay url provisional que completar después.
        assert not doc.url.startswith('bddat://')
        assert doc.url.endswith('.pdf')
        assert f'#{sol.id}' in (doc.asunto or '')

        cert = CertificadoFase.query.get(res.certificado_id)
        # ADR-043 §D: no cuelga de ninguna fase — certifica la instrucción completa.
        assert cert.fase_id is None
        # La vuelta que faltaba (#827) y que #838 necesitará para deshacer el sello.
        assert cert.documento_id == res.documento_id
        assert os.path.isfile(cert.ruta_pdf)
        assert os.path.getsize(cert.ruta_pdf) > 0

    def test_no_se_reemite(self, arbol_esftt, app_ctx):
        sol = _solicitud_certificable(arbol_esftt)

        primero = _consolidar(sol, app_ctx)
        segundo = _consolidar(sol, app_ctx)

        assert primero.consolidado is True
        assert segundo.consolidado is False
        assert 'ya está emitido' in segundo.error
        assert sol.documento_fin_instruccion_id == primero.documento_id

    def test_la_consolidacion_queda_en_bitacora(self, arbol_esftt, app_ctx):
        from app.models.bitacora import Bitacora

        sol = _solicitud_certificable(arbol_esftt)

        res = _consolidar(sol, app_ctx)

        entrada = (Bitacora.query
                   .filter_by(tabla='documentos', registro_id=res.documento_id)
                   .order_by(Bitacora.id.desc()).first())
        assert entrada is not None
        assert entrada.detalle['tipo_documento'] == 'CERT_FIN_INSTRUCCION'
        assert entrada.detalle['solicitud_id'] == sol.id
        assert entrada.detalle['certificado_fase_id'] == res.certificado_id

    def test_el_informe_viaja_tambien_cuando_consolida(self, arbol_esftt, app_ctx):
        """El endpoint responde siempre con el informe, consolidado o no."""
        sol = _solicitud_certificable(arbol_esftt)

        datos = _consolidar(sol, app_ctx).a_dict()

        assert datos['consolidado'] is True
        assert datos['limpio'] is True
        assert datos['documento_id'] is not None
        assert datos['bloques'], 'el informe debe llevar el relato de lo instruido'
        assert datos['pendientes'] == []


# ---------------------------------------------------------------------------
# D) La bisagra: la regla del art. 82.1 antes y después de consolidar
# ---------------------------------------------------------------------------

class TestBisagra:

    def test_regla_bloquea_antes_y_deja_pasar_despues(self, arbol_esftt, app_ctx):
        """Se mira la regla del art. 82.1 en concreto, no `permitido` global: otras
        reglas del catálogo pueden seguir bloqueando por su cuenta, y eso es
        correcto — el certificado levanta la suya, no las demás."""
        from app.services.assembler import auditar_multi, evaluar_multi

        sol = _solicitud_certificable(arbol_esftt)
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
        # Y desde #827 el mensaje señala la salida en vez de prohibir a secas.
        assert 'informe' in (bloqueo.motivo or '')

        assert _consolidar(sol, app_ctx).consolidado is True

        despues = _regla_821(auditar_multi('CREAR', sol.expediente, objeto=objeto))
        assert all(not r.disparada for r in despues)

    def test_variable_es_de_la_solicitud_no_del_expediente(self, arbol_esftt, app_ctx):
        """ADR-043 §C/§D: el ámbito es la solicitud. Con dos solicitudes en el mismo
        expediente, el certificado de la primera no vale para la segunda — que es
        exactamente lo que hace mal `cert_fin_ip_consultas._buscar_existente`."""
        from app.services.assembler import build

        primera = _solicitud_certificable(arbol_esftt)
        assert _consolidar(primera, app_ctx).consolidado is True

        segunda = arbol_esftt.solicitud_nueva()
        assert segunda.expediente_id == primera.expediente_id, (
            'solicitud_nueva debe colgar del mismo expediente para que este test valga')

        _, vars_primera = build(primera.expediente, objeto=primera)
        _, vars_segunda = build(segunda.expediente, objeto=segunda)

        assert vars_primera['solicitud_tiene_cert_fin_instruccion'] is True
        assert vars_segunda['solicitud_tiene_cert_fin_instruccion'] is False

    def test_fase_finalizadora_por_tipo_de_solicitud(self, app_ctx):
        """El sujeto contra el que se audita sale del tipo de solicitud: la
        solicitud INTERESADO resuelve por RECONOCIMIENTO_INTERESADO (ADR-043 §C)."""
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.services.informe_instruccion import codigo_fase_finalizadora

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
# E) El snapshot congelado, con el orden de §E ter
# ---------------------------------------------------------------------------

class TestSnapshotDelActo:

    def test_la_regla_del_821_consta_disparada_y_se_marca_aparte(self, arbol_esftt, app_ctx):
        """Cambio de premisa respecto al diseño anterior. Antes se anclaba el
        documento ANTES de auditar para que la regla no saliera disparada; ahora se
        evalúa primero y no se crea nada hasta que la revisión sale limpia, así que
        la regla consta disparada — y es cierto que lo estaba en ese momento.

        Lo que impide que el certificado se desmienta a sí mismo no es maquillar el
        snapshot, sino que sus ids viajen en `reglas_del_acto` para que el PDF las
        presente como satisfechas por el propio certificado."""
        from app.models.certificados_fase import CertificadoFase

        sol = _solicitud_certificable(arbol_esftt)

        res = _consolidar(sol, app_ctx)
        assert res.consolidado is True

        cert = CertificadoFase.query.get(res.certificado_id)
        del_821 = [r for r in cert.reglas_evaluadas
                   if r['regla_id'] in res.informe.reglas_del_acto]
        assert del_821, 'la regla del art. 82.1 debe constar entre las evaluadas'
        assert all(r['disparada'] is True for r in del_821)
        # Y consta con su norma citada, que es lo que las 36/37/38 no tienen.
        assert all('82.1' in (r.get('norma_compilada') or '') for r in del_821)

    def test_ninguna_otra_regla_bloqueante_queda_disparada(self, arbol_esftt, app_ctx):
        """Lo que sí garantiza el orden nuevo: si algo más bloqueaba, no se habría
        consolidado. El snapshot de un certificado emitido no puede tener ninguna
        regla bloqueante viva que no sea la del propio acto."""
        from app.models.certificados_fase import CertificadoFase

        sol = _solicitud_certificable(arbol_esftt)

        res = _consolidar(sol, app_ctx)
        assert res.consolidado is True

        cert = CertificadoFase.query.get(res.certificado_id)
        vivas = [r for r in cert.reglas_evaluadas
                 if r['disparada'] and not r['neutralizada']
                 and r['efecto'] == 'BLOQUEAR'
                 and r['regla_id'] not in res.informe.reglas_del_acto]
        assert vivas == [], f'reglas bloqueantes en un certificado emitido: {vivas}'

    def test_variables_ctx_recoge_el_estado_del_momento(self, arbol_esftt, app_ctx):
        from app.models.certificados_fase import CertificadoFase

        sol = _solicitud_certificable(arbol_esftt)

        res = _consolidar(sol, app_ctx)
        cert = CertificadoFase.query.get(res.certificado_id)

        # False, no True: el snapshot es de antes de crear el certificado.
        assert cert.variables_ctx['solicitud_tiene_cert_fin_instruccion'] is False
        assert cert.sujeto.endswith('/RESOLUCION')
