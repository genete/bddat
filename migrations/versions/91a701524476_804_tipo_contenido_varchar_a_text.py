"""804_tipo_contenido_varchar_a_text

Revision ID: 91a701524476
Revises: 776_plazo_elaborar_admision
Create Date: 2026-08-23 07:38:52.061169

Issue #804 — documentos.tipo_contenido era VARCHAR(50); el MIME de .docx
moderno ('application/vnd.openxmlformats-officedocument.wordprocessingml.document')
tiene 74 caracteres y desbordaba la columna, bloqueando el guardado de
cualquier escrito .docx real (INSERT con StringDataRightTruncation). Mismo
precedente que 45b0d1302dd4 (documentos.url): ampliar a Text() en vez de
fijar otro tope que un formato futuro (.xlsx, .pptx) pueda volver a agotar.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91a701524476'
down_revision = '776_plazo_elaborar_admision'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('documentos', 'tipo_contenido',
        existing_type=sa.String(length=50),
        type_=sa.Text(),
        schema='public')


def downgrade():
    op.alter_column('documentos', 'tipo_contenido',
        existing_type=sa.Text(),
        type_=sa.String(length=50),
        schema='public')
