"""377_seed_descripciones_tipos_documentos

Revision ID: 377_seed_descripciones_tipos_documentos
Revises: merge_heads_seed_catalogo_base
Create Date: 2026-05-17

Issue #377 — Pobla la columna descripcion de tipos_documentos con el
catálogo ESFTT revisado (código, nombre, fecha_administrativa).
Los 50 tipos del catálogo ya existen en BD (337_seed_tipos_documentos);
esta migración solo añade las descripciones.
CERT_PLAZO_TABLON se deja sin descripción hasta resolver el modelado
del procedimiento de tablón (ver #416).
"""
from alembic import op
import sqlalchemy as sa


revision = '377_descripciones_tipos_doc'
down_revision = 'merge_heads_seed_catalogo_base'
branch_labels = None
depends_on = None

# (codigo, descripcion)
_DESCRIPCIONES = [
    # Justificantes de notificación
    ('JUSTIFICANTE_NOTIFICA',
     'Acuse de entrega electrónica emitido por la plataforma Notifica-PNT. '
     'Fecha administrativa: fecha de entrega al interesado, deducida automáticamente '
     'del documento; el usuario debe cotejar el valor deducido con el real.'),
    ('JUSTIFICANTE_BANDEJA',
     'Justificante de transmisión electrónica generado por BandeJA. '
     'Fecha administrativa: fecha de transmisión, deducida automáticamente; '
     'el usuario debe cotejar el valor deducido con el real.'),
    ('JUSTIFICANTE_SIR',
     'Justificante de notificación cursada por registro SIR/ARIES. '
     'Fecha administrativa: fecha de práctica de la notificación tal como consta '
     'en el justificante; se introduce manualmente.'),
    ('JUSTIFICANTE_POSTAL',
     'Acuse de recibo de notificación practicada por correo postal. '
     'Fecha administrativa: fecha de entrega acreditada en el acuse de recibo; '
     'se introduce manualmente.'),
    # Justificantes de publicación
    ('JUSTIFICANTE_BOE',
     'Justificante de publicación del anuncio en el BOE, aportado por el promotor. '
     'Cierra el primer período de espera e inicia el plazo de IP. '
     'Fecha administrativa: fecha de publicación en el BOE tal como consta en el justificante.'),
    ('JUSTIFICANTE_BOP',
     'Justificante de publicación del anuncio obtenido de la plataforma del BOP. '
     'Cierra el primer período de espera e inicia el plazo de IP. '
     'Fecha administrativa: fecha de publicación efectiva en el BOP.'),
    ('JUSTIFICANTE_BOJA',
     'Justificante de publicación del anuncio obtenido de la plataforma SIBOJA del BOJA. '
     'Cierra el primer período de espera e inicia el plazo de IP. '
     'Fecha administrativa: fecha de publicación efectiva en el BOJA.'),
    ('JUSTIFICANTE_PRENSA',
     'Justificante de publicación del anuncio en el diario de mayor difusión de la provincia, '
     'aportado por el titular. Cierra el primer período de espera e inicia el plazo de IP. '
     'Fecha administrativa: fecha de publicación en prensa tal como consta en el justificante.'),
    ('JUSTIFICANTE_TABLON',
     'Certificado emitido por el ayuntamiento acreditando que el anuncio ha sido expuesto '
     'en su tablón de edictos. '
     'Fecha administrativa: fecha de inicio de la exposición tal como consta en el certificado; '
     'se introduce manualmente.'),
    ('JUSTIFICANTE_PORTAL',
     'URL permanente generada por la plataforma DRUPAL del portal de transparencia, '
     'acreditando la publicación del expediente e indicando si el período de IP está activo. '
     'Fecha administrativa: no aplica.'),
    # Documentos generados por BDDAT
    ('CERT_PLAZO_CUMPLIDO',
     'Certificado generado automáticamente por BDDAT al vencer un plazo procedimental. '
     'Acredita el transcurso del plazo o la ausencia de respuesta, con fundamento jurídico '
     'y cómputo incluidos. '
     'Fecha administrativa: fecha de vencimiento del plazo, calculada automáticamente; '
     'no requiere entrada manual.'),
    ('DIAGNOSTICO',
     'Registro estructurado de la decisión técnica adoptada en una tarea de análisis. '
     'Se genera y almacena en BDDAT; no produce efectos jurídicos propios. '
     'Fecha administrativa: no aplica (NULL por diseño).'),
    # ANALISIS_SOLICITUD / inicio
    ('OFICIO_REQUERIMIENTO',
     'Escrito administrativo que requiere al titular la subsanación de deficiencias '
     'en la documentación presentada. '
     'Fecha administrativa: fecha de firma.'),
    ('SUBSANACION',
     'Documentación aportada por el titular en respuesta al requerimiento de subsanación. '
     'Fecha administrativa: fecha de registro de entrada; el documento puede ser parseado '
     'para deducir el valor, pero debe cotejarse con el real.'),
    ('OFICIO_INICIO',
     'Escrito que comunica al titular el inicio formal de la tramitación del expediente. '
     'Fecha administrativa: fecha de firma.'),
    # Informe ministerial
    ('OFICIO_114_RD1955',
     'Escrito de solicitud del informe preceptivo a la Administración General del Estado '
     'conforme al art. 114 del RD 1955/2000. '
     'Fecha administrativa: fecha de firma.'),
    ('INFORME_114_RD1955',
     'Informe emitido por el Ministerio en cumplimiento del art. 114 del RD 1955/2000. '
     'Se recibe y analiza antes de continuar la tramitación. '
     'Fecha administrativa: fecha del informe tal como consta en el documento.'),
    # Compatibilidad ambiental
    ('DOC_SOLICITUD_AAU',
     'Solicitud de autorización ambiental unificada presentada por el titular '
     'con el modelo oficial. Se consume al tramitar la consulta de compatibilidad ambiental. '
     'Fecha administrativa: fecha de registro de entrada.'),
    ('OFICIO_COMPATIBILIDAD_AMBIENTAL',
     'Escrito de remisión de la solicitud de compatibilidad ambiental '
     'al órgano ambiental competente. '
     'Fecha administrativa: fecha de firma.'),
    ('INFORME_COMPATIBILIDAD_AMBIENTAL',
     'Informe emitido por el órgano ambiental sobre la compatibilidad del proyecto '
     'con las figuras de protección ambiental. El sentido lo evalúa el técnico instructor. '
     'Fecha administrativa: fecha del informe tal como consta en el documento.'),
    ('DOC_COMUNICACION_AUDIENCIA',
     'Escrito del órgano ambiental comunicando al órgano sustantivo la apertura de la '
     'audiencia al interesado por posible incompatibilidad. El órgano sustantivo registra '
     'el documento sin actuación adicional. '
     'Fecha administrativa: fecha del escrito del órgano ambiental.'),
    # Consultas a organismos sectoriales
    ('DOC_SEPARATA',
     'Documentación técnica del proyecto aportada por el solicitante como base '
     'para las consultas a organismos sectoriales. '
     'Fecha administrativa: fecha de registro de entrada.'),
    ('OFICIO_SEPARATA',
     'Escrito de solicitud de informe o pronunciamiento al organismo sectorial afectado, '
     'adjuntando la separata del proyecto. '
     'Fecha administrativa: fecha de firma.'),
    ('RESPUESTA_ORGANISMO',
     'Respuesta del organismo sectorial a la consulta realizada. '
     'Puede incluir conformidad, oposición, reparos o condicionado. '
     'Fecha administrativa: fecha del documento del organismo.'),
    ('OFICIO_TRASLADO_RESPUESTA',
     'Escrito de traslado al titular de la respuesta recibida del organismo sectorial. '
     'Fecha administrativa: fecha de firma.'),
    ('RESPUESTA_TITULAR',
     'Contestación del titular a los reparos o condicionado del organismo sectorial. '
     'Fecha administrativa: fecha de registro de entrada.'),
    ('OFICIO_TRASLADO_REPAROS',
     'Escrito de traslado al organismo sectorial de la respuesta del titular a sus reparos. '
     'Fecha administrativa: fecha de firma.'),
    # Información pública
    ('DOC_PROYECTO',
     'Proyecto técnico aportado por el titular que describe las características '
     'de la instalación. Se usa como referencia en múltiples tareas de análisis '
     'y elaboración a lo largo del expediente. '
     'Fecha administrativa: fecha de registro de entrada.'),
    ('ANUNCIO_IP',
     'Anuncio oficial que abre el período de información pública del expediente. '
     'Documento único compartido por todos los trámites de publicación. '
     'Fecha administrativa: fecha de firma.'),
    ('OFICIO_PUBLICAR_TITULAR',
     'Escrito al titular indicándole que tramite la publicación del anuncio '
     'en boletines y prensa. '
     'Fecha administrativa: fecha de firma.'),
    ('OFICIO_PUBLICAR_BOLETIN',
     'Escrito de remisión del anuncio de información pública al BOP. '
     'No aplica a ANUNCIO_BOJA, que tramita la publicación vía plataforma SIBOJA. '
     'Fecha administrativa: fecha de firma.'),
    ('ANUNCIO_PUBLICADO',
     'Copia del anuncio tal como fue publicado en el boletín oficial (BOP o BOJA). '
     'Introducida por la administración al verificar la publicación en la plataforma '
     'del boletín. '
     'Fecha administrativa: fecha de publicación efectiva en el boletín; '
     'determina el inicio del plazo de IP.'),
    ('OFICIO_TABLON',
     'Escrito de solicitud de exposición del anuncio en el tablón de edictos '
     'de los ayuntamientos afectados. Se firma un único documento; '
     'el usuario lo divide por municipio. '
     'Fecha administrativa: fecha de firma.'),
    # Alegaciones de información pública
    ('ALEGACION_IP',
     'Escrito de alegaciones presentado por un interesado durante el período '
     'de información pública. Puede haber varias por expediente; '
     'se analizan individualmente y en conjunto. '
     'Fecha administrativa: fecha de registro de entrada.'),
    ('OFICIO_TRASLADO_ALEGACION',
     'Escrito de traslado al titular de las alegaciones recibidas durante '
     'la información pública. '
     'Fecha administrativa: fecha de firma.'),
    ('RESPUESTA_TITULAR_ALEGACION',
     'Contestación del titular a las alegaciones que le han sido trasladadas. '
     'Una respuesta por alegación; se analiza en conjunto en ANALISIS_ALEGACIONES. '
     'Fecha administrativa: fecha de registro de entrada.'),
    # Figura ambiental externa
    ('OFICIO_SOLICITUD_FIGURA',
     'Escrito dirigido al promotor instándole a obtener la figura ambiental externa '
     'aplicable ante el órgano ambiental competente. '
     'La espera posterior no tiene plazo predefinido. '
     'Fecha administrativa: fecha de firma.'),
    ('FIGURA_AMBIENTAL_EXTERNA',
     'Figura ambiental obtenida por el promotor ante el órgano ambiental '
     '(EIA, AAU u otra). Aportada al expediente sin plazo predefinido. '
     'Fecha administrativa: fecha de la resolución o informe del órgano ambiental '
     'tal como consta en el documento.'),
    # Resolución
    ('CERT_FIN_INSTRUCCION',
     'Certificado generado automáticamente por BDDAT al completarse todas las fases '
     'de instrucción requeridas. Recoge el tipo de expediente, fases completadas, '
     'resultados y fundamento jurídico que habilita la resolución. '
     'Fecha administrativa: fecha de generación, calculada automáticamente.'),
    ('RESOLUCION',
     'Acto administrativo que concede o deniega la autorización solicitada. '
     'Fecha administrativa: fecha de firma.'),
    ('RESOLUCION_PUBLICADA',
     'Copia de la resolución publicada en el boletín oficial correspondiente. '
     'Una instancia por boletín. '
     'Fecha administrativa: fecha de publicación efectiva en el boletín.'),
    # Fase AAU_AAUS_INTEGRADA
    ('CERT_FIN_IP_CONSULTAS',
     'Certificado que acredita la conclusión de las fases de IP y consultas sectoriales. '
     'Habilita el inicio de la fase ambiental integrada. '
     'Fecha administrativa: fecha de finalización de la última fase habilitante, '
     'calculada automáticamente.'),
    ('OFICIO_RESULTADO_IP_CON',
     'Escrito de remisión al órgano ambiental del conjunto de contestaciones '
     'a consultas y alegaciones de la IP. '
     'Fecha administrativa: fecha de firma.'),
    ('DOC_DICTAMEN_AMBIENTAL',
     'Dictamen emitido por el órgano ambiental sobre el resultado de la instrucción '
     'ambiental. Puede ser favorable, condicionado o desfavorable; '
     'la valoración se registra en el análisis técnico. '
     'Fecha administrativa: fecha del dictamen tal como consta en el documento.'),
    ('OFICIO_OBS_DICTAMEN',
     'Escrito de respuesta al dictamen ambiental con las observaciones del órgano sustantivo. '
     'Se emite siempre para activar el cómputo del plazo siguiente. '
     'Fecha administrativa: fecha de firma.'),
    ('DOC_PROPUESTA_INF_VINC',
     'Propuesta de informe vinculante emitida por el órgano ambiental tras la audiencia '
     'a los interesados del procedimiento ambiental. '
     'Fecha administrativa: fecha de la propuesta tal como consta en el documento.'),
    ('OFICIO_OBS_PROP_INF_VINC',
     'Escrito de observaciones a la propuesta de informe vinculante del órgano ambiental. '
     'Se emite siempre para activar el plazo siguiente. '
     'Fecha administrativa: fecha de firma.'),
    ('DOC_INFORME_VINCULANTE',
     'Informe vinculante definitivo emitido por el órgano ambiental. '
     'Sus condiciones se incorporan obligatoriamente a la autorización. '
     'Fecha administrativa: fecha del informe tal como consta en el documento.'),
    ('OFICIO_DISCREPANCIA_INF_VINC',
     'Escrito de planteamiento de discrepancia ante el Consejo de Gobierno cuando '
     'el órgano sustantivo no comparte el informe vinculante. '
     'Solo se emite si el análisis previo diagnostica discrepancia. '
     'Fecha administrativa: fecha de firma.'),
    ('RESOLUCION_DISCREPANCIA_INF_VINC',
     'Resolución del Consejo de Gobierno que dirime la discrepancia sobre el informe '
     'vinculante. Vincula al órgano sustantivo y cierra el trámite. '
     'Fecha administrativa: fecha de la resolución del Consejo de Gobierno '
     'tal como consta en el documento.'),
]


def upgrade():
    conn = op.get_bind()
    for codigo, descripcion in _DESCRIPCIONES:
        conn.execute(
            sa.text("""
                UPDATE public.tipos_documentos
                SET descripcion = :descripcion
                WHERE codigo = :codigo
            """),
            {'codigo': codigo, 'descripcion': descripcion}
        )


def downgrade():
    conn = op.get_bind()
    codigos = [t[0] for t in _DESCRIPCIONES]
    conn.execute(
        sa.text("""
            UPDATE public.tipos_documentos
            SET descripcion = NULL
            WHERE codigo = ANY(:codigos)
        """),
        {'codigos': codigos}
    )
