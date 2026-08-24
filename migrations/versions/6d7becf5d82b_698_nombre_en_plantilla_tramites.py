"""698 nombre en plantilla tramites

Revision ID: 6d7becf5d82b
Revises: 0fa314d1c76e
Create Date: 2026-08-24 09:48:45.291364

Issue #698. `tipos_tramites.nombre_en_plantilla` se RECUPERA como fuente
principal del nombre del documento generado — dato de catálogo, editable
por el supervisor en tablas_maestras (#171). El servicio
`app/services/nombres_documentos.py` lo combina con ajustes/sustituciones de
código solo donde el dato no basta (ver docstring del servicio).

Se puebla aquí SOLO lo que #698 implementa (el resto queda en 0/30, cae al
fallback de código crudo — issue de seguimiento #809 para ir completando):

- REQUERIMIENTO_SUBSANACION → 'Requerimiento' (el servicio añade el
  sufijo de vuelta " 2", " 3"... cuando aplica)
- ELABORACION → 'Resolución' — OJO: este código es compartido por
  RESOLUCION y RECONOCIMIENTO_INTERESADO (fases_tramites, ADR-037/#725);
  hoy solo RESOLUCION.ELABORACION está implementado, así que no hay
  colisión real todavía. Cuando #809 aborde RECONOCIMIENTO_INTERESADO.ELABORACION
  hay que resolver esa ambigüedad ahí (no aquí).

NO SE TOCA NINGUNA COLUMNA (decisión de Carlos, 2026-08-24): ni
`tipos_fases.nombre_en_plantilla` ni `tipos_expedientes.nombre_en_plantilla`
se eliminan, aunque en el diseño de #698 ni la fase ni el tipo de expediente
aparecen como token en el nombre del documento generado — quedan sin
consumidor de código, pero se dejan intactas por si en el futuro hacen
falta (p.ej. desambiguar por fase un trámite compartido, o algún otro uso
no previsto todavía). Tampoco se toca `tipos_solicitudes.nombre_en_plantilla`
(en uso activo) ni `tipos_tareas.nombre_en_plantilla` (sin consumidor,
tampoco se toca).

Esta migración es solo el UPDATE de datos de arriba — no hay ningún
`add_column`/`drop_column`.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d7becf5d82b'
down_revision = '0fa314d1c76e'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    conn.execute(sa.text(
        "UPDATE public.tipos_tramites SET nombre_en_plantilla = 'Requerimiento' "
        "WHERE codigo = 'REQUERIMIENTO_SUBSANACION'"
    ))
    conn.execute(sa.text(
        "UPDATE public.tipos_tramites SET nombre_en_plantilla = 'Resolución' "
        "WHERE codigo = 'ELABORACION'"
    ))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE public.tipos_tramites SET nombre_en_plantilla = NULL "
        "WHERE codigo IN ('REQUERIMIENTO_SUBSANACION', 'ELABORACION')"
    ))
