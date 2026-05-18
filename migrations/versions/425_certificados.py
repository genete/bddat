"""425_certificados

Revision ID: 425_certificados
Revises: a4d067a1d5bf
Create Date: 2026-05-18

Issue #425 — Crea la tabla certificados: almacén bddat:// para documentos
internos generados por el motor (CERT_PLAZO_CUMPLIDO, CERT_FIN_INSTRUCCION, …).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '425_certificados'
down_revision = 'a4d067a1d5bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'certificados',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK documentos. Determina el tipo vía tipo_documento.codigo'),
        sa.Column('generado_en', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()'),
                  comment='Momento de creación del registro'),
        sa.Column('datos', JSONB(), nullable=False, server_default='{}',
                  comment='Contenido tipo-específico del certificado'),
        sa.PrimaryKeyConstraint('id', name='pk_certificados'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'],
                                name='fk_certificado_documento'),
        sa.UniqueConstraint('documento_id', name='uq_certificado_documento'),
        schema='public',
    )
    op.execute("GRANT SELECT ON public.certificados TO claude_desktop")


def downgrade():
    op.drop_table('certificados', schema='public')
