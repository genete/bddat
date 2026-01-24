from app import db

class Tramite(db.Model):
    """
    Contenedor organizativo de tareas dentro de una fase.
    
    PROPÓSITO:
        Representa un trámite administrativo dentro de una fase procedimental.
        Agrupa tareas relacionadas con una actuación administrativa concreta
        (SOLICITUD_INFORME, ANUNCIO_BOP, RECEPCION_ALEGACION, etc.).
    
    FILOSOFÍA:
        - Estructura mínima: solo fechas, tipo y observaciones
        - Semántica en TIPO: patrones de tareas viven en TIPOS_TRAMITES
        - Sin campos específicos: remitentes, destinatarios y documentos viven en tareas
        - Fecha fin sugestionable: puede calcularse como MAX(TAREAS.fecha_fin)
    
    CAMPO FASE_ID:
        - NOT NULL: Todo trámite pertenece a una fase
        - Define contexto procedimental del trámite
    
    CAMPO TIPO_TRAMITE_ID:
        - NOT NULL: Define tipo de actuación administrativa
        - Determina patrón de tareas esperadas (definido en motor de reglas)
    
    CAMPOS FECHA_INICIO / FECHA_FIN:
        - fecha_inicio NULL = trámite planificado no iniciado
        - fecha_fin NULL = trámite pendiente o en curso
        - fecha_fin NOT NULL = trámite completado (registro manual)
    
    ESTADOS DEDUCIBLES (no almacenados):
        - PENDIENTE: fecha_inicio IS NULL
        - EN_CURSO: fecha_inicio NOT NULL AND fecha_fin IS NULL
        - COMPLETADO: fecha_fin NOT NULL
    
    PATRONES DE TAREAS:
        Cada TIPO_TRAMITE_ID define secuencia esperada (ejemplos):
        - SOLICITUD_INFORME: REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO
        - RECEPCION_INFORME: INCORPORAR → ANALISIS
        - ANUNCIO_BOP: REDACTAR → FIRMAR → NOTIFICAR → ESPERARPLAZO → INCORPORAR → ESPERARPLAZO
        
        Patrones se combinan según reglas de negocio (no hardcoded).
    
    RELACIONES:
        - fase → FASES.id (FK, fase contenedora)
        - tipo_tramite → TIPOS_TRAMITES.id (FK, tipo de actuación)
        - tareas ← TAREAS.tramite_id (tareas ejecutadas en trámite)
    
    REGLAS DE NEGOCIO:
        - No puede finalizarse si existen tareas asociadas sin finalizar
        - Secuencias determinadas por motor de reglas
        - Trámites pueden ejecutarse en paralelo dentro de una fase
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Diseño minimalista mantenido.
    """
    __tablename__ = 'tramites'
    __table_args__ = (
        db.Index('idx_tramites_fase', 'fase_id'),
        db.Index('idx_tramites_tipo', 'tipo_tramite_id'),
        db.Index('idx_tramites_fechas', 'fecha_inicio', 'fecha_fin'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado del trámite'
    )
    
    fase_id = db.Column(
        db.Integer,
        db.ForeignKey('public.fases.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a FASES. Fase a la que pertenece el trámite'
    )
    
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_tramites.id'),
        nullable=False,
        comment='FK a TIPOS_TRAMITES. Tipo de actuación administrativa'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio administrativo. NULL = trámite planificado no iniciado'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización (registro manual). NULL = trámite pendiente/en curso'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios del técnico sobre el trámite'
    )
    
    # Relaciones
    fase = db.relationship('Fase', backref='tramites')
    tipo_tramite = db.relationship('TipoTramite', backref='tramites')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tramite id={self.id} fase={self.fase_id} tipo={self.tipo_tramite_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        estado = "Completado" if self.fecha_fin else ("En curso" if self.fecha_inicio else "Planificado")
        return f'Trámite {self.id} - {estado}'
