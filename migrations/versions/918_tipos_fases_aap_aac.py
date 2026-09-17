"""918_tipos_fases_aap_aac — alta de RESOLUCION_AAP y RESOLUCION_AAC

Revision ID: 918_tipos_fases_aap_aac
Revises: 893_tipos_solicitudes_nombre_en_plantilla
Create Date: 2026-09-17

Issue #918, ADR-047 §A. Fases finalizadoras alternativas a RESOLUCION para
cuando AAP y AAC (solas o con DUP) se resuelven en actos separados;
RESOLUCION conserva su código y significado para el acto conjunto, sin
cambios. abrev calcado del patrón RES_DUP (914_tipos_fases_dup, ADR-046);
nombre_en_plantilla NULL, mismo criterio que RESOLUCION y RESOLUCION_DUP —
el nombre de fichero lo compone tipos_tramites.nombre_en_plantilla, no este
campo.
"""
from alembic import op
import sqlalchemy as sa


revision = '918_tipos_fases_aap_aac'
down_revision = '893_tipos_solicitudes_nombre_en_plantilla'
branch_labels = None
depends_on = None

_FASES = [
    # (codigo, nombre, abrev, es_finalizadora)
    ('RESOLUCION_AAP', 'Resolución de Autorización Administrativa Previa', 'RES_AAP', True),
    ('RESOLUCION_AAC', 'Resolución de Autorización Administrativa de Construcción', 'RES_AAC', True),
]


def upgrade():
    conn = op.get_bind()
    for codigo, nombre, abrev, es_finalizadora in _FASES:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_fases (codigo, nombre, abrev, es_finalizadora)
            VALUES (:codigo, :nombre, :abrev, :es_finalizadora)
            ON CONFLICT DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'abrev': abrev,
               'es_finalizadora': es_finalizadora})


def downgrade():
    conn = op.get_bind()
    for codigo, _nombre, _abrev, _es_finalizadora in _FASES:
        conn.execute(sa.text(
            "DELETE FROM public.tipos_fases WHERE codigo = :codigo"
        ), {'codigo': codigo})
