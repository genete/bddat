from app import db

class Solicitud(db.Model):
    """
    Actos administrativos solicitados por el peticionario.
    
    PROPÓSITO:
        Representa actos administrativos individuales (AAP, AAC, DUP, etc.)
        solicitados por el promotor. Permite gestión individualizada de cada
        solicitud con su estado propio, independiente del expediente global.
    
    FILOSOFÍA:
        - Una solicitud puede tener MÚLTIPLES TIPOS simultáneamente (vía SOLICITUDES_TIPOS)
        - Motor de reglas aplica lógica sobre tipos individuales, no combinaciones
        - Cada solicitud es una instancia independiente con estado y trazabilidad propios
        - Permite secuencias temporales (MOD requiere AAC previa)
    
    CAMPO EXPEDIENTE_ID:
        - NOT NULL: Toda solicitud pertenece a un expediente
        - FK a EXPEDIENTES (public schema)
    
    CAMPO SOLICITUD_AFECTADA_ID:
        - NULLABLE: Solo para DESISTIMIENTO o RENUNCIA
        - Referencia a otra SOLICITUD previa que se desiste/renuncia
        - Permite rastrear dependencias entre solicitudes
    
    CAMPO FECHA_SOLICITUD:
        - NOT NULL: Fecha oficial de presentación
        - Determina plazos de resolución
        - Fecha administrativa con efectos jurídicos
    
    CAMPO ESTADO:
        - EN_TRAMITE: Solicitud activa en procedimiento
        - RESUELTA: Resolución firme emitida
        - DESISTIDA: Peticionario desiste
        - ARCHIVADA: Procedimiento finalizado sin resolución (caducidad, etc.)
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - solicitud_afectada → SOLICITUDES.id (FK self-referencia, para DESISTIMIENTO/RENUNCIA)
        - solicitudes_tipos ← SOLICITUDES_TIPOS.solicitudid (tipos de la solicitud)
    
    REGLAS DE NEGOCIO:
        - Tipos múltiples: Gestionados en tabla puente SOLICITUDES_TIPOS
        - DESISTIMIENTO/RENUNCIA: Requiere SOLICITUD_AFECTADA_ID NOT NULL
        - MOD: Debe existir AAC previa en el expediente (validar en interfaz)
        - Estado RESUELTA: Debe existir resolución asociada (validar)
    
    NOTAS DE VERSIÓN:
        v3.0: ELIMINADO tipo_solicitud_id (movido a SOLICITUDES_TIPOS N:M).
              AÑADIDO solicitud_afectada_id.
    """
    __tablename__ = 'solicitudes'
    __table_args__ = (
        db.Index('idx_solicitudes_expediente', 'expediente_id'),
        db.Index('idx_solicitudes_fecha', 'fecha_solicitud'),
        db.Index('idx_solicitudes_estado', 'estado'),
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado de la solicitud'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id', use_alter=True, name='fk_solicitudes_expediente'),
        nullable=False,
        comment='FK a EXPEDIENTES. Expediente al que pertenece la solicitud'
    )
    
    solicitud_afectada_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id'),
        nullable=True,
        comment='FK a SOLICITUDES. Para DESISTIMIENTO/RENUNCIA, solicitud que se desiste'
    )
    
    fecha_solicitud = db.Column(
        db.Date,
        nullable=False,
        comment='Fecha oficial de presentación de la solicitud'
    )
    
    estado = db.Column(
        db.String(20),
        default='EN_TRAMITE',
        nullable=False,
        comment='Estado: EN_TRAMITE, RESUELTA, DESISTIDA, ARCHIVADA'
    )
    
    observaciones = db.Column(
        db.String(2000),
        nullable=True,
        comment='Notas o comentarios adicionales del técnico'
    )
    
    # Relaciones
    expediente = db.relationship('Expediente', backref='solicitudes')
    solicitud_afectada = db.relationship('Solicitud', remote_side=[id], backref='solicitudes_dependientes')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Solicitud id={self.id} expediente={self.expediente_id} estado={self.estado}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Solicitud {self.id} - {self.estado}'
