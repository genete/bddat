"""893_tipos_solicitudes_nombre_en_plantilla — corrige nombre_en_plantilla desplazado

Revision ID: 893_tipos_solicitudes_nombre_en_plantilla
Revises: 914_catalogo_plazos_dup
Create Date: 2026-09-17

Issue #893 — la migración `c3d4e5f6a7b8_fase3_nombre_en_plantilla` sembró
`tipos_solicitudes.nombre_en_plantilla` de los ids 19/20/21 con los nombres
de un catálogo de combinaciones anterior al vigente (desplazamiento de
sigla). Corrige por clave natural (`siglas`), no por id.

De paso (tarea 2 del issue): ids 4/5 (`AE_PROVISIONAL`/`AE_DEFINITIVA`)
tenían `nombre_en_plantilla` = "AAE Provisional"/"AAE Definitiva".
NORMATIVA_PLAZOS.md §2.1 y §2.2 confirman que RD 1955/2000 y LSE 24/2013
usan "autorización de explotación" (sin "administrativa") — coherente con
que `siglas` ya usaba "AE_..." y no "AAE_...". Se corrige a juego.
"""
from alembic import op
import sqlalchemy as sa


revision = '893_tipos_solicitudes_nombre_en_plantilla'
down_revision = '914_catalogo_plazos_dup'
branch_labels = None
depends_on = None

_CORRECCIONES = (
    ('AE_PROVISIONAL', 'AE Provisional'),
    ('AE_DEFINITIVA', 'AE Definitiva'),
    ('AAP+AAC+DUP', 'AAP+AAC+DUP'),
    ('AAC+DUP', 'AAC+DUP'),
    ('AE_DEFINITIVA+AAT', 'AE_DEFINITIVA+AAT'),
)


def upgrade():
    conn = op.get_bind()
    for siglas, nombre_en_plantilla in _CORRECCIONES:
        conn.execute(sa.text("""
            UPDATE public.tipos_solicitudes
            SET nombre_en_plantilla = :nombre_en_plantilla
            WHERE siglas = :siglas
        """), {'siglas': siglas, 'nombre_en_plantilla': nombre_en_plantilla})


def downgrade():
    """No revierte, a propósito.

    Reintroducir los nombres cruzados ("AAP+AAC+RAIPEE+RADNE" en una
    solicitud AAC+DUP, entre otros) sería reintroducir a mano un valor que
    sabemos incorrecto. El estado anterior queda documentado arriba y en
    el issue #893, no en el downgrade.
    """
    pass
