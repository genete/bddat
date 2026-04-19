from app import db

class Fase(db.Model):
    """
    Contenedor temporal de trámites con objetivo procedimental concreto.
    
    PROPÓSITO:
        Representa cada fase concreta del procedimiento administrativo que atraviesa
        una solicitud. Es una instancia de un TIPO_FASE con datos temporales y
        resultado específicos.
    
    FILOSOFÍA:
        - Contenedor temporal de trámites
        - Campos mínimos: Solo metadatos administrativos (fechas, tipo, resultado)
        - Semántica en TIPO: La lógica procedimental vive en TIPOS_FASES
        - Resultado manual: El técnico evalúa y registra el resultado
        - Fecha fin sugerida: Puede calcularse como MAX(TRAMITES.FECHA_FIN), pero se registra manualmente
    
    CAMPO SOLICITUD_ID:
        - NOT NULL: Toda fase pertenece a una solicitud específica
        - FK a SOLICITUDES (public schema)
        - Cada fase se ejecuta dentro de una solicitud
    
    CAMPO TIPO_FASE_ID:
        - NOT NULL: Define qué tipo de fase es (ADMISIBILIDAD, CONSULTAS, etc.)
        - FK a TIPOS_FASES (estructura schema)
        - Determina trámites obligatorios según motor de reglas
    
    CAMPO FECHA_INICIO:
        - NULLABLE: NULL = fase planificada pero no iniciada
        - NOT NULL = fase en curso o finalizada
    
    CAMPO FECHA_FIN:
        - NULLABLE: NULL = fase pendiente o en curso
        - NOT NULL = fase completada
        - Se puede deducir como última fecha de trámites, pero se rellena manualmente
    
    CAMPO RESULTADO_FASE_ID:
        - NULLABLE: Se rellena al finalizar la fase
        - FK a TIPOS_RESULTADOS_FASES (estructura schema)
        - Obligatorio al establecer FECHA_FIN (validación interfaz)
    
    CAMPO DOCUMENTO_RESULTADO_ID:
        - NULLABLE: Documento oficial que formaliza el resultado
        - FK a DOCUMENTOS (public schema)
        - Documento clave (ej: informe favorable, resolución de inadmisión)
    
    ESTADOS DEDUCIBLES:
        - PENDIENTE: FECHA_INICIO IS NULL
        - EN_CURSO: FECHA_INICIO NOT NULL AND FECHA_FIN IS NULL
        - COMPLETADA: FECHA_FIN IS NOT NULL
        - EXITOSA: FECHA_FIN NOT NULL AND RESULTADO_FASE_ID indica éxito
    
    RELACIONES:
        - solicitud → SOLICITUDES.id (FK CASCADE, solicitud contenedora)
        - tipo_fase → TIPOS_FASES.id (FK, definición de la fase)
        - resultado_fase → TIPOS_RESULTADOS_FASES.id (FK, resultado)
        - documento_resultado → DOCUMENTOS.id (FK, documento formalizador)
        - tramites ← TRAMITES.fase_id (trámites de esta fase)
    
    REGLAS DE NEGOCIO:
        - No puede finalizarse si hay trámites sin finalizar
        - RESULTADO_FASE_ID obligatorio al establecer FECHA_FIN
        - Secuencias determinadas por motor de reglas
        - FECHA_FIN debe ser >= FECHA_INICIO
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Diseño minimalista mantenido.
    """
    __tablename__ = 'fases'
    __table_args__ = (
        db.Index('idx_fases_solicitud', 'solicitud_id'),
        db.Index('idx_fases_tipo', 'tipo_fase_id'),
        db.Index('idx_fases_resultado', 'resultado_fase_id'),
        db.Index('idx_fases_fechas', 'fecha_inicio', 'fecha_fin'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la fase'
    )
    
    solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id', ondelete='CASCADE'),
        nullable=False,
        comment='FK a SOLICITUDES. Solicitud a la que pertenece la fase'
    )
    
    tipo_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_fases.id'),
        nullable=False,
        comment='FK a TIPOS_FASES. Tipo de fase (ADMISIBILIDAD, CONSULTAS, etc.)'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio de la fase. NULL = fase planificada no iniciada'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización de la fase. NULL = fase pendiente o en curso'
    )
    
    resultado_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_resultados_fases.id'),
        nullable=True,
        comment='FK a TIPOS_RESULTADOS_FASES. Resultado de la fase al finalizar'
    )
    
    documento_resultado_id = db.Column(
        db.Integer,
        db.ForeignKey('public.documentos.id'),
        nullable=True,
        comment='FK a DOCUMENTOS. Documento oficial que formaliza el resultado'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    solicitud = db.relationship('Solicitud', backref='fases')
    tipo_fase = db.relationship('TipoFase', backref='fases_instanciadas')
    resultado_fase = db.relationship('TipoResultadoFase', backref='fases_con_resultado')
    documento_resultado = db.relationship('Documento', foreign_keys=[documento_resultado_id], backref='fases_resultado')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Fase id={self.id} tipo={self.tipo_fase_id} solicitud={self.solicitud_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Fase {self.id} - {self.tipo_fase.nombre if self.tipo_fase else "Sin tipo"}'

    # --- Estados deducibles ---
    # La completitud se deduce de documento_resultado_id y de los trámites hijos.
    # El resultado formal lo fija el técnico mediante resultado_fase_id + documento_resultado_id.

    @property
    def finalizada(self):
        """True si la fase tiene documento de resultado asociado (el técnico lo formalizó)."""
        return self.documento_resultado_id is not None

    @property
    def planificada(self):
        """True si la fase no tiene trámites aún."""
        return len(self.tramites) == 0

    @property
    def en_curso(self):
        """True si la fase tiene trámites pero no está finalizada."""
        return not self.planificada and not self.finalizada

    @property
    def finalizada_favorable(self):
        """True si la fase está finalizada con resultado favorable o favorable condicionado."""
        return (
            self.finalizada
            and self.resultado_fase_id is not None
            and self.resultado_fase.codigo in ('FAVORABLE', 'FAVORABLE_CONDICIONADO')
        )
