"""motor_reglas_agnostico_renombrar_columnas

Revision ID: d715b074b58c
Revises: f77b09ef7c1e
Create Date: 2026-04-17

Refactoriza las tablas reglas_motor y condiciones_regla para el motor agnóstico.
Las tablas estaban vacías en el momento de la migración.

reglas_motor:
  evento      → accion        (CREAR|INICIAR|FINALIZAR|BORRAR)
  entidad     → sujeto        (SOLICITUD|FASE|TRAMITE|TAREA|EXPEDIENTE)
  tipo_id     → tipo_sujeto_id
  accion      → efecto        (BLOQUEAR|ADVERTIR)
  mensaje     → eliminado (el texto se compila en la vista)
  params_extra → eliminado
  norma_compilada ADD (temporal hasta paso 3 cuando se cree tabla normas)
  prioridad   ADD (orden entre reglas del mismo trío accion/sujeto/tipo_sujeto_id)

condiciones_regla:
  tipo_criterio, parametros, negacion, operador_siguiente → eliminados
  nombre_variable ADD  (clave en el dict de variables del ContextAssembler)
  operador ADD         (EQ|NEQ|IN|NOT_IN|IS_NULL|NOT_NULL|GT|GTE|LT|LTE|BETWEEN|NOT_BETWEEN)
  valor ADD            (JSON — valor de referencia)
"""
from alembic import op
import sqlalchemy as sa


revision = 'd715b074b58c'
down_revision = 'f77b09ef7c1e'
branch_labels = None
depends_on = None


