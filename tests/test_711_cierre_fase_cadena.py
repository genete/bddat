"""
Tests de `_check_cierre_fase` — #711 (corrige #419).

Sustituyen a `tests/test_419_invariante_cierre_fase.py`, que mockeaba `db` entero
(`q.first` devolvía lo que se le dijera) y por tanto verificaba el `if` posterior a la
consulta, nunca el SQL ni la semántica: sus cuatro tests pasaban con el check roto.
Cobertura del resto del módulo, con el mismo criterio: #715.

Aquí el árbol se monta de verdad en BD y revierte por el SAVEPOINT de `app_ctx`
(`_check_cierre_fase` es de solo lectura — no hay commit() que se escape, a diferencia
de test_678).

Los dos ejes que cubren:
  - Cadena de subsanación (ANALISIS_DOCUMENTAL → N × REQUERIMIENTO_SUBSANACION):
    diagnósticos iterativos, solo cuenta el último.
  - Fuera de la cadena (CONSULTA_SEPARATA, uno por organismo): diagnósticos
    paralelos, cualquier desfavorable sin consumir sigue bloqueando.
"""
import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _montar_fase(codigo_fase, specs):
    """Monta una fase nueva con un trámite por spec y devuelve (fase, tareas_analizar).

    `specs` es una lista de tuplas (codigo_tramite, resultado_diagnostico, consumido):
      - resultado_diagnostico None → el trámite no produce diagnóstico
      - consumido True → una tarea ELABORAR del mismo trámite vincula ese
        documento como CONSUMIDO (el "acuse de recibo" que preveía #419)
    """
    from app import db
    from app.models.solicitudes import Solicitud
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_documentos import TipoDocumento

    solicitud = Solicitud.query.first()
    if solicitud is None:
        pytest.skip('No hay solicitudes en la BD de desarrollo')

    tipo_analizar = _tipo(TipoTarea, 'ANALIZAR')
    tipo_elaborar = _tipo(TipoTarea, 'ELABORAR')
    tipo_diagnostico = _tipo(TipoDocumento, 'DIAGNOSTICO')

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, codigo_fase).id)
    db.session.add(fase)
    db.session.flush()

    tareas_analizar = []
    for codigo_tramite, resultado, consumido in specs:
        tramite = Tramite(fase_id=fase.id,
                          tipo_tramite_id=_tipo(TipoTramite, codigo_tramite).id)
        db.session.add(tramite)
        db.session.flush()

        tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_analizar.id)
        db.session.add(tarea)
        db.session.flush()
        tareas_analizar.append(tarea)

        if resultado is None:
            continue

        doc = Documento(expediente_id=solicitud.expediente_id,
                        tipo_doc_id=tipo_diagnostico.id,
                        url=f'bddat://diagnosticos/test-{tarea.id}')
        db.session.add(doc)
        db.session.flush()
        db.session.add(Diagnostico(documento_id=doc.id, resultado=resultado, defectos=[]))
        db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))

        if consumido:
            consumidora = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_elaborar.id)
            db.session.add(consumidora)
            db.session.flush()
            db.session.add(DocumentoTarea(tarea_id=consumidora.id, documento_id=doc.id,
                                          rol='CONSUMIDO'))
        db.session.flush()

    return fase, tareas_analizar


# ---------------------------------------------------------------------------
# Cadena de subsanación — solo cuenta el último diagnóstico
# ---------------------------------------------------------------------------

