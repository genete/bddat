"""500_doc_borrador_firma — tipo de documento BORRADOR_FIRMA (subestado FIRMA de ELABORAR)

Revision ID: 500_doc_borrador_firma
Revises: 500_seed_abrev_esftt
Create Date: 2026-05-31

Issue #500 — Vista de árbol del expediente (ADR-016), MODELO_ESTADOS_SEMAFORO §3/§11.
Añade el tipo de documento `BORRADOR_FIRMA`: el PDF listo para firma que la tarea
ELABORAR consume como insumo del subpaso de firma. Su presencia entre los documentos
CONSUMIDOS distingue el subestado PENDIENTE_FIRMA (🟡) de PENDIENTE_REDACTAR (🔴).
Origen INTERNO (lo genera la administración). No crea tabla → sin GRANT.
"""
from alembic import op
import sqlalchemy as sa


revision = '500_doc_borrador_firma'
down_revision = '500_seed_abrev_esftt'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Idempotente: no duplica si ya existe (uq sobre codigo).
    conn.execute(sa.text("""
        INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
        VALUES (
            'BORRADOR_FIRMA',
            'Borrador para firma',
            'PDF de un documento ELABORADO, listo para enviar a la firma. Se vincula como '
            'documento CONSUMIDO de la tarea ELABORAR; su producido es el PDF ya firmado.',
            'INTERNO'
        )
        ON CONFLICT (codigo) DO NOTHING
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.tipos_documentos WHERE codigo = 'BORRADOR_FIRMA'"))
