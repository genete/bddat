"""391_organismos_expediente

Revision ID: 391_organismos_expediente
Revises: 387_eliminar_whitelists_esft
Create Date: 2026-05-15

Crea la tabla organismos_expediente para gestionar la relación entre
organismos consultados y expedientes. Diseño: DISEÑO_CONSULTAS_ORGANISMOS.md §2.
"""
from alembic import op
import sqlalchemy as sa

revision = '391_organismos_expediente'
down_revision = '387_eliminar_whitelists_esft'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'organismos_expediente',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('expediente_id', sa.Integer(), nullable=False,
                  comment='FK expedientes. Expediente al que pertenece la consulta'),
        sa.Column('organismo_id', sa.Integer(), nullable=False,
                  comment='FK entidades (rol_consultado=True). Organismo consultado'),
        sa.Column('via', sa.String(30), nullable=False, server_default='consulta',
                  comment='Vía de resolución: consulta o declaracion_responsable'),
        sa.Column('documento_id', sa.Integer(), nullable=True,
                  comment='Documento de declaración responsable (solo si via=declaracion_responsable)'),
        sa.Column('estado', sa.String(40), nullable=False, server_default='pendiente',
                  comment='Estado del ciclo de vida del organismo en el expediente'),
        sa.Column('num_iteraciones_organismo', sa.Integer(), nullable=False, server_default='0',
                  comment='Contador de trámites CONSULTA_TRASLADO_ORGANISMO creados'),
        sa.Column('tramite_id', sa.Integer(), nullable=True,
                  comment='FK al trámite CONSULTA_SEPARATA asociado. NULL hasta que se crea'),
        sa.Column('plazo_legal_dias', sa.Integer(), nullable=True,
                  comment='Plazo legal en días capturado al crear la separata'),
        sa.PrimaryKeyConstraint('id', name='pk_organismos_expediente'),
        sa.ForeignKeyConstraint(['expediente_id'], ['public.expedientes.id'],
                                name='fk_org_exp_expediente', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organismo_id'], ['public.entidades.id'],
                                name='fk_org_exp_organismo'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'],
                                name='fk_org_exp_documento'),
        sa.ForeignKeyConstraint(['tramite_id'], ['public.tramites.id'],
                                name='fk_org_exp_tramite'),
        sa.UniqueConstraint('expediente_id', 'organismo_id', name='uq_org_exp_expediente_organismo'),
        sa.UniqueConstraint('tramite_id', name='uq_org_exp_tramite'),
        sa.CheckConstraint("via IN ('consulta', 'declaracion_responsable')",
                           name='ck_org_exp_via'),
        sa.CheckConstraint(
            "estado IN ('pendiente','separata_enviada','en_tramitacion',"
            "'cerrado_favorable','cerrado_con_condicionados','audiencia_previa','exonerado')",
            name='ck_org_exp_estado',
        ),
        schema='public',
    )
    op.create_index('idx_org_exp_expediente', 'organismos_expediente', ['expediente_id'], schema='public')
    op.create_index('idx_org_exp_organismo', 'organismos_expediente', ['organismo_id'], schema='public')


def downgrade():
    op.drop_index('idx_org_exp_organismo', table_name='organismos_expediente', schema='public')
    op.drop_index('idx_org_exp_expediente', table_name='organismos_expediente', schema='public')
    op.drop_table('organismos_expediente', schema='public')
