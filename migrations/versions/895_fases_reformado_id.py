"""895_fases_reformado_id

Revision ID: 895_fases_reformado_id
Revises: 887_reglas_ancla
Create Date: 2026-09-10

`fases.reformado_id` — la versión del proyecto que cubre cada fase (ADR-044 §E, R3 #895).

*Nullable* a propósito: NULL significa versión inicial (la anterior al primer
reformado), así que no hay filas retroactivas que crear ni backfill que adivinar.

`ON DELETE RESTRICT`, no `SET NULL`: el corte muere en CASCADE con su documento
(#885); si esa cascada llegara a las fases con SET NULL, se quedarían
silenciosamente en la versión inicial. Con RESTRICT el borrado se niega, y quien
explica el motivo es la guarda del pool y `revertir_reformado` (ver commit del
servicio `app/services/reformados.py`).
"""
from alembic import op
import sqlalchemy as sa

revision = '895_fases_reformado_id'
down_revision = '887_reglas_ancla'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'fases',
        sa.Column('reformado_id', sa.Integer(), nullable=True,
                  comment='FK a REFORMADOS_PROYECTO. Versión del proyecto que cubre la fase '
                          '(ADR-044 §E). NULL = versión inicial. La rellena crear_fase, no el técnico'),
        schema='public',
    )
    op.create_foreign_key(
        'fk_fases_reformado', 'fases', 'reformados_proyecto',
        ['reformado_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )
    op.create_index('idx_fases_reformado', 'fases', ['reformado_id'], schema='public')


def downgrade():
    op.drop_index('idx_fases_reformado', table_name='fases', schema='public')
    op.drop_constraint('fk_fases_reformado', 'fases', type_='foreignkey', schema='public')
    op.drop_column('fases', 'reformado_id', schema='public')
