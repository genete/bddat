"""725_seed_fases_tramites — vocabulario y cardinalidad por fase (ADR-037)

Revision ID: 725_seed_fases_tramites
Revises: 725_fases_tramites
Create Date: 2026-08-03

Issue #725, ADR-037 — Pobla fases_tramites con las asociaciones definidas en
ESTRUCTURA_FTT.json (fuente de verdad, v6.2). Falla ruidosamente si algún
código de fase o trámite no existe en BD — salvo la excepción documentada
abajo.

GAP DETECTADO (no introducido por esta migración, preexistente): la fase
CONSULTA_OPERADOR_SISTEMA y sus trámites SOLICITUD_INFORME_OPERADOR /
RECEPCION_INFORME_OPERADOR están documentados en ESTRUCTURA_FTT.json (ligados
a RD 88/2026) pero no sembrados en tipos_fases/tipos_tramites — confirmado
contra BD real, 2026-08-03. Se omiten aquí; añadir esta fila cuando se creen
esos catálogos.

Cardinalidad NULL (ilimitada) — con justificación textual del propio JSON:
  - CONSULTA_SEPARATA: "Un trámite por organismo."
  - CONSULTA_TRASLADO_TITULAR / CONSULTA_TRASLADO_ORGANISMO: ciclo de reparos
    de rondas sucesivas; el propio JSON prevé que el motor "cuente iteraciones
    ... para advertir si se supera 1 iteración" (aviso de motor, no tope
    estructural).
  - REQUERIMIENTO_SUBSANACION: cada vuelta de subsanación es un trámite nuevo
    (#711/#714, TRAMITES_CADENA_SUBSANACION).
  - TABLON_AYUNTAMIENTOS: "uno por ayuntamiento" (explícito en el JSON).
  - RECEPCION_ALEGACION: "alegación individual" — una fila por alegación
    recibida (distinto de ANALISIS_ALEGACIONES, análisis conjunto único).
Todo lo demás: cardinalidad 1 (valor por defecto, sin marcador especial).
"""
from alembic import op
import sqlalchemy as sa


revision = '725_seed_fases_tramites'
down_revision = '725_fases_tramites'
branch_labels = None
depends_on = None

_ILIMITADA = frozenset({
    'CONSULTA_SEPARATA', 'CONSULTA_TRASLADO_TITULAR', 'CONSULTA_TRASLADO_ORGANISMO',
    'REQUERIMIENTO_SUBSANACION', 'TABLON_AYUNTAMIENTOS', 'RECEPCION_ALEGACION',
})

# (tipo_fase.codigo, [tipo_tramite.codigo, ...])
# Fuente: ESTRUCTURA_FTT.json v6.2. CONSULTA_OPERADOR_SISTEMA omitida (ver docstring).
_VOCABULARIO = [
    ('ANALISIS_SOLICITUD', ['ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION', 'COMUNICACION_INICIO']),
    ('CONSULTA_MINISTERIO', ['SOLICITUD_INFORME', 'RECEPCION_INFORME']),
    ('COMPATIBILIDAD_AMBIENTAL', ['SOLICITUD_COMPATIBILIDAD', 'COMUNICACION_AUDIENCIA', 'RECEPCION_INFORME']),
    ('CONSULTAS', ['CONSULTA_SEPARATA', 'CONSULTA_TRASLADO_TITULAR', 'CONSULTA_TRASLADO_ORGANISMO']),
    ('INFORMACION_PUBLICA', [
        'REDACTAR_ANUNCIO', 'ANUNCIO_BOE', 'ANUNCIO_BOP', 'ANUNCIO_PRENSA', 'ANUNCIO_BOJA',
        'TABLON_AYUNTAMIENTOS', 'PORTAL_TRANSPARENCIA', 'ANUNCIO_TITULAR',
        'RECEPCION_ALEGACION', 'ANALISIS_ALEGACIONES',
    ]),
    ('FIGURA_AMBIENTAL_EXTERNA', ['SOLICITUD_FIGURA', 'RECEPCION_FIGURA']),
    ('AAU_AAUS_INTEGRADA', [
        'REMISION_RESULTADO_IP_CONSULTAS', 'RECEPCION_DICTAMEN', 'RECEPCION_PROPUESTA_INF_VINC',
        'RECEPCION_INFORME_VINCULANTE', 'DISCREPANCIA_INF_VINC', 'REGISTRO_INTERESADOS',
    ]),
    ('RECONOCIMIENTO_INTERESADO', ['ELABORACION', 'NOTIFICACION']),
    ('RESOLUCION', ['ELABORACION', 'NOTIFICACION', 'PUBLICACION']),
]


def _get_id(conn, tabla, codigo):
    result = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"),
        {'c': codigo}
    )
    id_ = result.scalar()
    if id_ is None:
        raise ValueError(f"Código '{codigo}' no encontrado en {tabla} — migración abortada")
    return id_


def upgrade():
    conn = op.get_bind()

    for fase_codigo, tramites in _VOCABULARIO:
        tf_id = _get_id(conn, 'tipos_fases', fase_codigo)
        for tramite_codigo in tramites:
            tt_id = _get_id(conn, 'tipos_tramites', tramite_codigo)
            cardinalidad = None if tramite_codigo in _ILIMITADA else 1
            conn.execute(sa.text("""
                INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id, cardinalidad_maxima)
                VALUES (:tf_id, :tt_id, :card)
                ON CONFLICT DO NOTHING
            """), {'tf_id': tf_id, 'tt_id': tt_id, 'card': cardinalidad})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM public.fases_tramites"))
