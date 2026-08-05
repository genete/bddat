"""728_consejerias_delegaciones_territoriales

Revision ID: 728_consejerias_delegaciones_territoriales
Revises: 725_creacion_generica_tramite
Create Date: 2026-08-05

Issue #728 — Crea consejerias_delegaciones_territoriales: composición de
Consejerías de la Delegación Territorial propia (1 ó 2, según el decreto de
organización territorial vigente). Fundacional, sin FK. Ver ADR-039 §1.

Se puebla en esta misma migración con la fila única (nuestra Delegación
Territorial), verificada contra el Decreto 190/2026, de 30 de julio (BOJA
extraordinario núm. 15).
"""
from alembic import op
import sqlalchemy as sa


revision = '728_consejerias_delegaciones_territoriales'
down_revision = '725_creacion_generica_tramite'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'consejerias_delegaciones_territoriales',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('consejeria_1_nombre', sa.String(200), nullable=False,
                  comment='Nombre completo de la primera Consejería, tal cual figura en el decreto vigente'),
        sa.Column('consejeria_2_nombre', sa.String(200), nullable=True,
                  comment='Nombre completo de la segunda Consejería, si la delegación agrupa dos. NULL si agrupa solo una'),
        sa.PrimaryKeyConstraint('id', name='pk_consejerias_delegaciones_territoriales'),
        schema='public',
    )

    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO public.consejerias_delegaciones_territoriales "
            "(consejeria_1_nombre, consejeria_2_nombre) VALUES (:c1, :c2)"
        ),
        {
            'c1': 'Consejería de Economía, Hacienda y Fondos Europeos',
            'c2': 'Consejería de Universidad, Industria, Energía e Innovación',
        },
    )

    op.execute("GRANT SELECT ON public.consejerias_delegaciones_territoriales TO claude_desktop")


def downgrade():
    op.drop_table('consejerias_delegaciones_territoriales', schema='public')
