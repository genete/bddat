"""
Tests de fricción simétrica — #724.

Dos ejes, ambos extienden la escalera de reversión de ADR-033 §5 (#714 ya había
añadido el criterio de vigencia dentro de la cadena de subsanación):

  1. Revertir un diagnóstico cuando el ELABORAR de la vuelta que desencadenó ya
     produjo el escrito (redactado o firmado) pero aún no se ha notificado —
     antes libre, ahora forzable con justificación
     (`diagnosticos._hay_elaborar_producido_sin_notificar_en_cadena`).
  2. Modificar un check documental/técnico/requerimiento que ya figuraba en un
     diagnóstico NOTIFICADO de una vuelta anterior de la cadena — antes libre
     (el candado de `_candado_diagnostico_producido` solo mira la tarea
     actual), ahora forzable con justificación
     (`diagnosticos.diagnostico_donde_se_exigio_item`/
     `diagnostico_donde_se_exigio_requerimiento`, sobre
     `invariantes_esftt.diagnosticos_notificados_cadena`).

Montan el árbol de verdad en BD (mismo patrón que test_714/test_717: app_ctx con
rollback por SAVEPOINT) porque ambos criterios navegan relaciones reales
(fase.tramites, tramite.tareas) que un stub no reproduce fielmente. Los
`defectos` de cada `Diagnostico` se fijan a mano en el test (JSONB arbitrario) —
no hace falta catálogo real de requisitos/ítems técnicos para probar el
emparejamiento por id, solo su forma (ver consolidacion_defectos.py).
"""
import datetime

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _montar_fase(codigo_fase, specs):
    """Monta una fase con trámites de la cadena de subsanación (u otra, para los
    casos "fuera de la cadena").

    `specs` es una lista de dicts:
      - tramite: código de trámite (p.ej. 'ANALISIS_DOCUMENTAL')
      - resultado: resultado del diagnóstico de su ANALIZAR, o None si no produce
      - defectos: lista de dicts para Diagnostico.defectos (default [])
      - notificado: True si el trámite lleva un NOTIFICAR (anterior al ANALIZAR,
        orden real del flujo: notifica el requerimiento de ESA vuelta, apoyado en
        el diagnóstico de la vuelta ANTERIOR) con fila en `notificaciones`
      - elaborar_producido: True si el trámite lleva un ELABORAR con documento
        PRODUCIDO (antes del NOTIFICAR, si lo hay — mismo orden real)

    Devuelve (fase, tareas_analizar) — tareas_analizar en el mismo orden que specs.
    """
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico
    from app.models.notificaciones import Notificacion
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_documentos import TipoDocumento

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    tipo_analizar = _tipo(TipoTarea, 'ANALIZAR')
    tipo_notificar = _tipo(TipoTarea, 'NOTIFICAR')
    tipo_elaborar = _tipo(TipoTarea, 'ELABORAR')
    tipo_diagnostico = _tipo(TipoDocumento, 'DIAGNOSTICO')
    tipo_doc_generico = TipoDocumento.query.first()
    if tipo_doc_generico is None:
        pytest.skip('No hay tipos de documento en el catálogo de esta BD')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, codigo_fase).id)
    db.session.add(fase)
    db.session.flush()

    tareas_analizar = []
    for spec in specs:
        tramite = Tramite(fase_id=fase.id,
                          tipo_tramite_id=_tipo(TipoTramite, spec['tramite']).id)
        db.session.add(tramite)
        db.session.flush()

        if spec.get('elaborar_producido'):
            elaborar = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_elaborar.id)
            db.session.add(elaborar)
            db.session.flush()
            doc_escrito = Documento(expediente_id=solicitud.expediente_id,
                                    tipo_doc_id=tipo_doc_generico.id,
                                    url=f'test-724-escrito-{elaborar.id}.odt')
            db.session.add(doc_escrito)
            db.session.flush()
            db.session.add(DocumentoTarea(tarea_id=elaborar.id, documento_id=doc_escrito.id, rol='PRODUCIDO'))
            db.session.flush()

        if spec.get('notificado'):
            notificar = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_notificar.id)
            db.session.add(notificar)
            db.session.flush()
            db.session.add(Notificacion(
                tarea_id=notificar.id, canal='NOTIFICA',
                fecha_puesta_disposicion=datetime.date(2026, 7, 20), numero_intento=1,
            ))
            db.session.flush()

        tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_analizar.id)
        db.session.add(tarea)
        db.session.flush()
        tareas_analizar.append(tarea)

        resultado = spec.get('resultado')
        if resultado is None:
            continue

        doc = Documento(expediente_id=solicitud.expediente_id,
                        tipo_doc_id=tipo_diagnostico.id,
                        url=f'bddat://diagnosticos/test-724-{tarea.id}')
        db.session.add(doc)
        db.session.flush()
        db.session.add(Diagnostico(documento_id=doc.id, resultado=resultado,
                                   defectos=spec.get('defectos', [])))
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()

    return fase, tareas_analizar


# ---------------------------------------------------------------------------
# Punto 1 — progreso aguas abajo sin notificar (peldaño 2 ter, forzable)
# ---------------------------------------------------------------------------

