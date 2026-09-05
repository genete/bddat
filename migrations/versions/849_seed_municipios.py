"""849_seed_municipios — los municipios entran por migración

Revision ID: 849_seed_municipios
Revises: 827b_cert_documento
Create Date: 2026-09-05

`scripts/data/municipios.sql` era el último canal de datos fuera de las
migraciones: una instalación limpia se quedaba con la tabla vacía salvo que
alguien se acordara de cargarlo a mano. #348 lo dejó fuera a propósito
—"no son catálogo de sistema"—, pero el precio es que `flask db upgrade` no
basta para tener un sistema utilizable: sin municipios no se puede dar de alta
un proyecto.

Se lee el fichero en vez de copiar 8132 INSERT aquí: el dump sigue siendo la
fuente legible y diffeable, y esta migración solo lo aplica. Se filtran sus
metacomandos de psql (`\\restrict`, `SET`, `SELECT pg_catalog...`), que
SQLAlchemy no entiende.
"""
import os
import re

from alembic import op
import sqlalchemy as sa


revision = '849_seed_municipios'
down_revision = '827b_cert_documento'
branch_labels = None
depends_on = None

RUTA_SQL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'scripts', 'data', 'municipios.sql',
)

# Solo las sentencias de inserción; el resto del dump es ruido de pg_dump.
_INSERT = re.compile(r'^INSERT INTO public\.municipios VALUES .*;$')


def upgrade():
    if not os.path.isfile(RUTA_SQL):
        raise RuntimeError(f'No se encuentra {RUTA_SQL} — sin él no hay municipios')

    conn = op.get_bind()
    lote, insertados = [], 0
    with open(RUTA_SQL, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if not _INSERT.match(linea):
                continue
            # Idempotente: en la BD de desarrollo la tabla ya está poblada por
            # el canal antiguo y esta migración no debe reventar allí.
            lote.append(linea[:-1] + ' ON CONFLICT (id) DO NOTHING')
            if len(lote) >= 500:
                conn.execute(sa.text('; '.join(lote)))
                insertados += len(lote)
                lote = []
    if lote:
        conn.execute(sa.text('; '.join(lote)))
        insertados += len(lote)

    if insertados == 0:
        raise RuntimeError(f'{RUTA_SQL} no contenía ningún INSERT de municipios')

    # Los INSERT llevan id explícito y eso no mueve la secuencia (#849).
    conn.execute(sa.text(
        "SELECT setval(pg_get_serial_sequence('public.municipios', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM public.municipios))"
    ))


def downgrade():
    # Falla ruidosamente si algún proyecto tiene municipios asociados, que es lo
    # correcto: son datos de referencia, no se retiran con un expediente vivo.
    op.execute('DELETE FROM public.municipios')
