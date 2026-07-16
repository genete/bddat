"""601_operadores_condiciones_requisito

Revision ID: 6502bc446277
Revises: 073a0df4493f
Create Date: 2026-07-16 09:48:19.584289

Ensancha ck_condiciones_requisito_operador a los 12 operadores del catálogo
compartido (app/services/operadores.py) — paridad con ck_condiciones_regla_operador
y ck_condiciones_excepcion_operador. Antes solo admitía EQ/NEQ/IN/NOT_IN/IS_NULL/
NOT_NULL; #601 corrige el evaluador Python pero sin este ALTER el Supervisor no
podía guardar una condición GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN (la BD la rechazaba).

Ensanchar un CHECK constraint es seguro: ninguna fila existente puede violarlo.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6502bc446277'
down_revision = '073a0df4493f'
branch_labels = None
depends_on = None

_OPERADORES_ANTERIOR = "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL')"
_OPERADORES_NUEVO = (
    "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
    "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')"
)


def upgrade():
    op.drop_constraint(
        'ck_condiciones_requisito_operador', 'condiciones_requisito', schema='public'
    )
    op.create_check_constraint(
        'ck_condiciones_requisito_operador', 'condiciones_requisito',
        _OPERADORES_NUEVO, schema='public',
    )


def downgrade():
    op.drop_constraint(
        'ck_condiciones_requisito_operador', 'condiciones_requisito', schema='public'
    )
    op.create_check_constraint(
        'ck_condiciones_requisito_operador', 'condiciones_requisito',
        _OPERADORES_ANTERIOR, schema='public',
    )
