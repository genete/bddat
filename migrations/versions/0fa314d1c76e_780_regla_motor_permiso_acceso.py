"""780 regla motor permiso acceso

Revision ID: 0fa314d1c76e
Revises: 93b1032b3b08
Create Date: 2026-08-24 09:39:10.985912

Issue #780 — vía (b): regla de motor que bloquea el avance de fase de una
AAP renovable mientras el permiso de acceso y conexión no esté cubierto en
el checklist documental (RequisitoDocumental sembrado en la migración
anterior, 93b1032b3b08_780_seed_permiso_acceso_conexion).

Requiere que app/services/variables/calculado.py ya tenga registrada la
función 'tiene_punto_acceso_conexion' (commit [SERVICIO] #780, ANTES de
esta migración) — así catalogo_variables.activa=TRUE se marca solo cuando
la función ya existe, a diferencia del orden real de #582 (ver
ANALISIS_780.md §4.3).

Diseño (ver ANALISIS_780.md §2.3 y §4.3):

  - Regla: BLOQUEAR CREAR sobre sujeto='Renovable/AAP/ANY' — el propio
    patrón de sujeto acota ya por tipo de expediente (Renovable) y tipo de
    solicitud (AAP, siglas); el comodín ANY en la 3a posición cubre
    cualquier fase. A diferencia de la regla de la tasa (#582, sujeto
    'ANY/ANY/ANY' con condición añadida), aquí no hace falta una condición
    de encuadre: el propio sujeto la codifica, sin necesitar la variable
    es_renovable_rdl23 (pendiente de implementar a propósito, ver
    ANALISIS_780.md §2.3).

  - Condiciones en AND:
      1. tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD' (variable
         genérica #388, mismo uso que #582 — no bloquea la propia fase de
         análisis documental, solo el avance posterior a ella).
      2. tiene_punto_acceso_conexion EQ false (variable nueva, calculado.py).

  - Escape: puede_escapar=True es ya el comportamiento genérico de TODA
    regla BLOQUEAR del motor (app/services/motor_reglas.py:215) — cubre el
    caso residual de permisos de acceso obtenidos antes del 27/12/2013
    (fuera del ámbito literal del RD-ley 23/2020) sin diseño adicional.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fa314d1c76e'
down_revision = '93b1032b3b08'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. catalogo_variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        SELECT 'tiene_punto_acceso_conexion',
               'El requisito documental del permiso de acceso y conexión está '
               'cubierto para la solicitud (instalaciones renovables)',
               'boolean', n.id, TRUE
        FROM public.normas n WHERE n.codigo = 'RDL_23_2020'
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Regla: BLOQUEAR CREAR cualquier fase posterior a ANALISIS_SOLICITUD
    #    de una AAP renovable sin permiso de acceso cubierto
    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
        SELECT 'CREAR', 'Renovable/AAP/ANY', 'BLOQUEAR', n.id, '1', '2', 10, TRUE,
               'No se puede admitir a trámite ni tramitar una AAP de instalación '
               'renovable sin haber acreditado el permiso de acceso y conexión a '
               'la red (RD-ley 23/2020, art. 1)'
        FROM public.normas n WHERE n.codigo = 'RDL_23_2020'
        RETURNING id
    """))
    regla_id = result.scalar()

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'NEQ', '"ANALISIS_SOLICITUD"'::json, 1
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tipo_sujeto_solicitado'
    """), {'regla_id': regla_id})

    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla
            (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 2
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tiene_punto_acceso_conexion'
    """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'Renovable/AAP/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RDL_23_2020')
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'Renovable/AAP/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
          AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RDL_23_2020')
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables WHERE nombre = 'tiene_punto_acceso_conexion'
    """))
