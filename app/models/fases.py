from app import db

class Fase(db.Model):
    """
    Fases procedimentales instanciadas en expedientes.
    
    PROPÓSITO:
        Representa cada fase concreta del procedimiento administrativo que atraviesa
        un expediente. Es una instancia de un TIPO_FASE con datos temporales y
        resultado específicos.
    
    FILOSOFÍA:
        - Instancia concreta de TIPOS_FASES (catálogo maestro)
        - Captura fechas de inicio/fin y resultado de la fase
        - Trazabilidad: Quién, cuándo, resultado
        - Resultado condiciona fases siguientes según motor de reglas
    
    CAMPO EXPEDIENTE_ID:
        - NOT NULL: Toda fase pertenece a un expediente
        - FK a EXPEDIENTES (public schema)
    
    CAMPO TIPO_FASE_ID:
        - NOT NULL: Define qué tipo de fase es (ADMISIBILIDAD, CONSULTAS, etc.)
        - FK a TIPOS_FASES (estructura schema)
        - Determina tareas y trámites obligatorios
    
    CAMPO FECHA_INICIO:
        - NOT NULL: Marca inicio de la fase
        - Determina plazos de resolución
    
    CAMPO FECHA_FIN:
        - NULLABLE: Fase en curso si es NULL
        - Marca finalización de la fase
    
    CAMPO RESULTADO_FASE_ID:
        - NULLABLE: Se rellena al finalizar la fase
        - FK a TIPOS_RESULTADOS_FASES (estructura schema)
        - Determina continuidad del procedimiento (avanza, paraliza, archiva)
    
    CAMPO USUARIO_ID:
        - NULLABLE: Técnico responsable de la fase
        - FK a USUARIOS (estructura schema)
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - tipo_fase → TIPOS_FASES.id (FK, definición de la fase)
        - resultado_fase → TIPOS_RESULTADOS_FASES.id (FK, resultado de la fase)
        - usuario → USUARIOS.id (FK, responsable)
        - tramites ← TRAMITES.fase_id (trámites realizados en esta fase)
    
    REGLAS DE NEGOCIO:
        - FECHA_FIN debe ser >= FECHA_INICIO
        - RESULTADO_FASE_ID solo se rellena si FECHA_FIN NOT NULL
        - Secuencia de fases condicionada por RESULTADO_FASE_ID según motor de reglas
        - Un expediente puede tener múltiples instancias del mismo TIPO_FASE
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla operacional estable.
    """
    __tablename__ = 'fases'
    __table_args__ = (
        db.Index('idx_fases_expediente', 'expediente_id'),
        db.Index('idx_fases_tipo', 'tipo_fase_id'),
        db.Index('idx_fases_usuario', 'usuario_id'),
        db.Index('idx_fases_fecha_inicio', 'fecha_inicio'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la fase'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', use_alter=True, name='fk_fases_expediente'),
        nullable=False,
        comment='FK a EXPEDIENTES. Expediente al que pertenece la fase'
    )
    
    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_fases.id'),
        nullable=False,
        comment='FK a TIPOS_FASES. Tipo de fase (ADMISIBILIDAD, CONSULTAS, etc.)'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=False,
        comment='Fecha de inicio de la fase'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización de la fase. NULL si está en curso'
    )
    
    resultado_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_resultados_fases.id'),
        nullable=True,
        comment='FK a TIPOS_RESULTADOS_FASES. Resultado de la fase al finalizar'
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.usuarios.id'),
        nullable=True,
        comment='FK a USUARIOS. Técnico responsable de la fase'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    expediente = db.relationship('Expediente', backref='fases')
    tipo_fase = db.relationship('TipoFase', backref='fases_instanciadas')
    resultado_fase = db.relationship('TipoResultadoFase', backref='fases_con_resultado')
    usuario = db.relationship('Usuario', backref='fases_responsable')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Fase id={self.id} tipo={self.tipo_fase_id} expediente={self.expediente_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Fase {self.id} - {self.tipo_fase.nombre if self.tipo_fase else "Sin tipo"}'