class TestCadenaSubsanacion:

    def test_vuelta_favorable_supera_al_desfavorable_anterior(self, app_ctx):
        """El caso de #711: AT-2004 desfavorable → requerimiento → subsanado favorable.

        El desfavorable original nunca se consume (nadie crea ese vínculo, ver #717),
        pero la vuelta posterior lo supera → la fase puede cerrarse FAVORABLE.
        """
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'FAVORABLE') is None

    def test_ultimo_de_la_cadena_desfavorable_sin_consumir_bloquea(self, app_ctx):
        """Defectos que persisten tras la subsanación: sigue sin poder cerrarse favorable."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'desfavorable', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'FAVORABLE')
        assert resultado is not None
        assert resultado.permitido is False
        assert 'desfavorable' in resultado.norma_compilada.lower()

    def test_ultimo_de_la_cadena_desfavorable_consumido_no_bloquea(self, app_ctx):
        """El escape de #419 se conserva: desfavorable consumido aguas abajo deja cerrar."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', True),
        ])

        assert _check_cierre_fase(fase.id, 'DESISTIDA') is None

    def test_unico_diagnostico_desfavorable_sin_consumir_bloquea(self, app_ctx):
        """Sin vueltas, el comportamiento de #419 queda intacto."""
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'FAVORABLE') is not None


# ---------------------------------------------------------------------------
# Fuera de la cadena — diagnósticos paralelos, ninguno supera a otro
# ---------------------------------------------------------------------------

class TestDiagnosticosParalelos:

    def test_desfavorable_de_un_organismo_no_lo_supera_otro_posterior(self, app_ctx):
        """Guardia de regresión del hallazgo que acotó el arreglo (#711).

        Una fase CONSULTAS tiene un CONSULTA_SEPARATA por organismo y cada uno produce
        su diagnóstico. Son paralelos: que el organismo consultado después responda
        favorable NO resuelve el desfavorable del anterior. Con el criterio ingenuo
        "el último de la fase manda" esto dejaría cerrar la fase con un desfavorable
        sin atender.
        """
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('CONSULTAS', [
            ('CONSULTA_SEPARATA', 'desfavorable', False),
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        resultado = _check_cierre_fase(fase.id, 'FAVORABLE')
        assert resultado is not None, (
            'Un diagnóstico desfavorable de otro organismo no puede quedar superado '
            'por el de un organismo consultado después'
        )
        assert resultado.permitido is False

    def test_todos_los_organismos_favorables_no_bloquea(self, app_ctx):
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('CONSULTAS', [
            ('CONSULTA_SEPARATA', 'favorable', False),
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'FAVORABLE') is None


# ---------------------------------------------------------------------------
# Cortocircuito por resultado
# ---------------------------------------------------------------------------

class TestResultadoDesfavorable:

    def test_desfavorable_nunca_bloquea(self, app_ctx):
        """Cerrar DESFAVORABLE no pasa por el check, haya lo que haya en la fase.

        Nota: esta asimetría (nunca se comprueba el caso simétrico — cerrar
        DESFAVORABLE con un diagnóstico favorable vigente) está registrada como hueco
        de diseño en docs/CONTEXTO_ACTUAL.md, pendiente de la revisión de RESOLUCIÓN.
        """
        from app.services.invariantes_esftt import _check_cierre_fase

        fase, _ = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
        ])

        assert _check_cierre_fase(fase.id, 'DESFAVORABLE') is None


# ---------------------------------------------------------------------------
# Helper de cadena
# ---------------------------------------------------------------------------

class TestUltimaTareaCadena:

    def test_ignora_los_diagnosticos_fuera_de_la_cadena(self, app_ctx):
        from app.services.invariantes_esftt import _ultima_tarea_cadena_subsanacion

        fase, tareas = _montar_fase('CONSULTAS', [
            ('CONSULTA_SEPARATA', 'favorable', False),
        ])

        assert _ultima_tarea_cadena_subsanacion(fase.id) is None

    def test_devuelve_la_ultima_vuelta(self, app_ctx):
        from app.services.invariantes_esftt import _ultima_tarea_cadena_subsanacion

        fase, tareas = _montar_fase('ANALISIS_SOLICITUD', [
            ('ANALISIS_DOCUMENTAL', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'desfavorable', False),
            ('REQUERIMIENTO_SUBSANACION', 'favorable', False),
        ])

        assert _ultima_tarea_cadena_subsanacion(fase.id) == tareas[-1].id
