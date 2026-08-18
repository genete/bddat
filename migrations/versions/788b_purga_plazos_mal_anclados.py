"""788b_purga_plazos_mal_anclados

Revision ID: 788b_purga_plazos
Revises: 788a_niveles_plazos
Create Date: 2026-08-18

Issue #788 (migración B) — retira las tres filas que no sobreviven al rediseño
de niveles y cierra la puerta con un CheckConstraint.

QUÉ SE BORRA
============

1. Duplicado mal anclado del art. 131 (2 filas, nivel FASE, camino
   `ANY/ANY/CONSULTAS`). Las puso el seed de #341 el 30-abr-2026, antes de que
   #463 (25-may-2026) declarase el MISMO plazo en el nivel del acto. Contaban los
   30/15 días desde la fecha de solicitud, cuando la norma los cuenta desde la
   notificación a cada organismo. No se pierde nada: la fila superviviente
   —`CONSULTA_SEPARATA`, ahora en su tarea `ESPERAR_PLAZO`— conserva las mismas
   dos condiciones (`es_solicitud_aac_pura` + `tiene_solicitud_aap_favorable`).

   La validación de colisión de #786 no podía detectarlo: compara filas dentro
   del mismo nivel, y estas estaban en un nivel distinto de sus gemelas.

2. Residuo de smoke test (1 fila, nivel TRAMITE, `CONSULTA_SEPARATA`, 3 MESES,
   `SILENCIO_DESESTIMATORIO`, `norma_origen` NULL, `orden` 100, condición
   `max_tension_nominal_kv GT 36`). Misma huella que lo purgado por #787 —
   `norma_origen` NULL es el discriminante fuerte: toda fila real de este catálogo
   cita su norma. Es además la única fila de nivel TRAMITE que la migración A dejó
   en pie a propósito, por no ser configuración.

`condiciones_plazo` cuelga con ON DELETE CASCADE — no hace falta borrarla aparte.

EL CONSTRAINT
=============

`ck_catalogo_plazos_tipo_elemento` se instala aquí y no en la migración A porque
hasta este punto la tabla aún tenía filas de FASE y de TRAMITE. No sustituye a la
validación del CRUD: son capas distintas. El CRUD valida para dar un error
legible al Supervisor; el constraint cubre lo que escribe SIN pasar por él, que
es justo por donde entraron los dos incidentes reales de esta tabla — el
duplicado de arriba lo puso una migración de seed, y las 14 filas basura de #787
un test con la limpieza rota.
"""
from alembic import op
import sqlalchemy as sa


revision = '788b_purga_plazos'
down_revision = '788a_niveles_plazos'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # --- 1. Duplicado del art. 131 anclado a la fase CONSULTAS ---------------
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'FASE'
          AND camino = 'ANY/ANY/CONSULTAS'
          AND campo_fecha ->> 'fk' = 'documento_solicitud_id'
    """))

    # --- 2. Residuo de smoke test en CONSULTA_SEPARATA -----------------------
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'TRAMITE'
          AND camino = 'ANY/ANY/ANY/CONSULTA_SEPARATA'
          AND norma_origen IS NULL
    """))

    # --- 3. Cierre: la tabla solo admite ya los dos niveles que portan fecha --
    op.create_check_constraint(
        'ck_catalogo_plazos_tipo_elemento',
        'catalogo_plazos',
        "tipo_elemento IN ('SOLICITUD', 'TAREA')",
        schema='public',
    )


def downgrade():
    """Suelta el constraint; no restaura las filas.

    El constraint sí tiene que caer: si no, el downgrade de la migración A —que
    devuelve filas a FASE y TRAMITE— chocaría contra él.

    Las tres filas no se restauran a propósito. Dos eran un duplicado que la
    propia norma desmiente y la tercera basura de test: recrearlas sería
    reintroducir el defecto, no revertir un cambio de configuración.
    """
    op.drop_constraint(
        'ck_catalogo_plazos_tipo_elemento',
        'catalogo_plazos',
        type_='check',
        schema='public',
    )
