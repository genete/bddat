"""add documento_solicitud_id to solicitudes

Revision ID: b7f95d61a7a9
Revises: d715b074b58c
Create Date: 2026-04-19 18:06:46.908716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f95d61a7a9'
down_revision = 'd715b074b58c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE public.solicitudes
            ADD COLUMN documento_solicitud_id INTEGER
            REFERENCES public.documentos(id) ON DELETE SET NULL;

        CREATE INDEX idx_solicitudes_doc_solicitud
            ON public.solicitudes(documento_solicitud_id);
    """)


def downgrade():
    op.execute("""
        DROP INDEX IF EXISTS public.idx_solicitudes_doc_solicitud;
        ALTER TABLE public.solicitudes DROP COLUMN IF EXISTS documento_solicitud_id;
    """)