class TestProgresoAguasAbajoSinNotificar:

    def test_elaborar_producido_sin_notificar_bloquea_forzable(self, app_ctx):
        """El escenario que motiva #724: escrito redactado/firmado, aún sin
        notificar. Antes de este cambio, revertir aquí era libre."""
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'elaborar_producido': True},
        ])

        bloqueo = _motivo_diagnostico_superado(tareas[0])
        assert bloqueo is not None
        assert bloqueo.puede_escapar is True
        assert 'notificado' in bloqueo.motivo

    def test_sin_elaborar_producido_no_bloquea(self, app_ctx):
        """ADR-033 §5: un REQUERIMIENTO_SUBSANACION creado pero sin ELABORAR
        producido sigue siendo "sin progreso" — su destino es borrarse, libre."""
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION'},
        ])

        assert _motivo_diagnostico_superado(tareas[0]) is None

    def test_elaborar_producido_y_notificado_manda_ya_comunicado(self, app_ctx):
        """Si además ya se notificó, gana el criterio 1 (#714) — puerta cerrada,
        no el nuevo criterio forzable: evaluar antes el forzable dejaría
        escapable un caso ya notificado (mismo razonamiento que #714)."""
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'elaborar_producido': True, 'notificado': True},
        ])

        bloqueo = _motivo_diagnostico_superado(tareas[0])
        assert bloqueo is not None
        assert bloqueo.puede_escapar is False
        assert 'comunicado al titular' in bloqueo.motivo

    def test_elaborar_de_vuelta_mas_lejana_tambien_bloquea(self, app_ctx):
        """El progreso aguas abajo no tiene que ser de la vuelta inmediatamente
        siguiente — cualquier ELABORAR posterior en la cadena cuenta."""
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'elaborar_producido': True},
        ])

        bloqueo = _motivo_diagnostico_superado(tareas[1])
        assert bloqueo is not None
        assert bloqueo.puede_escapar is True

    def test_forzar_con_justificacion_revierte_y_deja_rastro_en_bitacora(self, app_ctx):
        from flask_login import login_user
        from app.models.usuarios import Usuario
        from app.models.bitacora import Bitacora
        from app.models.diagnosticos import Diagnostico
        from app.services.diagnosticos import revertir_diagnostico

        usuario = Usuario.query.first()
        if usuario is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable'},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'elaborar_producido': True},
        ])
        tarea = tareas[0]
        diag_id = tarea.documento_producido.diagnostico.id

        with app_ctx.test_request_context():
            login_user(usuario)
            revertir_diagnostico(tarea, justificacion='El escrito tenía un error, lo rehago')

        assert Diagnostico.query.filter_by(id=diag_id).first() is None
        entrada = (
            Bitacora.query
            .filter_by(tabla='tareas', registro_id=tarea.id, operacion='ALTERAR')
            .order_by(Bitacora.id.desc())
            .first()
        )
        assert entrada is not None
        assert entrada.detalle['escape'] is True
        assert entrada.detalle['justificacion'] == 'El escrito tenía un error, lo rehago'


# ---------------------------------------------------------------------------
# Punto 2 — recorrido de la cadena notificada (varias vueltas, no solo un salto)
# ---------------------------------------------------------------------------

