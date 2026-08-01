"""
Tests #717 — consumo real del diagnóstico por el ELABORAR de REQUERIMIENTO_SUBSANACION.

Monta el árbol de verdad en BD (mismo patrón que test_714_reversion_diagnostico_
superado.py: app_ctx con rollback por SAVEPOINT) porque la resolución del
diagnóstico anterior (`diagnostico_tramite_anterior`) depende de relaciones
reales (fase.tramites, tramite.tareas) que un stub no reproduce fielmente.

El documento PRODUCIDO del ELABORAR es un .odt real en disco (FILESYSTEM_BASE
→ tmp_path, fixture `fs_tmp` de conftest.py): la extracción de texto
(`extraccion_texto_documento.extraer_texto`) abre el fichero de verdad, no se
mockea — es justo lo que hay que probar (#182 embebe el código como texto, no
como metadato, R10).

Ejes que cubren:
  - Derivación correcta: token propio + diagnóstico anterior desfavorable.
  - Guardas de "no derivar nada": sin token, token de otra tarea, diagnóstico
    favorable (ADR-033 §5: no es consumible), tarea/trámite que no es
    ELABORAR de REQUERIMIENTO_SUBSANACION.
  - Idempotencia: no duplica el vínculo si se llama dos veces.
  - Integración con editar_tarea(): solo deriva en la transición a un
    producido NUEVO — un guardado posterior que no cambia el producido no
    repone un vínculo que el técnico haya quitado a mano (botón ✕, la vía de
    "deshacer" que exige ADR-033 §5).
  - Cierre del checklist: revertir_diagnostico ya bloquea de verdad (peldaño 3
    de ADR-033 §5) una vez existe el vínculo derivado.
  - _check_cierre_fase no gana ninguna condición nueva (criterio innegociable
    del issue): sigue leyendo CONSUMIDO genéricamente.
"""
import zipfile
import io

import pytest


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _odt_bytes(texto: str) -> bytes:
    """.odt mínimo (zip con content.xml) cuyo texto es exactamente `texto`.

    No necesita namespaces ODF reales: extraer_texto()/_extraer_odt() solo
    hace root.itertext() sobre content.xml y styles.xml, indiferente al
    esquema de las etiquetas.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
        z.writestr('content.xml', f'<root><p>{texto}</p></root>')
    return buffer.getvalue()


def _doc_producido_elaborar(tarea_elaborar, tmp_path, texto: str):
    """Crea en BD y en disco el documento PRODUCIDO de `tarea_elaborar`.

    `texto` es el contenido íntegro del .odt — normalmente el código de
    seguimiento compuesto con componer_codigo(), o cualquier otra cadena para
    probar las guardas de "sin token" / "token ajeno".
    """
    from app import db
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.tipos_documentos import TipoDocumento

    expediente_id = tarea_elaborar.tramite.fase.solicitud.expediente_id
    nombre = f'escrito_{tarea_elaborar.id}.odt'
    (tmp_path / nombre).write_bytes(_odt_bytes(texto))

    tipo_doc = TipoDocumento.query.first()
    doc = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_doc.id, url=nombre)
    db.session.add(doc)
    db.session.flush()
    db.session.add(DocumentoTarea(tarea_id=tarea_elaborar.id, documento_id=doc.id, rol='PRODUCIDO'))
    db.session.flush()
    return doc


def _montar_cadena(resultado_anterior='desfavorable', codigo_tramite_anterior='ANALISIS_DOCUMENTAL'):
    """Fase con un ANALIZAR (diagnóstico `resultado_anterior`) seguido de un
    REQUERIMIENTO_SUBSANACION con ELABORAR (sin producido aún).

    Devuelve (tarea_analizar, tarea_elaborar, diagnostico).
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

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=_tipo(TipoFase, 'ANALISIS_SOLICITUD').id)
    db.session.add(fase)
    db.session.flush()

    tramite_anterior = Tramite(fase_id=fase.id,
                               tipo_tramite_id=_tipo(TipoTramite, codigo_tramite_anterior).id)
    db.session.add(tramite_anterior)
    db.session.flush()

    tarea_analizar = Tarea(tramite_id=tramite_anterior.id, tipo_tarea_id=tipo_analizar.id)
    db.session.add(tarea_analizar)
    db.session.flush()

    doc_diag = Documento(expediente_id=solicitud.expediente_id, tipo_doc_id=tipo_diagnostico.id,
                         url=f'bddat://diagnosticos/test-717-{tarea_analizar.id}')
    db.session.add(doc_diag)
    db.session.flush()
    diagnostico = Diagnostico(documento_id=doc_diag.id, resultado=resultado_anterior, defectos=[])
    db.session.add(diagnostico)
    db.session.add(DocumentoTarea(tarea_id=tarea_analizar.id, documento_id=doc_diag.id, rol='PRODUCIDO'))
    db.session.flush()

    tramite_subsanacion = Tramite(fase_id=fase.id,
                                  tipo_tramite_id=_tipo(TipoTramite, 'REQUERIMIENTO_SUBSANACION').id)
    db.session.add(tramite_subsanacion)
    db.session.flush()

    tarea_elaborar = Tarea(tramite_id=tramite_subsanacion.id, tipo_tarea_id=tipo_elaborar.id)
    db.session.add(tarea_elaborar)
    db.session.flush()

    return tarea_analizar, tarea_elaborar, diagnostico


