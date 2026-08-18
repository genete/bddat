"""788a_catalogo_plazos_niveles

Revision ID: 788a_niveles_plazos
Revises: 787_purga_residuo_smoke
Create Date: 2026-08-18

Issue #788 (migración A) — las filas de `catalogo_plazos` bajan al nivel que sí
porta la fecha de inicio del cómputo.

PROBLEMA
========

Un plazo necesita fecha de inicio, y en BDDAT solo hay dos portadores de fecha
administrativa (DISEÑO_FECHAS_PLAZOS §2.bis): la Solicitud, por
`documento_solicitud_id`, y la Tarea, por `documentos_tarea` (ADR-010). La Fase
no llega a ninguno —`documento_resultado_id` es el documento de CIERRE, no de
inicio— y el Trámite no tiene ningún vínculo documental.

Las filas declaradas en esos dos niveles dejaron su huella en el código: el
resolutor tenía una rama exclusiva para FASE que TREPABA a `fase.solicitud` para
encontrar el ancla, y `campo_fecha.via_tarea_tipo` existía con el único cometido
de BAJAR de un trámite a la tarea que sí tenía el documento. Una fila que
necesita moverse de nivel para encontrar su fecha está declarada en el nivel
equivocado.

Se comprobó fase a fase (10 de 10): ninguna norma fija plazo propio a una Fase.
Los 1/3/6 meses de los arts. 128, 131.7, 132 bis/ter, 133, 138 y 145.4 son el
plazo de la SOLICITUD para resolver y notificar (art. 21.3.b LPACAP); que el acto
que lo consume viva en la fase finalizadora no lo convierte en plazo de la fase.
Los 15/30 días de los arts. 127.2 / 131.1 son de cada organismo consultado, desde
la notificación de SU separata — un acto, y todo acto es una tarea.

QUÉ HACE
========

1. Plazos de resolución: 11 filas `FASE` con camino `…/RESOLUCION` pasan a
   `SOLICITUD` perdiendo el último segmento. `campo_fecha` no cambia: ya era
   `{"fk": "documento_solicitud_id"}` — señal de que la fila nunca fue de la
   fase. Efecto colateral querido: el plazo pasa a resolverse desde que hay
   documento de solicitud, no desde que alguien crea la fase RESOLUCION.

2. Plazos de espera: 5 filas `TRAMITE` pasan a `TAREA`, añadiendo el segmento
   `ESPERAR_PLAZO` al camino y sustituyendo la indirección `via_tarea_tipo` por
   el rol directo. `ESTRUCTURA_FTT` declara que el `ESPERAR_PLAZO` consume el
   justificante que produce su `NOTIFICAR` hermana, así que
   `{via: NOTIFICAR, rol: PRODUCIDO}` y `{"rol": "CONSUMIDO"}` apuntan al mismo
   documento: la traducción es exacta, no una aproximación.

3. `tipo_documento` en las tres filas de `ANUNCIO_*`. Su trámite tiene DOS tareas
   `ESPERAR_PLAZO` —la que aguarda a que salga la publicación y la de los 30 días
   de exposición— y el camino no las distingue, así que hoy la fila se aplica a la
   primera que aparece. Declarar el tipo del documento que porta la fecha la ata a
   la segunda, que es la que cuenta el plazo del art. 125, y deja la primera libre
   (#789). El dato ya existía en `tramites_tareas_documentos`.

CRITERIO DE SELECCIÓN
=====================

Por contenido, no por id: los ids de esta BD no valen en otra. La fila residual
de `CONSULTA_SEPARATA` (3 MESES, `norma_origen` NULL, `via_tarea_tipo` =
ESPERAR_PLAZO con rol CONSUMIDO) queda deliberadamente fuera de los WHERE de
aquí — la retira la migración B, que además instala el CheckConstraint una vez
la tabla ya no tiene filas de FASE ni de TRAMITE.
"""
from alembic import op
import sqlalchemy as sa


revision = '788a_niveles_plazos'
down_revision = '787_purga_residuo_smoke'
branch_labels = None
depends_on = None


# Las 11 combinaciones de siglas con plazo de resolución (#448, desdobladas en #785).
_SIGLAS_RESOLUCION = (
    'AE_PROVISIONAL', 'AE_DEFINITIVA', 'AE_DEFINITIVA+AAT',
    'AAP', 'AAC', 'AAP+AAC', 'AAP+AAC+DUP', 'AAC+DUP',
    'AAT', 'CIERRE', 'DUP',
)

