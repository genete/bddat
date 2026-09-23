"""
Tests #928 (N1) §5 — app/services/notificaciones.py: fechas y estado del acto
de notificar, derivados de sus documentos (ADR-049 §C).

Una función por caso de la tabla del propio issue (ADR §C, destinatario
titular). Cada caso monta una tarea NOTIFICAR real (`ArbolESFTT`) y vincula
sus documentos con el rol de la tabla — los documentos son `bddat://`, sin
fichero físico, así que `rutas_esftt.py` no entra en juego.

Dos casos no se pueden montar contra una fila `Notificacion` real todavía,
ambos anticipados por el propio issue:
  - `resultado = RECHAZADA`: el CHECK de la BD solo admite CORRECTA/INCORRECTA
    hasta que 928c lo relaje. Se prueba con un doble (`_TareaFalsa`).
  - `estado_sede` rama 'JUSTIFICADA': `sede_justificacion` no existe en el
    modelo hasta 928c ("se prueba con un doble hasta que llegue 928c", §5).
"""
from types import SimpleNamespace

import pytest

from app.services.notificaciones import (
    canal_de_tipo,
    documentos_a_notificar,
    estado_sede,
    fecha_cumplimiento,
    fecha_efectos,
    justificantes_previos,
    notificacion_efectuada,
    resultados_validos,
)


def _montar_notificar(arbol_esftt, *, vinculos, resultado=None, canal='NOTIFICA', numero_intento=None):
    """Tarea NOTIFICAR real con los documentos de `vinculos` —lista de
    (codigo_tipo, rol, fecha)— vinculados con ese rol. `resultado=None` deja
    la tarea sin fila `Notificacion` (aún sin registrar)."""
    fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
    tramite = arbol_esftt.tramite(fase, 'NOTIFICACION')
    tarea = arbol_esftt.tarea(tramite, 'NOTIFICAR')
    expediente_id = fase.solicitud.expediente_id

    for i, (codigo_tipo, rol, fecha) in enumerate(vinculos):
        doc = arbol_esftt.documento(expediente_id, codigo_tipo,
                                     f'{tarea.id}-{i}-{codigo_tipo}', fecha=fecha)
        arbol_esftt.vincular(tarea, doc, rol)

    if resultado is not None:
        kwargs = {'canal': canal}
        if numero_intento is not None:
            kwargs['numero_intento'] = numero_intento
        arbol_esftt.notificacion(tarea, resultado=resultado, **kwargs)

    return tarea


def _fecha(dias_antes=0):
    from datetime import timedelta
    from app.services.reloj_simulado import hoy
    return hoy() - timedelta(days=dias_antes)


# ---------------------------------------------------------------------------
# Tabla de casos (ADR-049 §C, destinatario titular)
# ---------------------------------------------------------------------------

def test_notifica_leida(app_ctx, arbol_esftt):
    f_disposicion, f_notifica = _fecha(10), _fecha(3)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO', f_disposicion),
        ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', f_notifica),
    ], resultado='CORRECTA')

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_disposicion
    assert cumplimiento.documento.tipo_doc.codigo == 'JUSTIFICANTE_NOTIFICA_DISPOSICION'
    assert efectos.fecha == f_notifica
    assert efectos.documento.tipo_doc.codigo == 'JUSTIFICANTE_NOTIFICA'
    assert notificacion_efectuada(tarea) is True


def test_notifica_rechazada(app_ctx):
    """`resultado = RECHAZADA` — CHECK de BD lo bloquea hasta 928c (doble)."""
    f_disposicion, f_notifica = _fecha(10), _fecha(3)
    doc_disposicion = SimpleNamespace(
        id=1, tipo_doc=SimpleNamespace(codigo='JUSTIFICANTE_NOTIFICA_DISPOSICION'),
        fecha_administrativa=f_disposicion)
    doc_notifica = SimpleNamespace(
        id=2, tipo_doc=SimpleNamespace(codigo='JUSTIFICANTE_NOTIFICA'),
        fecha_administrativa=f_notifica)
    tarea = SimpleNamespace(
        vinculos_documento=[
            SimpleNamespace(rol='CONSUMIDO', documento=doc_disposicion),
            SimpleNamespace(rol='PRODUCIDO', documento=doc_notifica),
        ],
        notificacion=SimpleNamespace(resultado='RECHAZADA', canal='NOTIFICA'),
        documento_producido=doc_notifica,
        ejecutada=True,
    )

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_disposicion
    assert efectos.fecha == f_notifica
    assert notificacion_efectuada(tarea) is True


