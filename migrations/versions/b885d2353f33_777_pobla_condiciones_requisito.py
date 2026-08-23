"""777_pobla_condiciones_requisito

Revision ID: b885d2353f33
Revises: 5eb35f788ab2
Create Date: 2026-08-23 10:15:00.000000

Issue #777 — puebla condiciones_requisito para los 3 requisitos cuya
descripcion_legal ya llevaba la condición escrita en prosa:

  ESCRITURAS_SOCIEDAD   <- solicitante_es_persona_juridica = true
  PODER_REPRESENTACION  <- solicitud_por_representante     = true
  DR_NO_DUP             <- solicitud_incluye_dup            = true

Corrige de paso requisitos_documentales.descripcion_legal de NIF_TITULAR y
ESCRITURAS_SOCIEDAD, que seguían hablando de "el solicitante" — arrastre del
seed original de #408, inconsistente con el rename CIF_NIF->NIF_TITULAR y la
corrección de que ambos documentos son del TITULAR, no de quien tramita
(migración 5eb35f788ab2).

Revisados los 8 requisitos del catálogo actual (#408): MODELO_SOLICITUD,
NIF_TITULAR, MODELO_046, MODELO_909 y JUSTIFICANTE_PAGO_TASA quedan
universales A PROPÓSITO, no por olvido. El catálogo de #408 es parcial —
cubre solo el caso base de solicitud de autorización (AAP/AAC/DUP), no los
21 tipos_solicitudes del sistema (AAT, AE_PROVISIONAL, RAIPEE, RADNE,
DESISTIMIENTO, RENUNCIA, RECURSO, CORRECCION_ERRORES...). Condicionar estos
5 requisitos por tipo de solicitud (p.ej. DOC_PROYECTO no debería exigirse
en un DESISTIMIENTO) es contenido normativo nuevo: línea de #408 ("estudio
andaluz completo de documentación requerida"), no de #777.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b885d2353f33'
down_revision = '5eb35f788ab2'
branch_labels = None
depends_on = None

# (codigo_tipo_documento, nombre_variable)
_CONDICIONES = [
    ('ESCRITURAS_SOCIEDAD', 'solicitante_es_persona_juridica'),
    ('PODER_REPRESENTACION', 'solicitud_por_representante'),
    ('DR_NO_DUP', 'solicitud_incluye_dup'),
]

_DESCRIPCIONES_LEGALES = [
    ('NIF_TITULAR', 'NIF del titular.'),
    ('ESCRITURAS_SOCIEDAD',
     'Escritura de constitución de la sociedad, cuando el titular sea persona '
     'jurídica.'),
]


def upgrade():
    conn = op.get_bind()

    for codigo_tipo, nombre_var in _CONDICIONES:
        conn.execute(sa.text("""
            INSERT INTO public.condiciones_requisito
                (requisito_id, variable_id, operador, valor, orden)
            SELECT rd.id, cv.id, 'EQ', 'true'::jsonb, 1
            FROM public.requisitos_documentales rd
            JOIN public.tipos_documentos td ON td.id = rd.tipo_documento_id
            JOIN public.catalogo_variables cv ON cv.nombre = :nombre_var
            WHERE td.codigo = :codigo_tipo
              AND NOT EXISTS (
                  SELECT 1 FROM public.condiciones_requisito cr
                  WHERE cr.requisito_id = rd.id
              )
        """), {'codigo_tipo': codigo_tipo, 'nombre_var': nombre_var})

    for codigo_tipo, descripcion_legal in _DESCRIPCIONES_LEGALES:
        conn.execute(sa.text("""
            UPDATE public.requisitos_documentales
            SET descripcion_legal = :descripcion_legal
            WHERE tipo_documento_id = (
                SELECT id FROM public.tipos_documentos WHERE codigo = :codigo_tipo
            )
        """), {'codigo_tipo': codigo_tipo, 'descripcion_legal': descripcion_legal})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE public.requisitos_documentales
        SET descripcion_legal = 'CIF/NIF del solicitante.'
        WHERE tipo_documento_id = (
            SELECT id FROM public.tipos_documentos WHERE codigo = 'NIF_TITULAR'
        )
    """))
    conn.execute(sa.text("""
        UPDATE public.requisitos_documentales
        SET descripcion_legal = 'Escritura de constitución de la sociedad, cuando el solicitante sea persona jurídica.'
        WHERE tipo_documento_id = (
            SELECT id FROM public.tipos_documentos WHERE codigo = 'ESCRITURAS_SOCIEDAD'
        )
    """))

    codigos_tipo = [c[0] for c in _CONDICIONES]
    conn.execute(sa.text("""
        DELETE FROM public.condiciones_requisito
        WHERE requisito_id IN (
            SELECT rd.id
            FROM public.requisitos_documentales rd
            JOIN public.tipos_documentos td ON td.id = rd.tipo_documento_id
            WHERE td.codigo = ANY(:codigos_tipo)
        )
    """), {'codigos_tipo': codigos_tipo})
