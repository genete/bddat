"""323_configuracion_sistema

Revision ID: 323_configuracion_sistema
Revises: 477_fix_norma_origen_cierre
Create Date: 2026-05-25

Issue #323 — Tabla genérica de configuración del sistema + seed modo global del motor.
"""
import sqlalchemy as sa
from alembic import op


revision = '323_configuracion_sistema'
down_revision = '477_fix_norma_origen_cierre'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'configuracion_sistema',
        sa.Column('clave',     sa.String(80),  primary_key=True),
        sa.Column('valor',     sa.Text(),       nullable=False),
        sa.Column('tipo_dato', sa.String(20),   nullable=False),
        sa.Column('etiqueta',  sa.String(200),  nullable=True),
        schema='public',
    )

    op.execute("""
        INSERT INTO public.configuracion_sistema (clave, valor, tipo_dato, etiqueta) VALUES
        ('motor.modo_operacion', 'BLOQUEAR', 'enum',
         'Modo global del motor de reglas: BLOQUEAR | SOLO_ADVERTIR | INACTIVO')
    """)

    op.execute("GRANT SELECT ON public.configuracion_sistema TO claude_desktop")


def downgrade():
    op.drop_table('configuracion_sistema', schema='public')
