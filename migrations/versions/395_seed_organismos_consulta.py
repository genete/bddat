"""395_seed_organismos_consulta

Revision ID: 395_seed_organismos_consulta
Revises: 391_organismos_expediente
Create Date: 2026-05-15

Issue #395 — Seed de ConsultaNombrada 'organismos_consulta'.

Inserta la consulta nombrada que lista todos los organismos consultados
de un expediente con su estado y fechas del ciclo de consulta.
Disponible en plantillas como: {%tr for org in organismos_consulta %}
"""
import json
from alembic import op
import sqlalchemy as sa

revision = '395_seed_organismos_consulta'
down_revision = '391_organismos_expediente'
branch_labels = None
depends_on = None

_SQL_ORGANISMOS_CONSULTA = """\
SELECT
    e.nombre_completo                                        AS organismo_nombre,
    e.nif                                                    AS organismo_nif,
    oe.plazo_legal_dias                                      AS organismo_plazo_legal,
    oe.estado                                                AS organismo_resultado,
    TO_CHAR(d_notif.fecha_administrativa, 'DD/MM/YYYY')      AS organismo_fecha_envio,
    TO_CHAR(d_resp.fecha_administrativa,  'DD/MM/YYYY')      AS organismo_fecha_respuesta
FROM public.organismos_expediente oe
JOIN public.entidades e
    ON e.id = oe.organismo_id
LEFT JOIN public.tramites tr
    ON tr.id = oe.tramite_id
LEFT JOIN public.tareas t_n
    ON t_n.tramite_id = tr.id
    AND t_n.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'NOTIFICAR')
LEFT JOIN public.documentos d_notif
    ON d_notif.id = t_n.documento_producido_id
LEFT JOIN public.tareas t_a
    ON t_a.tramite_id = tr.id
    AND t_a.tipo_tarea_id = (SELECT id FROM public.tipos_tareas WHERE codigo = 'ANALIZAR')
LEFT JOIN public.documentos d_resp
    ON d_resp.id = t_a.documento_usado_id
WHERE oe.expediente_id = :expediente_id
ORDER BY e.nombre_completo"""

_COLUMNAS = [
    {"campo": "organismo_nombre",        "descripcion": "Nombre completo del organismo"},
    {"campo": "organismo_nif",           "descripcion": "NIF del organismo"},
    {"campo": "organismo_plazo_legal",   "descripcion": "Plazo legal en días"},
    {"campo": "organismo_resultado",     "descripcion": "Estado del organismo al cierre (ej. cerrado_favorable)"},
    {"campo": "organismo_fecha_envio",   "descripcion": "Fecha de envío de la separata (DD/MM/YYYY)"},
    {"campo": "organismo_fecha_respuesta", "descripcion": "Fecha de respuesta del organismo (DD/MM/YYYY)"},
]


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO public.consultas_nombradas
                (nombre, descripcion, sql, columnas, activo)
            VALUES
                (:nombre, :descripcion, :sql, CAST(:columnas AS jsonb), :activo)
            ON CONFLICT (nombre) DO NOTHING
        """),
        {
            "nombre": "organismos_consulta",
            "descripcion": (
                "Lista de organismos consultados del expediente "
                "con estado y fechas del ciclo de consulta"
            ),
            "sql": _SQL_ORGANISMOS_CONSULTA,
            "columnas": json.dumps(_COLUMNAS, ensure_ascii=False),
            "activo": True,
        },
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM public.consultas_nombradas WHERE nombre = 'organismos_consulta'")
    )
