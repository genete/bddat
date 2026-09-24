"""Tests issue #346 — tramites_tareas_documentos: mapa semántico de documentos.

Requieren BD con migraciones 337 y 346 aplicadas.
"""
import pytest


# ---------------------------------------------------------------------------
# Test 1 — Sin BD: estructura del modelo
# ---------------------------------------------------------------------------

def test_modelo_importable():
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    assert TramiteTareaDocumento.__tablename__ == 'tramites_tareas_documentos'


def test_modelo_en_all():
    import app.models as m
    assert 'TramiteTareaDocumento' in m.__all__


def test_pk_id():
    """PK compuesta -> id autoincremental (#928, N1): admite varias filas
    ENTRADA distintas en el mismo (tramite, orden_tarea, rol)."""
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    pk_cols = {c.name for c in TramiteTareaDocumento.__table__.primary_key.columns}
    assert pk_cols == {'id'}


def test_indice_unico_impide_duplicado_exacto(app_ctx):
    """El índice único funcional ocupa el lugar de la antigua PK compuesta
    como guarda de duplicados: no dos filas del mismo (tramite, orden, rol)
    con el mismo tipo_documento_id."""
    from app import db
    from sqlalchemy.exc import IntegrityError
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento

    fila = db.session.query(TramiteTareaDocumento).filter(
        TramiteTareaDocumento.rol == 'ENTRADA',
        TramiteTareaDocumento.tipo_documento_id.isnot(None),
    ).first()
    assert fila is not None, 'la semilla debe traer alguna fila ENTRADA con tipo_documento_id'

    duplicado = TramiteTareaDocumento(
        tipo_tramite_id=fila.tipo_tramite_id, orden_tarea=fila.orden_tarea,
        rol=fila.rol, tipo_documento_id=fila.tipo_documento_id, obligatorio=False,
    )
    db.session.add(duplicado)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_indice_unico_permite_varias_entradas_distintas(app_ctx):
    """NOTIFICACION.NOTIFICAR ya tiene ENTRADA=RESOLUCION (obligatorio); añadir
    una ENTRADA distinta (JUSTIFICANTE_SEDE, opcional) en el mismo paso no
    choca — es justo lo que añadió la migración 928b para los 12 trámites
    cuyo NOTIFICAR va al titular."""
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_documentos import TipoDocumento

    tipo_tramite = TipoTramite.query.filter_by(codigo='NOTIFICACION').first()
    tipo_doc = TipoDocumento.query.filter_by(codigo='JUSTIFICANTE_NOTIFICA_DISPOSICION').first()
    assert tipo_tramite is not None and tipo_doc is not None, (
        'la semilla debe traer NOTIFICACION y JUSTIFICANTE_NOTIFICA_DISPOSICION'
    )

    filas = TramiteTareaDocumento.query.filter_by(
        tipo_tramite_id=tipo_tramite.id, orden_tarea=1, rol='ENTRADA',
    ).all()
    codigos = {f.tipo_documento.codigo if f.tipo_documento else None for f in filas}
    assert 'RESOLUCION' in codigos
    assert 'JUSTIFICANTE_NOTIFICA_DISPOSICION' in codigos


def test_tipo_documento_id_nullable():
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    col = TramiteTareaDocumento.__table__.c['tipo_documento_id']
    assert col.nullable is True


# ---------------------------------------------------------------------------
# Test 2 — Con BD: ESPERAR_PLAZO con plazo>0 tiene ENTRADA mapeada
# ---------------------------------------------------------------------------

def test_esperar_plazo_con_plazo_tiene_entrada(app_ctx):
    """
    Todos los trámites con tarea ESPERAR_PLAZO y plazo > 0 deben tener al menos
    una fila ENTRADA en tramites_tareas_documentos para ese (tramite, orden).

    Los EP con plazo=0 se modelan con ENTRADA NULL y obligatorio=False, por lo
    que también tienen fila ENTRADA — este test verifica simplemente que no hay
    ningún par (tramite, orden_EP) sin fila ENTRADA en el mapa.
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    esperar_id = db.session.query(TipoTarea.id).filter_by(codigo='ESPERAR_PLAZO').scalar()
    assert esperar_id is not None

    pares_ep = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id == esperar_id)
        .all()
    )
    assert len(pares_ep) > 0, "No hay tareas ESPERAR_PLAZO en tramites_tareas"

    for tt_id, orden in pares_ep:
        entrada = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='ENTRADA')
            .first()
        )
        assert entrada is not None, (
            f"ESPERAR_PLAZO sin ENTRADA mapeada: tipo_tramite_id={tt_id} orden={orden}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Con BD: NOTIFICAR siempre tiene SALIDA mapeada
# ---------------------------------------------------------------------------

def test_notificar_tiene_salida(app_ctx):
    """
    Todos los pares (tramite, orden) con tarea NOTIFICAR tienen fila SALIDA
    en tramites_tareas_documentos (aunque sea NULL polimórfico).
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    notificar_id = db.session.query(TipoTarea.id).filter_by(codigo='NOTIFICAR').scalar()
    assert notificar_id is not None

    pares = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id == notificar_id)
        .all()
    )
    assert len(pares) > 0

    for tt_id, orden in pares:
        salida = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='SALIDA')
            .first()
        )
        assert salida is not None, (
            f"NOTIFICAR sin SALIDA mapeada: tipo_tramite_id={tt_id} orden={orden}"
        )


