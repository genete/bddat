"""paso3_motor_normas_catalogo

Revision ID: a9cd38df8797
Revises: 95c2e862e8d6
Create Date: 2026-04-21 20:07:34.474035

Crea tablas normas y catalogo_variables.
Ajusta reglas_motor: añade norma_id/articulo/apartado, elimina norma_compilada.
Ajusta condiciones_regla: sustituye nombre_variable VARCHAR por variable_id FK.
"""
from alembic import op
import sqlalchemy as sa


revision = 'a9cd38df8797'
down_revision = '95c2e862e8d6'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Crear normas
    op.create_table(
        'normas',
        sa.Column('id',      sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('codigo',  sa.String(30),  nullable=False),
        sa.Column('titulo',  sa.String(300), nullable=False),
        sa.Column('url_eli', sa.String(500), nullable=True),
        sa.UniqueConstraint('codigo', name='uq_normas_codigo'),
        schema='public',
    )
    op.create_index('idx_normas_codigo', 'normas', ['codigo'], unique=True, schema='public')

    # 2. Crear catalogo_variables (FK → normas)
    op.create_table(
        'catalogo_variables',
        sa.Column('id',        sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('nombre',    sa.String(80),  nullable=False),
        sa.Column('etiqueta',  sa.String(150), nullable=False),
        sa.Column('tipo_dato', sa.String(20),  nullable=False),
        sa.Column('norma_id',  sa.Integer,     nullable=True),
        sa.Column('activa',    sa.Boolean,     nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['norma_id'], ['public.normas.id'], name='fk_catalogo_variables_norma'),
        sa.UniqueConstraint('nombre', name='uq_catalogo_variables_nombre'),
        schema='public',
    )
    op.create_index('idx_catalogo_variables_nombre', 'catalogo_variables', ['nombre'], unique=True, schema='public')

    # 3. Ajustar reglas_motor
    op.add_column('reglas_motor',
        sa.Column('norma_id',  sa.Integer,    nullable=True,
                  comment='FK a normas — norma legal de la regla'),
        schema='public')
    op.add_column('reglas_motor',
        sa.Column('articulo',  sa.String(20), nullable=True,
                  comment='Artículo exacto: "24.3" | "DA4" | "DF2"'),
        schema='public')
    op.add_column('reglas_motor',
        sa.Column('apartado',  sa.String(20), nullable=True,
                  comment='Sub-apartado si procede'),
        schema='public')
    op.create_foreign_key(
        'fk_reglas_motor_norma', 'reglas_motor', 'normas',
        ['norma_id'], ['id'], source_schema='public', referent_schema='public'
    )
    op.drop_column('reglas_motor', 'norma_compilada', schema='public')

    # 4. Ajustar condiciones_regla
    op.drop_index('idx_condiciones_regla_variable', table_name='condiciones_regla', schema='public')
    op.drop_column('condiciones_regla', 'nombre_variable', schema='public')
    op.add_column('condiciones_regla',
        sa.Column('variable_id', sa.Integer, nullable=False, server_default='0',
                  comment='FK a catalogo_variables'),
        schema='public')
    op.create_foreign_key(
        'fk_condiciones_regla_variable', 'condiciones_regla', 'catalogo_variables',
        ['variable_id'], ['id'], source_schema='public', referent_schema='public'
    )
    op.alter_column('condiciones_regla', 'variable_id', server_default=None, schema='public')
    op.create_index('idx_condiciones_regla_variable', 'condiciones_regla', ['variable_id'], schema='public')


def downgrade():
    # 4. Restaurar condiciones_regla
    op.drop_index('idx_condiciones_regla_variable', table_name='condiciones_regla', schema='public')
    op.drop_constraint('fk_condiciones_regla_variable', 'condiciones_regla', schema='public', type_='foreignkey')
    op.drop_column('condiciones_regla', 'variable_id', schema='public')
    op.add_column('condiciones_regla',
        sa.Column('nombre_variable', sa.String(80), nullable=False, server_default=''),
        schema='public')
    op.alter_column('condiciones_regla', 'nombre_variable', server_default=None, schema='public')
    op.create_index('idx_condiciones_regla_variable', 'condiciones_regla', ['nombre_variable'], schema='public')

    # 3. Restaurar reglas_motor
    op.drop_constraint('fk_reglas_motor_norma', 'reglas_motor', schema='public', type_='foreignkey')
    op.drop_column('reglas_motor', 'norma_id',  schema='public')
    op.drop_column('reglas_motor', 'articulo',  schema='public')
    op.drop_column('reglas_motor', 'apartado',  schema='public')
    op.add_column('reglas_motor',
        sa.Column('norma_compilada', sa.String(300), nullable=True),
        schema='public')

    # 2. Drop catalogo_variables
    op.drop_index('idx_catalogo_variables_nombre', table_name='catalogo_variables', schema='public')
    op.drop_table('catalogo_variables', schema='public')

    # 1. Drop normas
    op.drop_index('idx_normas_codigo', table_name='normas', schema='public')
    op.drop_table('normas', schema='public')