class TestDiagnosticosNotificadosCadena:
    """invariantes_esftt.diagnosticos_notificados_cadena — recorre toda la
    cadena hacia atrás (#724, Carlos: "no son solo dos vueltas, hay expedientes
    con varias")."""

    def test_dos_vueltas_devuelve_el_diagnostico_notificado(self, app_ctx):
        from app.services.invariantes_esftt import diagnosticos_notificados_cadena

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 1', 'origen': 'documental', 'requisito_id': 1}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 2', 'origen': 'documental', 'requisito_id': 2}]},
        ])
        tramite_actual = tareas[-1].tramite

        resultado = diagnosticos_notificados_cadena(tramite_actual)

        assert len(resultado) == 1
        assert resultado[0].defectos[0]['requisito_id'] == 1

    def test_tres_vueltas_mas_reciente_primero(self, app_ctx):
        from app.services.invariantes_esftt import diagnosticos_notificados_cadena

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 1', 'origen': 'documental', 'requisito_id': 1}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 2', 'origen': 'documental', 'requisito_id': 2}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 3', 'origen': 'documental', 'requisito_id': 3}]},
        ])
        tramite_actual = tareas[-1].tramite

        resultado = diagnosticos_notificados_cadena(tramite_actual)

        assert [d.defectos[0]['texto'] for d in resultado] == ['Vuelta 2', 'Vuelta 1']

    def test_hueco_sin_notificar_no_corta_el_recorrido_hacia_atras(self, app_ctx):
        """Un hueco sin notificar es raro (implica una vuelta creada sin haber
        notificado la anterior), pero no debe esconder vueltas más antiguas que
        sí se notificaron correctamente."""
        from app.services.invariantes_esftt import diagnosticos_notificados_cadena

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 1', 'origen': 'documental', 'requisito_id': 1}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 2', 'origen': 'documental', 'requisito_id': 2}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Vuelta 3', 'origen': 'documental', 'requisito_id': 3}]},
        ])
        tramite_actual = tareas[-1].tramite

        resultado = diagnosticos_notificados_cadena(tramite_actual)

        assert [d.defectos[0]['texto'] for d in resultado] == ['Vuelta 1']

    def test_fuera_de_la_cadena_no_devuelve_nada(self, app_ctx):
        from app.services.invariantes_esftt import diagnosticos_notificados_cadena

        _, tareas = _montar_fase('CONSULTAS', [
            {'tramite': 'CONSULTA_SEPARATA', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'X', 'origen': 'documental', 'requisito_id': 1}]},
            {'tramite': 'CONSULTA_SEPARATA', 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnosticos_notificados_cadena(tareas[-1].tramite) == []


# ---------------------------------------------------------------------------
# Punto 2 — emparejamiento por ítem (documental/técnico/requerimiento)
# ---------------------------------------------------------------------------

class TestDiagnosticoDondeSeExigio:

    def test_item_documental_encontrado_en_vuelta_notificada(self, app_ctx):
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Falta el anejo X', 'origen': 'documental', 'requisito_id': 42}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        defecto = diagnostico_donde_se_exigio_item(tareas[-1], 'documental', 42)

        assert defecto is not None
        assert defecto['texto'] == 'Falta el anejo X'

    def test_item_tecnico_encontrado_en_vuelta_notificada(self, app_ctx):
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Falta anejo de cálculo', 'origen': 'tecnico', 'item_tecnico_id': 7}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        defecto = diagnostico_donde_se_exigio_item(tareas[-1], 'tecnico', 7)

        assert defecto is not None

    def test_item_no_exigido_antes_devuelve_none(self, app_ctx):
        """Ítem nunca mencionado en una vuelta notificada: exigencia nueva y
        legítima, no hay de qué desdecirse — "se le pudo pasar y siempre
        estamos a tiempo de pedirlo"."""
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Falta el anejo X', 'origen': 'documental', 'requisito_id': 42}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnostico_donde_se_exigio_item(tareas[-1], 'documental', 999) is None

    def test_diagnostico_no_notificado_no_cuenta_como_ya_exigido(self, app_ctx):
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Falta el anejo X', 'origen': 'documental', 'requisito_id': 42}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnostico_donde_se_exigio_item(tareas[-1], 'documental', 42) is None

    def test_defecto_legacy_sin_id_no_bloquea(self, app_ctx):
        """Diagnósticos producidos antes de #724 no llevan requisito_id/
        item_tecnico_id — degradación aceptada (la BD de desarrollo es
        desechable, no se protege retroactivamente)."""
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Falta algo', 'origen': 'documental'}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnostico_donde_se_exigio_item(tareas[-1], 'documental', 42) is None

    def test_requerimiento_de_catalogo_empareja_por_id_no_por_texto(self, app_ctx):
        """El id de RequerimientoTarea no es estable (se borra y recrea en cada
        guardado del shuttle); el de catálogo sí — el emparejamiento debe usar
        ese, no el texto, para sobrevivir a una reformulación del texto."""
        from app.services.diagnosticos import diagnostico_donde_se_exigio_requerimiento

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Aportar certificado', 'origen': 'requerimiento',
                          'catalogo_requerimientos_id': 7}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        defecto = diagnostico_donde_se_exigio_requerimiento(
            tareas[-1], catalogo_requerimientos_id=7, texto='Aportar certificado (texto reformulado)',
        )
        assert defecto is not None

    def test_requerimiento_libre_empareja_por_texto_exacto(self, app_ctx):
        from app.services.diagnosticos import diagnostico_donde_se_exigio_requerimiento

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            {'tramite': 'ANALISIS_DOCUMENTAL', 'resultado': 'desfavorable',
             'defectos': [{'texto': 'Redacción manual del requerimiento', 'origen': 'requerimiento',
                          'catalogo_requerimientos_id': None}]},
            {'tramite': 'REQUERIMIENTO_SUBSANACION', 'notificado': True, 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnostico_donde_se_exigio_requerimiento(
            tareas[-1], catalogo_requerimientos_id=None, texto='Redacción manual del requerimiento',
        ) is not None
        assert diagnostico_donde_se_exigio_requerimiento(
            tareas[-1], catalogo_requerimientos_id=None, texto='Texto distinto',
        ) is None

    def test_fuera_de_la_cadena_no_aplica(self, app_ctx):
        """CONSULTA_SEPARATA no es cadena de subsanación (#711, en espejo): no
        hay "vuelta anterior" de la que desdecirse."""
        from app.services.diagnosticos import diagnostico_donde_se_exigio_item

        _, tareas = _montar_fase('CONSULTAS', [
            {'tramite': 'CONSULTA_SEPARATA', 'notificado': True, 'resultado': 'desfavorable',
             'defectos': [{'texto': 'X', 'origen': 'documental', 'requisito_id': 1}]},
            {'tramite': 'CONSULTA_SEPARATA', 'resultado': 'desfavorable', 'defectos': []},
        ])

        assert diagnostico_donde_se_exigio_item(tareas[-1], 'documental', 1) is None
