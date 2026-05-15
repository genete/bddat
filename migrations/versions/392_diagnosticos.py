"""392_diagnosticos

Revision ID: 392_diagnosticos
Revises: 395_seed_organismos_consulta
Create Date: 2026-05-15

Issue #392 — Crea la tabla diagnosticos para almacenar el resultado del
análisis documental producido por las tareas ANALIZAR.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '392_diagnosticos'
down_revision = '395_seed_organismos_consulta'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'diagnosticos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK documentos. Documento de tipo DIAGNOSTICO producido por ANALIZAR'),
        sa.Column('resultado', sa.String(20), nullable=False,
                  comment='Resultado del diagnóstico: favorable, condicionado o desfavorable'),
        sa.Column('defectos', JSONB(), nullable=False, server_default='[]',
                  comment='Lista de defectos detectados. Items pueden incluir catalogo_id cuando exista ese catálogo'),
        sa.PrimaryKeyConstraint('id', name='pk_diagnosticos'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'],
                                name='fk_diagnostico_documento'),
        sa.UniqueConstraint('documento_id', name='uq_diagnostico_documento'),
        sa.CheckConstraint(
            "resultado IN ('favorable', 'condicionado', 'desfavorable')",
            name='ck_diagnostico_resultado',
        ),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.diagnosticos TO claude_desktop")


def downgrade():
    op.drop_table('diagnosticos', schema='public')