# ---------------------------------------------------------------------------
# El hook en sí — llamado directamente, mismo patrón que test_458
# ---------------------------------------------------------------------------

class TestHook717Derivacion:

    def test_token_propio_y_diagnostico_desfavorable_deriva_el_vinculo(self, app_ctx, fs_tmp):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, diagnostico = _montar_cadena('desfavorable')
        codigo = componer_codigo(tarea_elaborar.id)
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, f'Cabecera\n{codigo}\nPie de página.')

        advertencia = _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)

        assert advertencia is None
        vinculos_consumido = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos_consumido) == 1
        assert vinculos_consumido[0].documento_id == diagnostico.documento_id

    def test_sin_token_no_deriva_y_avisa(self, app_ctx, fs_tmp):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico

        _, tarea_elaborar, _ = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, 'Un escrito cualquiera sin código.')

        advertencia = _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)

        assert advertencia is not None
        assert 'código de seguimiento' in advertencia['motivo']
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_token_de_otra_tarea_no_deriva_y_avisa(self, app_ctx, fs_tmp):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, _ = _montar_cadena('desfavorable')
        codigo_ajeno = componer_codigo(tarea_elaborar.id + 999)
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, codigo_ajeno)

        advertencia = _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)

        assert advertencia is not None
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_diagnostico_favorable_no_es_consumible(self, app_ctx, fs_tmp):
        """ADR-033 §5: un ELABORAR de REQUERIMIENTO_SUBSANACION solo consume
        diagnósticos con defectos; un favorable no es consumible. Silencioso
        (no es nada que el técnico pueda corregir subiendo otro documento)."""
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, _ = _montar_cadena('favorable')
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, componer_codigo(tarea_elaborar.id))

        advertencia = _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)

        assert advertencia is None
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']

    def test_segunda_vuelta_consume_el_diagnostico_de_la_primera_no_el_original(self, app_ctx, fs_tmp):
        """Encadenamiento real: el ELABORAR de la vuelta 2 consume el ANALIZAR
        de la vuelta 1 (REQUERIMIENTO_SUBSANACION anterior), no el de
        ANÁLISIS_DOCUMENTAL — mismo criterio que ContextoSubsanacion."""
        from app import db
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo
        from app.models.tramites import Tramite
        from app.models.tareas import Tarea
        from app.models.tipos_tramites import TipoTramite
        from app.models.tipos_tareas import TipoTarea

        tarea_analizar_1, tarea_elaborar_1, _ = _montar_cadena('desfavorable')
        fase = tarea_elaborar_1.tramite.fase

        # Vuelta 1 completa: el ELABORAR de la primera vuelta produce un
        # ANALIZAR posterior con diagnóstico desfavorable otra vez.
        tramite_1 = tarea_elaborar_1.tramite
        tarea_analizar_2 = Tarea(tramite_id=tramite_1.id, tipo_tarea_id=_tipo(TipoTarea, 'ANALIZAR').id)
        db.session.add(tarea_analizar_2)
        db.session.flush()
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.diagnosticos import Diagnostico
        from app.models.tipos_documentos import TipoDocumento
        doc_diag_2 = Documento(expediente_id=fase.solicitud.expediente_id,
                               tipo_doc_id=_tipo(TipoDocumento, 'DIAGNOSTICO').id,
                               url=f'bddat://diagnosticos/test-717b-{tarea_analizar_2.id}')
        db.session.add(doc_diag_2)
        db.session.flush()
        diagnostico_2 = Diagnostico(documento_id=doc_diag_2.id, resultado='desfavorable', defectos=[])
        db.session.add(diagnostico_2)
        db.session.add(DocumentoTarea(tarea_id=tarea_analizar_2.id, documento_id=doc_diag_2.id, rol='PRODUCIDO'))
        db.session.flush()

        # Vuelta 2: nuevo REQUERIMIENTO_SUBSANACION con su propio ELABORAR.
        tramite_2 = Tramite(fase_id=fase.id, tipo_tramite_id=_tipo(TipoTramite, 'REQUERIMIENTO_SUBSANACION').id)
        db.session.add(tramite_2)
        db.session.flush()
        tarea_elaborar_2 = Tarea(tramite_id=tramite_2.id, tipo_tarea_id=_tipo(TipoTarea, 'ELABORAR').id)
        db.session.add(tarea_elaborar_2)
        db.session.flush()

        doc = _doc_producido_elaborar(tarea_elaborar_2, fs_tmp, componer_codigo(tarea_elaborar_2.id))
        _hook_717_elaborar_consumido_diagnostico(tarea_elaborar_2, doc.id)

        vinculos = [v for v in tarea_elaborar_2.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos) == 1
        assert vinculos[0].documento_id == doc_diag_2.id  # el de la vuelta 1, no el original

    def test_llamar_dos_veces_no_duplica_el_vinculo(self, app_ctx, fs_tmp):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, diagnostico = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, componer_codigo(tarea_elaborar.id))

        _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)
        _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)  # no debe lanzar IntegrityError

        vinculos = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos) == 1

    def test_no_es_elaborar_no_hace_nada(self, app_ctx):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico

        tarea_analizar, _, _ = _montar_cadena('desfavorable')

        # id_producido arbitrario: si el hook llegara a mirar el documento
        # (no debería, la tarea no es ELABORAR) Documento.query.get devolvería
        # None y fallaría más abajo — la ausencia de excepción ya prueba el
        # cortocircuito por tipo de tarea.
        advertencia = _hook_717_elaborar_consumido_diagnostico(tarea_analizar, id_producido=99999)
        assert advertencia is None

    def test_sin_id_producido_no_hace_nada(self, app_ctx):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico

        _, tarea_elaborar, _ = _montar_cadena('desfavorable')
        assert _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, None) is None


