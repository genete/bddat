"""780 seed permiso acceso conexion

Revision ID: 93b1032b3b08
Revises: b885d2353f33
Create Date: 2026-08-24 09:37:17.410624

Issue #780 — El permiso de acceso y conexión a la red es condición de
admisión a trámite de la AAP para instalaciones renovables sujetas al
RD-ley 23/2020 (art. 1) — NORMATIVA_MAPA_PROCEDIMENTAL.md §2.7. Hoy no se
comprueba en ningún punto: no está entre los requisitos documentales, no
existe el tipo de documento ni la norma en catálogo.

Esta migración cubre la vía (a) — requisito documental condicionado — y la
norma nueva que consumirá también la regla de motor de la vía (b)
(migración siguiente, 780_regla_motor_permiso_acceso):

  1. Norma RDL_23_2020 (Real Decreto-ley 23/2020, de 23 de junio).
  2. TipoDocumento PERMISO_ACCESO_CONEXION (origen EXTERNO — lo aporta el
     titular/promotor).
  3. RequisitoDocumental sobre ese tipo, norma_id -> RD_1183_2020 (regula
     el permiso en sí; la condición de ADMISIÓN la impone RD-ley 23/2020,
     citado en la regla de motor, no aquí). RD_1183_2020 ya existe en
     catálogo (id=9, sembrada previamente).
  4. CondicionRequisito: tipo_expediente EQ 'Renovable' — variable ya
     existente y activa (app/services/variables/calculado.py:386). Solo
     aparece en el checklist de expedientes renovables.

Decisión de alcance (ver docs_prueba/temp/issue-780-permiso-acceso-conexion/
ANALISIS_780.md §2.3): NO se condiciona por fecha de obtención del permiso
(>27/12/2013, ámbito literal del RD-ley 23/2020) porque implicaría añadir
fecha_permiso_acceso, dato sin captura hoy en BDDAT. Se acota solo por
tipo_expediente='Renovable'; el caso residual de permisos pre-2013 queda
cubierto por el bypass con justificación genérico del motor (ver migración
siguiente).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93b1032b3b08'
down_revision = 'b885d2353f33'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Norma
    conn.execute(sa.text("""
        INSERT INTO public.normas (codigo, titulo, url_eli) VALUES
        ('RDL_23_2020',
         'Real Decreto-ley 23/2020, de 23 de junio, por el que se aprueban '
         'medidas en materia de energía y en otros ámbitos para la '
         'reactivación económica',
         NULL)
        ON CONFLICT (codigo) DO NOTHING
    """))

    # 2. TipoDocumento
    conn.execute(sa.text("""
        INSERT INTO public.tipos_documentos (codigo, nombre, origen)
        VALUES ('PERMISO_ACCESO_CONEXION',
                'Permiso de acceso y conexión a la red',
                'EXTERNO')
        ON CONFLICT (codigo) DO NOTHING
    """))

    # 3. RequisitoDocumental (norma_id -> RD_1183_2020, ya sembrada, id=9)
    conn.execute(sa.text("""
        INSERT INTO public.requisitos_documentales
            (tipo_documento_id, descripcion_legal, norma_id, articulo, orden)
        SELECT td.id,
               'Permiso de acceso y conexión a la red otorgado por el gestor '
               'de la red (REE en transporte, distribuidora en distribución). '
               'Condición de admisión a trámite de la AAP para instalaciones '
               'de generación renovable (RD-ley 23/2020, art. 1).',
               n.id, '3', 9
        FROM public.tipos_documentos td
        JOIN public.normas n ON n.codigo = 'RD_1183_2020'
        WHERE td.codigo = 'PERMISO_ACCESO_CONEXION'
          AND NOT EXISTS (
              SELECT 1 FROM public.requisitos_documentales rd
              WHERE rd.tipo_documento_id = td.id
          )
    """))

    # 4. CondicionRequisito: tipo_expediente EQ 'Renovable'
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_requisito
            (requisito_id, variable_id, operador, valor, orden)
        SELECT rd.id, cv.id, 'EQ', '"Renovable"'::jsonb, 1
        FROM public.requisitos_documentales rd
        JOIN public.tipos_documentos td ON td.id = rd.tipo_documento_id
        JOIN public.catalogo_variables cv ON cv.nombre = 'tipo_expediente'
        WHERE td.codigo = 'PERMISO_ACCESO_CONEXION'
          AND NOT EXISTS (
              SELECT 1 FROM public.condiciones_requisito cr
              WHERE cr.requisito_id = rd.id
          )
    """))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_requisito
        WHERE requisito_id IN (
            SELECT rd.id
            FROM public.requisitos_documentales rd
            JOIN public.tipos_documentos td ON td.id = rd.tipo_documento_id
            WHERE td.codigo = 'PERMISO_ACCESO_CONEXION'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.requisitos_documentales
        WHERE tipo_documento_id = (
            SELECT id FROM public.tipos_documentos
            WHERE codigo = 'PERMISO_ACCESO_CONEXION'
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.tipos_documentos WHERE codigo = 'PERMISO_ACCESO_CONEXION'
    """))
    conn.execute(sa.text("""
        DELETE FROM public.normas WHERE codigo = 'RDL_23_2020'
    """))
