"""849_seed_catalogo_pendiente — el catálogo que solo vivía en desarrollo

Revision ID: 849_seed_catalogo_pendiente
Revises: 849_seed_municipios
Create Date: 2026-09-05

Al construir la base de tests de #849 se comparó desarrollo con una instalación
limpia y apareció catálogo que ninguna migración crea: entró por la interfaz y
nunca se formalizó. Una instalación nueva de BDDAT no lo tendría.

Lo que se formaliza aquí, ya separado de los residuos de prueba (que se
borraron de desarrollo en el mismo issue):

- Nueve requerimientos reales del catálogo de la tarea ANALIZAR.
- El requisito documental DR_NO_DUP con su condición: la declaración
  responsable de no necesidad de DUP (DF 4ª del DL 26/2021).
- El texto del requisito del MODELO_909, corregido en desarrollo y no en la
  migración que lo creó.
- La fila de `tramites_tareas_documentos` que dice que REGISTRO_INTERESADOS
  produce un DIAGNOSTICO. La migración 488 sembró el trámite y su tarea, pero
  no el documento de salida.

Todo resuelve por CÓDIGO, nunca por id: los ids de catálogo no coinciden entre
instalaciones (MODELO_SOLICITUD es 146 en desarrollo y 56 en una base limpia).

Idempotente en las dos direcciones: en desarrollo estas filas ya existen.

Esto es un arreglo parcial, consciente. La reconstrucción limpia del historial
y el curado del catálogo con la dirección del servicio son #856.
"""
from alembic import op
import sqlalchemy as sa


revision = '849_seed_catalogo_pendiente'
down_revision = '849_seed_municipios'
branch_labels = None
depends_on = None


REQUERIMIENTOS = [
    ('Permiso de acceso y conexión a red de la instalación actual.', 'documental'),
    ('Carta de conformidad de la empresa distribuidora.', 'documental'),
    ('Convenio de cesión de las instalaciones a la compañía eléctrica.', 'documental'),
    ('Esquema Unifilar de la PSFV.', 'tecnica'),
    ('Relación de organismos afectados.', 'documental'),
    ('Deberá acreditar el número del registro de Puesta en Servicio de la '
     'instalación motivo de la reforma.', 'administrativa'),
    ('Un capítulo de planificación, definiendo las diferentes etapas, metas o '
     'hitos a alcanzar.', 'tecnica'),
    ('Plano en planta y alzado a escala del foso de recogida del líquido '
     'dieléctrico. Definirán los cortafuegos.', 'tecnica'),
    ('Deberá expresar en el proyecto el período de tiempo en el cual está '
     'prevista la ejecución de la instalación.', 'tecnica'),
]

TEXTO_DR_NO_DUP = (
    'Declaración responsable de no necesidad de solicitud de Declaración de '
    'Utilidad Pública, a los efectos de la DF4ª del DL 26/2021'
)

TEXTO_MODELO_909 = (
    'Modelo 909 carta de pago. Para ser realmente justificante de pago debe '
    'estar diligenciado'
)


def upgrade():
    conn = op.get_bind()

    # 1 — Requerimientos del catálogo de ANALIZAR
    for texto, categoria in REQUERIMIENTOS:
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_requerimientos (texto, categoria, activo)
            SELECT :texto, :categoria, TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM public.catalogo_requerimientos WHERE texto = :texto
            )
        """), {'texto': texto, 'categoria': categoria})

    # 2 — Requisito DR_NO_DUP. El tipo de documento y la norma existen ya:
    #     DR_NO_DUP lo crea el catálogo de tipos, DL_26_2021 la de normas.
    conn.execute(sa.text("""
        INSERT INTO public.requisitos_documentales
            (tipo_documento_id, descripcion_legal, norma_id, articulo, orden, activo)
        SELECT td.id, :texto, n.id, 'DF 4ª', 1, TRUE
        FROM public.tipos_documentos td, public.normas n
        WHERE td.codigo = 'DR_NO_DUP' AND n.codigo = 'DL_26_2021'
          AND NOT EXISTS (
              SELECT 1 FROM public.requisitos_documentales r
              WHERE r.tipo_documento_id = td.id
          )
    """), {'texto': TEXTO_DR_NO_DUP})

    # 3 — Su condición: solo se exige si la solicitud incluye DUP
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_requisito
            (requisito_id, variable_id, operador, valor, orden)
        SELECT r.id, v.id, 'EQ', 'true'::json, 1
        FROM public.requisitos_documentales r
        JOIN public.tipos_documentos td ON td.id = r.tipo_documento_id
        JOIN public.catalogo_variables v ON v.nombre = 'solicitud_incluye_dup'
        WHERE td.codigo = 'DR_NO_DUP'
          AND NOT EXISTS (
              SELECT 1 FROM public.condiciones_requisito c
              WHERE c.requisito_id = r.id AND c.variable_id = v.id
          )
    """))

    # 4 — El MODELO_909 es una carta de pago, y solo vale diligenciada.
    #     La migración que lo creó decía otra cosa; el texto bueno es el que se
    #     corrigió por la interfaz.
    conn.execute(sa.text("""
        UPDATE public.requisitos_documentales r
        SET descripcion_legal = :texto
        FROM public.tipos_documentos td
        WHERE td.id = r.tipo_documento_id AND td.codigo = 'MODELO_909'
    """), {'texto': TEXTO_MODELO_909})

    # 5 — REGISTRO_INTERESADOS produce un diagnóstico (la 488 dejó el trámite
    #     y su tarea ANALIZAR, pero no el documento de salida)
    conn.execute(sa.text("""
        INSERT INTO public.tramites_tareas_documentos
            (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
        SELECT tt.id, 1, 'SALIDA', td.id, TRUE
        FROM public.tipos_tramites tt, public.tipos_documentos td
        WHERE tt.codigo = 'REGISTRO_INTERESADOS' AND td.codigo = 'DIAGNOSTICO'
          AND NOT EXISTS (
              SELECT 1 FROM public.tramites_tareas_documentos x
              WHERE x.tipo_tramite_id = tt.id AND x.orden_tarea = 1
                AND x.rol = 'SALIDA' AND x.tipo_documento_id = td.id
          )
    """))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.tramites_tareas_documentos x
        USING public.tipos_tramites tt, public.tipos_documentos td
        WHERE x.tipo_tramite_id = tt.id AND x.tipo_documento_id = td.id
          AND tt.codigo = 'REGISTRO_INTERESADOS' AND td.codigo = 'DIAGNOSTICO'
          AND x.orden_tarea = 1 AND x.rol = 'SALIDA'
    """))

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_requisito c
        USING public.requisitos_documentales r, public.tipos_documentos td
        WHERE c.requisito_id = r.id AND r.tipo_documento_id = td.id
          AND td.codigo = 'DR_NO_DUP'
    """))

    conn.execute(sa.text("""
        DELETE FROM public.requisitos_documentales r
        USING public.tipos_documentos td
        WHERE r.tipo_documento_id = td.id AND td.codigo = 'DR_NO_DUP'
    """))

    for texto, _categoria in REQUERIMIENTOS:
        conn.execute(sa.text(
            'DELETE FROM public.catalogo_requerimientos WHERE texto = :texto'
        ), {'texto': texto})

    # El texto del MODELO_909 no se revierte: la migración que lo creó sigue
    # teniendo el suyo, y volver a escribirlo aquí duplicaría la fuente.
