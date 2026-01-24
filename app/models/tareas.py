from app import db

class Tarea(db.Model):
    """
    Tareas atómicas que componen los trámites administrativos.
    
    PROPÓSITO:
        Representa operaciones atómicas (enviar, recibir, publicar, revisar, etc.)
        que se realizan dentro de un trámite. Son las unidades mínimas de trabajo
        que no pueden descomponerse en operaciones más simples.
    
    FILOSOFÍA:
        - Instancia concreta de TIPOS_TAREAS (7 tipos atómicos)
        - Operación mínima indivisible
        - Puede consumir documentos (documento_usado_id)
        - Puede generar documentos (documento_producido_id)
        - Trazabilidad: Quién, cuándo, cómo
    
    CAMPO TRAMITE_ID:
        - NOT NULL: Toda tarea pertenece a un trámite
        - FK a TRAMITES (public schema)
        - Contexto procedimental de la tarea
    
    CAMPO TIPO_TAREA_ID:
        - NOT NULL: Define qué tipo de tarea atómica es
        - FK a TIPOS_TAREAS (estructura schema)
        - Solo 7 tipos atómicos posibles
    
    CAMPO DOCUMENTO_USADO_ID:
        - NULLABLE: Documento que se usa como input
        - FK a DOCUMENTOS (public schema)
        - Ej: Documento que se envía, revisa, publica
    
    CAMPO DOCUMENTO_PRODUCIDO_ID:
        - NULLABLE: Documento que se genera como output
        - FK a DOCUMENTOS (public schema)
        - Ej: Documento generado por la tarea (informe, resolución)
    
    CAMPO FECHA_TAREA:
        - NOT NULL: Fecha de realización de la tarea
        - Fecha administrativa con efectos jurídicos
    
    CAMPO USUARIO_ID:
        - NULLABLE: Usuario que realizó la tarea
        - FK a USUARIOS (estructura schema)
    
    RELACIONES:
        - tramite → TRAMITES.id (FK, trámite contenedor)
        - tipo_tarea → TIPOS_TAREAS.id (FK, tipo atómico)
        - documento_usado → DOCUMENTOS.id (FK, input)
        - documento_producido → DOCUMENTOS.id (FK, output)
        - usuario → USUARIOS.id (FK, responsable)
    
    REGLAS DE NEGOCIO:
        - DOCUMENTO_USADO_ID y DOCUMENTO_PRODUCIDO_ID pueden ser ambos NULL
        - Tipo de tarea determina si requiere/genera documentos
        - FECHA_TAREA debe estar dentro del rango del trámite
    
    NOTAS DE VERSIÓN:
        v3.0: RENOMBRADO documento_origen_id → documento_usado_id.
              RENOMBRADO documento_destino_id → documento_producido_id.
    """
    __tablename__ = 'tareas'
    __table_args__ = (
        db.Index('idx_tareas_tramite', 'tramite_id'),
        db.Index('idx_tareas_tipo', 'tipo_tarea_id'),
        db.Index('idx_tareas_usuario', 'usuario_id'),
        db.Index('idx_tareas_fecha', 'fecha_tarea'),
        db.Index('idx_tareas_documento_usado', 'documento_usado_id'),
        db.Index('idx_tareas_documento_producido', 'documento_producido_id'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la tarea'
    )
    
    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('public.tramites.id'),
        nullable=False,
        comment='FK a TRAMITES. Trámite al que pertenece la tarea'
    )
    
    tipo_tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_tareas.id'),
        nullable=False,
        comment='FK a TIPOS_TAREAS. Tipo de tarea atómica (7 tipos posibles)'
    )
    
    documento_usado_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento usado como input de la tarea'
    )
    
    documento_producido_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento generado como output de la tarea'
    )
    
    fecha_tarea = db.Column(
        db.Date,
        nullable=False,
        comment='Fecha de realización de la tarea'
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.usuarios.id'),
        nullable=True,
        comment='FK a USUARIOS. Usuario que realizó la tarea'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    tramite = db.relationship('Tramite', backref='tareas')
    tipo_tarea = db.relationship('TipoTarea', backref='tareas_instanciadas')
    documento_usado = db.relationship('Documento', foreign_keys=[documento_usado_id], backref='tareas_que_usan')
    documento_producido = db.relationship('Documento', foreign_keys=[documento_producido_id], backref='tareas_que_producen')
    usuario = db.relationship('Usuario', backref='tareas_realizadas')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tarea id={self.id} tipo={self.tipo_tarea_id} tramite={self.tramite_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Tarea {self.id} - {self.tipo_tarea.nombre if self.tipo_tarea else "Sin tipo"}'
