"""466_direccion_notificacion_id_organismos_expediente

Revision ID: 342a6f032b38
Revises: 470_cert_fin_ip_consultas
Create Date: 2026-05-26 19:20:17.862386

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '342a6f032b38'
down_revision = '470_cert_fin_ip_consultas'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'organismos_expediente',
        sa.Column(
            'direccion_notificacion_id',
            sa.Integer(),
            sa.ForeignKey('public.direcciones_notificacion.id', name='fk_org_exp_direccion_notif'),
            nullable=True,
            comment='FK direcciones_notificacion. Dirección elegida al añadir el organismo; NULL = usar la más reciente activa con rol CONSULTADO',
        ),
        schema='public',
    )
    op.create_index(
        'ix_organismos_expediente_direccion_notificacion_id',
        'organismos_expediente',
        ['direccion_notificacion_id'],
        schema='public',
    )


def downgrade():
    op.drop_index(
        'ix_organismos_expediente_direccion_notificacion_id',
        table_name='organismos_expediente',
        schema='public',
    )
    op.drop_column('organismos_expediente', 'direccion_notificacion_id', schema='public')
