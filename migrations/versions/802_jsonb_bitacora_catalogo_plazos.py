"""802_jsonb_bitacora_catalogo_plazos

Revision ID: 802_jsonb_bitacora
Revises: 863_condicion_dr_no_dup
Create Date: 2026-09-07

Issue #802 — unificar a jsonb dos columnas `json`: `bitacora.detalle` y
`catalogo_plazos.campo_fecha_cumplimiento`.

El reparto de las 15 columnas JSON del esquema (9 `json`, 6 `jsonb`) no
respondía a ningún criterio, sino a qué import tenía a mano quien escribió
cada modelo. Quitada de la ecuación la portabilidad a otro motor —ni `json`
ni `jsonb` existen en Oracle ni SQL Server; lo que daría portabilidad es el
tipo genérico `sqlalchemy.JSON`, ortogonal al tipo físico—, el criterio que
queda es: ¿se consultará alguna vez por dentro? → `jsonb`; ¿es un acta
inmutable cuyo texto exacto importa? → `json`.

`bitacora.detalle` es la tabla que más crece de todo el sistema (append-only,
451 filas ya en desarrollo) y la candidata número uno a índice GIN el día que
se necesite «¿quién tocó el campo X?» — nunca se filtró por su contenido
hasta ahora (solo por `usuario_id` y fecha), pero el argumento de fidelidad
textual no aplica: es un dict generado por código, no un documento externo.

`catalogo_plazos.campo_fecha_cumplimiento` es gemela de `campo_fecha` (mismo
vocabulario cerrado, mismo algoritmo, ADR-041 §D) y quedó en `json` por error
al implementar #778 (`778a_plazos_medida_unica.py`), justificado por la misma
portabilidad que no sostiene la decisión. La asimetría tenía consecuencia
práctica: `json` no soporta el operador `=` en PostgreSQL, y `campo_fecha` ya
se filtra así en `788a`.

451 y 21 filas: el `ALTER TABLE ... USING` es cuestión de segundos, sin
necesidad de por lotes.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '802_jsonb_bitacora'
down_revision = '863_condicion_dr_no_dup'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE public.bitacora ALTER COLUMN detalle '
               'TYPE jsonb USING detalle::jsonb')
    op.execute('ALTER TABLE public.catalogo_plazos ALTER COLUMN campo_fecha_cumplimiento '
               'TYPE jsonb USING campo_fecha_cumplimiento::jsonb')


def downgrade():
    op.execute('ALTER TABLE public.catalogo_plazos ALTER COLUMN campo_fecha_cumplimiento '
               'TYPE json USING campo_fecha_cumplimiento::json')
    op.execute('ALTER TABLE public.bitacora ALTER COLUMN detalle '
               'TYPE json USING detalle::json')
