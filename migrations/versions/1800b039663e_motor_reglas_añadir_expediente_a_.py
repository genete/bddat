"""Motor reglas — añadir EXPEDIENTE a entidades válidas

Revision ID: 1800b039663e
Revises: 5c4f7a4bf22d
Create Date: 2026-02-27 19:31:33.451178

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1800b039663e'
down_revision = '5c4f7a4bf22d'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL no permite ALTER CHECK directamente — hay que drop + recrear
    op.drop_constraint('ck_reglas_motor_entidad', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_entidad',
        'reglas_motor',
        "entidad IN ('SOLICITUD','SOLICITUD_TIPO','FASE','TRAMITE','TAREA','EXPEDIENTE')",
        schema='public'
    )


def downgrade():
    op.drop_constraint('ck_reglas_motor_entidad', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_entidad',
        'reglas_motor',
        "entidad IN ('SOLICITUD','SOLICITUD_TIPO','FASE','TRAMITE','TAREA')",
        schema='public'
    )
