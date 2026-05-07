"""350_variable_tipo_tramite

Revision ID: 350_variable_tipo_tramite
Revises: 347a0b1c2d3e
Create Date: 2026-05-07

Issue #350 — Registra la variable tipo_tramite en catalogo_variables.
Necesaria para que _seleccionar_catalogo pueda discriminar el plazo
según el tipo de trámite en tareas ESPERAR_PLAZO.
"""
from alembic import op
import sqlalchemy as sa


revision = '350_variable_tipo_tramite'
down_revision = '347a0b1c2d3e'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'tipo_tramite',
            'Código del tipo de trámite activo en el contexto evaluado',
            'texto',
            NULL,
            TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre = 'tipo_tramite'"
    ))
