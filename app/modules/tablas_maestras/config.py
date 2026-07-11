"""Configuración de los 5 catálogos estructurales ESFTT administrados por #171.

Regla común: el campo identificador (`id_field`) se fija al crear y no se
edita nunca — capa 2 (reglas_motor/condiciones, datos) puede referenciar el
literal de CUALQUIER fila, no solo las que aparecen en
`app/checks/catalogo_requerido.py` (que solo cubre capa 3, Python
hardcodeado). `protegidos` es por tanto informativo (por qué esta fila
concreta además tiene comportamiento especial en Python), no lo que decide
la inmutabilidad — esa aplica a las 5 tablas por igual.

Ninguna fila es borrable (ni física ni lógicamente): son catálogos
referenciados por FK NOT NULL desde tablas operacionales (fases/tramites/
tareas) o consumidos como valor de motor (expediente/solicitud). `activo`
queda aplazado (pendiente de decisión, ver docs/CONTEXTO_ACTUAL.md #171).
"""
from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite

# Cada entrada de 'campos': (nombre_campo, etiqueta, tipo_input, requerido, maxlen)
# tipo_input ∈ {'text', 'textarea', 'bool'}

TIPOS = {
    'expediente': {
        'model':        TipoExpediente,
        'singular':     'Tipo de expediente',
        'plural':       'Tipos de expediente',
        'icon':         'fa-folder-tree',
        'id_field':     'tipo',
        'id_label':     'Tipo',
        'id_maxlen':    100,
        'campos': [
            ('descripcion',         'Descripción',         'text',     False, 200),
            ('nombre_en_plantilla', 'Nombre en plantilla', 'textarea', False, None),
        ],
        'permite_alta':      True,
        'aviso_combinacion': False,
        'protegidos':   set(),  # sin acoplamiento a capa 3 (#171, verificado)
    },
    'solicitud': {
        'model':        TipoSolicitud,
        'singular':     'Tipo de solicitud',
        'plural':       'Tipos de solicitud',
        'icon':         'fa-file-signature',
        'id_field':     'siglas',
        'id_label':     'Siglas',
        'id_maxlen':    100,
        'campos': [
            ('descripcion',         'Descripción',         'text',     True,  200),
            ('nombre_en_plantilla', 'Nombre en plantilla', 'textarea', False, None),
        ],
        'permite_alta':      True,
        'aviso_combinacion': True,  # combinaciones separadas por '+' (solicitudes.py)
        'protegidos':   set(REGISTROS_REQUERIDOS.get('TipoSolicitud', [])),
    },
    'fase': {
        'model':        TipoFase,
        'singular':     'Tipo de fase',
        'plural':       'Tipos de fase',
        'icon':         'fa-diagram-project',
        'id_field':     'codigo',
        'id_label':     'Código',
        'id_maxlen':    50,
        'campos': [
            ('nombre',              'Nombre',              'text',     True,  200),
            ('abrev',               'Abreviatura',         'text',     False, 20),
            ('nombre_en_plantilla', 'Nombre en plantilla', 'textarea', False, None),
            ('es_finalizadora',     'Fase finalizadora',   'bool',     False, None),
        ],
        'permite_alta':      True,
        'aviso_combinacion': False,
        'protegidos':   set(REGISTROS_REQUERIDOS.get('TipoFase', [])),
    },
    'tramite': {
        'model':        TipoTramite,
        'singular':     'Tipo de trámite',
        'plural':       'Tipos de trámite',
        'icon':         'fa-list-check',
        'id_field':     'codigo',
        'id_label':     'Código',
        'id_maxlen':    50,
        'campos': [
            ('nombre',              'Nombre',              'text',     True,  200),
            ('abrev',               'Abreviatura',         'text',     False, 20),
            ('nombre_en_plantilla', 'Nombre en plantilla', 'textarea', False, None),
        ],
        'permite_alta':      True,
        'aviso_combinacion': False,
        'protegidos':   set(REGISTROS_REQUERIDOS.get('TipoTramite', [])),
        # Editor anidado de tramites_tareas/tramites_tareas_documentos: #171 fase 2,
        # no incluido en este primer corte.
    },
    'tarea': {
        'model':        TipoTarea,
        'singular':     'Tipo de tarea',
        'plural':       'Tipos de tarea',
        'icon':         'fa-list-ol',
        'id_field':     'codigo',
        'id_label':     'Código',
        'id_maxlen':    50,
        'campos': [
            ('nombre',              'Nombre',              'text',     True,  200),
            ('abrev',               'Abreviatura',         'text',     False, 20),
            ('nombre_en_plantilla', 'Nombre en plantilla', 'textarea', False, None),
        ],
        # Catálogo cerrado (#171): estado_dominio.py/cola_administrativo.py/
        # invariantes_esftt.py asumen exactamente estos 4 códigos. Sin alta.
        'permite_alta':      False,
        'aviso_combinacion': False,
        'protegidos':   set(REGISTROS_REQUERIDOS.get('TipoTarea', [])),
    },
}
