"""914_tipos_fases_dup — alta de RESOLUCION_DUP y DATOS_CATASTRALES

Revision ID: 914_tipos_fases_dup
Revises: 914_tipos_solicitudes_aap_dup
Create Date: 2026-09-14

Issue #914, ADR-046. Fuente: ESTRUCTURA_ESF.json v2.4 / ESTRUCTURA_FTT.json
v6.5. Naming de RESOLUCION_DUP decidido en PRE-ADR-resolucion-doble-acto-dup.md
§4.1: codigo sin choque en tipos_fases (9 filas), abrev "RES_DUP" reserva
"DUP" para la solicitud, nombre_en_plantilla NULL (confirmado huérfano, §4.1.2
— el nombre de fichero lo compone tipos_tramites.nombre_en_plantilla, no este
campo).
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tipos_fases_dup'
down_revision = '914_tipos_solicitudes_aap_dup'
branch_labels = None
depends_on = None

_FASES = [
    # (codigo, nombre, abrev, es_finalizadora)
    ('RESOLUCION_DUP', 'Resolución de Declaración de Utilidad Pública', 'RES_DUP', True),
    ('DATOS_CATASTRALES', 'Datos Catastrales', 'DATOS CATASTR.', False),
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
