"""387_eliminar_whitelists_esft

Revision ID: 387_eliminar_whitelists_esft
Revises: 388_tipo_sujeto_solicitado
Create Date: 2026-05-15

ADR-007: Las tablas whitelist son blacklists implícitas que contradicen el
principio del motor (todo permitido excepto lo prohibido). Se eliminan; sus
restricciones pasarán al motor como reglas CREAR con base legal.
"""
from alembic import op
import sqlalchemy as sa

revision = '387_eliminar_whitelists_esft'
down_revision = '388_tipo_sujeto_solicitado'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Eliminar las tres tablas whitelist
    op.drop_table('fases_tramites', schema='public')
    op.drop_table('solicitudes_fases', schema='public')
    op.drop_table('expedientes_solicitudes', schema='public')

    # 2. Eliminar columna dead code en tramites_tareas
    op.drop_constraint('fk_tram_tareas_doc_consumido_tipo', 'tramites_tareas', schema='public', type_='foreignkey')
    op.drop_column('tramites_tareas', 'doc_consumido_tipo_id', schema='public')

    # 3. Eliminar reglas con INICIAR/FINALIZAR
    op.execute("DELETE FROM public.reglas_motor WHERE accion IN ('INICIAR', 'FINALIZAR')")

    # 4. Actualizar CHECK constraint
    op.drop_constraint('ck_reglas_motor_accion', 'reglas_motor', schema='public')
    op.create_check_constraint(
        'ck_reglas_motor_accion',
        'reglas_motor',
        "accion IN ('CREAR', 'BORRAR')",
        schema='public',
    )


def downgrade():
    # Restaurar CHECK constraint
    op.drop_constraint('ck_reglas_motor_accion', 'reglas_motor', schema='public')
    op.create_check_constraint(
        'ck_reglas_motor_accion',
        'reglas_motor',
        "accion IN ('CREAR','INICIAR','FINALIZAR','BORRAR')",
        schema='public',
    )

    # Restaurar columna (vacía — datos perdidos)
    op.add_column('tramites_tareas',
        sa.Column('doc_consumido_tipo_id', sa.Integer(), nullable=True),
        schema='public',
    )
    op.create_foreign_key(
        'fk_tram_tareas_doc_consumido_tipo',
        'tramites_tareas', 'tipos_documentos',
        ['doc_consumido_tipo_id'], ['id'],
        source_schema='public', referent_schema='public',
    )

    # Recrear tablas vacías (datos perdidos)
    op.create_table('expedientes_solicitudes',
        sa.Column('tipo_expediente_id', sa.Integer(), nullable=False),
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('tipo_expediente_id', 'tipo_solicitud_id', name='pk_expedientes_solicitudes'),
        sa.ForeignKeyConstraint(['tipo_expediente_id'], ['tipos_expedientes.id'], name='fk_exp_sol_tipo_expediente'),
        sa.ForeignKeyConstraint(['tipo_solicitud_id'], ['tipos_solicitudes.id'], name='fk_exp_sol_tipo_solicitud'),
        schema='public',
    )
    op.create_table('solicitudes_fases',
        sa.Column('tipo_solicitud_id', sa.Integer(), nullable=False),
        sa.Column('tipo_fase_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('tipo_solicitud_id', 'tipo_fase_id', name='pk_solicitudes_fases'),
        sa.ForeignKeyConstraint(['tipo_solicitud_id'], ['tipos_solicitudes.id'], name='fk_sol_fas_tipo_solicitud'),
        sa.ForeignKeyConstraint(['tipo_fase_id'], ['tipos_fases.id'], name='fk_sol_fas_tipo_fase'),
        schema='public',
    )
    op.create_table('fases_tramites',
        sa.Column('tipo_fase_id', sa.Integer(), nullable=False),
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('tipo_fase_id', 'tipo_tramite_id', name='pk_fases_tramites'),
        sa.ForeignKeyConstraint(['tipo_fase_id'], ['tipos_fases.id'], name='fk_fas_tram_tipo_fase'),
        sa.ForeignKeyConstraint(['tipo_tramite_id'], ['tipos_tramites.id'], name='fk_fas_tram_tipo_tramite'),
        schema='public',
    )
