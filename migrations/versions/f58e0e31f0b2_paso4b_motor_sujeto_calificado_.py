"""paso4b_motor_sujeto_calificado_excepciones

Revision ID: f58e0e31f0b2
Revises: 557859de1417
Create Date: 2026-04-23 12:12:13.802453

Refactoriza reglas_motor para sujeto calificado ESFTT y añade tablas de excepciones.

Cambios en reglas_motor:
  - sujeto: VARCHAR(20) con CHECK fijo → VARCHAR(200) sin CHECK
    El sujeto ahora es un patrón calificado: 'ANY/AAP/RESOLUCION'
    El matching es posicional por segmentos, con ANY como comodín.
  - Elimina tipo_sujeto_id (INTEGER): sustituido por la calificación en sujeto
  - Elimina índice idx_reglas_motor_lookup; crea idx_reglas_motor_accion_sujeto

Nuevas tablas:
  - excepciones_motor: excepciones ancladas a una regla concreta (regla_id FK)
  - condiciones_excepcion: condiciones de cada excepción (misma estructura que condiciones_regla)
"""
from alembic import op
import sqlalchemy as sa


revision = 'f58e0e31f0b2'
down_revision = '557859de1417'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Ajustar reglas_motor
    op.drop_index('idx_reglas_motor_lookup', table_name='reglas_motor', schema='public')
    op.drop_constraint('ck_reglas_motor_sujeto', 'reglas_motor', schema='public', type_='check')
    op.alter_column('reglas_motor', 'sujeto',
                    existing_type=sa.String(20),
                    type_=sa.String(200),
                    schema='public')
    op.drop_column('reglas_motor', 'tipo_sujeto_id', schema='public')
    op.create_index('idx_reglas_motor_accion_sujeto', 'reglas_motor',
                    ['accion', 'sujeto'], schema='public')

    # 2. Crear excepciones_motor
    op.create_table(
        'excepciones_motor',
        sa.Column('id',        sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('regla_id',  sa.Integer, nullable=False,
                  comment='FK a reglas_motor — prohibición que esta excepción neutraliza'),
        sa.Column('norma_id',  sa.Integer, nullable=True,
                  comment='FK a normas — norma que establece la excepción'),
        sa.Column('articulo',  sa.String(20), nullable=True,
                  comment='Artículo de la excepción: "DA1" | "DF4"'),
        sa.Column('apartado',  sa.String(20), nullable=True,
                  comment='Sub-apartado si procede'),
        sa.Column('activa',    sa.Boolean, nullable=False, server_default='true',
                  comment='Desactivar en lugar de borrar — preserva trazabilidad'),
        sa.ForeignKeyConstraint(['regla_id'], ['public.reglas_motor.id'],
                                name='fk_excepciones_motor_regla', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['norma_id'], ['public.normas.id'],
                                name='fk_excepciones_motor_norma'),
        schema='public',
    )
    op.create_index('idx_excepciones_motor_regla', 'excepciones_motor', ['regla_id'], schema='public')

    # 3. Crear condiciones_excepcion
    op.create_table(
        'condiciones_excepcion',
        sa.Column('id',           sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('excepcion_id', sa.Integer, nullable=False,
                  comment='FK a excepciones_motor'),
        sa.Column('variable_id',  sa.Integer, nullable=False,
                  comment='FK a catalogo_variables — variable evaluada'),
        sa.Column('operador',     sa.String(20), nullable=False,
                  comment='EQ|NEQ|IN|NOT_IN|IS_NULL|NOT_NULL|GT|GTE|LT|LTE|BETWEEN|NOT_BETWEEN'),
        sa.Column('valor',        sa.JSON, nullable=True,
                  comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL'),
        sa.Column('orden',        sa.Integer, nullable=False, server_default='1',
                  comment='Orden informativo dentro de la excepción'),
        sa.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL','GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_excepcion_operador'
        ),
        sa.ForeignKeyConstraint(['excepcion_id'], ['public.excepciones_motor.id'],
                                name='fk_condiciones_excepcion_excepcion', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variable_id'], ['public.catalogo_variables.id'],
                                name='fk_condiciones_excepcion_variable'),
        schema='public',
    )
    op.create_index('idx_condiciones_excepcion_excepcion', 'condiciones_excepcion',
                    ['excepcion_id'], schema='public')
    op.create_index('idx_condiciones_excepcion_variable', 'condiciones_excepcion',
                    ['variable_id'], schema='public')


def downgrade():
    # 3. Drop condiciones_excepcion
    op.drop_index('idx_condiciones_excepcion_variable',  table_name='condiciones_excepcion', schema='public')
    op.drop_index('idx_condiciones_excepcion_excepcion', table_name='condiciones_excepcion', schema='public')
    op.drop_table('condiciones_excepcion', schema='public')

    # 2. Drop excepciones_motor
    op.drop_index('idx_excepciones_motor_regla', table_name='excepciones_motor', schema='public')
    op.drop_table('excepciones_motor', schema='public')

    # 1. Restaurar reglas_motor
    op.drop_index('idx_reglas_motor_accion_sujeto', table_name='reglas_motor', schema='public')
    op.add_column('reglas_motor',
        sa.Column('tipo_sujeto_id', sa.Integer, nullable=True,
                  comment='ID en tipos_* del sujeto. NULL = aplica a todos los tipos'),
        schema='public')
    op.alter_column('reglas_motor', 'sujeto',
                    existing_type=sa.String(200),
                    type_=sa.String(20),
                    schema='public')
    op.create_check_constraint(
        'ck_reglas_motor_sujeto', 'reglas_motor',
        "sujeto IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')",
        schema='public'
    )
    op.create_index('idx_reglas_motor_lookup', 'reglas_motor',
                    ['accion', 'sujeto', 'tipo_sujeto_id'], schema='public')
