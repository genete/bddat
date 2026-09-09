"""887_reglas_ancla_principal

Revision ID: 887_reglas_ancla
Revises: 887_ancla_principal
Create Date: 2026-09-09

Las variables y las reglas que impiden seguir la solicitud mientras el proyecto no
tenga documento principal anclado (#887, ADR-044 §D).

**Dos reglas, y no por capricho de simetría:** el fundamento normativo depende de lo
que se pida, y `reglas_motor.articulo` se cita al bloquear.

  - RD 1955/2000 art. 123.1 (AAP): «A la solicitud se acompañará un anteproyecto de
    la instalación» — memoria, planos, presupuesto, separatas.
  - RD 1955/2000 art. 130.1 (AAC): la solicitud se presenta «junto con el proyecto de
    ejecución elaborado conforme a los Reglamentos técnicos en la materia».

**Y cuando se piden las dos juntas manda la del trámite más avanzado, la AAC.** Esto
no es un detalle de redacción: `evaluar_multi` evalúa el motor una vez por cada tipo
simple de `Solicitud.tipos_simples` y devuelve **el primer BLOQUEAR** que encuentra,
y ese orden es el de las siglas ('AAP' antes que 'AAC'). Una regla por sujeto sin más
haría que una AAP+AAC se bloqueara citando el anteproyecto del 123.1, cuando lo
exigible ahí es el proyecto de ejecución del 130.1.

De ahí el reparto:

  - Regla **simple**: sujeto `ANY/AAP/ANY` con la condición
    `solicitud_contiene_aac EQ false` — solo la AAP que se pide sola.
  - Regla **multi**: sujeto `ANY/AAC/ANY`, sin condición de tipo — cubre la AAC pura
    y **también** las combinadas, que es donde se pide la AAC junto a la AAP.

La condición se expresa con una variable («¿esta solicitud incluye la AAC?») y no
enumerando siglas del catálogo: hoy la única combinación de AAP sin AAC es 'AAP', pero
cualquier combinación nueva dejaría un hueco silencioso en la regla simple.

DUP no lleva regla propia: su documentación específica es la relación de bienes y
derechos (art. 143 y ss.), no el proyecto, y en el catálogo siempre acompaña a una AAP
o AAC que ya queda cubierta.

Condiciones comunes a las dos, en AND:

  1. tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD' — variable genérica (#388), mismo
     uso que #582 y #780: el análisis documental es donde la falta se detecta y se
     requiere, así que no se bloquea a sí mismo.
  2. proyecto_sin_principal EQ true — variable de dato.
  3. expediente_heredado EQ false — la excepción de los migrados del sistema anterior,
     como condición de la regla y no como bypass repetido fase tras fase.

Las tres variables nuevas se registran en `app/services/variables/` en el commit
anterior a esta migración, para que `activa=TRUE` solo se marque cuando la función ya
existe (orden de #780, no el de #582).

El escape no necesita diseño: `puede_escapar` es el comportamiento genérico de toda
regla BLOQUEAR, y cubre el expediente extraordinario que haya que sacar adelante sin
el proyecto identificado, con justificación en bitácora.
"""
from alembic import op
import sqlalchemy as sa

revision = '887_reglas_ancla'
down_revision = '887_ancla_principal'
branch_labels = None
depends_on = None


DESCRIPCION_AAP = (
    'No se puede tramitar ninguna fase posterior a ANÁLISIS_SOLICITUD de una AAP sin '
    'haber identificado cuál de los documentos del expediente es el proyecto '
    '(RD 1955/2000, art. 123.1: la solicitud se acompaña del anteproyecto)'
)
DESCRIPCION_AAC = (
    'No se puede tramitar ninguna fase posterior a ANÁLISIS_SOLICITUD de una AAC —sola '
    'o pedida junto a la AAP, donde manda la norma del trámite más avanzado— sin haber '
    'identificado cuál de los documentos del expediente es el proyecto '
    '(RD 1955/2000, art. 130.1: la solicitud se presenta junto con el proyecto de ejecución)'
)


def _condiciones_comunes(conn, regla_id):
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'NEQ', '"ANALISIS_SOLICITUD"'::json, 1
        FROM public.catalogo_variables cv WHERE cv.nombre = 'tipo_sujeto_solicitado'
    """), {'regla_id': regla_id})
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 2
        FROM public.catalogo_variables cv WHERE cv.nombre = 'proyecto_sin_principal'
    """), {'regla_id': regla_id})
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 3
        FROM public.catalogo_variables cv WHERE cv.nombre = 'expediente_heredado'
    """), {'regla_id': regla_id})


def upgrade():
    conn = op.get_bind()

    # 1. Las variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        SELECT 'proyecto_sin_principal',
               'El proyecto del expediente no tiene documento principal anclado',
               'boolean', n.id, TRUE
        FROM public.normas n WHERE n.codigo = 'RD1955_2000'
        ON CONFLICT (nombre) DO NOTHING
    """))
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, activa)
        VALUES ('expediente_heredado',
                'El expediente viene migrado del sistema anterior (datos incompletos posibles)',
                'boolean', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        SELECT 'solicitud_contiene_aac',
               'La solicitud pide la AAC, sola o combinada (determina la norma aplicable: '
               'la del trámite más avanzado)',
               'boolean', n.id, TRUE
        FROM public.normas n WHERE n.codigo = 'RD1955_2000'
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Regla simple — la AAP que se pide sola (art. 123.1)
    regla_aap = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
        SELECT 'CREAR', 'ANY/AAP/ANY', 'BLOQUEAR', n.id, '123', '1', 10, TRUE, :descripcion
        FROM public.normas n WHERE n.codigo = 'RD1955_2000'
        RETURNING id
    """), {'descripcion': DESCRIPCION_AAP}).scalar()
    _condiciones_comunes(conn, regla_aap)
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_regla (regla_id, variable_id, operador, valor, orden)
        SELECT :regla_id, cv.id, 'EQ', 'false'::json, 4
        FROM public.catalogo_variables cv WHERE cv.nombre = 'solicitud_contiene_aac'
    """), {'regla_id': regla_aap})

    # 3. Regla multi — la AAC, sola o junto a la AAP (art. 130.1)
    regla_aac = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
        SELECT 'CREAR', 'ANY/AAC/ANY', 'BLOQUEAR', n.id, '130', '1', 10, TRUE, :descripcion
        FROM public.normas n WHERE n.codigo = 'RD1955_2000'
        RETURNING id
    """), {'descripcion': DESCRIPCION_AAC}).scalar()
    _condiciones_comunes(conn, regla_aac)


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND sujeto IN ('ANY/AAP/ANY', 'ANY/AAC/ANY')
              AND articulo IN ('123', '130')
              AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RD1955_2000')
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE accion = 'CREAR' AND efecto = 'BLOQUEAR'
          AND sujeto IN ('ANY/AAP/ANY', 'ANY/AAC/ANY')
          AND articulo IN ('123', '130')
          AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'RD1955_2000')
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables
        WHERE nombre IN ('proyecto_sin_principal', 'expediente_heredado',
                         'solicitud_contiene_aac')
    """))
