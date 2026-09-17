"""918_fases_tramites_aap_aac — vocabulario de RESOLUCION_AAP y RESOLUCION_AAC

Revision ID: 918_fases_tramites_aap_aac
Revises: 918_tipos_fases_aap_aac
Create Date: 2026-09-17

Issue #918, ADR-047 §A, mismo patrón que 914_fases_tramites_dup (ADR-046).
Reutiliza los tipos_tramites ELABORACION/NOTIFICACION/PUBLICACION, ya
existentes y compartidos con RESOLUCION — solo se crean filas de
fases_tramites, ningún tipo_tramite nuevo.

Asimetría normativa confirmada con Carlos (RD 1955/2000): RESOLUCION_AAP
lleva PUBLICACION (art. 128.3, "la resolución deberá publicarse... y
deberá ser notificada"), calcado íntegro de RESOLUCION (3 trámites).
RESOLUCION_AAC NO lleva PUBLICACION (art. 131.8 solo exige "la resolución
deberá ser notificada", sin mención de publicación) — 2 trámites.

Cardinalidad 1 en las tres, igual que RESOLUCION (id 8).
"""
from alembic import op
import sqlalchemy as sa


revision = '918_fases_tramites_aap_aac'
down_revision = '918_tipos_fases_aap_aac'
branch_labels = None
depends_on = None

# (tipo_fase.codigo, [tipo_tramite.codigo, ...])
_VOCABULARIO = [
    ('RESOLUCION_AAP', ['ELABORACION', 'NOTIFICACION', 'PUBLICACION']),
    ('RESOLUCION_AAC', ['ELABORACION', 'NOTIFICACION']),
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
            conn.execute(sa.text("""
                INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id, cardinalidad_maxima)
                VALUES (:tf_id, :tt_id, 1)
                ON CONFLICT DO NOTHING
            """), {'tf_id': tf_id, 'tt_id': tt_id})


def downgrade():
    conn = op.get_bind()
    for fase_codigo, _tramites in _VOCABULARIO:
        conn.execute(sa.text("""
            DELETE FROM public.fases_tramites
            WHERE tipo_fase_id = (SELECT id FROM public.tipos_fases WHERE codigo = :c)
        """), {'c': fase_codigo})
