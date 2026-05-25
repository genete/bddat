"""416_seed_plazos_tablon

Revision ID: 416_seed_plazos_tablon
Revises: 001_bitacora
Create Date: 2026-05-25

Issue #416 — Seed `catalogo_plazos` para TABLON_AYUNTAMIENTOS.

DISEÑO
======

El trámite TABLON_AYUNTAMIENTOS tiene un único ESPERAR_PLAZO. El ayuntamiento
certifica que el anuncio estuvo expuesto, pero lo comunica cuando el período
ya ha concluido. El certificado (CERT_PLAZO_TABLON) porta como fecha_administrativa
la fecha de **inicio** de la exposición.

A diferencia del patrón habitual (rol CONSUMIDO — el documento de inicio llega
antes de que el plazo empiece), aquí el documento de referencia es el PRODUCIDO
por ESPERAR_PLAZO. El resolver de _resolver_campo_fecha en plazos.py ya soporta
rol PRODUCIDO; este seed es el único cambio necesario.

  campo_fecha = {"via_tarea_tipo": "ESPERAR_PLAZO", "rol": "PRODUCIDO"}
  plazo = 30 días naturales (art. 125 RD 1955/2000)
  efecto = SIN_EFECTO_AUTOMATICO

El ESPERAR_PLAZO queda COMPLETADO retroactivamente: en cuanto el tramitador
incorpora CERT_PLAZO_TABLON con fecha_administrativa = inicio de la exposición,
hoy() > (inicio + 30 días) ya es cierto.

Norma: NORMATIVA_PLAZOS.md §2.2; DISEÑO_FECHAS_PLAZOS.md §4.1 (rev. #416).
"""
import json

from alembic import op
import sqlalchemy as sa


revision = '416_seed_plazos_tablon'
down_revision = '001_bitacora'
branch_labels = None
depends_on = None


_CAMPO_FECHA = json.dumps({"via_tarea_tipo": "ESPERAR_PLAZO", "rol": "PRODUCIDO"})


def upgrade():
    conn = op.get_bind()

    plazo_id = conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, tipo_elemento_codigo, campo_fecha,
             plazo_valor, plazo_unidad,
             efecto_vencimiento_id, norma_origen, orden, activo)
        SELECT
            'TRAMITE',
            tt.id,
            'TABLON_AYUNTAMIENTOS',
            CAST(:campo_fecha AS jsonb),
            30,
            'DIAS_NATURALES',
            ep.id,
            'Art. 125 RD 1955/2000',
            10,
            TRUE
        FROM public.tipos_tramites tt
        CROSS JOIN public.efectos_plazo ep
        WHERE tt.codigo = 'TABLON_AYUNTAMIENTOS'
          AND ep.codigo = 'SIN_EFECTO_AUTOMATICO'
        RETURNING id
    """), {'campo_fecha': _CAMPO_FECHA}).scalar()

    if plazo_id is None:
        raise RuntimeError(
            "No se pudo insertar plazo TABLON_AYUNTAMIENTOS; "
            "verificar existencia de tipos_tramites.TABLON_AYUNTAMIENTOS "
            "y efectos_plazo.SIN_EFECTO_AUTOMATICO"
        )


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'TRAMITE'
          AND tipo_elemento_codigo = 'TABLON_AYUNTAMIENTOS'
    """))
