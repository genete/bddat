from app import db

class Tramite(db.Model):
    """
    Contenedor organizativo de tareas dentro de una fase.
    
    PROPÓSITO:
        Representa actuaciones administrativas concretas (solicitud de informe,
        anuncio BOP, recepción de alegación, etc.) realizadas durante una fase.
        Agrupa tareas atómicas bajo un patrón procedimental.
    
    FILOSOFÍA:
        - Contenedor organizativo de tareas
        - Estructura mínima: Solo fechas, tipo y observaciones
        - Semántica en TIPO: Patrones de tareas viven en TIPOS_TRAMITES
        - Sin campos específicos: Remitentes, destinatarios, documentos viven en tareas
        - Fecha fin sugerida: Puede calcularse como MAX(TAREAS.FECHA_FIN), pero se registra manualmente
    
    CAMPO FASE_ID:
        - NOT NULL: Todo trámite pertenece a una fase
        - FK a FASES (public schema)
        - Contexto procedimental del trámite
    
    CAMPO TIPO_TRAMITE_ID:
        - NOT NULL: Define qué tipo de trámite es
        - FK a TIPOS_TRAMITES (estructura schema)
        - Determina patrón de tareas obligatorias
    
    CAMPO FECHA_INICIO:
        - NULLABLE: NULL = trámite planificado no iniciado
        - NOT NULL = trámite en curso o finalizado
    
    CAMPO FECHA_FIN:
        - NULLABLE: NULL = trámite pendiente o en curso
        - NOT NULL = trámite completado
        - Se deduce como MAX(TAREAS.FECHA_FIN), pero se registra manualmente
    
    ESTADOS DEDUCIBLES:
        - PENDIENTE: FECHA_INICIO IS NULL
        - EN_CURSO: FECHA_INICIO NOT NULL AND FECHA_FIN IS NULL
        - COMPLETADO: FECHA_FIN IS NOT NULL
    
    RELACIONES:
        - fase → FASES.id (FK CASCADE, fase contenedora)
        - tipo_tramite → TIPOS_TRAMITES.id (FK, definición del trámite)
        - tareas ← TAREAS.tramite_id (tareas realizadas en este trámite)
    
    REGLAS DE NEGOCIO:
        - No puede finalizarse si hay tareas sin finalizar
        - Secuencias determinadas por motor de reglas
        - Trámites pueden ejecutarse en paralelo dentro de una fase
        - FECHA_FIN debe ser >= FECHA_INICIO
    
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
        db.ForeignKey('tipos_tramites.id'),
        nullable=False,
        comment='FK a TIPOS_TRAMITES. Tipo de trámite'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de inicio del trámite. NULL = trámite planificado no iniciado'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización del trámite. NULL = trámite pendiente o en curso'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    fase = db.relationship('Fase', backref='tramites')
    tipo_tramite = db.relationship('TipoTramite', backref='tramites_instanciados')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tramite id={self.id} tipo={self.tipo_tramite_id} fase={self.fase_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Trámite {self.id} - {self.tipo_tramite.nombre if self.tipo_tramite else "Sin tipo"}'

    # --- Estados deducibles ---
    # La completitud se deduce de documentos en las tareas hijas, no de campos de fecha.

    @property
    def finalizado(self):
        """True si todas las tareas del trámite que requieren documento producido lo tienen.
        Devuelve True si no hay tareas (trámite vacío — estado transitorio)."""
        _requieren = {'INCORPORAR', 'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}
        tareas_pendientes = [
            t for t in self.tareas
            if t.tipo_tarea and t.tipo_tarea.codigo in _requieren
            and t.documento_producido_id is None
        ]
        return len(tareas_pendientes) == 0

    @property
    def planificado(self):
        """True si el trámite no tiene ninguna tarea aún."""
        return len(self.tareas) == 0

    @property
    def en_curso(self):
        """True si el trámite tiene tareas pero no está finalizado."""
        return not self.planificado and not self.finalizado
