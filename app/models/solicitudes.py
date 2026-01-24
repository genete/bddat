from app import db

class Solicitud(db.Model):
    """
    Actos administrativos solicitados dentro de un expediente.
    
    PROPÓSITO:
        Representa una solicitud concreta de acto administrativo (AAP, AAC, MOD, etc.)
        presentada en un expediente. Cada solicitud puede contener múltiples tipos
        simultáneamente (gestionados en tabla puente solicitudes_tipos).
    
    FILOSOFÍA:
        - Una solicitud pertenece a un expediente (relación directa)
        - No apunta a proyecto específico (se deduce de expediente)
        - Actúa sobre el estado del proyecto en su momento de presentación
        - Estado temporal se reconstruye por documentos vigentes en FECHA
    
    CAMPO EXPEDIENTE_ID:
        - Relación directa con expediente (nuevo en v3.0)
        - Elimina dependencia transitiva vía proyecto
        - NOT NULL: Toda solicitud pertenece a un expediente
    
    CAMPO FECHA:
        - Fecha administrativa oficial (registro de entrada)
        - NULLABLE: Puede estar en preparación antes de presentarse
        - Define momento temporal para reconstruir estado del proyecto
    
    CAMPO SOLICITUD_AFECTADA_ID:
        - Autorreferencia a otra solicitud
        - Solo para tipos DESISTIMIENTO o RENUNCIA
        - Apunta a la solicitud que se desiste/renuncia
        - NULLABLE: Solo se usa en estos tipos especiales
    
    CAMPO FECHA_FIN:
        - Fecha de finalización/archivo de la solicitud
        - Resolución, caducidad, archivo o cierre administrativo
        - NULL = solicitud en curso
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - tipos ↔ TIPOS_SOLICITUDES (N:M vía solicitudes_tipos)
        - solicitud_afectada → SOLICITUDES.id (autorreferencia, opcional)
    
    REGLAS DE NEGOCIO:
        - Una solicitud puede tener múltiples tipos (tabla puente)
        - Si tipo es DESISTIMIENTO/RENUNCIA → solicitud_afectada_id NOT NULL
        - Estado del proyecto se determina por documentos vigentes en FECHA
        - FECHA determina documentos aplicables en DOCUMENTOS_PROYECTO
    
    NOTAS DE VERSIÓN:
        v3.0: AÑADIDO expediente_id. ELIMINADO proyecto_id (se deduce del expediente).
    """
    __tablename__ = 'solicitudes'
    __table_args__ = {'schema': 'public'}
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado de la solicitud'
    )
    
    expediente_id = db.Column(
        db.Integer,
        db.ForeignKey('public.expedientes.id'),
        nullable=False,
        comment='FK a EXPEDIENTES. Expediente al que pertenece la solicitud'
    )
    
    tipo_solicitud_id = db.Column(
        db.Integer,
        db.ForeignKey('estructura.tipos_solicitudes.id'),
        nullable=False,
        comment='FK a TIPOS_SOLICITUDES. Tipo principal (campo legacy, usar relación tipos)'
    )
    
    fecha = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha administrativa de presentación (registro entrada). NULL si en preparación'
    )
    
    solicitud_afectada_id = db.Column(
        db.Integer,
        db.ForeignKey('public.solicitudes.id'),
        nullable=True,
        comment='FK autorreferencia. Solo para DESISTIMIENTO/RENUNCIA'
    )
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha de finalización/archivo. NULL si solicitud en curso'
    )
    
    # Relaciones
    expediente = db.relationship('Expediente', backref='solicitudes')
    
    tipos = db.relationship(
        'TipoSolicitud',
        secondary='public.solicitudes_tipos',
        backref=db.backref('solicitudes', lazy='dynamic')
    )
    
    solicitud_afectada = db.relationship(
        'Solicitud',
        remote_side=[id],
        backref='solicitudes_derivadas'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Solicitud id={self.id} expediente={self.expediente_id}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        estado = "En curso" if not self.fecha_fin else f"Finalizada {self.fecha_fin}"
        return f'Solicitud {self.id} - {estado}'
