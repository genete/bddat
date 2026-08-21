"""778b_plazos_dato_del_catalogo

Revision ID: 778b_dato_catalogo
Revises: 778a_medida_unica
Create Date: 2026-08-21

Issue #778 (migración B) — el dato baja del código a la tabla.

La migración A abrió las columnas; esta las puebla con lo que hasta ahora vivía
escrito en `plazos.py`, para que el cambio de mecanismo no sea también un cambio
de configuración. No es poblado de catálogo (qué entradas faltan y con qué
valores queda fuera de #778): es traslado del mismo hecho a su sitio.

1. LA MARCA SUSPENSORA
======================

`_TRAMITES_SUSPENSION` listaba cuatro trámites como causa del art. 22.1. Tres
tienen fila en el catálogo y la reciben:

    REQUERIMIENTO_SUBSANACION   art. 22.1.a — subsanación al interesado
    SOLICITUD_INFORME           art. 22.1.d — informe preceptivo a organismo
    CONSULTA_SEPARATA           art. 22.1.d — separata a organismo (dos filas:
                                la condicionada del art. 131.1 párr. 2 y su
                                reserva; ambas describen el mismo plazo)

El cuarto, `SOLICITUD_COMPATIBILIDAD`, **no tiene fila** y por tanto deja de
suspender. No es un olvido de esta migración: es el corolario buscado en ADR-041
§E — un plazo sin entrada en el catálogo no suspende nada. Hasta hoy convivían
un trámite marcado como suspensor en el código y sin fila en la tabla, de modo
que el sistema lo pintaba como «plazo no configurado» a la vez que lo usaba para
mover la fecha límite de la solicitud. Esa contradicción ya no puede existir.

No se marca ningún `ANUNCIO_*` ni `CONSULTA_TRASLADO_*`: la información pública y
los traslados al peticionario (arts. 126 / 127.3 RD 1955/2000) son instrucción
ordinaria, corren DENTRO del plazo y lo consumen. Son justo los que lo aprietan.

2. EL SEÑALADOR DE CUMPLIMIENTO
===============================

Cada plazo se abre y se cierra en el mismo sitio (ADR-041 §D), verificado trámite
a trámite contra `tramites_tareas_documentos`: el documento PRODUCIDO de cada
`ESPERAR_PLAZO` es exactamente el que cierra esa espera — SUBSANACION,
INFORME_114_RD1955, RESPUESTA_ORGANISMO, RESPUESTA_TITULAR,
INFORME_COMPATIBILIDAD_AMBIENTAL, CERT_PLAZO_CUMPLIDO. No hace falta declarar
`tipo_documento`: el vínculo PRODUCIDO es único por tarea (Tarea.documento_producido).

La excepción es `TABLON_AYUNTAMIENTOS`, y se expresa por ausencia: allí el disparo
y el único candidato a cierre son el mismo documento —el certificado del
ayuntamiento llega tarde y trae consigo la fecha de exposición, con efecto
retroactivo (#416)—, así que la entrada se queda sin señalador y `VENCIDO` se lee
como «la exposición se completó», que es lo que el tramitador necesita ver.

Criterio general en vez de lista de caminos: toda fila de nivel TAREA que no sea
la del tablón cierra con su PRODUCIDO. Una fila de otra BD (p. ej. un ANUNCIO_BOJA
poblado allí y aquí no) queda igual de bien servida.

Las filas de nivel SOLICITUD reciben `{"fk": "documento_cierre_id"}`, la columna
que abrió la migración A.

3. PURGA DEL RESIDUO DE VERIFICACIÓN
====================================

Una fila de `ANY/AAP/ANY/ANUNCIO_BOE/ESPERAR_PLAZO` con `norma_origen` =
«Verificación navegador #788 (borrar tras revisar)» quedó activa tras la
verificación en navegador de #788. Se retira por contenido, mismo criterio que
#787 y #788: toda fila real de este catálogo cita su norma.
"""
from alembic import op
import sqlalchemy as sa


revision = '778b_dato_catalogo'
down_revision = '778a_medida_unica'
branch_labels = None
depends_on = None


# Trámites que el código listaba como causa de suspensión y tienen fila.
_CAMINOS_SUSPENSORES = (
    'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO',
    'ANY/ANY/ANY/SOLICITUD_INFORME/ESPERAR_PLAZO',
    'ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO',
)

_CUMPLIMIENTO_TAREA = '{"rol": "PRODUCIDO"}'
_CUMPLIMIENTO_SOLICITUD = '{"fk": "documento_cierre_id"}'

_MARCA_RESIDUO = 'Verificación navegador #788%'


def upgrade():
    conn = op.get_bind()

    # --- 0. Residuo de verificación en navegador -----------------------------
    conn.execute(
        sa.text("""
            DELETE FROM public.catalogo_plazos
            WHERE norma_origen LIKE :marca
        """),
        {'marca': _MARCA_RESIDUO},
    )

    # --- 1. La marca suspensora ---------------------------------------------
    for camino in _CAMINOS_SUSPENSORES:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET suspende_plazo_solicitud = TRUE
                WHERE tipo_elemento = 'TAREA'
                  AND camino = :camino
            """),
            {'camino': camino},
        )

    # --- 2. El señalador de cumplimiento — nivel TAREA ----------------------
    conn.execute(
        sa.text("""
            UPDATE public.catalogo_plazos
            SET campo_fecha_cumplimiento = CAST(:cumplimiento AS json)
            WHERE tipo_elemento = 'TAREA'
              AND camino NOT LIKE '%/TABLON_AYUNTAMIENTOS/%'
              AND campo_fecha_cumplimiento IS NULL
        """),
        {'cumplimiento': _CUMPLIMIENTO_TAREA},
    )

    # --- 3. El señalador de cumplimiento — nivel SOLICITUD ------------------
    conn.execute(
        sa.text("""
            UPDATE public.catalogo_plazos
            SET campo_fecha_cumplimiento = CAST(:cumplimiento AS json)
            WHERE tipo_elemento = 'SOLICITUD'
              AND campo_fecha_cumplimiento IS NULL
        """),
        {'cumplimiento': _CUMPLIMIENTO_SOLICITUD},
    )


def downgrade():
    """Vacía las dos columnas; no restaura la fila purgada.

    Recrear el residuo de verificación sería reintroducir basura, no revertir un
    cambio de configuración (mismo criterio que el downgrade de 788b).
    """
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET campo_fecha_cumplimiento = NULL,
            suspende_plazo_solicitud = FALSE
    """))
