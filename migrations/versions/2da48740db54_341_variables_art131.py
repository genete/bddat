"""341_variables_art131

Revision ID: 2da48740db54
Revises: 6a9c2d5e0232
Create Date: 2026-04-30 10:15:15.009008

Issue #341 sesión 3 — Registra las dos variables para art. 131.1 párr. 2 RD 1955/2000
en catalogo_variables con activa=TRUE:
  - tiene_solicitud_aap_favorable
  - es_solicitud_aac_pura
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2da48740db54'
down_revision = '6a9c2d5e0232'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables
            (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES
        (
            'tiene_solicitud_aap_favorable',
            'El expediente tiene resolución AAP favorable previa a la AAC en curso',
            'boolean',
            NULL,
            TRUE
        ),
        (
            'es_solicitud_aac_pura',
            'La solicitud en curso es AAC pura (sin DUP ni AAP combinada)',
            'boolean',
            NULL,
            TRUE
        )
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN (
            'tiene_solicitud_aap_favorable',
            'es_solicitud_aac_pura'
        )
    """))
