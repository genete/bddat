"""
Tests de la vigencia del diagnóstico al revertir — #714 (tapa el peldaño 3 de ADR-033 §5).

El check de `CONSUMIDO` de #678 no protege nada mientras nada cree ese vínculo (#717):
hoy se podía revertir un diagnóstico ya volcado en un requerimiento notificado. #714
añade el criterio de vigencia, simétrico al de #711.

Los tests montan el árbol de verdad en BD y revierten por el SAVEPOINT de `app_ctx`:
ninguno llega a ejecutar la reversión (que sí hace `commit()` — ver la nota de
test_678_reversion_diagnostico.py), porque todos comprueban el bloqueo *antes* de que
se toque nada. El caso reversible se comprueba sobre `_motivo_diagnostico_superado`,
por el mismo motivo: verifica el criterio sin destruir datos.

Ejes que cubren:
  - Superado por vuelta posterior (criterio 1).
  - Ya comunicado al titular: NOTIFICAR posterior con fila en `notificaciones`
    (criterio 2) — la ventana que el criterio 1 no alcanza.
  - Fuera de la cadena (CONSULTA_SEPARATA): diagnósticos paralelos, ninguno supera a
    otro, la reversión no se toca.
"""
import datetime

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _montar_fase(codigo_fase, specs):
    """Monta una fase nueva y devuelve (fase, tareas_analizar).

    `specs` es una lista de tuplas (codigo_tramite, resultado_diagnostico, notificado):
      - resultado_diagnostico None → el trámite no produce diagnóstico
      - notificado True → el trámite lleva además una tarea NOTIFICAR **anterior** a su
        ANALIZAR (el orden real: se notifica el requerimiento y luego se analiza lo que
        el titular aporte) con su fila de `notificaciones`

    Las tareas se crean en el orden del flujo, así que el orden por `id` reproduce el
    del árbol real — que es el único orden disponible (no hay columnas de fecha).
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
    tipo_diagnostico = _tipo(TipoDocumento, 'DIAGNOSTICO')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, codigo_fase).id)
    db.session.add(fase)
    db.session.flush()

    tareas_analizar = []
    for codigo_tramite, resultado, notificado in specs:
        tramite = Tramite(fase_id=fase.id,
                          tipo_tramite_id=_tipo(TipoTramite, codigo_tramite).id)
        db.session.add(tramite)
        db.session.flush()

        if notificado:
            notificar = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_notificar.id)
            db.session.add(notificar)
            db.session.flush()
            db.session.add(Notificacion(
                tarea_id=notificar.id,
                canal='NOTIFICA',
                fecha_puesta_disposicion=datetime.date(2026, 7, 20),
                numero_intento=1,
            ))
            db.session.flush()

        tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_analizar.id)
        db.session.add(tarea)
        db.session.flush()
        tareas_analizar.append(tarea)

        if resultado is None:
            continue

        doc = Documento(expediente_id=solicitud.expediente_id,
                        tipo_doc_id=tipo_diagnostico.id,
                        url=f'bddat://diagnosticos/test-714-{tarea.id}')
        db.session.add(doc)
        db.session.flush()
        db.session.add(Diagnostico(documento_id=doc.id, resultado=resultado, defectos=[]))
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        db.session.flush()

    return fase, tareas_analizar


# ---------------------------------------------------------------------------
# Criterio 1 — superado por una vuelta posterior
# ---------------------------------------------------------------------------

class TestSuperadoPorVueltaPosterior:

    def test_diagnostico_con_vuelta_posterior_no_es_reversible(self, app_ctx):
        """El caso de AT-2004: desfavorable → requerimiento → subsanado favorable.

        El desfavorable de la primera vuelta no tiene ningún vínculo CONSUMIDO (nadie
        lo crea, #717) y hasta #714 era reversible.
        """
        from app.services.diagnosticos import revertir_diagnostico, DiagnosticoSuperadoError

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', True),
        ])

        with pytest.raises(DiagnosticoSuperadoError, match='vuelta de subsanación posterior'):
            revertir_diagnostico(tareas[0])

    def test_el_ultimo_de_la_cadena_sigue_siendo_reversible(self, app_ctx):
        """La puerta hacia atrás de ADR-033 §5 no se cierra de más: el diagnóstico de la
        última vuelta —aunque haya notificaciones anteriores en la cadena— se revierte.

        Se comprueba el criterio, no la reversión: `revertir_diagnostico` hace commit()
        real y el SAVEPOINT de la fixture no lo desharía.
        """
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', True),
        ])

        assert _motivo_diagnostico_superado(tareas[-1]) is None

    def test_tercera_vuelta_deja_irreversibles_las_dos_anteriores(self, app_ctx):
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'desfavorable', True),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', True),
        ])

        assert _motivo_diagnostico_superado(tareas[0]) is not None
        assert _motivo_diagnostico_superado(tareas[1]) is not None
        assert _motivo_diagnostico_superado(tareas[2]) is None


# ---------------------------------------------------------------------------
# Criterio 2 — ya comunicado al titular (la ventana que el criterio 1 no alcanza)
# ---------------------------------------------------------------------------

class TestYaComunicadoAlTitular:

    def test_requerimiento_notificado_sin_vuelta_todavia_bloquea(self, app_ctx):
        """El estado real entre notificar y que el titular subsane: el requerimiento ya
        salió, pero su ANALIZAR aún no ha producido diagnóstico.

        El diagnóstico sigue siendo el ÚLTIMO de la cadena, así que el criterio 1 no
        dispara — y sin este segundo criterio quedaría reversible justo cuando ya es
        evidencia de lo comunicado al titular (el escenario que motiva #714).
        """
        from app.services.diagnosticos import revertir_diagnostico, DiagnosticoSuperadoError

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', None, True),
        ])

        with pytest.raises(DiagnosticoSuperadoError, match='comunicado al titular'):
            revertir_diagnostico(tareas[0])

    def test_requerimiento_creado_pero_no_notificado_no_bloquea(self, app_ctx):
        """ADR-033 §5: un requerimiento sin justificación «su destino es borrarse, no
        bloquea la reversión». Mientras no se haya notificado, la puerta sigue abierta.
        """
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', None, False),
        ])

        assert _motivo_diagnostico_superado(tareas[0]) is None

    def test_el_notificar_de_la_propia_vuelta_no_bloquea_su_analizar(self, app_ctx):
        """Guardia del criterio de orden: dentro de un mismo REQUERIMIENTO_SUBSANACION el
        NOTIFICAR es ANTERIOR al ANALIZAR —notifica el requerimiento de esa vuelta,
        apoyado en el diagnóstico de la anterior—, así que no puede superar al
        diagnóstico que ese ANALIZAR produce después. Comparar por trámite en vez de por
        `Tarea.id` cerraría la puerta a toda la cadena.
        """
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('REQUERIMIENTO_SUBSANACION', 'favorable', True),
        ])

        assert _motivo_diagnostico_superado(tareas[0]) is None


# ---------------------------------------------------------------------------
# Fuera de la cadena — diagnósticos paralelos (simetría con #711)
# ---------------------------------------------------------------------------

class TestFueraDeLaCadena:

    def test_consulta_separata_posterior_no_supera_a_la_anterior(self, app_ctx):
        """Una fase CONSULTAS tiene un CONSULTA_SEPARATA por organismo y son paralelos:
        que otro organismo informe después no se apoya en el informe del primero, luego
        no lo vuelve irreversible. Aplicar «el último de la fase manda» aquí bloquearía
        la reversión de todos los organismos menos uno, sin motivo.
        """
        from app.services.diagnosticos import _motivo_diagnostico_superado

        _, tareas = _montar_fase('CONSULTAS', [
            ('CONSULTA_SEPARATA', 'desfavorable', False),
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        assert _motivo_diagnostico_superado(tareas[0]) is None
        assert _motivo_diagnostico_superado(tareas[1]) is None
