from app import db

class Documento(db.Model):
    """
    Pool puro de archivos físicos asociados a expedientes.
    
    PROPÓSITO:
        Almacena metadatos de documentos físicos pertenecientes a expedientes.
        Tabla agnóstica: solo conoce su expediente, todas las demás relaciones
        (proyectos, tareas) se definen externamente apuntando hacia aquí.
    
    FILOSOFÍA:
        - El documento es una entidad pura del expediente
        - Solo tiene UN FK: expediente_id
        - Es completamente agnóstico respecto a:
          * Qué tarea lo produjo (se define en TAREAS.documento_producido_id)
          * Qué tareas lo usan (se define en TAREAS.documento_usado_id)
          * Si es parte de un proyecto (se define en DOCUMENTOS_PROYECTO)
        - Pool único de documentos por expediente, relaciones viven fuera
    
    CAMPO EXPEDIENTE_ID:
        - ÚNICO FK del documento
        - NOT NULL: Todo documento pertenece a un expediente
    
    CAMPO FECHA_ADMINISTRATIVA:
        - NO es la fecha del archivo físico (metadatos filesystem)
        - ES la fecha con efectos administrativos y legales
        - Ejemplos: fecha registro entrada, firma, notificación, publicación
        - Determina plazos, efectos jurídicos y secuencia administrativa
        - NOT NULL: Todo documento tiene fecha administrativa
    
    CAMPO URL:
        - Ruta o URL del archivo físico
        - Sistema de archivos local o repositorio documental
        - NOT NULL: Todo documento tiene ubicación física
    
    CAMPO HASH_MD5:
        - Verificación de integridad del archivo
        - Detección de duplicados
        - NULLABLE: Se calcula tras almacenamiento
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - documentos_proyecto ← DOCUMENTOS_PROYECTO.documento_id (tabla puente con proyectos)
        - tareas_producidas ← TAREAS.documento_producido_id (tareas que lo generaron)
        - tareas_usadas ← TAREAS.documento_usado_id (tareas que lo utilizan)
    
    REGLAS DE NEGOCIO:
        - Un documento pertenece a UN expediente
        - Un documento puede estar en N proyectos (vía DOCUMENTOS_PROYECTO)
        - Un documento puede ser producido por N tareas
        - Un documento puede ser usado por N tareas
        - FECHA_ADMINISTRATIVA determina vigencia en DOCUMENTOS_PROYECTO
    
    NOTAS DE VERSIÓN:
        v3.0: RENOMBRADO fecha_documento → fecha_administrativa.
              ELIMINADOS: tarea_origen_id, tarea_destino_id, proyecto_id.
    """
    __tablename__ = 'documentos'
    __table_args__ = (
        db.Index('idx_documentos_expediente', 'expediente_id'),
        db.Index('idx_documentos_fecha_administrativa', 'fecha_administrativa'),
        db.Index('idx_documentos_hash', 'hash_md5'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del documento'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', use_alter=True, name='fk_documentos_expediente'),
        nullable=False,
        comment='FK a EXPEDIENTES. ÚNCO FK del documento (tabla agnóstica)'
    )
    
    url = db.Column(
        db.String(500),
        nullable=False,
        comment='Ruta o URL del archivo físico en sistema de archivos o repositorio'
    )
    
    tipo_contenido = db.Column(
        db.String(50),
        nullable=True,
        comment='Tipo MIME del archivo (ej: application/pdf)'
    )
    
    fecha_administrativa = db.Column(
        db.Date,
        nullable=False,
        comment='Fecha con valor administrativo oficial (firma, registro, publicación)'
    )
    
    asunto = db.Column(
        db.String(500),
        nullable=True,
        comment='Descripción o asunto del documento'
    )
    
    origen = db.Column(
        db.String(100),
        nullable=True,
        comment='Procedencia del documento (EXTERNO, INTERNO, ORGANISMO_X, etc.)'
    )
    
    prioridad = db.Column(
        db.Integer,
        default=0,
        nullable=True,
        comment='Nivel de prioridad o relevancia (default: 0)'
    )
    
    nombre_display = db.Column(
        db.String(200),
        nullable=True,
        comment='Nombre legible para mostrar en interfaz'
    )
    
    hash_md5 = db.Column(
        db.String(32),
        nullable=True,
        comment='Hash MD5 para verificación de integridad y detección de duplicados'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relación con expediente
    expediente = db.relationship('Expediente', backref='documentos')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Documento id={self.id} expediente={self.expediente_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre_display or f'Documento {self.id}'
