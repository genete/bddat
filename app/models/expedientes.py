from app import db

class Expediente(db.Model):
    """
    Tabla principal de expedientes de tramitación administrativa.
    
    PROPÓSITO:
        Representa cada expediente único de tramitación de instalaciones de alta
        tensión. Es la entidad raíz que agrupa todo el proceso administrativo:
        proyecto, solicitudes, documentos, fases y trámites.
    
    FILOSOFÍA:
        - Expediente = contenedor administrativo único por instalación
        - Relación 1:1 con PROYECTO (un expediente, un proyecto técnico)
        - El proyecto evoluciona mediante documentos versionados
        - NUMERO_AT es identificador legacy del sistema anterior
        - Titular actual almacenado en TITULAR_ID (desnormalizado para rendimiento)
    
    CARACTERÍSTICAS:
        - Único en toda la organización (identificado por NUMERO_AT)
        - Puede estar sin responsable (huérfano) hasta asignación por supervisor
        - Clasificado por tipo (determina procedimiento aplicable)
        - Puede ser heredado del sistema anterior (datos incompletos)
        - Tiene un titular actual (snapshot del histórico)
    
    CAMPOS ESPECIALES:
        NUMERO_AT:
            - Número correlativo del sistema legacy
            - NO es el ID técnico, sino identificador administrativo
            - Único en la organización
            - Usado en referencias y búsquedas
        
        RESPONSABLE_ID:
            - NULL permitido: expediente "huérfano" sin asignar
            - Supervisor puede asignar según carga de trabajo o especialización
            - Una vez asignado, el tramitador tiene permisos completos
        
        HEREDADO:
            - TRUE: Expediente migrado del sistema anterior
            - FALSE/NULL: Expediente gestionado completamente en este sistema
            - Los heredados pueden tener información incompleta
        
        PROYECTO_ID:
            - UNIQUE constraint garantiza relación 1:1
            - Un expediente tiene exactamente un proyecto técnico
            - El proyecto evoluciona mediante documentos en DOCUMENTOS_PROYECTO
        
        TITULAR_ID:
            - FK a ENTIDADES (nullable)
            - Snapshot del titular actual del expediente
            - Desnormalización para rendimiento (evita JOIN con histórico)
            - NULL cuando expediente sin titular asignado (situación anómala transitoria)
            - Al cambiar titular:
              1. Se crea registro en HISTORICO_TITULARES_EXPEDIENTE
              2. Se actualiza TITULAR_ID con el nuevo valor
            - Histórico completo en HISTORICO_TITULARES_EXPEDIENTE
    
    RELACIONES:
        - responsable → USUARIOS (tramitador asignado, nullable)
        - tipo_expediente → TIPOS_EXPEDIENTES (clasificación normativa)
        - proyecto → PROYECTOS (relación 1:1, proyecto técnico único)
        - titular → ENTIDADES (titular actual, nullable, snapshot)
        - historico_titulares ← HISTORICO_TITULARES_EXPEDIENTE (1:N, histórico completo)
        - solicitudes ← SOLICITUDES (1:N, múltiples actos administrativos)
        - documentos ← DOCUMENTOS (1:N, pool de archivos del expediente)
    
    REGLAS DE NEGOCIO:
        1. Expediente puede crearse sin responsable (huérfano)
        2. NUMERO_AT debe ser único en la organización
        3. PROYECTO_ID es obligatorio y único (relación 1:1)
        4. TITULAR_ID es snapshot del titular actual (puede ser NULL temporalmente)
        5. El tipo de expediente determina:
           - Procedimientos aplicables
           - Solicitudes permitidas
           - Fases obligatorias
           - Organismos a consultar
    
    NOTAS DE VERSIÓN:
        v3.0: Añadido PROYECTO_ID (relación 1:1). Antes el proyecto
              apuntaba al expediente, ahora es inverso para mayor claridad.
        v3.1: RESPONSABLE_ID ahora nullable para permitir expedientes huérfanos.
        v3.2: Añadido TITULAR_ID (snapshot) + tabla HISTORICO_TITULARES_EXPEDIENTE
              para gestión completa de cambios de titularidad.
    """
    __tablename__ = 'expedientes'
    __table_args__ = (
        db.Index('idx_expedientes_numero_at', 'numero_at'),
        db.Index('idx_expedientes_responsable', 'responsable_id'),
        db.Index('idx_expedientes_tipo', 'tipo_expediente_id'),
        db.Index('idx_expedientes_proyecto', 'proyecto_id'),
        db.Index('idx_expedientes_titular', 'titular_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador técnico único autogenerado'
    )
    
    numero_at = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
        comment='Número administrativo del expediente (formato legacy, único en organización)'
    )
    
    responsable_id = db.Column(
        db.Integer,
        db.ForeignKey('public.usuarios.id'),
        nullable=True,  # ← CAMBIO: permite NULL para expedientes huérfanos
        comment='FK a USUARIOS. Tramitador asignado con permisos de gestión completa. NULL = huérfano sin asignar'
    )
    
    tipo_expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_expedientes.id'),
        comment='FK a TIPOS_EXPEDIENTES. Clasificación normativa que define procedimiento'
    )
    
    heredado = db.Column(
        db.Boolean,
        comment='TRUE si proviene del sistema anterior (datos incompletos posibles)'
    )
    
    proyecto_id = db.Column(
        db.Integer,
        db.ForeignKey('public.proyectos.id'),
        nullable=False,
        unique=True,
        comment='FK a PROYECTOS. Relación 1:1, un expediente tiene exactamente un proyecto'
    )
    
    titular_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id'),
        nullable=True,
        comment='FK a ENTIDADES. Titular actual del expediente (snapshot del histórico). NULL = sin titular asignado (anómalo transitorio)'
    )
    
    # Relaciones SQLAlchemy
    responsable = db.relationship(
        'Usuario',
        foreign_keys=[responsable_id],
        backref='expedientes_responsable'
    )
    
    proyecto = db.relationship(
        'Proyecto',
        foreign_keys=[proyecto_id],
        backref=db.backref('expediente', uselist=False)
    )
    
    tipo_expediente = db.relationship(
        'TipoExpediente',
        foreign_keys=[tipo_expediente_id],
        backref='expedientes'
    )
    
    titular = db.relationship(
        'Entidad',
        foreign_keys=[titular_id],
        lazy='joined',  # ← Carga eager por defecto (titular se usa casi siempre)
        backref='expedientes_como_titular'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Expediente id={self.id} numero_at={self.numero_at}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Expediente AT-{self.numero_at}'