def test_notifica_caducada(app_ctx, arbol_esftt):
    f_disposicion = _fecha(10)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO', f_disposicion),
        ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', _fecha(3)),
    ], resultado='INCORRECTA')

    cumplimiento = fecha_cumplimiento(tarea)
    assert cumplimiento.fecha == f_disposicion
    assert fecha_efectos(tarea) is None
    assert notificacion_efectuada(tarea) is False


def test_postal_a_la_primera(app_ctx, arbol_esftt):
    f_postal = _fecha(5)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', f_postal),
    ], resultado='CORRECTA', canal='POSTAL')

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_postal
    assert cumplimiento.documento.tipo_doc.codigo == 'JUSTIFICANTE_POSTAL'
    assert efectos.fecha == f_postal
    assert notificacion_efectuada(tarea) is True


def test_postal_primer_intento_fallido_segundo_correcto(app_ctx, arbol_esftt):
    f_1er, f_postal = _fecha(20), _fecha(5)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO', f_1er),
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', f_postal),
    ], resultado='CORRECTA', canal='POSTAL', numero_intento=2)

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_1er
    assert cumplimiento.documento.tipo_doc.codigo == 'JUSTIFICANTE_POSTAL_1ER'
    assert efectos.fecha == f_postal


def test_postal_dos_fallidos_antes_del_edicto(app_ctx, arbol_esftt):
    """Dos intentos postales fallidos: hasta que se publica el anuncio,
    `resultado` sigue INCORRECTA y no hay efectos (D1)."""
    f_1er = _fecha(30)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO', f_1er),
    ], resultado='INCORRECTA', canal='POSTAL', numero_intento=2)

    cumplimiento = fecha_cumplimiento(tarea)
    assert cumplimiento.fecha == f_1er
    assert fecha_efectos(tarea) is None
    assert notificacion_efectuada(tarea) is False


def test_postal_dos_fallidos_mas_edicto(app_ctx, arbol_esftt):
    """Publicado el anuncio, `resultado` pasa a CORRECTA (D1, ratificada):
    la tarea llega a FIN aunque los dos intentos postales fallaran."""
    f_1er, f_anuncio = _fecha(30), _fecha(2)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL_1ER', 'CONSUMIDO', f_1er),
        ('ANUNCIO_PUBLICADO', 'PRODUCIDO', f_anuncio),
    ], resultado='CORRECTA', canal='POSTAL', numero_intento=2)

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_1er
    assert efectos.fecha == f_anuncio
    assert efectos.documento.tipo_doc.codigo == 'ANUNCIO_PUBLICADO'
    assert notificacion_efectuada(tarea) is True


def test_edicto_directo(app_ctx, arbol_esftt):
    """Sin fila de `notificaciones` sin canal (CHECK actual: NOTIFICA,
    BANDEJA, SIR, POSTAL): el test la fabrica con POSTAL — qué canal lleva
    de verdad esta fila es de #568 (D15); el servicio no lee `canal`."""
    f_anuncio = _fecha(1)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('ANUNCIO_PUBLICADO', 'PRODUCIDO', f_anuncio),
    ], resultado='CORRECTA', canal='POSTAL')

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_anuncio
    assert cumplimiento.documento.tipo_doc.codigo == 'ANUNCIO_PUBLICADO'
    assert efectos.fecha == f_anuncio


def test_falta_el_acuse_del_primero(app_ctx, arbol_esftt):
    """Solo llega el justificante del 2º intento: sin POSTAL_1ER, el
    cumplimiento cae en el único documento presente — responsabilidad del
    usuario si de verdad falta el acuse del primero."""
    f_postal = _fecha(4)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', f_postal),
    ], resultado='CORRECTA', canal='POSTAL', numero_intento=2)

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.fecha == f_postal
    assert cumplimiento.documento.tipo_doc.codigo == 'JUSTIFICANTE_POSTAL'
    assert efectos.fecha == f_postal


@pytest.mark.parametrize('codigo,canal', [('JUSTIFICANTE_BANDEJA', 'BANDEJA'), ('JUSTIFICANTE_SIR', 'SIR')])
def test_bandeja_sir(app_ctx, arbol_esftt, codigo, canal):
    """BANDEJA/SIR no dan cumplimiento (no están en JUSTIFICANTES_CUMPLIMIENTO
    — es recepción, no puesta a disposición); sí dan efectos, el justificante
    mismo."""
    f_doc = _fecha(2)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        (codigo, 'PRODUCIDO', f_doc),
    ], resultado='CORRECTA', canal=canal)

    assert fecha_cumplimiento(tarea) is None
    efectos = fecha_efectos(tarea)
    assert efectos.fecha == f_doc
    assert efectos.documento.tipo_doc.codigo == codigo