def upgrade():
    # -----------------------------------------------------------------------
    # reglas_motor
    # -----------------------------------------------------------------------
    op.drop_constraint('ck_reglas_motor_evento',  'reglas_motor', schema='public')
    op.drop_constraint('ck_reglas_motor_entidad', 'reglas_motor', schema='public')
    op.drop_constraint('ck_reglas_motor_accion',  'reglas_motor', schema='public')
    op.drop_index('idx_reglas_motor_lookup', table_name='reglas_motor', schema='public')

    # Renombrar en orden: primero accion→efecto (libera el nombre), luego evento→accion
    op.alter_column('reglas_motor', 'accion',  new_column_name='efecto',         schema='public')
    op.alter_column('reglas_motor', 'evento',  new_column_name='accion',         schema='public')
    op.alter_column('reglas_motor', 'entidad', new_column_name='sujeto',         schema='public')
    op.alter_column('reglas_motor', 'tipo_id', new_column_name='tipo_sujeto_id', schema='public')

    op.drop_column('reglas_motor', 'mensaje',      schema='public')
    op.drop_column('reglas_motor', 'params_extra', schema='public')

    op.add_column('reglas_motor',
        sa.Column('norma_compilada', sa.String(300), nullable=True,
                  comment='Referencia normativa (temporal hasta tabla normas en paso 3)'),
        schema='public'
    )
    op.add_column('reglas_motor',
        sa.Column('prioridad', sa.Integer, nullable=False, server_default='0',
                  comment='Orden entre reglas del mismo (accion, sujeto, tipo_sujeto_id)'),
        schema='public'
    )

    op.create_check_constraint(
        'ck_reglas_motor_accion', 'reglas_motor',
        "accion IN ('CREAR','INICIAR','FINALIZAR','BORRAR')", schema='public'
    )
    op.create_check_constraint(
        'ck_reglas_motor_sujeto', 'reglas_motor',
        "sujeto IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')", schema='public'
    )
    op.create_check_constraint(
        'ck_reglas_motor_efecto', 'reglas_motor',
        "efecto IN ('BLOQUEAR','ADVERTIR')", schema='public'
    )
    op.create_index(
        'idx_reglas_motor_lookup', 'reglas_motor',
        ['accion', 'sujeto', 'tipo_sujeto_id'], schema='public'
    )

    # -----------------------------------------------------------------------
    # condiciones_regla
    # -----------------------------------------------------------------------
    op.drop_constraint('ck_condiciones_regla_operador', 'condiciones_regla', schema='public')
    op.drop_index('idx_condiciones_regla_criterio', table_name='condiciones_regla', schema='public')

    op.drop_column('condiciones_regla', 'tipo_criterio',      schema='public')
    op.drop_column('condiciones_regla', 'parametros',         schema='public')
    op.drop_column('condiciones_regla', 'negacion',           schema='public')
    op.drop_column('condiciones_regla', 'operador_siguiente', schema='public')

    op.add_column('condiciones_regla',
        sa.Column('nombre_variable', sa.String(80), nullable=False, server_default='',
                  comment='Clave en el dict de variables del ContextAssembler'),
        schema='public'
    )
    op.add_column('condiciones_regla',
        sa.Column('operador', sa.String(20), nullable=False, server_default='EQ',
                  comment='EQ|NEQ|IN|NOT_IN|IS_NULL|NOT_NULL|GT|GTE|LT|LTE|BETWEEN|NOT_BETWEEN'),
        schema='public'
    )
    op.add_column('condiciones_regla',
        sa.Column('valor', sa.JSON, nullable=True,
                  comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL'),
        schema='public'
    )

    op.create_check_constraint(
        'ck_condiciones_regla_operador', 'condiciones_regla',
        "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL','GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
        schema='public'
    )
    op.create_index(
        'idx_condiciones_regla_variable', 'condiciones_regla',
        ['nombre_variable'], schema='public'
    )


def downgrade():
    # condiciones_regla
    op.drop_constraint('ck_condiciones_regla_operador', 'condiciones_regla', schema='public')
    op.drop_index('idx_condiciones_regla_variable', table_name='condiciones_regla', schema='public')
    op.drop_column('condiciones_regla', 'nombre_variable', schema='public')
    op.drop_column('condiciones_regla', 'operador',        schema='public')
    op.drop_column('condiciones_regla', 'valor',           schema='public')
    op.add_column('condiciones_regla',
        sa.Column('tipo_criterio', sa.String(40), nullable=False, server_default=''), schema='public')
    op.add_column('condiciones_regla',
        sa.Column('parametros', sa.JSON, nullable=False, server_default='{}'), schema='public')
    op.add_column('condiciones_regla',
        sa.Column('negacion', sa.Boolean, nullable=False, server_default='false'), schema='public')
    op.add_column('condiciones_regla',
        sa.Column('operador_siguiente', sa.String(5), nullable=False, server_default='AND'),
        schema='public')
    op.create_check_constraint(
        'ck_condiciones_regla_operador', 'condiciones_regla',
        "operador_siguiente IN ('AND','OR')", schema='public'
    )
    op.create_index('idx_condiciones_regla_criterio', 'condiciones_regla', ['tipo_criterio'], schema='public')

    # reglas_motor
    op.drop_constraint('ck_reglas_motor_accion', 'reglas_motor', schema='public')
    op.drop_constraint('ck_reglas_motor_sujeto', 'reglas_motor', schema='public')
    op.drop_constraint('ck_reglas_motor_efecto', 'reglas_motor', schema='public')
    op.drop_index('idx_reglas_motor_lookup', table_name='reglas_motor', schema='public')
    op.drop_column('reglas_motor', 'norma_compilada', schema='public')
    op.drop_column('reglas_motor', 'prioridad',       schema='public')
    op.alter_column('reglas_motor', 'efecto',         new_column_name='accion',   schema='public')
    op.alter_column('reglas_motor', 'tipo_sujeto_id', new_column_name='tipo_id',  schema='public')
    op.alter_column('reglas_motor', 'sujeto',         new_column_name='entidad',  schema='public')
    op.alter_column('reglas_motor', 'accion',         new_column_name='evento',   schema='public')
    op.add_column('reglas_motor',
        sa.Column('mensaje', sa.String(500), nullable=False, server_default=''), schema='public')
    op.add_column('reglas_motor',
        sa.Column('params_extra', sa.String(100), nullable=True), schema='public')
    op.create_check_constraint(
        'ck_reglas_motor_evento', 'reglas_motor',
        "evento IN ('CREAR','INICIAR','FINALIZAR','BORRAR')", schema='public'
    )
    op.create_check_constraint(
        'ck_reglas_motor_entidad', 'reglas_motor',
        "entidad IN ('SOLICITUD','FASE','TRAMITE','TAREA','EXPEDIENTE')", schema='public'
    )
    op.create_check_constraint(
        'ck_reglas_motor_accion', 'reglas_motor',
        "accion IN ('BLOQUEAR','ADVERTIR')", schema='public'
    )
    op.create_index('idx_reglas_motor_lookup', 'reglas_motor', ['evento', 'entidad', 'tipo_id'], schema='public')
