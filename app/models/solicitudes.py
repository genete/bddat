from app import db

class Solicitud(db.Model):
    """
    Actos administrativos solicitados por el peticionario.
    
    PROPÓSITO:
        Representa actos administrativos individuales (AAP, AAC, DUP, etc.)
        solicitados por el promotor. Permite gestión individualizada de cada
        solicitud con su estado propio, independiente del expediente global.
    
    FILOSOFÍA:
        - Una solicitud puede tener MÚTIPLES TIPOS simultáneamente (vía SOLICITUDES_TIPOS)
        - Motor de reglas aplica lógica sobre tipos individuales, no combinaciones
        - Cada solicitud es una instancia independiente con estado y trazabilidad propios
        - Permite secuencias temporales (MOD requiere AAC previa)
    
    CAMPO EXPEDIENTE_ID:
        - NOT NULL: Toda solicitud pertenece a un expediente
        - FK a EXPEDIENTES (public schema)
    
    CAMPO ENTIDAD_ID:
        - NOT NULL: Identifica al solicitante (promotor/titular)
        - FK a ENTIDADES (public schema)
        - Puede diferir del titular del expediente (cambios de titularidad)
        - Permite rastrear quién solicitó cada acto administrativo
    
    CAMPO SOLICITUD_AFECTADA_ID:
        - NULLABLE: Solo para DESISTIMIENTO o RENUNCIA
        - Referencia a otra SOLICITUD previa que se desiste/renuncia
        - Permite rastrear dependencias entre solicitudes
    
    CAMPO FECHA_SOLICITUD:
        - NOT NULL: Fecha oficial de presentación
        - Determina plazos de resolución
        - Fecha administrativa con efectos jurídicos
    
    CAMPO FECHA_FIN:
        - NULLABLE: Fecha real de finalización de la solicitud
        - Puede ser rellenada manualmente o automáticamente por el sistema
        - Fuente de verdad alternativa vs. "todas las fases finalizadas"
        - Protección contra confusiones: solicitud cerrada con fases pendientes
        - Si NULL: solicitud aún en curso
    
    CAMPO ESTADO:
        - EN_TRAMITE: Solicitud activa en procedimiento
        - RESUELTA: Resolución firme emitida
        - DESISTIDA: Peticionario desiste
        - ARCHIVADA: Procedimiento finalizado sin resolución (caducidad, etc.)
    
    RELACIONES:
        - expediente → EXPEDIENTES.id (FK, expediente contenedor)
        - entidad → ENTIDADES.id (FK, solicitante)
        - solicitud_afectada → SOLICITUDES.id (FK self-referencia, para DESISTIMIENTO/RENUNCIA)
        - solicitudes_tipos ← SOLICITUDES_TIPOS.solicitud_id (tipos de la solicitud)
    
    REGLAS DE NEGOCIO:
        - Tipos múltiples: Gestionados en tabla puente SOLICITUDES_TIPOS
        - DESISTIMIENTO/RENUNCIA: Requiere SOLICITUD_AFECTADA_ID NOT NULL
        - MOD: Debe existir AAC previa en el expediente (validar en interfaz)
        - Estado RESUELTA: Debe existir resolución asociada (validar)
        - FECHA_FIN: Si estado = RESUELTA/DESISTIDA/ARCHIVADA, debería tener fecha_fin
    
    NOTAS DE VERSIÓN:
        v3.0: ELIMINADO tipo_solicitud_id (movido a SOLICITUDES_TIPOS N:M).
              AÑADIDO solicitud_afectada_id.
        v3.1: AÑADIDO entidad_id (solicitante).
              AÑADIDO fecha_fin (finalización real).
              AÑADIDO properties: activa, es_desistimiento_o_renuncia.
    """
    __tablename__ = 'solicitudes'
    __table_args__ = (
        db.Index('idx_solicitudes_expediente', 'expediente_id'),
        db.Index('idx_solicitudes_entidad', 'entidad_id'),
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
    
    entidad_id = db.Column(
        db.Integer,
        db.ForeignKey('public.entidades.id', use_alter=True, name='fk_solicitudes_entidad'),
        nullable=False,
        comment='FK a ENTIDADES. Solicitante (promotor/titular) de la solicitud'
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
    
    fecha_fin = db.Column(
        db.Date,
        nullable=True,
        comment='Fecha real de finalización de la solicitud. NULL si aún en curso'
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
    entidad = db.relationship('Entidad', backref='solicitudes')
    solicitud_afectada = db.relationship('Solicitud', remote_side=[id], backref='solicitudes_dependientes')
    
    # Properties
    @property
    def activa(self):
        """
        Determina si la solicitud está activa (en curso).
        
        Returns:
            bool: True si estado es EN_TRAMITE, False en caso contrario.
        
        Uso:
            if solicitud.activa:
                # Solicitud aún en procedimiento
        """
        return self.estado == 'EN_TRAMITE'
    
    @property
    def es_desistimiento_o_renuncia(self):
        """
        Determina si esta solicitud es un desistimiento o renuncia.
        
        Returns:
            bool: True si tiene solicitud_afectada_id (referencia a otra solicitud).
        
        Regla de negocio:
            Solo solicitudes de DESISTIMIENTO/RENUNCIA tienen solicitud_afectada_id.
        
        Uso:
            if solicitud.es_desistimiento_o_renuncia:
                solicitud_original = solicitud.solicitud_afectada
        """
        return self.solicitud_afectada_id is not None
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Solicitud id={self.id} expediente={self.expediente_id} entidad={self.entidad_id} estado={self.estado}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'Solicitud {self.id} - {self.estado}'
