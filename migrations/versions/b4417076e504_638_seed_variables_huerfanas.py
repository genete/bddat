"""638_seed_variables_huerfanas

Revision ID: b4417076e504
Revises: e5d05d4df0f2
Create Date: 2026-07-15 14:06:45.080102

Issue #638 — 4 variables con función ya implementada en el Variable Registry
pero nunca sembradas/activadas en catalogo_variables (huérfanas a medio ciclo
de vida, ver DISEÑO_CONTEXT_ASSEMBLER.md §"Ciclo de vida de una variable"):

  - sin_linea_aerea               (app/services/variables/dato.py)
  - max_tension_nominal_kv        (app/services/variables/dato.py)
  - solo_suelo_urbano_urbanizable (app/services/variables/dato.py)
  - tramite_publicar_existe       (app/services/variables/calculado.py)

El único intento previo de sembrarlas era scripts/seed_motor_variables.py,
un script suelto nunca convertido en migración — a diferencia del resto de
variables del sistema (ver 470_cert_fin_ip_consultas.py).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4417076e504'
down_revision = 'e5d05d4df0f2'
branch_labels = None
depends_on = None

_VARIABLES = [
    ('sin_linea_aerea',
     'Sin línea aérea (instalación íntegramente subterránea)', 'boolean'),
    ('max_tension_nominal_kv',
     'Tensión nominal máxima (kV)', 'numerico'),
    ('solo_suelo_urbano_urbanizable',
     'Recorrido íntegro en suelo urbano o urbanizable', 'boolean'),
    ('tramite_publicar_existe',
     'Trámite PUBLICAR existe en fase RESOLUCIÓN', 'boolean'),
]


def upgrade():
    conn = op.get_bind()
    for nombre, etiqueta, tipo_dato in _VARIABLES:
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
            VALUES (:nombre, :etiqueta, :tipo_dato, NULL, TRUE)
            ON CONFLICT (nombre) DO NOTHING
        """), {'nombre': nombre, 'etiqueta': etiqueta, 'tipo_dato': tipo_dato})


def downgrade():
    conn = op.get_bind()
    for nombre, _etiqueta, _tipo_dato in _VARIABLES:
        conn.execute(sa.text("""
            DELETE FROM public.catalogo_variables WHERE nombre = :nombre
        """), {'nombre': nombre})
