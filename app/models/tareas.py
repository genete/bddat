from app import db

class Tarea(db.Model):
    """
    Unidad de trabajo registrable con entrada/salida documental.
    
    PROPÓSITO:
        Representa operaciones atómicas (incorporar, analizar, redactar, firmar,
        notificar, publicar, esperar plazo) que se realizan dentro de un trámite.
        Son las unidades mínimas de trabajo con entrada/salida documental clara.
    
    FILOSOFÍA:
        - Unidad de trabajo registrable con entrada/salida clara
        - Relación unidireccional: TAREA → DOCUMENTO (no al revés)
        - Documento agnóstico: El documento no sabe de tareas
        - Un documento, un productor: Solo una tarea puede producir un documento (UNIQUE)
        - Un documento, múltiples consumidores: Varias tareas pueden usar el mismo documento
    
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
        - Ej: Documento que se analiza, firma, publica
        - NULL para INCORPORAR, ESPERARPLAZO
    
    CAMPO DOCUMENTO_PRODUCIDO_ID:
        - NULLABLE: Documento que se genera como output
        - FK a DOCUMENTOS (public schema)
        - UNIQUE: Un documento solo puede ser producido por una tarea
        - Ej: Documento generado (informe, resolución, justificante)
        - NULL para ESPERARPLAZO o tareas no finalizadas
    
    CAMPO FECHA_INICIO:
        - NULLABLE: NULL = tarea planificada no iniciada
        - NOT NULL = tarea en curso o finalizada
    
    CAMPO FECHA_FIN:
        - NULLABLE: NULL = tarea pendiente o en curso
        - NOT NULL = tarea completada
        - Determina cierre administrativo
    
    CAMPO NOTAS:
        - Campo libre para información adicional
        - Puede contener datos específicos según tipo:
          * Plazos (ESPERARPLAZO)
          * Referencia publicación (PUBLICAR)
          * Remitente (INCORPORAR)
    
    SEMÁNTICA SEGÚN TIPO:
        - INCORPORAR: usado=NULL, producido=obligatorio
        - ANALISIS: usado=obligatorio, producido=obligatorio
        - REDACTAR: usado=opcional, producido=obligatorio
        - FIRMAR: usado=obligatorio, producido=obligatorio
        - NOTIFICAR: usado=obligatorio, producido=obligatorio
        - PUBLICAR: usado=obligatorio, producido=obligatorio
        - ESPERARPLAZO: usado=NULL, producido=NULL
    
    RELACIONES:
        - tramite → TRAMITES.id (FK CASCADE, trámite contenedor)
        - tipo_tarea → TIPOS_TAREAS.id (FK, tipo atómico)
        - documento_usado → DOCUMENTOS.id (FK, input)
        - documento_producido → DOCUMENTOS.id (FK UNIQUE, output)
    
    REGLAS DE NEGOCIO:
        - Antes de FECHA_FIN NOT NULL: Verificar documento_producido para tipos que lo requieren
        - documento_usado y documento_producido deben pertenecer al mismo expediente
        - UNIQUE en documento_producido_id garantiza un solo productor
    
    NOTAS DE VERSIÓN:
        v3.0: AÑADIDO documento_usado_id (antes en DOCUMENTOS.tarea_destino_id).
              AÑADIDO documento_producido_id (antes en DOCUMENTOS.tarea_origen_id).
    """
    __tablename__ = 'tareas'
    __table_args__ = (
        db.Index('idx_tareas_tramite', 'tramite_id'),
        db.Index('idx_tareas_tipo', 'tipo_tarea_id'),
        db.Index('idx_tareas_fechas', 'fecha_inicio', 'fecha_fin'),
        db.Index('idx_tareas_documento_usado', 'documento_usado_id'),
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
        db.ForeignKey('public.tramites.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a TRAMITES. Trámite al que pertenece la tarea'
    )
    
    tipo_tarea_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_tareas.id'),
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
        unique=True,
        comment='FK UNIQUE a DOCUMENTOS. Documento generado como output de la tarea'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio de la tarea. NULL = tarea planificada no iniciada'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización de la tarea. NULL = tarea pendiente o en curso'
    )
    
    notas = db.Column(
        db.String(2000),
        nullable=True,
        comment='Observaciones o información adicional (plazos, referencia, remitente, etc.)'
    )
    
    # Relaciones
    tramite = db.relationship('Tramite', backref='tareas')
    tipo_tarea = db.relationship('TipoTarea', backref='tareas_instanciadas')
    documento_usado = db.relationship('Documento', foreign_keys=[documento_usado_id], backref='tareas_que_usan')
    documento_producido = db.relationship('Documento', foreign_keys=[documento_producido_id], backref='tarea_productora')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tarea id={self.id} tipo={self.tipo_tarea_id} tramite={self.tramite_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Tarea {self.id} - {self.tipo_tarea.nombre if self.tipo_tarea else "Sin tipo"}'