# ---------------------------------------------------------------------------
# Test 4 — Con BD: no hay tipo_documento_id que no exista en tipos_documentos
# ---------------------------------------------------------------------------

def test_sin_tipo_documento_id_huerfano(app_ctx):
    """
    Todos los tipo_documento_id no nulos en tramites_tareas_documentos
    referencian un registro existente en tipos_documentos.
    """
    from app import db
    from sqlalchemy import text

    resultado = db.session.execute(text("""
        SELECT ttd.tipo_tramite_id, ttd.orden_tarea, ttd.rol, ttd.tipo_documento_id
        FROM public.tramites_tareas_documentos ttd
        LEFT JOIN public.tipos_documentos td ON td.id = ttd.tipo_documento_id
        WHERE ttd.tipo_documento_id IS NOT NULL
          AND td.id IS NULL
    """)).fetchall()

    assert resultado == [], (
        f"tipo_documento_id huérfanos encontrados: {resultado}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Con BD: auditoría de huecos en ELABORAR y ANALIZAR
# ---------------------------------------------------------------------------

def test_elaborar_analizar_tienen_salida(app_ctx):
    """
    Ningún par (tramite, orden_tarea) con tarea ELABORAR o ANALIZAR carece
    de fila SALIDA en tramites_tareas_documentos.
    """
    from app import db
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea

    codigos = ['ELABORAR', 'ANALIZAR']
    ids = (
        db.session.query(TipoTarea.id)
        .filter(TipoTarea.codigo.in_(codigos))
        .all()
    )
    tarea_ids = [r[0] for r in ids]
    assert len(tarea_ids) == 2

    pares = (
        db.session.query(TramiteTarea.tipo_tramite_id, TramiteTarea.orden)
        .filter(TramiteTarea.tipo_tarea_id.in_(tarea_ids))
        .all()
    )
    assert len(pares) > 0

    huecos = []
    for tt_id, orden in pares:
        salida = (
            db.session.query(TramiteTareaDocumento)
            .filter_by(tipo_tramite_id=tt_id, orden_tarea=orden, rol='SALIDA')
            .first()
        )
        if salida is None:
            huecos.append((tt_id, orden))

    assert huecos == [], (
        f"ELABORAR/ANALIZAR sin SALIDA mapeada: {huecos}"
    )


# ---------------------------------------------------------------------------
# Test 6 — Con BD: entradas múltiples de DATOS_CATASTRALES (#927)
# ---------------------------------------------------------------------------

# Consumidos que declara ESTRUCTURA_FTT.json (nota de cada trámite) para los
# pasos con varias ENTRADA: {(trámite, orden, tarea): {tipo_documento: obligatorio}}.
# Es un manifiesto EXACTO: falla si alguien quita un código, añade uno de más o
# cambia su obligatoriedad. Editarlo exige cambiar antes la fuente (el JSON).
ENTRADAS_DATOS_CATASTRALES = {
    ('SOLICITUD_CATASTRALES', 1, 'ANALIZAR'): {
        'XML_PARA_CATASTRO': True,
        'DR_DATOS_CATASTRALES': False,   # «si se aportó en origen»
    },
    ('REQUERIMIENTO_CATASTRALES', 1, 'ELABORAR'): {
        'DIAGNOSTICO': True,
    },
    ('REMISION_ACUERDO_DATOS', 1, 'ELABORAR'): {
        'XML_DE_CATASTRO': True,
        'DR_DATOS_CATASTRALES': True,
        'DIAGNOSTICO': True,
    },
    ('ANALISIS_RBDA', 1, 'ANALIZAR'): {
        'RBDA': True,
        'RBDA_DIRECCIONES': True,
    },
}


def _entradas_de_catalogo(tramite_codigo, orden):
    """{codigo_tipo_documento | None: obligatorio} de todas las ENTRADA del paso."""
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento
    from app.models.tipos_tramites import TipoTramite

    tipo_tramite = TipoTramite.query.filter_by(codigo=tramite_codigo).first()
    assert tipo_tramite is not None, f'la semilla debe traer el trámite {tramite_codigo}'
    filas = TramiteTareaDocumento.query.filter_by(
        tipo_tramite_id=tipo_tramite.id, orden_tarea=orden, rol='ENTRADA',
    ).all()
    return {(f.tipo_documento.codigo if f.tipo_documento else None): f.obligatorio
            for f in filas}, len(filas)


@pytest.mark.parametrize('paso', sorted(ENTRADAS_DATOS_CATASTRALES))
def test_entradas_multiples_datos_catastrales_exactas(app_ctx, paso):
    """El paso consume exactamente lo que declara la fuente, ni más ni menos, y
    sin filas duplicadas (el índice único ya lo impide; se comprueba el recuento)."""
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tramites import TipoTramite

    tramite_codigo, orden, tarea_codigo = paso

    # El (trámite, orden) apunta a la tarea que dice el manifiesto
    tipo_tramite = TipoTramite.query.filter_by(codigo=tramite_codigo).first()
    assert tipo_tramite is not None, f'la semilla debe traer el trámite {tramite_codigo}'
    slot = TramiteTarea.query.filter_by(tipo_tramite_id=tipo_tramite.id, orden=orden).first()
    assert slot is not None and slot.tipo_tarea.codigo == tarea_codigo, (
        f'{tramite_codigo}#{orden} debería ser {tarea_codigo}'
    )

    esperado = ENTRADAS_DATOS_CATASTRALES[paso]
    real, n_filas = _entradas_de_catalogo(tramite_codigo, orden)
    assert real == esperado, f'ENTRADA de {tramite_codigo}#{orden}: {real} != {esperado}'
    assert n_filas == len(esperado)


@pytest.mark.parametrize('paso', sorted(ENTRADAS_DATOS_CATASTRALES))
def test_radar_ofrece_cada_entrada_multiple(app_ctx, arbol_esftt, paso):
    """Cada tipo consumido del paso hace candidata a la tarea (CONSUMIDO, exacta):
    la multi-entrada no puede quedarse en «solo la primera fila»."""
    from app.services.huerfanos import tareas_candidatas

    tramite_codigo, _orden, tarea_codigo = paso
    tarea = arbol_esftt.tarea_propia(
        tarea_codigo, codigo_fase='DATOS_CATASTRALES', codigo_tramite=tramite_codigo)
    exp_id = tarea.tramite.fase.solicitud.expediente_id

    for tipo_codigo in ENTRADAS_DATOS_CATASTRALES[paso]:
        doc = arbol_esftt.documento(exp_id, tipo_codigo, f'927-{tarea.id}-{tipo_codigo}')
        propias = [c for c in tareas_candidatas(doc) if c['tarea_id'] == tarea.id]
        assert any(c['rol'] == 'CONSUMIDO' and c['coincidencia'] == 'exacta'
                   for c in propias), (
            f'{tipo_codigo} no hace candidata a {tramite_codigo}.{tarea_codigo}: {propias}'
        )


# ---------------------------------------------------------------------------
# Test 7 — Con BD: todo ANALIZAR consume algo (ESTRUCTURA_FTT.json: «≥1 oblig.»)
# ---------------------------------------------------------------------------

# Excepciones conocidas. El test exige IGUALDAD: al declarar la entrada de una,
# hay que quitarla de aquí — y un ANALIZAR nuevo sin entrada falla.
ANALIZAR_SIN_ENTRADA = {
    ('REGISTRO_INTERESADOS', 1),        # sin revisar
    ('REQUERIMIENTO_CATASTRALES', 4),   # la fuente no fija el tipo de la respuesta
}


def test_todo_analizar_tiene_entrada(app_ctx):
    from app import db
    from app.models.tipos_tramites import TipoTramite
    from app.models.tramites_tareas import TramiteTarea
    from app.models.tipos_tareas import TipoTarea
    from app.models.tramites_tareas_documentos import TramiteTareaDocumento

    analizar_id = db.session.query(TipoTarea.id).filter_by(codigo='ANALIZAR').scalar()
    assert analizar_id is not None

    huecos = set()
    for slot in TramiteTarea.query.filter_by(tipo_tarea_id=analizar_id).all():
        hay = TramiteTareaDocumento.query.filter_by(
            tipo_tramite_id=slot.tipo_tramite_id, orden_tarea=slot.orden, rol='ENTRADA',
        ).first()
        if hay is None:
            huecos.add((TipoTramite.query.get(slot.tipo_tramite_id).codigo, slot.orden))

    assert huecos == ANALIZAR_SIN_ENTRADA, (
        f'ANALIZAR sin ENTRADA: {sorted(huecos)} (esperados {sorted(ANALIZAR_SIN_ENTRADA)})'
    )
