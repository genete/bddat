from app import db

class Tarea(db.Model):
    """
    Unidad de trabajo registrable con entrada/salida documental.
    
    PROPÓSITO:
        Representa una tarea atómica dentro de un trámite administrativo.
        Cada tarea tiene entrada/salida documental clara y tipo definido
        (INCORPORAR, ANALISIS, REDACTAR, FIRMAR, NOTIFICAR, PUBLICAR, ESPERARPLAZO).
    
    FILOSOFÍA:
        - Relación unidireccional: TAREA → DOCUMENTO (no al revés)
        - Documento agnóstico: no sabe de tareas, tareas apuntan a documentos
        - Un documento, un productor: UNIQUE en documento_producido_id
        - Un documento, múltiples consumidores: N tareas pueden usar mismo documento_usado_id
    
    CAMPO TRAMITE_ID:
        - NOT NULL: Toda tarea pertenece a un trámite
        - Define contexto administrativo de la tarea
    
    CAMPO TIPO_TAREA_ID:
        - NOT NULL: Define tipo atómico (uno de los 7 tipos)
        - Determina semántica de entrada/salida documental
    
    CAMPO DOCUMENTO_USADO_ID:
        - Documento de entrada que consume la tarea
        - NULLABLE: Tipos sin entrada (INCORPORAR, ESPERARPLAZO)
        - Debe pertenecer al mismo expediente (validar en lógica)
    
    CAMPO DOCUMENTO_PRODUCIDO_ID:
        - Documento de salida que genera la tarea
        - NULLABLE: Solo NOT NULL cuando tarea finaliza
        - UNIQUE: Un documento solo puede ser producido por una tarea
    
    CAMPOS FECHA_INICIO / FECHA_FIN:
        - fecha_inicio NULL = tarea planificada no iniciada
        - fecha_fin NULL = tarea pendiente o en curso
        - fecha_fin NOT NULL = tarea completada
    
    CAMPO NOTAS:
        - Campo libre para información específica según tipo
        - Ejemplos: plazos (ESPERARPLAZO), referencia publicación (PUBLICAR)
    
    RELACIONES:
        - tramite → TRAMITES.id (FK, trámite contenedor)
        - tipo_tarea → TIPOS_TAREAS.id (FK, tipo atómico)
        - documento_usado → DOCUMENTOS.id (FK opcional, entrada)
        - documento_producido → DOCUMENTOS.id (FK UNIQUE opcional, salida)
    
    REGLAS DE NEGOCIO:
        - Antes de fecha_fin NOT NULL: verificar documento_producido_id si obligatorio
        - documento_usado_id debe pertenecer al mismo expediente
        - Un documento solo puede ser producido por una tarea (UNIQUE)
        - Varias tareas pueden usar el mismo documento de entrada
    
    NOTAS DE VERSIÓN:
        v3.0: AÑADIDOS documento_usado_id y documento_producido_id.
              Antes vivían en DOCUMENTOS (tarea_destino_id, tarea_origen_id).
    """
    __tablename__ = 'tareas'
    __table_args__ = (
        db.Index('idx_tareas_tramite', 'tramite_id'),
        db.Index('idx_tareas_tipo', 'tipo_tarea_id'),
        db.Index('idx_tareas_documento_usado', 'documento_usado_id'),
        db.Index('idx_tareas_fechas', 'fecha_inicio', 'fecha_fin'),
        {'schema': 'estructura'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la tarea'
    )
    
    tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tramites.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TRAMITES. Trámite al que pertenece la tarea'
    )
    
    tipo_tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_tareas.id'),
        nullable=False,
        comment='FK a TIPOS_TAREAS. Tipo atómico de la tarea'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio administrativo. NULL = tarea planificada no iniciada'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización. NULL = tarea pendiente/en curso'
    )
    
    notas = db.Column(
        db.String(2000),
        nullable=True,
        comment='Observaciones o información adicional específica del tipo'
    )
    
    documento_usado_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.documentos.id'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento de entrada. NULL para INCORPORAR/ESPERARPLAZO'
    )
    
    documento_producido_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.documentos.id'),
        nullable=True,
        unique=True,
        comment='FK UNIQUE a DOCUMENTOS. Documento de salida. Un documento = un productor'
    )
    
    # Relaciones
    tramite = db.relationship('Tramite', backref='tareas')
    tipo_tarea = db.relationship('TipoTarea', backref='tareas')
    documento_usado = db.relationship('Documento', foreign_keys=[documento_usado_id], backref='tareas_consumidoras')
    documento_producido = db.relationship('Documento', foreign_keys=[documento_producido_id], backref=db.backref('tarea_productora', uselist=False))
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tarea id={self.id} tramite={self.tramite_id} tipo={self.tipo_tarea_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        estado = "Finalizada" if self.fecha_fin else ("En curso" if self.fecha_inicio else "Planificada")
        return f'Tarea {self.id} - {estado}'
