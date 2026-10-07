"""
Tests #717 — consumo real del diagnóstico por el ELABORAR de REQUERIMIENTO_SUBSANACION.

Monta el árbol de verdad en BD (mismo patrón que test_714_reversion_diagnostico_
superado.py: app_ctx con rollback por SAVEPOINT) porque la resolución del
diagnóstico anterior (`diagnostico_tramite_anterior`) depende de relaciones
reales (fase.tramites, tramite.tareas) que un stub no reproduce fielmente.

El documento PRODUCIDO del ELABORAR es un .odt real en el almacén de pruebas (fixture
`almacen_tmp`): la extracción de texto
(`extraccion_texto_documento.extraer_texto`) lee el contenido de verdad, no se
mockea — es justo lo que hay que probar (#182 embebe el código como texto, no
como metadato, R10).

Qué se prueba aquí (#1007): lo que puede romper otro código. La segunda vuelta depende
de `diagnostico_tramite_anterior`, compartida con ContextoSubsanacion, y el primer
guardado, del enganche de `editar_tarea` con el hook y del lector. Las guardas del
propio hook —sin código o con el de otra tarea no deriva, un diagnóstico favorable no
se consume, solo actúa ante un producido nuevo— están en su código y su docstring y no
llevan test: solo se romperían editándolas. `revertir_diagnostico` ante un diagnóstico
consumido lo prueba test_678.
"""
import zipfile
import io


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


def _doc_producido_elaborar(tarea_elaborar, texto: str):
    """Crea en BD y en el almacén el documento PRODUCIDO de `tarea_elaborar`.

    `texto` es el contenido íntegro del .odt — normalmente el código de
    seguimiento compuesto con componer_codigo(), o cualquier otra cadena para
    probar las guardas de "sin token" / "token ajeno".
    """
    from app import db
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.tipos_documentos import TipoDocumento
    from tests.conftest import documento_con_contenido_de_prueba

    tipo_doc = TipoDocumento.query.first()
    doc = documento_con_contenido_de_prueba(
        f'escrito_{tarea_elaborar.id}.odt', _odt_bytes(texto),
        expediente_id=tarea_elaborar.tramite.fase.solicitud.expediente_id, tipo_doc_id=tipo_doc.id)
    db.session.add(DocumentoTarea(tarea_id=tarea_elaborar.id, documento_id=doc.id, rol='PRODUCIDO'))
    db.session.flush()
    return doc


def _montar_cadena(resultado_anterior='desfavorable', codigo_tramite_anterior='ANALISIS_DOCUMENTAL'):
    """Fase con un ANALIZAR (diagnóstico `resultado_anterior`) seguido de un
    REQUERIMIENTO_SUBSANACION con ELABORAR (sin producido aún).

    Devuelve (tarea_analizar, tarea_elaborar, diagnostico).

    Construye sobre el builder compartido `ArbolESFTT` (#752): antes duplicaba a mano
    los mismos inserts de Fase/Tramite/Tarea/Documento que test_714 y test_724 tenían
    cada uno por su lado.
    """
    from app import db
    from tests.conftest import ArbolESFTT
    arbol = ArbolESFTT(db)

    fase = arbol.fase('ANALISIS_SOLICITUD')

    tramite_anterior = arbol.tramite(fase, codigo_tramite_anterior)
    tarea_analizar = arbol.tarea(tramite_anterior, 'ANALIZAR')
    diagnostico = arbol.diagnostico(tarea_analizar, resultado_anterior)

    tramite_subsanacion = arbol.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
    tarea_elaborar = arbol.tarea(tramite_subsanacion, 'ELABORAR')

    return tarea_analizar, tarea_elaborar, diagnostico


# ---------------------------------------------------------------------------
# El hook en sí — llamado directamente, mismo patrón que test_458
# ---------------------------------------------------------------------------

class TestHook717Derivacion:

    def test_segunda_vuelta_consume_el_diagnostico_de_la_primera_no_el_original(self, app_ctx, almacen_tmp):
        """Encadenamiento real: el ELABORAR de la vuelta 2 consume el ANALIZAR
        de la vuelta 1 (REQUERIMIENTO_SUBSANACION anterior), no el de
        ANÁLISIS_DOCUMENTAL — mismo criterio que ContextoSubsanacion."""
        from app import db
        from tests.conftest import ArbolESFTT
        from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico
        from app.services.codigo_seguimiento import componer_codigo
        arbol = ArbolESFTT(db)

        tarea_analizar_1, tarea_elaborar_1, _ = _montar_cadena('desfavorable')
        fase = tarea_elaborar_1.tramite.fase

        # Vuelta 1 completa: el ELABORAR de la primera vuelta produce un
        # ANALIZAR posterior con diagnóstico desfavorable otra vez.
        tramite_1 = tarea_elaborar_1.tramite
        tarea_analizar_2 = arbol.tarea(tramite_1, 'ANALIZAR')
        diagnostico_2 = arbol.diagnostico(tarea_analizar_2, 'desfavorable')
        doc_diag_2 = diagnostico_2.documento

        # Vuelta 2: nuevo REQUERIMIENTO_SUBSANACION con su propio ELABORAR.
        tramite_2 = arbol.tramite(fase, 'REQUERIMIENTO_SUBSANACION')
        tarea_elaborar_2 = arbol.tarea(tramite_2, 'ELABORAR')

        doc = _doc_producido_elaborar(tarea_elaborar_2, componer_codigo(tarea_elaborar_2.id))
        _hook_717_elaborar_consumido_diagnostico(tarea_elaborar_2, doc.id)

        vinculos = [v for v in tarea_elaborar_2.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos) == 1
        assert vinculos[0].documento_id == doc_diag_2.id  # el de la vuelta 1, no el original


# ---------------------------------------------------------------------------
# Integración con editar_tarea(): el enganche del hook y el lector, de punta a punta
# ---------------------------------------------------------------------------

class TestIntegracionEditarTarea:

    def test_primer_guardado_del_producido_deriva_el_consumido(self, app_ctx, almacen_tmp):
        from app.services import mutaciones_arbol as svc
        from app.services.codigo_seguimiento import componer_codigo

        _, tarea_elaborar, diagnostico = _montar_cadena('desfavorable')
        doc = _doc_producido_elaborar_sin_vinculo(tarea_elaborar, componer_codigo(tarea_elaborar.id))

        resultado = svc.editar_tarea(tarea_elaborar, documentos_consumidos_ids=[],
                                     documento_producido_id=doc.id, notas=None)

        assert resultado.ok
        # Llega hasta el técnico vía el mismo canal que las advertencias del
        # motor (store.js las muestra como toast) — no es un fallo, pero es
        # una mutación en la trastienda que debe conocer.
        assert resultado.advertencia is not None
        assert 'automátic' in resultado.advertencia['motivo']
        vinculos = [v for v in tarea_elaborar.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos) == 1
        assert vinculos[0].documento_id == diagnostico.documento_id


def _doc_producido_elaborar_sin_vinculo(tarea_elaborar, texto: str):
    """Como _doc_producido_elaborar pero sin crear el DocumentoTarea PRODUCIDO
    — para los tests de editar_tarea(), que es quien debe crearlo."""
    from app.models.tipos_documentos import TipoDocumento
    from tests.conftest import documento_con_contenido_de_prueba

    tipo_doc = TipoDocumento.query.first()
    return documento_con_contenido_de_prueba(
        f'escrito_{tarea_elaborar.id}.odt', _odt_bytes(texto),
        expediente_id=tarea_elaborar.tramite.fase.solicitud.expediente_id, tipo_doc_id=tipo_doc.id)
