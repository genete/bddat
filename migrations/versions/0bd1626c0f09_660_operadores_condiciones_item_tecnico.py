"""660_operadores_condiciones_item_tecnico

Revision ID: 0bd1626c0f09
Revises: 6502bc446277
Create Date: 2026-07-16 09:48:29.074199

Ensancha ck_condiciones_item_tecnico_operador a los 12 operadores del catálogo
compartido — gemelo exacto de la migración 601 (condiciones_item_tecnico
reproduce el mismo CHECK constraint limitado que condiciones_requisito, ver
CondicionItemTecnico.__doc__). Issue #660.

Ensanchar un CHECK constraint es seguro: ninguna fila existente puede violarlo.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bd1626c0f09'
down_revision = '6502bc446277'
branch_labels = None
depends_on = None

_OPERADORES_ANTERIOR = "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL')"
_OPERADORES_NUEVO = (
    "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
    "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')"
)


def upgrade():
    op.drop_constraint(
        'ck_condiciones_item_tecnico_operador', 'condiciones_item_tecnico', schema='public'
    )
    op.create_check_constraint(
        'ck_condiciones_item_tecnico_operador', 'condiciones_item_tecnico',
        _OPERADORES_NUEVO, schema='public',
    )


def downgrade():
    op.drop_constraint(
        'ck_condiciones_item_tecnico_operador', 'condiciones_item_tecnico', schema='public'
    )
    op.create_check_constraint(
        'ck_condiciones_item_tecnico_operador', 'condiciones_item_tecnico',
        _OPERADORES_ANTERIOR, schema='public',
    )