# Trámites cuyo plazo baja a su tarea ESPERAR_PLAZO.
#   codigo_tramite → (via_tarea_tipo y rol que identifican la fila, campo_fecha nuevo)
_TRASLADOS_A_TAREA = (
    ('CONSULTA_SEPARATA',            'NOTIFICAR',     'PRODUCIDO', '{"rol": "CONSUMIDO"}'),
    ('CONSULTA_TRASLADO_TITULAR',    'NOTIFICAR',     'PRODUCIDO', '{"rol": "CONSUMIDO"}'),
    ('CONSULTA_TRASLADO_ORGANISMO',  'NOTIFICAR',     'PRODUCIDO', '{"rol": "CONSUMIDO"}'),
    # El tablón es el caso retroactivo (#416): la fecha de inicio la trae el
    # certificado que el ayuntamiento devuelve al final, no un documento de entrada.
    ('TABLON_AYUNTAMIENTOS',         'ESPERAR_PLAZO', 'PRODUCIDO',
     '{"rol": "PRODUCIDO", "tipo_documento": "CERT_PLAZO_TABLON"}'),
)

_ANUNCIOS = ('ANUNCIO_BOE', 'ANUNCIO_BOP', 'ANUNCIO_PRENSA')


def upgrade():
    conn = op.get_bind()

    # --- 1. Plazos de resolución: FASE → SOLICITUD ---------------------------
    for siglas in _SIGLAS_RESOLUCION:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET tipo_elemento = 'SOLICITUD',
                    camino        = :camino_nuevo
                WHERE tipo_elemento = 'FASE'
                  AND camino = :camino_viejo
            """),
            {'camino_viejo': f'ANY/{siglas}/RESOLUCION',
             'camino_nuevo': f'ANY/{siglas}'},
        )

    # --- 2. Plazos de espera: TRAMITE → TAREA -------------------------------
    for codigo, via, rol, campo_fecha_nuevo in _TRASLADOS_A_TAREA:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET tipo_elemento = 'TAREA',
                    camino        = camino || '/ESPERAR_PLAZO',
                    campo_fecha   = CAST(:campo_fecha AS jsonb)
                WHERE tipo_elemento = 'TRAMITE'
                  AND camino = :camino
                  AND campo_fecha ->> 'via_tarea_tipo' = :via
                  AND campo_fecha ->> 'rol' = :rol
            """),
            {'camino': f'ANY/ANY/ANY/{codigo}', 'via': via, 'rol': rol,
             'campo_fecha': campo_fecha_nuevo},
        )

    # --- 3. tipo_documento en las esperas de exposición de anuncios ---------
    for codigo in _ANUNCIOS:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET campo_fecha = campo_fecha || '{"tipo_documento": "ANUNCIO_PUBLICADO"}'::jsonb
                WHERE tipo_elemento = 'TAREA'
                  AND camino = :camino
                  AND campo_fecha ->> 'rol' = 'CONSUMIDO'
            """),
            {'camino': f'ANY/ANY/ANY/{codigo}/ESPERAR_PLAZO'},
        )


def downgrade():
    """Reversible: son traslados de nivel, no purga (eso es la migración B)."""
    conn = op.get_bind()

    for codigo in _ANUNCIOS:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET campo_fecha = campo_fecha - 'tipo_documento'
                WHERE tipo_elemento = 'TAREA'
                  AND camino = :camino
                  AND campo_fecha ->> 'tipo_documento' = 'ANUNCIO_PUBLICADO'
            """),
            {'camino': f'ANY/ANY/ANY/{codigo}/ESPERAR_PLAZO'},
        )

    for codigo, via, rol, campo_fecha_nuevo in _TRASLADOS_A_TAREA:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET tipo_elemento = 'TRAMITE',
                    camino        = :camino_viejo,
                    campo_fecha   = jsonb_build_object('via_tarea_tipo', :via, 'rol', :rol)
                WHERE tipo_elemento = 'TAREA'
                  AND camino = :camino_nuevo
                  AND campo_fecha = CAST(:campo_fecha AS jsonb)
            """),
            {'camino_viejo': f'ANY/ANY/ANY/{codigo}',
             'camino_nuevo': f'ANY/ANY/ANY/{codigo}/ESPERAR_PLAZO',
             'via': via, 'rol': rol, 'campo_fecha': campo_fecha_nuevo},
        )

    for siglas in _SIGLAS_RESOLUCION:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET tipo_elemento = 'FASE',
                    camino        = :camino_viejo
                WHERE tipo_elemento = 'SOLICITUD'
                  AND camino = :camino_nuevo
                  AND campo_fecha ->> 'fk' = 'documento_solicitud_id'
                  AND norma_origen IS NOT NULL
            """),
            {'camino_nuevo': f'ANY/{siglas}',
             'camino_viejo': f'ANY/{siglas}/RESOLUCION'},
        )