# ---------------------------------------------------------------------------
# Integración con editar_tarea(): guarda de "solo en transición a producido nuevo"
# ---------------------------------------------------------------------------

class TestIntegracionEditarTarea:

    def test_primer_guardado_del_producido_deriva_el_consumido(self, app_ctx, fs_tmp):
        from app.services import mutaciones_arbol as svc
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, diagnostico = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar_sin_vinculo(tarea_elaborar, fs_tmp, componer_codigo(tarea_elaborar.id))

        resultado = svc.editar_tarea(tarea_elaborar, documentos_consumidos_ids=[],
                                     documento_producido_id=doc.id, notas=None)

        assert resultado.ok
        vinculos = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos) == 1
        assert vinculos[0].documento_id == diagnostico.documento_id

    def test_reguardado_sin_cambiar_producido_no_repone_lo_que_el_tecnico_quito(self, app_ctx, fs_tmp):
        """El botón ✕ de la Despensa es la vía real de "deshacer esa
        vinculación" que exige ADR-033 §5 — si el hook se repite en cada
        guardado, ese botón dejaría de funcionar."""
        from app.services import mutaciones_arbol as svc
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, diagnostico = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar_sin_vinculo(tarea_elaborar, fs_tmp, componer_codigo(tarea_elaborar.id))

        svc.editar_tarea(tarea_elaborar, documentos_consumidos_ids=[],
                         documento_producido_id=doc.id, notas=None)
        assert [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']

        # El técnico deshace la vinculación a mano (documentos_consumidos_ids
        # ya no la incluye) y vuelve a guardar sin tocar el producido.
        resultado = svc.editar_tarea(tarea_elaborar, documentos_consumidos_ids=[],
                                     documento_producido_id=doc.id, notas='Nota nueva')

        assert resultado.ok
        assert not [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']


def _doc_producido_elaborar_sin_vinculo(tarea_elaborar, tmp_path, texto: str):
    """Como _doc_producido_elaborar pero sin crear el DocumentoTarea PRODUCIDO
    — para los tests de editar_tarea(), que es quien debe crearlo."""
    from app import db
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento

    expediente_id = tarea_elaborar.tramite.fase.solicitud.expediente_id
    nombre = f'escrito_{tarea_elaborar.id}.odt'
    (tmp_path / nombre).write_bytes(_odt_bytes(texto))

    tipo_doc = TipoDocumento.query.first()
    doc = Documento(expediente_id=expediente_id, tipo_doc_id=tipo_doc.id, url=nombre)
    db.session.add(doc)
    db.session.flush()
    return doc


# ---------------------------------------------------------------------------
# Cierre del checklist: revertir_diagnostico bloquea de verdad (peldaño 3, ADR-033 §5)
# ---------------------------------------------------------------------------

class TestCierraPeldano3ADR033:

    def test_revertir_diagnostico_consumido_lanza_error_con_la_tarea_elaborar(self, app_ctx, fs_tmp):
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.diagnosticos import revertir_diagnostico, DiagnosticoConsumidoError
        from app.services.codigo_seguimiento import componer_codigo

        tarea_analizar, tarea_elaborar, _ = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar(tarea_elaborar, fs_tmp, componer_codigo(tarea_elaborar.id))
        _hook_717_elaborar_consumido_diagnostico(tarea_elaborar, doc.id)

        with pytest.raises(DiagnosticoConsumidoError) as exc:
            revertir_diagnostico(tarea_analizar)

        assert exc.value.tarea_consumidora.id == tarea_elaborar.id
