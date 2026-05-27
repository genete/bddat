"""paso4a_proyectos_variables_dato

Revision ID: 557859de1417
Revises: a9cd38df8797
Create Date: 2026-04-23 12:12:10.280839

Añade 3 campos a proyectos para variables dato del motor de reglas:
  - sin_linea_aerea              BOOLEAN  (true = no contiene ninguna línea aérea)
  - max_tension_nominal_kv       NUMERIC  (tensión máxima de los elementos)
  - solo_suelo_urbano_urbanizable BOOLEAN  (true = recorrido íntegro en suelo urbano/urbanizable)

Todos nullable: no rompen expedientes existentes.
En el futuro los dos primeros podrán deducirse de los elementos de la instalación.
"""
from alembic import op
import sqlalchemy as sa


revision = '557859de1417'
down_revision = 'a9cd38df8797'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('proyectos',
        sa.Column('sin_linea_aerea', sa.Boolean, nullable=True,
                  comment='True si la instalación no contiene ninguna línea aérea (futuro: deducible de elementos)'),
        schema='public')
    op.add_column('proyectos',
        sa.Column('max_tension_nominal_kv', sa.Numeric(6, 2), nullable=True,
                  comment='Tensión nominal máxima de los elementos de la instalación en kV (futuro: deducible)'),
        schema='public')
    op.add_column('proyectos',
        sa.Column('solo_suelo_urbano_urbanizable', sa.Boolean, nullable=True,
                  comment='True si el recorrido íntegro de las instalaciones es en suelo urbano o urbanizable'),
        schema='public')


def downgrade():
    op.drop_column('proyectos', 'solo_suelo_urbano_urbanizable', schema='public')
    op.drop_column('proyectos', 'max_tension_nominal_kv', schema='public')
    op.drop_column('proyectos', 'sin_linea_aerea', schema='public')
