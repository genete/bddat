"""seed_catalogo_base — datos estructurales de catálogo

Revision ID: seed_catalogo_base
Revises:
Create Date: 2026-05-07

Rama paralela al esquema (down_revision=None, depends_on='dfdeb43518d6').
Inserta los datos de catálogo que antes cargaba datos_estructurales.sql.
Usa ON CONFLICT (id) DO NOTHING → idempotente sobre BD existente.

Nota: tipos_tareas ID 1 lleva codigo='ANALIZAR' (corregido desde 'ANALISIS').
La BD de desarrollo sigue con 'ANALISIS' hasta que se ejecute manualmente:
    UPDATE public.tipos_tareas SET codigo = 'ANALIZAR' WHERE id = 1;
"""
from alembic import op


revision = 'seed_catalogo_base'
down_revision = None
branch_labels = None
depends_on = 'dfdeb43518d6'


def upgrade():
    op.execute("""
        INSERT INTO public.roles (id, nombre, descripcion) VALUES
        (1, 'ADMIN',          'Administrador total: gestiona alembic_version y schema legacy'),
        (2, 'SUPERVISOR',     'Gestión de usuarios, tablas maestras y configuración del sistema'),
        (3, 'TRAMITADOR',     'Tramitación de expedientes con acceso lectura a estructura'),
        (4, 'ADMINISTRATIVO', 'Tareas administrativas con acceso lectura a estructura')
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("""
        INSERT INTO public.tipos_expedientes (id, tipo, descripcion) VALUES
        (1, 'Transporte',         'Expediente que tramita instalaciones de transporte de energía eléctrica'),
        (2, 'Distribución',       'Expediente que tramita instalaciones de distribución de energía eléctrica'),
        (3, 'Distribución cedida','Expediente que tramita instalaciones de distribución de energía eléctrica cedidas de particular a compañía'),
        (4, 'Renovable',          'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes renovables'),
        (5, 'Autoconsumo',        'Expediente que tramita instalaciones de autoconsumo'),
        (6, 'LineaDirecta',       'Expediente que tramita líneas directas para consumo'),
        (7, 'Convencional',       'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes convencionales'),
        (8, 'Otros',              'Otros tipos de expedientes')
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("""
        INSERT INTO public.tipos_ia (id, siglas, descripcion) VALUES
        (1, 'AAI',    'Autorización Ambiental Integrada'),
        (2, 'AAU',    'Autorización Ambiental Unificada'),
        (3, 'AAUS',   'Autorización Ambiental Unificada Simplificada'),
        (4, 'CA',     'Calificación Ambiental'),
        (5, 'EXENTO', 'Exento de instrumento ambiental')
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("""
        INSERT INTO public.tipos_resultados_fases (id, codigo, nombre) VALUES
        (1, 'FAVORABLE',              'Favorable'),
        (2, 'FAVORABLE_CONDICIONADO', 'Favorable con Condiciones'),
        (3, 'DESFAVORABLE',           'Desfavorable'),
        (4, 'NO_PROCEDE',             'No Procede'),
        (5, 'DESISTIDA',              'Desistida por el Solicitante'),
        (6, 'ARCHIVADA',              'Archivada')
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("""
        INSERT INTO public.tipos_tramites (id, codigo, nombre) VALUES
        (1,  'ANALISIS_DOCUMENTAL',        'Análisis Documental'),
        (2,  'REQUERIMIENTO_SUBSANACION',  'Requerimiento de Subsanación'),
        (3,  'COMUNICACION_INICIO',        'Comunicación de Inicio'),
        (4,  'SOLICITUD_INFORME',          'Solicitud de Informe'),
        (5,  'RECEPCION_INFORME',          'Recepción de Informe'),
        (6,  'SOLICITUD_COMPATIBILIDAD',   'Solicitud de Compatibilidad'),
        (7,  'AUDIENCIA',                  'Audiencia'),
        (8,  'CONSULTA_SEPARATA',          'Separata a Organismo'),
        (9,  'CONSULTA_TRASLADO_TITULAR',  'Traslado al Titular'),
        (10, 'CONSULTA_TRASLADO_ORGANISMO','Traslado al Organismo'),
        (11, 'ANUNCIO_BOE',                'Anuncio en BOE'),
        (12, 'ANUNCIO_BOP',                'Anuncio en BOP'),
        (13, 'ANUNCIO_PRENSA',             'Anuncio en Prensa'),
        (14, 'TABLON_AYUNTAMIENTOS',       'Tablón de Ayuntamientos'),
        (15, 'PORTAL_TRANSPARENCIA',       'Portal de Transparencia'),
        (16, 'RECEPCION_ALEGACION',        'Recepción de Alegación'),
        (17, 'ANALISIS_ALEGACIONES',       'Análisis de Alegaciones'),
        (18, 'SOLICITUD_FIGURA',           'Solicitud de Instrumento Ambiental'),
        (19, 'RECEPCION_FIGURA',           'Recepción de Instrumento Ambiental'),
        (20, 'REMISION_MEDIO_AMBIENTE',    'Remisión a Medio Ambiente'),
        (21, 'RECEPCION_DICTAMEN',         'Recepción de Dictamen Ambiental'),
        (22, 'ELABORACION',                'Elaboración de Resolución'),
        (23, 'NOTIFICACION',               'Notificación de Resolución'),
        (24, 'PUBLICACION',                'Publicación de Resolución')
        ON CONFLICT (id) DO NOTHING
    """)

    # IDs 1-8; ID 9 (RECONOCIMIENTO_INTERESADO) lo inserta 8deef1de808e
    op.execute("""
        INSERT INTO public.tipos_fases (id, codigo, nombre) VALUES
        (1, 'ANALISIS_SOLICITUD',      'Análisis de Solicitud'),
        (2, 'CONSULTA_MINISTERIO',     'Consulta al Ministerio'),
        (3, 'COMPATIBILIDAD_AMBIENTAL','Compatibilidad Ambiental'),
        (4, 'CONSULTAS',               'Consultas a Organismos'),
        (5, 'INFORMACION_PUBLICA',     'Información Pública'),
        (6, 'FIGURA_AMBIENTAL_EXTERNA','Instrumento Ambiental Externo'),
        (7, 'AAU_AAUS_INTEGRADA',      'AAU/AAUS Integrada'),
        (8, 'RESOLUCION',              'Resolución')
        ON CONFLICT (id) DO NOTHING
    """)

    # ID 1: codigo='ANALIZAR' (corregido desde 'ANALISIS' de la BD de dev)
    op.execute("""
        INSERT INTO public.tipos_tareas (id, codigo, nombre) VALUES
        (1, 'ANALIZAR',     'Revisión técnica o jurídica de documentación con generación de informe'),
        (2, 'REDACTAR',     'Creación de documento administrativo (borrador)'),
        (3, 'FIRMAR',       'Firma autorizada del documento'),
        (4, 'NOTIFICAR',    'Comunicación a destinatario identificado'),
        (5, 'PUBLICAR',     'Publicación en medios oficiales (BOE, BOP, tablón, portal)'),
        (6, 'ESPERAR_PLAZO','Suspensión temporal con fecha límite o indefinida'),
        (7, 'INCORPORAR',   'Incorporación de documentación externa al sistema')
        ON CONFLICT (id) DO NOTHING
    """)

    # IDs 1-17; IDs 18-21 (combinados) los inserta a1b2c3d4e5f6
    op.execute("""
        INSERT INTO public.tipos_solicitudes (id, siglas, descripcion) VALUES
        (1,  'AAP',              'Autorización Administrativa Previa'),
        (2,  'AAC',              'Autorización Administrativa de Construcción'),
        (3,  'DUP',              'Declaración de Utilidad Pública'),
        (4,  'AE_PROVISIONAL',   'Autorización de Explotación Provisional para Pruebas'),
        (5,  'AE_DEFINITIVA',    'Autorización de Explotación Definitiva'),
        (6,  'AAT',              'Autorización de Transmisión de Titularidad'),
        (7,  'RAIPEE_PREVIA',    'Inscripción Previa en RAIPEE'),
        (8,  'RAIPEE_DEFINITIVA','Inscripción Definitiva en RAIPEE'),
        (9,  'RADNE',            'Inscripción en Registro de Autoconsumo'),
        (10, 'CIERRE',           'Autorización de Cierre de Instalación'),
        (11, 'DESISTIMIENTO',    'Desistimiento de la Solicitud'),
        (12, 'RENUNCIA',         'Renuncia de la Autorización'),
        (13, 'AMPLIACION_PLAZO', 'Ampliación de Plazo de Ejecución'),
        (14, 'INTERESADO',       'Condición de Interesado en el Expediente'),
        (15, 'RECURSO',          'Recurso Administrativo'),
        (16, 'CORRECCION_ERRORES','Corrección de Errores en Resolución'),
        (17, 'OTRO',             'Otro tipo de solicitud')
        ON CONFLICT (id) DO NOTHING
    """)

    # Poner cada secuencia por delante del último id insertado a mano (#849).
    # Insertar con `id` explícito no la mueve, así que la siguiente migración
    # que inserte SIN id recibe el valor 1 y choca con la fila ya sembrada.
    # En la BD de desarrollo nunca se vio porque estos datos entraron por otra
    # vía; en una instalación desde cero rompe el upgrade. Mismo defecto que
    # #637 corrigió solo para `normas`.
    for tabla in ('roles', 'tipos_expedientes', 'tipos_ia',
                  'tipos_resultados_fases', 'tipos_tramites', 'tipos_fases',
                  'tipos_tareas', 'tipos_solicitudes'):
        op.execute(
            f"SELECT setval(pg_get_serial_sequence('public.{tabla}', 'id'), "
            f"(SELECT COALESCE(MAX(id), 1) FROM public.{tabla}))"
        )


def downgrade():
    # Borrar solo las filas insertadas por esta migración.
    # Las filas añadidas por migraciones posteriores ya habrán sido eliminadas
    # por sus propios downgrade antes de llegar aquí.
    op.execute("DELETE FROM public.tipos_solicitudes WHERE id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17)")
    op.execute("DELETE FROM public.tipos_tareas WHERE id IN (1,2,3,4,5,6,7)")
    op.execute("DELETE FROM public.tipos_fases WHERE id IN (1,2,3,4,5,6,7,8)")
    op.execute("DELETE FROM public.tipos_tramites WHERE id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24)")
    op.execute("DELETE FROM public.tipos_resultados_fases WHERE id IN (1,2,3,4,5,6)")
    op.execute("DELETE FROM public.tipos_ia WHERE id IN (1,2,3,4,5)")
    op.execute("DELETE FROM public.tipos_expedientes WHERE id IN (1,2,3,4,5,6,7,8)")
    op.execute("DELETE FROM public.roles WHERE id IN (1,2,3,4)")
