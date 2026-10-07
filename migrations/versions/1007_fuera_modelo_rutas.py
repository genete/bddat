"""1007_fuera_modelo_rutas — fuera las columnas del modelo de rutas: hash_md5, tipo_contenido y ruta_pdf

Revision ID: 1007_fuera_modelo_rutas
Revises: 1007_check_url_o_fichero_ref
Create Date: 2026-10-07

Issue #1007 (ADR-050 §C, §M), PR 5. Tras el corte del PR 4 nadie escribe ni lee estas columnas:

- `documentos.hash_md5` y su índice `idx_documentos_hash`: el contenido lo señala `fichero_ref` y
  la deduplicación la da `ficheros.contenido_sha256`.
- `documentos.tipo_contenido`: el formato es `ficheros.formato`, detectado por el contenido.
- `certificados_fase.ruta_pdf`: el PDF del certificado está en el almacén, como documento.

Solo el esquema. Los valores que queden en desarrollo son datos de operación y se pierden.

Downgrade: vuelve a crear las tres columnas, vacías, y el índice.
"""
from alembic import op
import sqlalchemy as sa


revision = '1007_fuera_modelo_rutas'
down_revision = '1007_check_url_o_fichero_ref'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('idx_documentos_hash', table_name='documentos', schema='public')
    op.drop_column('documentos', 'hash_md5', schema='public')
    op.drop_column('documentos', 'tipo_contenido', schema='public')
    op.drop_column('certificados_fase', 'ruta_pdf', schema='public')


def downgrade():
    op.add_column('certificados_fase', sa.Column('ruta_pdf', sa.Text(), nullable=True),
                  schema='public')
    op.add_column('documentos', sa.Column(
        'tipo_contenido', sa.Text(), nullable=True,
        comment='Tipo MIME del archivo (ej: application/pdf)'), schema='public')
    op.add_column('documentos', sa.Column(
        'hash_md5', sa.String(32), nullable=True,
        comment='Hash MD5 para verificación de integridad y detección de duplicados'), schema='public')
    op.create_index('idx_documentos_hash', 'documentos', ['hash_md5'], schema='public')
