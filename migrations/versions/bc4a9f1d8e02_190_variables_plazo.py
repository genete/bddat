"""190_variables_plazo

Revision ID: bc4a9f1d8e02
Revises: 39fccabb9426
Create Date: 2026-04-28

Registra las variables de plazo en catalogo_variables (#190):
  - estado_plazo  — 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO'
  - efecto_plazo  — 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | ...

Ambas activa=TRUE (stub Fase 2: siempre devuelven SIN_PLAZO/NINGUNO).
La lógica real se implementa en #172 (plazos en días hábiles).
"""
from alembic import op
import sqlalchemy as sa


revision = 'bc4a9f1d8e02'
down_revision = '39fccabb9426'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa) VALUES "
        "('estado_plazo', 'Estado del plazo del elemento en tramitación', 'texto', NULL, TRUE), "
        "('efecto_plazo', 'Efecto legal del vencimiento del plazo', 'texto', NULL, TRUE)"
    ))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre IN ('estado_plazo', 'efecto_plazo')"
    ))
