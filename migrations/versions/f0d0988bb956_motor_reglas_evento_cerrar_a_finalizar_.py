"""Motor reglas — evento CERRAR a FINALIZAR añadir INICIAR

Revision ID: f0d0988bb956
Revises: cae8e6d884af
Create Date: 2026-02-28 08:59:04.925762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0d0988bb956'
down_revision = 'cae8e6d884af'
branch_labels = None
depends_on = None


def upgrade():
    # Las tablas están vacías — migración limpia sin datos
    op.drop_constraint('ck_reglas_motor_evento', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_evento',
        'reglas_motor',
        "evento IN ('CREAR','INICIAR','FINALIZAR','BORRAR')",
        schema='public'
    )


def downgrade():
    op.drop_constraint('ck_reglas_motor_evento', 'reglas_motor', schema='public', type_='check')
    op.create_check_constraint(
        'ck_reglas_motor_evento',
        'reglas_motor',
        "evento IN ('CREAR','CERRAR','BORRAR')",
        schema='public'
    )
