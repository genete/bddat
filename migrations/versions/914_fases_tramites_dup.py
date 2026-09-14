"""914_fases_tramites_dup — vocabulario de RESOLUCION_DUP y DATOS_CATASTRALES

Revision ID: 914_fases_tramites_dup
Revises: 914_tipos_tramites_tareas
Create Date: 2026-09-14

Issue #914, ADR-046, mismo patrón que 725_seed_fases_tramites (ADR-037).
RESOLUCION_DUP reutiliza los tipos_tramites ELABORACION y NOTIFICACION, ya
existentes y compartidos con RESOLUCION — solo se crea la fila de
fases_tramites, no un tipo_tramite nuevo (PRE-ADR §4.1.1: la colisión de
nombre de fichero se resuelve en nombres_documentos.py, no aquí).

Cardinalidad NULL (ilimitada), con justificación:
  - PUBLICACION_BOP: "una instancia por provincia afectada" (ADR-046 §D) —
    mismo caso que TABLON_AYUNTAMIENTOS en INFORMACION_PUBLICA.
  - REQUERIMIENTO_CATASTRALES: repetible, cada ronda de subsanación es un
    trámite nuevo (DISEÑO_RESOLUCION_DUP.md §2) — mismo caso que
    REQUERIMIENTO_SUBSANACION.
Todo lo demás: cardinalidad 1 (valor por defecto).
"""
from alembic import op
import sqlalchemy as sa


revision = '914_fases_tramites_dup'
down_revision = '914_tipos_tramites_tareas'
branch_labels = None
depends_on = None

_ILIMITADA = frozenset({'PUBLICACION_BOP', 'REQUERIMIENTO_CATASTRALES'})

# (tipo_fase.codigo, [tipo_tramite.codigo, ...])
_VOCABULARIO = [
    ('RESOLUCION_DUP', [
        'ELABORACION', 'NOTIFICACION', 'NOTIFICACION_ORGANISMOS', 'NOTIFICACION_INTERESADOS',
        'PUBLICACION_BOP', 'PUBLICACION_BOJA', 'PUBLICACION_BOE',
        'REQUERIMIENTO_RBDA_DEFINITIVA',
    ]),
    ('DATOS_CATASTRALES', [
        'SOLICITUD_CATASTRALES', 'REQUERIMIENTO_CATASTRALES', 'REMISION_ACUERDO_DATOS',
        'ANALISIS_RBDA', 'TOMA_RAZON_RBDA',
    ]),
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
    for fase_codigo, _tramites in _VOCABULARIO:
        conn.execute(sa.text("""
            DELETE FROM public.fases_tramites
            WHERE tipo_fase_id = (SELECT id FROM public.tipos_fases WHERE codigo = :c)
        """), {'c': fase_codigo})
