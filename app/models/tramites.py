from app import db

class Tramite(db.Model):
    """
    Trámites administrativos realizados dentro de fases.
    
    PROPÓSITO:
        Representa actuaciones administrativas concretas (solicitud de informe,
        anuncio BOP, notificación, etc.) realizadas durante una fase.
        Agrupa tareas atómicas bajo un patrón procedimental.
    
    FILOSOFÍA:
        - Instancia concreta de TIPOS_TRAMITES (catálogo maestro)
        - Agrupa N tareas atómicas bajo un patrón procedimental
        - Trazabilidad: Quién, cuándo, cómo
        - Motor de reglas define patrón de tareas según TIPO_TRAMITE_ID
    
    CAMPO FASE_ID:
        - NOT NULL: Todo trámite pertenece a una fase
        - FK a FASES (public schema)
        - Contexto procedimental del trámite
    
    CAMPO TIPO_TRAMITE_ID:
        - NOT NULL: Define qué tipo de trámite es
        - FK a TIPOS_TRAMITES (estructura schema)
        - Determina patrón de tareas obligatorias
    
    CAMPO FECHA_INICIO:
        - NOT NULL: Marca inicio del trámite
        - Determina plazos
    
    CAMPO FECHA_FIN:
        - NULLABLE: Trámite en curso si es NULL
        - Marca finalización del trámite
    
    CAMPO USUARIO_ID:
        - NULLABLE: Técnico responsable del trámite
        - FK a USUARIOS (estructura schema)
    
    RELACIONES:
        - fase → FASES.id (FK, fase contenedora)
        - tipo_tramite → TIPOS_TRAMITES.id (FK, definición del trámite)
        - usuario → USUARIOS.id (FK, responsable)
        - tareas ← TAREAS.tramite_id (tareas realizadas en este trámite)
    
    REGLAS DE NEGOCIO:
        - FECHA_FIN debe ser >= FECHA_INICIO
        - Un trámite puede tener múltiples tareas
        - Patrón de tareas definido por TIPO_TRAMITE_ID en motor de reglas
    
    NOTAS DE VERSIÓN:
        v3.0: Sin cambios estructurales. Tabla operacional estable.
    """
    __tablename__ = 'tramites'
    __table_args__ = (
        db.Index('idx_tramites_fase', 'fase_id'),
        db.Index('idx_tramites_tipo', 'tipo_tramite_id'),
        db.Index('idx_tramites_usuario', 'usuario_id'),
        db.Index('idx_tramites_fecha_inicio', 'fecha_inicio'),
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
        db.ForeignKey('public.fases.id'),
        nullable=False,
        comment='FK a FASES. Fase a la que pertenece el trámite'
    )
    
    tipo_tramite_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_tramites.id'),
        nullable=False,
        comment='FK a TIPOS_TRAMITES. Tipo de trámite'
    )
    
    fecha_inicio = db.Column(
        db.Date,
        nullable=False,
        comment='Fecha de inicio del trámite'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización del trámite. NULL si está en curso'
    )
    
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.usuarios.id'),
        nullable=True,
        comment='FK a USUARIOS. Técnico responsable del trámite'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    fase = db.relationship('Fase', backref='tramites')
    tipo_tramite = db.relationship('TipoTramite', backref='tramites_instanciados')
    usuario = db.relationship('Usuario', backref='tramites_responsable')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Tramite id={self.id} tipo={self.tipo_tramite_id} fase={self.fase_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Trámite {self.id} - {self.tipo_tramite.nombre if self.tipo_tramite else "Sin tipo"}'
