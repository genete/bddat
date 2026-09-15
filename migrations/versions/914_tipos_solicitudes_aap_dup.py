"""914_tipos_solicitudes_aap_dup — alta de AAP+DUP (ex-#911)

Revision ID: 914_tipos_solicitudes_aap_dup
Revises: 901_certificado_sol_reformado
Create Date: 2026-09-14

Issue #914 (absorbe #911) — ADR-046. AAP+DUP es la combinación con el acto
de DUP diferido: la AAP se resuelve con normalidad, la DUP queda a la
espera de que conste AAC otorgada en solicitud posterior (art. 143.2
RD 1955/2000; ADR-045 §C). Fila nueva, sin id reciclado (a diferencia de
18/19/20/21, que sí reciclaron ids de combos obsoletos — paso6_5,
e40ce8475305): no hay ningún tipo obsoleto libre que reutilizar aquí.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tipos_solicitudes_aap_dup'
down_revision = '901_certificado_sol_reformado'
branch_labels = None
depends_on = None

_SIGLAS = 'AAP+DUP'
_DESCRIPCION = ('Autorización Administrativa Previa + Declaración de Utilidad '
                 'Pública (acto de DUP diferido)')
_NOMBRE_EN_PLANTILLA = 'AAP+DUP'


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.tipos_solicitudes (siglas, descripcion, nombre_en_plantilla)
        VALUES (:siglas, :descripcion, :nombre_en_plantilla)
        ON CONFLICT DO NOTHING
    """), {'siglas': _SIGLAS, 'descripcion': _DESCRIPCION,
           'nombre_en_plantilla': _NOMBRE_EN_PLANTILLA})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM public.tipos_solicitudes WHERE siglas = :siglas"
    ), {'siglas': _SIGLAS})
