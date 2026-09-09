"""887_ancla_proyecto_principal

Revision ID: 887_ancla_principal
Revises: 885_reformados_proyecto
Create Date: 2026-09-09

`proyectos.documento_principal_id` — el ancla documental del proyecto (ADR-044 §D).

*Nullable* a propósito: en el alta de expediente el único documento que entra es el
escrito de solicitud, así que el ancla se rellena cuando el proyecto llega al pool.
Los expedientes existentes se quedan con NULL, y de eso se encarga la regla de motor
que siembra la migración siguiente — no un backfill, que tendría que adivinar cuál de
los DOC_PROYECTO del pool es el principal.

FK sin ON DELETE: retirar el ancla es poner la FK a NULL desde la aplicación, y el
documento sigue en el pool. La guarda del pool impide borrarlo mientras conste.
"""
from alembic import op
import sqlalchemy as sa

revision = '887_ancla_principal'
down_revision = '885_reformados_proyecto'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'proyectos',
        sa.Column('documento_principal_id', sa.Integer(), nullable=True,
                  comment='FK a DOCUMENTOS. El DOC_PROYECTO que materializa el proyecto '
                          '(ADR-044 §D). NULL hasta que llega al pool'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_proyectos_documento_principal', 'proyectos', 'documentos',
        ['documento_principal_id'], ['id'],
        source_schema='public', referent_schema='public',
    )
    op.create_index('idx_proyectos_documento_principal', 'proyectos',
                    ['documento_principal_id'], schema='public')


def downgrade():
    op.drop_index('idx_proyectos_documento_principal', table_name='proyectos', schema='public')
    op.drop_constraint('fk_proyectos_documento_principal', 'proyectos',
                       type_='foreignkey', schema='public')
    op.drop_column('proyectos', 'documento_principal_id', schema='public')
