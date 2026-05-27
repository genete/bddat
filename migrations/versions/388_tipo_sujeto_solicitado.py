"""388_tipo_sujeto_solicitado

Revision ID: 388_tipo_sujeto_solicitado
Revises: 346_tramites_tareas_documentos
Create Date: 2026-05-15

Issue #388 — Registra tipo_sujeto_solicitado en catalogo_variables.
Prerrequisito de #387: permite expresar restricciones F→T con NOT_IN
sin multiplicar reglas BLOQUEAR por cada trámite prohibido.
"""
from alembic import op
import sqlalchemy as sa


revision = '388_tipo_sujeto_solicitado'
down_revision = '346_tramites_tareas_documentos'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'tipo_sujeto_solicitado',
            'Código del tipo de objeto que se quiere crear o sobre el que se actúa (TipoFase o TipoTramite)',
            'texto',
            NULL,
            TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.catalogo_variables WHERE nombre = 'tipo_sujeto_solicitado'"
    ))
