"""Motor reglas — eliminar SOLICITUD_TIPO de entidades, lo gestiona handler SOLICITUD

Revision ID: 20e383031811
Revises: 1800b039663e
Create Date: 2026-02-27 19:33:55.342175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20e383031811'
down_revision = '1800b039663e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('ck_reglas_motor_entidad', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_entidad',
        'reglas_motor',
        "entidad IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')",
        schema='public'
    )


def downgrade():
    op.drop_constraint('ck_reglas_motor_entidad', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_entidad',
        'reglas_motor',
        "entidad IN ('SOLICITUD','SOLICITUD_TIPO','FASE','TRAMITE','TAREA','EXPEDIENTE')",
        schema='public'
    )
