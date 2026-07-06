"""582 regla tasa impagada

Revision ID: 07948f0f5f2c
Revises: b88f9bb4755b
Create Date: 2026-07-06 08:55:02.054181

Issue #582 — Regla de motor: tasa impagada bloquea toda fase posterior a
ANÁLISIS_SOLICITUD (art. 45.1 Ley 10/2021, de 28 de diciembre, de tasas y
precios públicos de la Comunidad Autónoma de Andalucía).

Diseño (ver docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md §7):

  - Variable 'tasa_impagada': True si el requisito documental de la tasa
    (RequisitoDocumental cuyo TipoDocumento tiene codigo='JUSTIFICANTE_PAGO_TASA')
    no está cubierto en documentos_requisito para la solicitud en contexto.
    Ese TipoDocumento/RequisitoDocumental lo puebla #408 — mientras no exista,
    la variable degrada a False (no bloquea) y loguea warning, mismo patrón
    que app/services/requisitos.py::evaluar_requisitos (#347).

  - Regla: BLOQUEAR CREAR sobre cualquier fase (sujeto='ANY/ANY/ANY', 3
    segmentos = TipoExpediente/Siglas/CodigoTipoFase → solo casa con creación
    de fase, no de trámite) EXCEPTO ANALISIS_SOLICITUD, combinando dos
    condiciones en AND:
      1. tipo_sujeto_solicitado NEQ 'ANALISIS_SOLICITUD'
         (variable genérica ya existente, #388 — evita enumerar las 7 fases
         posteriores una a una: cualquier fase nueva que se añada al catálogo
         queda cubierta automáticamente, sin tocar esta regla)
      2. tasa_impagada EQ true
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07948f0f5f2c'
down_revision = 'b88f9bb4755b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Norma
    conn.execute(sa.text("""
        INSERT INTO public.normas (id, codigo, titulo, url_eli) VALUES
        (12, 'LEY_10_2021_TASAS',
         'Ley 10/2021, de 28 de diciembre, de tasas y precios públicos de la Comunidad Autónoma de Andalucía',
         NULL)
        ON CONFLICT (codigo) DO NOTHING
    """))

    # 2. catalogo_variables
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        SELECT 'tasa_impagada',
               'El requisito documental de justificante de pago de tasa no está cubierto para la solicitud',
               'boolean', n.id, TRUE
        FROM public.normas n WHERE n.codigo = 'LEY_10_2021_TASAS'
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 3. Regla: BLOQUEAR CREAR cualquier fase con tasa impagada
    result = conn.execute(sa.text("""
        INSERT INTO public.reglas_motor
            (accion, sujeto, efecto, norma_id, articulo, apartado, prioridad, activa, descripcion)
        SELECT 'CREAR', 'ANY/ANY/ANY', 'BLOQUEAR', n.id, '45', '1', 10, TRUE,
               'No se puede tramitar ninguna fase posterior a ANÁLISIS_SOLICITUD sin haber efectuado el pago de la tasa correspondiente'
        FROM public.normas n WHERE n.codigo = 'LEY_10_2021_TASAS'
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
        SELECT :regla_id, cv.id, 'EQ', 'true'::json, 2
        FROM public.catalogo_variables cv
        WHERE cv.nombre = 'tasa_impagada'
    """), {'regla_id': regla_id})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_regla
        WHERE regla_id IN (
            SELECT id FROM public.reglas_motor
            WHERE sujeto = 'ANY/ANY/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
              AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'LEY_10_2021_TASAS')
        )
    """))
    conn.execute(sa.text("""
        DELETE FROM public.reglas_motor
        WHERE sujeto = 'ANY/ANY/ANY' AND accion = 'CREAR' AND efecto = 'BLOQUEAR'
          AND norma_id = (SELECT id FROM public.normas WHERE codigo = 'LEY_10_2021_TASAS')
    """))
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables WHERE nombre = 'tasa_impagada'
    """))
    conn.execute(sa.text("""
        DELETE FROM public.normas WHERE codigo = 'LEY_10_2021_TASAS'
    """))
