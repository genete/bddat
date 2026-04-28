from app import db

class Fase(db.Model):
    """
    Contenedor temporal de trámites con objetivo procedimental concreto.

    PROPÓSITO:
        Representa cada fase concreta del procedimiento administrativo que atraviesa
        una solicitud. Es una instancia de un TIPO_FASE con datos y resultado específicos.

    FILOSOFÍA:
        - Contenedor temporal de trámites
        - Campos mínimos: Solo tipo, resultado y documento de formalización
        - Semántica en TIPO: La lógica procedimental vive en TIPOS_FASES
        - Resultado manual: El técnico evalúa y registra el resultado
        - Sin campos de fecha propios: ver §2.bis DISEÑO_FECHAS_PLAZOS.md

    CAMPO SOLICITUD_ID:
        - NOT NULL: Toda fase pertenece a una solicitud específica
        - FK a SOLICITUDES (public schema)

    CAMPO TIPO_FASE_ID:
        - NOT NULL: Define qué tipo de fase es (ADMISIBILIDAD, CONSULTAS, etc.)
        - FK a TIPOS_FASES (estructura schema)
        - Determina trámites obligatorios según motor de reglas

    CAMPO RESULTADO_FASE_ID:
        - NULLABLE: Se rellena al formalizar el cierre de la fase
        - FK a TIPOS_RESULTADOS_FASES (estructura schema)

    CAMPO DOCUMENTO_RESULTADO_ID:
        - NULLABLE: Documento oficial que formaliza el resultado
        - FK a DOCUMENTOS (public schema)
        - Su presencia define que la fase está FINALIZADA
        - La transición NULL→NOT NULL está sujeta a validación por motor de reglas

    ESTADOS DEDUCIBLES (properties, no columna):
        - PLANIFICADA: len(tramites) == 0
        - EN_CURSO: tramites presentes, no todos finalizados, sin documento de resultado
        - PDTE_CIERRE: todos los trámites finalizados, pero documento_resultado_id IS NULL
        - FINALIZADA: documento_resultado_id IS NOT NULL

    RELACIONES:
        - solicitud → SOLICITUDES.id (FK CASCADE, solicitud contenedora)
        - tipo_fase → TIPOS_FASES.id (FK, definición de la fase)
        - resultado_fase → TIPOS_RESULTADOS_FASES.id (FK, resultado)
        - documento_resultado → DOCUMENTOS.id (FK, documento formalizador)
        - tramites ← TRAMITES.fase_id (trámites de esta fase)

    REGLAS DE NEGOCIO:
        - No puede finalizarse si hay trámites sin finalizar (motor de reglas)
        - Transición NULL→NOT NULL en resultado_fase_id/documento_resultado_id evaluada por motor
        - Secuencias de fases determinadas por motor de reglas
    """
    __tablename__ = 'fases'
    __table_args__ = (
        db.Index('idx_fases_solicitud', 'solicitud_id'),
        db.Index('idx_fases_tipo', 'tipo_fase_id'),
        db.Index('idx_fases_resultado', 'resultado_fase_id'),
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
    
    resultado_fase_id = db.Column(
        db.Integer,
        db.ForeignKey('tipos_resultados_fases.id'),
        nullable=True,
        comment='FK a TIPOS_RESULTADOS_FASES. Solo relevante en fases finalizadoras (es_finalizadora=True). Las fases intermedias cierran por documento_resultado_id; su resultado_fase_id debe quedar NULL.'
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
    def pdte_cierre(self):
        """True si todos los trámites están finalizados pero falta documento_resultado_id.
        La transición de este estado a FINALIZADA requiere acción manual del técnico,
        validada por el motor (ver §311 P3 DISEÑO_MOTOR_AGNOSTICO.md)."""
        return (
            not self.planificada
            and not self.finalizada
            and all(t.finalizado for t in self.tramites)
        )

    @property
    def en_curso(self):
        """True si hay trámites en ejecución (no todos finalizados) y la fase no está cerrada."""
        return not self.planificada and not self.finalizada and not self.pdte_cierre

    @property
    def finalizada_favorable(self):
        """True si la fase está finalizada con resultado favorable o favorable condicionado."""
        return (
            self.finalizada
            and self.resultado_fase_id is not None
            and self.resultado_fase.codigo in ('FAVORABLE', 'FAVORABLE_CONDICIONADO')
        )

    @property
    def estado(self):
        """Estado de la fase: PLANIFICADA | EN_CURSO | PDTE_CIERRE | FINALIZADA."""
        if self.finalizada:
            return 'FINALIZADA'
        if self.pdte_cierre:
            return 'PDTE_CIERRE'
        if self.planificada:
            return 'PLANIFICADA'
        return 'EN_CURSO'
