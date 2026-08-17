"""787_purga_residuo_smoke_catalogos

Revision ID: 787_purga_residuo_smoke
Revises: 785_catalogo_plazos_camino
Create Date: 2026-08-17

Issue #787 — purga del residuo que los smoke tests del CRUD dejaron en
`catalogo_plazos` y `reglas_motor` antes del arreglo de #672.

ORIGEN
======

14 filas en `catalogo_plazos` y otras 14 en `reglas_motor`, idénticas entre sí
dentro de cada tabla, sin ninguna correspondencia con el catálogo legal.

Las depositó, una por ejecución de la suite, el par de tests de "añadir
condición" de los smoke del CRUD:

    tests/smoke/test_smoke_catalogo_plazos.py::test_supervisor_puede_anadir_condicion_between
    tests/smoke/test_smoke_reglas_motor.py::test_supervisor_puede_anadir_condicion

Ambos crean la fila con `_crear_para_editar()` —que la marca en un campo de
texto (`norma_origen` / `descripcion`)— y luego la editan con un POST que NO
envía ese campo: el endpoint real lo deja a NULL y borra el marcador que la
fixture de limpieza necesitaba para encontrarla. La fila y su condición
quedaban huérfanas. `c49a9c8` (#672, 18-jul-2026) cerró la fuga capturando el
id en el momento de la creación; lo ya depositado entre `c41458a` (#632,
14-jul-2026) y ese arreglo es lo que esta migración retira.

HUELLA (por qué son residuo y no catálogo)
==========================================

catalogo_plazos — `_crear_para_editar()` compone la fila con los primeros
valores que encuentra en cada catálogo maestro, no con datos normativos:

    tipo_elemento='SOLICITUD', camino='ANY/AAP'  (TipoSolicitud.query.first())
    plazo 3 MESES, campo_fecha={'fk': 'documento_solicitud_id'}
    efecto_vencimiento_id → 'NINGUNO'            (EfectoPlazo.query.first())
    norma_origen NULL, orden=100                 (el POST de edición no los envía)
    condición max_tension_nominal_kv BETWEEN [10, 20]   (el 'cond_valor': '10, 20' del test)

reglas_motor — mismo mecanismo:

    accion='CREAR', sujeto='ANY/AAP', efecto='BLOQUEAR'
    descripcion NULL, norma_id NULL, prioridad=0
    condición max_tension_nominal_kv GTE 10

`norma_origen` / `descripcion` a NULL es el discriminante fuerte: toda fila real
de estos dos catálogos cita su norma. Las 14 de `catalogo_plazos` eran además
las únicas de nivel SOLICITUD de la tabla — el nivel queda a cero filas tras la
purga, que es lo correcto: el plazo de resolución vive a nivel FASE.

Las 14 reglas estaban `activa=TRUE` y habrían bloqueado `CREAR` sobre cualquier
solicitud AAP en cuanto la condición disparase, con mensaje vacío (`norma_id`
NULL). No llegó a ocurrir porque `max_tension_nominal_kv` es NULL en los 10
proyectos de la BD de desarrollo y una variable ausente no dispara la condición
(`motor_reglas._evaluar_condiciones`).

NOTA SOBRE #785
===============

El criterio de migración de `785_catalogo_plazos_camino_sftt` conservó estas 14
filas describiéndolas como "condiciones que expresan supuesto legal real
(`max_tension_nominal_kv` en SOLICITUD/AAP)". Era una lectura equivocada de la
misma basura: el BETWEEN [10, 20] sale del literal del test, no del RD 1955/2000.
Las filas se migraron al camino nuevo sin más daño que arrastrarlas.

CRITERIO DE BORRADO
===================

Por patrón, no por id: los ids concretos de esta BD (479, 494, 509, 524, 539,
554, 569, 584, 599, 614, 629, 644, 659, 674 en `catalogo_plazos`; 200, 211, 222,
233, 244, 255, 266, 277, 288, 299, 310, 321, 332, 343 en `reglas_motor`) valen
solo aquí, y cualquier clon habrá acumulado un número distinto de ejecuciones.

`condiciones_plazo`, `condiciones_regla` y `excepciones_motor` cuelgan de sus
padres con ON DELETE CASCADE — no hace falta borrarlas por separado.
"""
from alembic import op
import sqlalchemy as sa


revision = '787_purga_residuo_smoke'
down_revision = '785_catalogo_plazos_camino'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # --- catalogo_plazos ------------------------------------------------------
    # El efecto se resuelve por código, no por id, para no depender del orden
    # del seed en otra BD.
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'SOLICITUD'
          AND camino = 'ANY/AAP'
          AND norma_origen IS NULL
          AND plazo_valor = 3
          AND plazo_unidad = 'MESES'
          AND efecto_vencimiento_id = (
              SELECT id FROM public.efectos_plazo WHERE codigo = 'NINGUNO'
          )
    """))

    # --- reglas_motor ---------------------------------------------------------
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE accion = 'CREAR'
          AND sujeto = 'ANY/AAP'
          AND efecto = 'BLOQUEAR'
          AND descripcion IS NULL
          AND norma_id IS NULL
    """))


def downgrade():
    """No-op deliberado.

    El upgrade retira basura de test, no configuración: no hay nada que
    restaurar y recrearla sería reintroducir el defecto. La migración es
    idempotente en ambos sentidos.
    """
    pass
