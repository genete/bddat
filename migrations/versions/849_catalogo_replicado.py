"""849_catalogo_replicado

Revision ID: 849_catalogo_replicado
Revises: 428b_ancla_solicitud
Create Date: 2026-09-06

Issue #849 — hace converger el catálogo de una instalación construida desde
cero con el de desarrollo. Once puntos, todos por clave natural y todos
idempotentes: en desarrollo esta migración es un no-op salvo el punto 1, y esa
es justamente la comprobación de que está bien escrita.

**Por qué hacía falta.** `flask db upgrade heads` sobre base vacía llega al
final desde #849.A, pero el catálogo que produce no es el de desarrollo. Dos
causas distintas, mismo efecto:

- Migraciones de corrección que localizan la fila por su `id` autoincremental.
  En una base construida desde cero esos ids son otros: el `UPDATE` afecta a 0
  filas y no da ningún error (`b29f4e7f3d6b_782_fix_norma_origen_placeholders`,
  `477_fix_norma_origen_cierre`, `685e93a0c79e_fix_datos_test346…`,
  `8a18f2077c0c_814_variables_reglas_ip_aau`), o peor, acierta de fila y falla
  de significado (`c3d4e5f6a7b8_fase3_nombre_en_plantilla`, ver punto 8).
- Curado hecho a mano sobre la base de desarrollo que nunca volvió al repo. Se
  formaliza aquí porque #856 recreará esa base: lo que solo viva ahí, se pierde.

De ahora en adelante ninguna de las dos cosas debería repetirse — las dos
reglas están escritas en `docs/guias/REGLAS_DESARROLLO.md`, §"reglas que solo
se notan instalando desde cero".

Fuera de alcance a propósito (#849 replica el catálogo de desarrollo, no lo
cura): `catalogo_variables.sin_linea_aerea` sigue sin norma, aunque
`8a18f2077c0c` la declare del Decreto 9/2011 igual que sus dos hermanas, y las
otras siete provincias de `unidades_organo_propio` siguen sin datos de sede.
Ambas cosas son curado, y su sitio es #856.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '849_catalogo_replicado'
down_revision = '428b_ancla_solicitud'
branch_labels = None
depends_on = None


# Etiquetas de `catalogo_variables`: dos migraciones siembran las mismas tres
# variables con textos distintos y las dos usan ON CONFLICT DO NOTHING
# (`b4417076e504` #638 y `8a18f2077c0c` #814), así que en una instalación
# limpia gana siempre la primera y la segunda se descarta en silencio.
_ETIQUETAS_VARIABLE = [
    ('sin_linea_aerea', 'Instalación sin ninguna línea aérea'),
    ('max_tension_nominal_kv', 'Tensión nominal máxima de la instalación (kV)'),
    ('solo_suelo_urbano_urbanizable', 'Recorrido íntegro en suelo urbano o urbanizable'),
]

# Trámites y fases que SÍ llevan `nombre_en_plantilla` en desarrollo. Los dos
# trámites los puebla `6d7becf5d82b` (#698) resolviendo por código, así que ya
# coinciden; se listan aquí como excepción del borrado del punto 8.
_TRAMITES_CON_NOMBRE = ('REQUERIMIENTO_SUBSANACION', 'ELABORACION')
_FASES_CON_NOMBRE = ('RECONOCIMIENTO_INTERESADO',)


def upgrade():
    conn = op.get_bind()
    tocadas = {}

    def _ejecutar(clave, sql, **params):
        tocadas[clave] = conn.execute(sa.text(sql), params).rowcount

    # 1 — Título de la norma D9_2011, con los acentos rotos en desarrollo
    #     (`AndalucÃ­a`). Es el único punto que corrige desarrollo en vez de
    #     copiarlo: aquí la base construida desde cero es la que está bien.
    _ejecutar('normas.D9_2011', """
        UPDATE public.normas
        SET titulo = 'Decreto 9/2011, de 26 de enero (Junta de Andalucía)'
        WHERE codigo = 'D9_2011'
          AND titulo <> 'Decreto 9/2011, de 26 de enero (Junta de Andalucía)'
    """)

    # 2 — Regla del motor: la exención de Información Pública se comprueba por
    #     `solicitud_incluye_dup`, no enumerando a mano dos combinaciones con
    #     DUP. La migración #814 lo hacía con `WHERE regla_id = 38`; la regla
    #     no tiene clave natural, así que se localiza por (accion, sujeto,
    #     descripcion), que es lo que ya usa test_470_cert_fin_ip_consultas.py.
    #     Sin esto, una instalación limpia no bloquea la apertura de RESOLUCION
    #     sin IP concluida en un AAC+DUP.
    _ejecutar('condiciones_regla.ip_dup', """
        UPDATE public.condiciones_regla c
        SET variable_id = (SELECT id FROM public.catalogo_variables
                           WHERE nombre = 'solicitud_incluye_dup'),
            operador = 'EQ',
            valor = 'true'::jsonb
        FROM public.reglas_motor r
        WHERE c.regla_id = r.id
          AND r.accion = 'CREAR'
          AND r.sujeto = 'ANY/ANY/RESOLUCION'
          AND r.descripcion = 'La fase de Información Pública no ha concluido'
          AND c.variable_id = (SELECT id FROM public.catalogo_variables
                               WHERE nombre = 'tipo_solicitud')
    """)

    # 3 — `catalogo_plazos`: los cinco PLACEHOLDER que #782 dejó sin sustituir
    #     (localizaba por id 5, 7, 8, 9 y 10). Además de la cita, en tres de
    #     ellos cambia la unidad: 30 días naturales frente a 30 hábiles no es
    #     un matiz de redacción, son dos fechas distintas.
    _ejecutar('plazos.requerimiento', """
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 68.1 LPACAP'
        WHERE camino = 'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO'
          AND norma_origen LIKE 'PLACEHOLDER%'
    """)
    _ejecutar('plazos.solicitud_informe', """
        UPDATE public.catalogo_plazos
        SET camino = 'ANY/ANY/CONSULTA_MINISTERIO/SOLICITUD_INFORME/ESPERAR_PLAZO',
            plazo_valor = 2,
            plazo_unidad = 'MESES',
            norma_origen = 'Art. 114 RD 1955/2000'
        WHERE camino = 'ANY/ANY/ANY/SOLICITUD_INFORME/ESPERAR_PLAZO'
          AND norma_origen LIKE 'PLACEHOLDER%'
    """)
    for tramite, norma in (('ANUNCIO_BOE', 'Art. 125.1 RD 1955/2000'),
                           ('ANUNCIO_BOP', 'Art. 125.1 RD 1955/2000'),
                           ('ANUNCIO_PRENSA', 'Art. 144 RD 1955/2000')):
        _ejecutar(f'plazos.{tramite.lower()}', """
            UPDATE public.catalogo_plazos
            SET plazo_unidad = 'DIAS_HABILES',
                norma_origen = :norma
            WHERE camino = :camino
              AND norma_origen LIKE 'PLACEHOLDER%'
        """, norma=norma, camino=f'ANY/ANY/ANY/{tramite}/ESPERAR_PLAZO')

    # 4 — Cita del cierre. Dos migraciones se pisan por `WHERE id = 111`
    #     (`685e93a0c79e` la pone, `477_fix_norma_origen_cierre` la quita), y
    #     en una base limpia ninguna de las dos encuentra la fila.
    _ejecutar('plazos.cierre', """
        UPDATE public.catalogo_plazos
        SET norma_origen = 'Art. 138 RD 1955/2000 (mod. RD 88/2026)'
        WHERE tipo_elemento = 'SOLICITUD'
          AND camino = 'ANY/CIERRE'
          AND norma_origen = 'Art. 138 RD 1955/2000'
    """)

    # 5 — Etiquetas de las tres variables del Decreto 9/2011.
    for nombre, etiqueta in _ETIQUETAS_VARIABLE:
        _ejecutar(f'variables.{nombre}', """
            UPDATE public.catalogo_variables
            SET etiqueta = :etiqueta
            WHERE nombre = :nombre AND etiqueta <> :etiqueta
        """, nombre=nombre, etiqueta=etiqueta)

    # 6 — Norma de dos de esas tres. `sin_linea_aerea` se queda sin norma
    #     porque así está en desarrollo (ver "fuera de alcance" arriba).
    _ejecutar('variables.norma_d9_2011', """
        UPDATE public.catalogo_variables
        SET norma_id = (SELECT id FROM public.normas WHERE codigo = 'D9_2011')
        WHERE nombre IN ('max_tension_nominal_kv', 'solo_suelo_urbano_urbanizable')
          AND norma_id IS NULL
    """)

    # 7 — Tipos de documento: el nombre curado en desarrollo. La descripción
    #     del MODELO_909 ya la trae `849_seed_catalogo_pendiente`; faltaba el
    #     nombre, que se quedó por el camino.
    _ejecutar('tipos_documentos.dr_no_dup', """
        UPDATE public.tipos_documentos
        SET nombre = 'Declaración Responsable de No solicitud de Declaración de Utilidad Pública',
            descripcion = 'Cuando se presenta, se usa para evitar la información pública si se cumplen otros requisitos'
        WHERE codigo = 'DR_NO_DUP'
          AND nombre <> 'Declaración Responsable de No solicitud de Declaración de Utilidad Pública'
    """)
    _ejecutar('tipos_documentos.modelo_909', """
        UPDATE public.tipos_documentos
        SET nombre = 'Modelo 909 carta de pago tasa'
        WHERE codigo = 'MODELO_909'
          AND nombre <> 'Modelo 909 carta de pago tasa'
    """)

    # 8 — `nombre_en_plantilla` cruzado. `c3d4e5f6a7b8` lo puebla con un
    #     `CASE id WHEN 1 THEN…` escrito para el catálogo de marzo de 2026. En
    #     desarrollo no casó ningún id y quedó a NULL; en una base limpia casan
    #     todos y cada fila recibe el nombre de otra —INFORMACION_PUBLICA ->
    #     'Compatibilidad Ambiental', ANUNCIO_BOE -> 'Informe Compatibilidad'—,
    #     que es lo que acabaría en el nombre del documento generado
    #     (app/services/nombres_documentos.py). Se vacía lo cruzado: el dato
    #     bueno se va poblando por código en #809, no se inventa aquí.
    _ejecutar('tipos_fases.nombre_en_plantilla', """
        UPDATE public.tipos_fases
        SET nombre_en_plantilla = NULL
        WHERE nombre_en_plantilla IS NOT NULL
          AND codigo <> ALL(:conservados)
    """, conservados=list(_FASES_CON_NOMBRE))
    _ejecutar('tipos_tramites.nombre_en_plantilla', """
        UPDATE public.tipos_tramites
        SET nombre_en_plantilla = NULL
        WHERE nombre_en_plantilla IS NOT NULL
          AND codigo <> ALL(:conservados)
    """, conservados=list(_TRAMITES_CON_NOMBRE))

    # 9 — Abreviatura de la tarea ANALIZAR: `0869cda75380` la puso con el
    #     código anterior ('ANALISIS'), y `348_seed_catalogo_base` renombró el
    #     código sin tocarla.
    _ejecutar('tipos_tareas.abrev', """
        UPDATE public.tipos_tareas
        SET abrev = 'ANALIZAR'
        WHERE codigo = 'ANALIZAR' AND abrev <> 'ANALIZAR'
    """)

    # 10 — Datos de sede de Sevilla. `728_unidades_organo_propio` deja las tres
    #      columnas a NULL en las ocho provincias; las de Sevilla se rellenaron
    #      a mano en desarrollo. Las otras siete siguen vacías: son dato real
    #      que hay que recopilar, no inventar.
    _ejecutar('unidades_organo_propio.sevilla', """
        UPDATE public.unidades_organo_propio
        SET sede_direccion = 'Avda. de Grecia, s/n, 41071 Sevilla',
            sede_telefono = '955 063 400',
            sede_correo = 'industria.se@juntadeandalucia.es'
        WHERE provincia = 'Sevilla' AND sede_direccion IS NULL
    """)

    # 11 — Plantilla del requerimiento de subsanación. Las otras cuatro las
    #      siembran migraciones (#402, #403, #404, #776); esta se dio de alta a
    #      mano en desarrollo y nunca volvió al repo, así que una instalación
    #      nueva no puede generar el escrito pese a tener su generador
    #      (`ContextoSubsanacion`, app/services/context_builders/) implementado.
    _ejecutar('plantillas.requerimiento_subsanacion', """
        INSERT INTO public.plantillas
            (codigo, nombre, descripcion, ruta_plantilla, contexto_clase,
             tipo_documento_id, tipo_tramite_id, tipo_fase_id, activo)
        SELECT 'REQUERIMIENTO_SUBSANACION',
               'Requerimiento de subsanación',
               'Requerimiento a titular para subsanación de defectos en la solicitud.',
               'escritos/requerimiento_subsanacion.docx',
               'ContextoSubsanacion',
               (SELECT id FROM public.tipos_documentos WHERE codigo = 'OFICIO_REQUERIMIENTO'),
               (SELECT id FROM public.tipos_tramites WHERE codigo = 'REQUERIMIENTO_SUBSANACION'),
               (SELECT id FROM public.tipos_fases WHERE codigo = 'ANALISIS_SOLICITUD'),
               TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM public.plantillas WHERE codigo = 'REQUERIMIENTO_SUBSANACION'
        )
    """)

    total = sum(tocadas.values())
    detalle = ', '.join(f'{k}={v}' for k, v in tocadas.items() if v)
    print(f'[849_catalogo_replicado] filas corregidas: {total}'
          + (f' ({detalle})' if detalle else ' — nada que corregir'))


def downgrade():
    """No revierte, a propósito.

    Los diez puntos hacen converger el catálogo con el de desarrollo. Bajar
    esta revisión significaría reintroducir a mano valores que sabemos
    incorrectos —la regla de IP sin cubrir AAC+DUP, cinco plazos con su cita
    en PLACEHOLDER y tres de ellos con la unidad equivocada, los nombres de
    plantilla cruzados—, y en la base de desarrollo el daño sería real.

    El estado anterior no se pierde: cada punto documenta arriba qué migración
    lo dejó así y con qué valor.
    """
    pass
