"""932_certificados_tipo_fase — tipo y fase_id en certificados (ADR-049 §F, N3)

Revision ID: 932_certificados_tipo_fase
Revises: 796_suspension_solo_causa_a
Create Date: 2026-09-24

Issue #932. Infraestructura de esquema para N4 (CERT_CUMPLIMIENTO_FASE):

1. `tipo` (VARCHAR(50), NOT NULL): código del tipo de certificado, mismo patrón
   que `certificados_fase.tipo_cert`. Hasta ahora se deducía por join a
   `documentos.tipo_doc_id -> tipos_documentos.codigo`; no sirve para un índice
   único sin desnormalizarlo. Backfill de las filas existentes (CERT_PLAZO_CUMPLIDO,
   CERT_FIN_IP_CONSULTAS) desde ese mismo join; en desarrollo, a fecha de esta
   migración, la tabla está vacía.
2. `fase_id` (FK nullable a fases.id, ON DELETE RESTRICT): mismo patrón que
   solicitud_id/reformado_id. NULL en las filas actuales (ninguna cuelga de una
   fase); lo rellenará N4 (CERT_CUMPLIMIENTO_FASE, uno por fase finalizadora,
   sin reformado_id porque las fases finalizadoras no se repiten por ronda,
   ADR-044 R5).
3. Índice único parcial (fase_id, tipo) WHERE fase_id IS NOT NULL: "como mucho
   un certificado emitido por tipo y elemento" (ADR-049 §F), mismo estilo que
   los dos índices parciales ya existentes para solicitud_id/reformado_id. Sirve
   también de índice de la FK: `fase_id = X` implica el predicado.

Sin CHECK de vocabulario de `tipo` (mismo criterio que #930 D7 para
`campo_fecha_cumplimiento`): lo sostienen los tests sobre filas reales y el
código que ya valida contra `tipos_documentos` al construir el Documento.
"""
from alembic import op
import sqlalchemy as sa


revision = '932_certificados_tipo_fase'
down_revision = '796_suspension_solo_causa_a'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    op.add_column(
        'certificados',
        sa.Column(
            'tipo', sa.String(50), nullable=True,
            comment='Código del tipo de certificado (tipos_documentos.codigo). '
                    'Denormalizado desde documentos.tipo_doc_id para permitir '
                    'el índice único (fase_id, tipo) sin join.',
        ),
        schema='public',
    )
    op.add_column(
        'certificados',
        sa.Column(
            'fase_id', sa.Integer(), nullable=True,
            comment='FK a FASES. NULL salvo en certificados anclados a una fase '
                    '(hoy, CERT_CUMPLIMIENTO_FASE, N4) — ver docstring de la clase',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_certificado_fase', 'certificados', 'fases', ['fase_id'], ['id'],
        source_schema='public', referent_schema='public', ondelete='RESTRICT',
    )

    conn.execute(sa.text("""
        UPDATE public.certificados c
        SET tipo = td.codigo
        FROM public.documentos d
        JOIN public.tipos_documentos td ON td.id = d.tipo_doc_id
        WHERE d.id = c.documento_id
    """))

    pendientes = conn.execute(sa.text(
        "SELECT count(*) FROM public.certificados WHERE tipo IS NULL"
    )).scalar()
    if pendientes:
        raise RuntimeError(
            f'{pendientes} fila(s) de certificados sin tipo tras el backfill — '
            'revisar documento_id / tipo_doc_id antes de continuar'
        )

    op.alter_column('certificados', 'tipo', nullable=False, schema='public')

    op.create_index(
        'uq_certificado_fase_tipo', 'certificados', ['fase_id', 'tipo'],
        unique=True, schema='public',
        postgresql_where=sa.text('fase_id IS NOT NULL'),
    )


def downgrade():
    op.drop_index('uq_certificado_fase_tipo', table_name='certificados', schema='public')
    op.drop_constraint('fk_certificado_fase', 'certificados', type_='foreignkey',
                       schema='public')
    op.drop_column('certificados', 'fase_id', schema='public')
    op.drop_column('certificados', 'tipo', schema='public')