def test_pdf_polivalente(app_ctx, arbol_esftt):
    """El mismo PDF sube dos veces con tipos distintos (ADR-049 §B): dos
    filas Documento, una CONSUMIDO (disposición) y otra PRODUCIDO (efectos).
    Prerrequisito #926 (mover_a_esftt/mover_a_pool) no entra aquí — los
    documentos son bddat://, sin fichero físico compartido que mover."""
    f_disposicion, f_notifica = _fecha(8), _fecha(1)
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO', f_disposicion),
        ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', f_notifica),
    ], resultado='CORRECTA')

    cumplimiento = fecha_cumplimiento(tarea)
    efectos = fecha_efectos(tarea)
    assert cumplimiento.documento.id != efectos.documento.id  # dos filas distintas
    assert cumplimiento.fecha == f_disposicion
    assert efectos.fecha == f_notifica


# ---------------------------------------------------------------------------
# documentos_a_notificar / justificantes_previos (§8: contrato de NOTIFICAR)
# ---------------------------------------------------------------------------

def test_documentos_a_notificar_excluye_los_previos(app_ctx, arbol_esftt):
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('RESOLUCION', 'CONSUMIDO', _fecha(15)),
        ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'CONSUMIDO', _fecha(10)),
        ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', _fecha(3)),
    ], resultado='CORRECTA')

    a_notificar = documentos_a_notificar(tarea)
    previos = justificantes_previos(tarea)
    assert [d.tipo_doc.codigo for d in a_notificar] == ['RESOLUCION']
    assert [d.tipo_doc.codigo for d in previos] == ['JUSTIFICANTE_NOTIFICA_DISPOSICION']


# ---------------------------------------------------------------------------
# estado_sede (§5: "se prueba con un doble hasta que llegue 928c")
# ---------------------------------------------------------------------------

def test_estado_sede_no_aplica_sin_fila(app_ctx, arbol_esftt):
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', _fecha(1)),
    ])  # sin resultado -> sin fila Notificacion
    assert estado_sede(tarea) is None


def test_estado_sede_no_aplica_fuera_de_postal(app_ctx, arbol_esftt):
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_NOTIFICA', 'PRODUCIDO', _fecha(1)),
    ], resultado='CORRECTA', canal='NOTIFICA')
    assert estado_sede(tarea) is None


def test_estado_sede_puesta(app_ctx, arbol_esftt):
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_SEDE', 'CONSUMIDO', _fecha(6)),
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', _fecha(1)),
    ], resultado='CORRECTA', canal='POSTAL')
    assert estado_sede(tarea) == 'PUESTA'


def test_estado_sede_pendiente(app_ctx, arbol_esftt):
    tarea = _montar_notificar(arbol_esftt, vinculos=[
        ('JUSTIFICANTE_POSTAL', 'PRODUCIDO', _fecha(1)),
    ], resultado='CORRECTA', canal='POSTAL')
    assert estado_sede(tarea) == 'PENDIENTE'


def test_estado_sede_justificada():
    """`sede_justificacion` no existe hasta 928c: doble."""
    tarea = SimpleNamespace(
        notificacion=SimpleNamespace(canal='POSTAL', sede_justificacion='Motivo justificado'),
        vinculos_documento=[],
    )
    assert estado_sede(tarea) == 'JUSTIFICADA'


# ---------------------------------------------------------------------------
# canal_de_tipo / resultados_validos
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('codigo,canal_esperado', [
    ('JUSTIFICANTE_NOTIFICA_DISPOSICION', 'NOTIFICA'),
    ('JUSTIFICANTE_NOTIFICA', 'NOTIFICA'),
    ('JUSTIFICANTE_POSTAL_1ER', 'POSTAL'),
    ('JUSTIFICANTE_POSTAL', 'POSTAL'),
    ('JUSTIFICANTE_BANDEJA', 'BANDEJA'),
    ('JUSTIFICANTE_SIR', 'SIR'),
])
def test_canal_de_tipo(codigo, canal_esperado):
    assert canal_de_tipo(codigo) == canal_esperado


@pytest.mark.parametrize('codigo', ['JUSTIFICANTE_SEDE', 'ANUNCIO_PUBLICADO', 'RESOLUCION'])
def test_canal_de_tipo_sin_canal_propio(codigo):
    assert canal_de_tipo(codigo) is None


def test_resultados_validos_rechazada_solo_notifica_y_postal():
    assert 'RECHAZADA' in resultados_validos('NOTIFICA')
    assert 'RECHAZADA' in resultados_validos('POSTAL')
    assert 'RECHAZADA' not in resultados_validos('BANDEJA')
    assert 'RECHAZADA' not in resultados_validos('SIR')
