"""652_sentido_diagnostico — sentido de la respuesta de un organismo en el diagnóstico

Revision ID: 652_sentido_diagnostico
Revises: 652_reglas_traslados
Create Date: 2026-11-09

Issue #652 (ADR-042 §D, DISEÑO_CONSULTAS_ORGANISMOS.md §4). El diagnóstico de la tarea
ANALIZAR de la respuesta de un organismo dice si es favorable, condicionada o
desfavorable, pero «desfavorable» junta dos cosas que el ciclo trata distinto: la
oposición y los reparos (cada una se cuenta aparte para avisar de cuándo debería
archivarse la consulta). El sentido de la respuesta no queda escrito en ningún otro
sitio —solo lo lee quien tramita en el PDF del organismo—, así que se guarda aquí.

Columna opcional, `sentido`: `oposicion` o `reparos`, y solo con resultado
`desfavorable`. En el resto de diagnósticos (análisis de solicitud, requerimientos,
traslados al titular…) queda siempre vacía: el resultado general no cambia de
significado. Que sea obligatoria en la respuesta de un organismo no se puede escribir
como restricción de BD (depende del tipo de trámite de la tarea): lo exige
`diagnosticos.crear_diagnostico`.
"""
from alembic import op
import sqlalchemy as sa


revision = '652_sentido_diagnostico'
down_revision = '652_reglas_traslados'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'diagnosticos',
        sa.Column(
            'sentido', sa.String(10), nullable=True,
            comment='Solo en la respuesta de un organismo con resultado desfavorable: '
                    'oposicion o reparos (#652)'),
        schema='public',
    )
    op.create_check_constraint(
        'ck_diagnostico_sentido', 'diagnosticos',
        "sentido IS NULL OR sentido IN ('oposicion', 'reparos')", schema='public')
    op.create_check_constraint(
        'ck_diagnostico_sentido_desfavorable', 'diagnosticos',
        "sentido IS NULL OR resultado = 'desfavorable'", schema='public')


def downgrade():
    op.drop_constraint('ck_diagnostico_sentido_desfavorable', 'diagnosticos',
                       schema='public', type_='check')
    op.drop_constraint('ck_diagnostico_sentido', 'diagnosticos',
                       schema='public', type_='check')
    op.drop_column('diagnosticos', 'sentido', schema='public')
