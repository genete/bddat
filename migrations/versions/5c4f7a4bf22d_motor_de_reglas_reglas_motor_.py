"""Motor de reglas — reglas_motor, condiciones_regla, tipos_solicitudes_compatibles

Revision ID: 5c4f7a4bf22d
Revises: 606202414595
Create Date: 2026-02-27 19:25:48.832792

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c4f7a4bf22d'
down_revision = '606202414595'
branch_labels = None
depends_on = None


def upgrade():
    # --- REGLAS_MOTOR ---
    op.create_table(
        'reglas_motor',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evento', sa.String(10), nullable=False),
        sa.Column('entidad', sa.String(20), nullable=False),
        sa.Column('tipo_id', sa.Integer(), nullable=True),
        sa.Column('accion', sa.String(10), nullable=False),
        sa.Column('mensaje', sa.String(500), nullable=False),
        sa.Column('norma', sa.String(200), nullable=True),
        sa.Column('params_extra', sa.String(100), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("evento IN ('CREAR','CERRAR','BORRAR')", name='ck_reglas_motor_evento'),
        sa.CheckConstraint(
            "entidad IN ('SOLICITUD','SOLICITUD_TIPO','FASE','TRAMITE','TAREA')",
            name='ck_reglas_motor_entidad'
        ),
        sa.CheckConstraint("accion IN ('BLOQUEAR','ADVERTIR')", name='ck_reglas_motor_accion'),
        schema='public'
    )
    op.create_index('idx_reglas_motor_lookup', 'reglas_motor', ['evento', 'entidad', 'tipo_id'], schema='public')

    # --- CONDICIONES_REGLA ---
    op.create_table(
        'condiciones_regla',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('regla_id', sa.Integer(), nullable=False),
        sa.Column('tipo_criterio', sa.String(40), nullable=False),
        sa.Column('parametros', sa.JSON(), nullable=False),
        sa.Column('negacion', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('orden', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('operador_siguiente', sa.String(5), nullable=False, server_default=sa.text("'AND'")),
        sa.ForeignKeyConstraint(['regla_id'], ['public.reglas_motor.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("operador_siguiente IN ('AND','OR')", name='ck_condiciones_regla_operador'),
        schema='public'
    )
    op.create_index('idx_condiciones_regla_regla', 'condiciones_regla', ['regla_id'], schema='public')
    op.create_index('idx_condiciones_regla_criterio', 'condiciones_regla', ['tipo_criterio'], schema='public')

    # --- TIPOS_SOLICITUDES_COMPATIBLES ---
    op.create_table(
        'tipos_solicitudes_compatibles',
        sa.Column('tipo_a_id', sa.Integer(), nullable=False),
        sa.Column('tipo_b_id', sa.Integer(), nullable=False),
        sa.Column('nota', sa.String(200), nullable=True),
        sa.ForeignKeyConstraint(['tipo_a_id'], ['tipos_solicitudes.id']),
        sa.ForeignKeyConstraint(['tipo_b_id'], ['tipos_solicitudes.id']),
        sa.PrimaryKeyConstraint('tipo_a_id', 'tipo_b_id'),
        sa.CheckConstraint('tipo_a_id < tipo_b_id', name='ck_compatibles_orden'),
        schema='public'
    )
    op.create_index('idx_compatibles_tipo_a', 'tipos_solicitudes_compatibles', ['tipo_a_id'], schema='public')
    op.create_index('idx_compatibles_tipo_b', 'tipos_solicitudes_compatibles', ['tipo_b_id'], schema='public')


def downgrade():
    op.drop_table('tipos_solicitudes_compatibles', schema='public')
    op.drop_table('condiciones_regla', schema='public')
    op.drop_table('reglas_motor', schema='public')
