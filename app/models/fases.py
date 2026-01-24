from app import db

class Fase(db.Model):
    """
    Contenedor temporal de trámites con objetivo procedimental concreto.
    
    PROPÓSITO:
        Representa una fase procedimental dentro de una solicitud administrativa.
        Agrupa trámites relacionados con un objetivo común (ADMISIBILIDAD, CONSULTAS,
        INFORMACION_PUBLICA, RESOLUCION, etc.).
    
    FILOSOFÍA:
        - Campos mínimos: solo metadatos administrativos (fechas, tipo, resultado)
        - Semántica en TIPO: lógica procedimental vive en TIPOS_FASES
        - Resultado manual: técnico evalúa y registra tras analizar documentos
        - Fecha fin sugestionable: puede calcularse como MAX(TRAMITES.fecha_fin)
    
    CAMPO SOLICITUD_ID:
        - NOT NULL: Toda fase pertenece a una solicitud
        - Define contexto administrativo de la fase
    
    CAMPO TIPO_FASE_ID:
        - NOT NULL: Define tipo procedimental según catálogo
        - Determina trámites obligatorios y secuencia administrativa
    
    CAMPO RESULTADO_FASE_ID:
        - Resultado o desenlace de la fase
        - NULLABLE: Solo se rellena al cerrar fase
        - Obligatorio cuando fecha_fin NOT NULL (validar en interfaz)
        - Valores: FAVORABLE, DESFAVORABLE, CONDICIONADO, etc.
    
    CAMPO DOCUMENTO_RESULTADO_ID:
        - Documento oficial que formaliza el resultado
        - NULLABLE: No todas las fases generan documento específico
        - Ejemplos: informe favorable, resolución de inadmisión
    
    CAMPOS FECHA_INICIO / FECHA_FIN:
        - fecha_inicio NULL = fase planificada no iniciada
        - fecha_fin NULL = fase pendiente o en curso
        - fecha_fin NOT NULL = fase completada (registro manual)
    
    ESTADOS DEDUCIBLES (no almacenados):
        - PENDIENTE: fecha_inicio IS NULL
        - EN_CURSO: fecha_inicio NOT NULL AND fecha_fin IS NULL
        - COMPLETADA: fecha_fin NOT NULL
        - EXITOSA: fecha_fin NOT NULL AND resultado indica éxito
    
    RELACIONES:
        - solicitud → SOLICITUDES.id (FK, solicitud contenedora)
        - tipo_fase → TIPOS_FASES.id (FK, tipo procedimental)
        - resultado_fase → TIPOS_RESULTADOS_FASES.id (FK opcional, resultado)
        - documento_resultado → DOCUMENTOS.id (FK opcional, documento resultado)
        - tramites ← TRAMITES.fase_id (trámites ejecutados en fase)
    
    REGLAS DE NEGOCIO:
        - No puede finalizarse si existen trámites asociados sin finalizar
        - resultado_fase_id obligatorio al establecer fecha_fin
        - Secuencias de fases determinadas por motor de reglas
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Diseño minimalista mantenido.
    """
    __tablename__ = 'fases'
    __table_args__ = (
        db.Index('idx_fases_solicitud', 'solicitud_id'),
        db.Index('idx_fases_tipo', 'tipo_fase_id'),
        db.Index('idx_fases_resultado', 'resultado_fase_id'),
        db.Index('idx_fases_fechas', 'fecha_inicio', 'fecha_fin'),
        {'schema': 'estructura'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la fase'
    )
    
    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.solicitudes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a SOLICITUDES. Solicitud a la que pertenece la fase'
    )
    
    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_fases.id'),
        nullable=False,
        comment='FK a TIPOS_FASES. Tipo procedimental de la fase'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio administrativo. NULL = fase planificada no iniciada'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización (registro manual). NULL = fase pendiente/en curso'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios del técnico sobre la fase'
    )
    
    resultado_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_resultados_fases.id'),
        nullable=True,
        comment='FK a TIPOS_RESULTADOS_FASES. Resultado de la fase (obligatorio si fecha_fin NOT NULL)'
    )
    
    documento_resultado_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.documentos.id'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento oficial que formaliza el resultado'
    )
    
    # Relaciones
    solicitud = db.relationship('Solicitud', backref='fases')
    tipo_fase = db.relationship('TipoFase', backref='fases')
    resultado_fase = db.relationship('TipoResultadoFase', backref='fases')
    documento_resultado = db.relationship('Documento', backref='fases_resultado')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Fase id={self.id} solicitud={self.solicitud_id} tipo={self.tipo_fase_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        estado = "Completada" if self.fecha_fin else ("En curso" if self.fecha_inicio else "Planificada")
        return f'Fase {self.id} - {estado}'
