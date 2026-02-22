# app/models/autorizados_titular.py
"""
Modelo AutorizadoTitular - Relación N:N entre titulares y autorizados.

Tabla: AUTORIZADOS_TITULAR (O_020)
Descripción: Gestiona autorizaciones entre administrados. Un titular puede
             autorizar a otros administrados para actuar en su nombre.
"""

from app import db
from sqlalchemy.orm import validates
from datetime import datetime


class AutorizadoTitular(db.Model):
    """
    Tabla N:N que registra autorizaciones entre administrados.
    
    Permite que un titular (administrado) autorice a otro administrado
    para actuar en su nombre en la tramitación de expedientes.
    
    Características:
    - Borrado lógico: campo `activo` para revocar sin perder historial
    - Observaciones flexibles: permite metadatos sin modificar schema
    - Autoautorización implícita: el titular puede actuar por sí mismo sin entrada en BD
    - Validación en Python: ambas entidades deben ser administrados
    """
    
    __tablename__ = 'autorizados_titular'
    
    # Campos
    id = db.Column(
        db.Integer, 
        primary_key=True,
        comment='Identificador único del registro de autorización'
    )
    
    titular_entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.entidades.id', ondelete='CASCADE'), 
        nullable=False,
        index=True,
        comment='Administrado titular que concede la autorización. Debe tener entrada en entidades_administrados'
    )
    
    autorizado_entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.entidades.id', ondelete='CASCADE'), 
        nullable=False,
        index=True,
        comment='Administrado autorizado para representar al titular. Debe tener entrada en entidades_administrados'
    )
    
    activo = db.Column(
        db.Boolean, 
        nullable=False, 
        default=True,
        index=True,
        comment='Indica si la autorización está vigente. FALSE = revocada/suspendida'
    )
    
    observaciones = db.Column(
        db.Text, 
        nullable=True,
        comment='Notas libres del tramitador. Usos: ámbito (expediente específico/general), vigencia temporal, motivo desactivación, tipo de poder'
    )
    
    created_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        comment='Fecha y hora de creación del registro'
    )
    
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        comment='Fecha y hora de última actualización'
    )
    
    # Constraints
    __table_args__ = (
        # No puede autorizarse a sí mismo (autoautorización es implícita)
        db.CheckConstraint(
            'titular_entidad_id != autorizado_entidad_id',
            name='chk_no_autoautorizacion'
        ),
        # Evitar duplicados
        db.UniqueConstraint(
            'titular_entidad_id', 
            'autorizado_entidad_id',
            name='uq_titular_autorizado'
        ),
        # Índice compuesto para consultas frecuentes
        db.Index('idx_titular_activo', 'titular_entidad_id', 'activo'),
        {'schema': 'public'}
    )
    
    # Relaciones
    titular = db.relationship(
        'Entidad',
        foreign_keys=[titular_entidad_id],
        backref=db.backref('autorizaciones_otorgadas', lazy='dynamic')
    )
    
    autorizado = db.relationship(
        'Entidad',
        foreign_keys=[autorizado_entidad_id],
        backref=db.backref('autorizaciones_recibidas', lazy='dynamic')
    )
    
    def __repr__(self):
        estado = 'ACTIVA' if self.activo else 'INACTIVA'
        titular_nombre = self.titular.nombre_completo if self.titular else '?'
        autorizado_nombre = self.autorizado.nombre_completo if self.autorizado else '?'
        return f'<AutorizadoTitular {self.id}: {titular_nombre} → {autorizado_nombre} [{estado}]>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'id': self.id,
            'titular_entidad_id': self.titular_entidad_id,
            'titular_nombre': self.titular.nombre_completo if self.titular else None,
            'titular_cif_nif': self.titular.cif_nif if self.titular else None,
            'autorizado_entidad_id': self.autorizado_entidad_id,
            'autorizado_nombre': self.autorizado.nombre_completo if self.autorizado else None,
            'autorizado_cif_nif': self.autorizado.cif_nif if self.autorizado else None,
            'activo': self.activo,
            'observaciones': self.observaciones,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @validates('titular_entidad_id')
    def validate_titular(self, key, titular_id):
        """Valida que el titular exista y esté activo."""
        from app.models.entidad import Entidad
        entidad = Entidad.query.get(titular_id)
        if not entidad:
            raise ValueError(f"Entidad titular {titular_id} no existe")
        if not entidad.activo:
            raise ValueError(f"{entidad.nombre_completo} (ID {titular_id}) no está activa")
        return titular_id

    @validates('autorizado_entidad_id')
    def validate_autorizado(self, key, autorizado_id):
        """Valida que el autorizado exista y esté activo."""
        from app.models.entidad import Entidad
        entidad = Entidad.query.get(autorizado_id)
        if not entidad:
            raise ValueError(f"Entidad autorizada {autorizado_id} no existe")
        if not entidad.activo:
            raise ValueError(f"{entidad.nombre_completo} (ID {autorizado_id}) no está activa")
        return autorizado_id
    
    def revocar(self, motivo=None):
        """
        Revoca la autorización (borrado lógico).
        
        Args:
            motivo (str, optional): Razón de la revocación. Se añade a observaciones.
        """
        self.activo = False
        
        if motivo:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            revocacion_nota = f"\n[REVOCADA {timestamp}] {motivo}"
            
            if self.observaciones:
                self.observaciones += revocacion_nota
            else:
                self.observaciones = revocacion_nota.strip()
    
    def restaurar(self, motivo=None):
        """
        Restaura una autorización revocada.
        
        Args:
            motivo (str, optional): Razón de la restauración. Se añade a observaciones.
        """
        self.activo = True
        
        if motivo:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            restauracion_nota = f"\n[RESTAURADA {timestamp}] {motivo}"
            
            if self.observaciones:
                self.observaciones += restauracion_nota
            else:
                self.observaciones = restauracion_nota.strip()
    
    @staticmethod
    def puede_actuar_como(entidad_id, titular_id):
        """
        Comprueba si una entidad puede actuar en nombre de un titular.
        
        Regla: El titular SIEMPRE puede actuar por sí mismo (autoautorización implícita).
        Para otros autorizados, debe existir autorización activa en BD.
        
        Args:
            entidad_id (int): ID de la entidad que intenta actuar
            titular_id (int): ID del titular
        
        Returns:
            bool: True si puede actuar, False en caso contrario
        """
        # Autoautorización implícita
        if entidad_id == titular_id:
            return True
        
        # Buscar autorización activa
        autorizacion = AutorizadoTitular.query.filter_by(
            titular_entidad_id=titular_id,
            autorizado_entidad_id=entidad_id,
            activo=True
        ).first()
        
        return autorizacion is not None
    
    @staticmethod
    def obtener_autorizados_de_titular(titular_id, solo_activos=True):
        """
        Obtiene todos los autorizados de un titular.
        
        Args:
            titular_id (int): ID del titular
            solo_activos (bool): Si True, solo devuelve autorizaciones activas
        
        Returns:
            list[AutorizadoTitular]: Lista de autorizaciones
        """
        query = AutorizadoTitular.query.filter_by(titular_entidad_id=titular_id)
        
        if solo_activos:
            query = query.filter_by(activo=True)
        
        return query.order_by(AutorizadoTitular.created_at.desc()).all()
    
    @staticmethod
    def obtener_titulares_de_autorizado(autorizado_id, solo_activos=True):
        """
        Obtiene todos los titulares de un autorizado.
        
        Args:
            autorizado_id (int): ID del autorizado
            solo_activos (bool): Si True, solo devuelve autorizaciones activas
        
        Returns:
            list[AutorizadoTitular]: Lista de autorizaciones
        """
        query = AutorizadoTitular.query.filter_by(autorizado_entidad_id=autorizado_id)
        
        if solo_activos:
            query = query.filter_by(activo=True)
        
        return query.order_by(AutorizadoTitular.created_at.desc()).all()
    
    @staticmethod
    def crear_autorizacion(titular_id, autorizado_id, observaciones=None):
        """
        Crea una nueva autorización.
        
        Args:
            titular_id (int): ID del titular
            autorizado_id (int): ID del autorizado
            observaciones (str, optional): Observaciones iniciales
        
        Returns:
            AutorizadoTitular: Nueva autorización creada
        
        Raises:
            ValueError: Si los IDs son iguales o si alguna entidad no es administrado
        """
        if titular_id == autorizado_id:
            raise ValueError(
                "No se puede crear autorización explícita del titular sobre sí mismo. "
                "La autoautorización es implícita."
            )
        
        # Las validaciones se ejecutarán automáticamente via @validates
        autorizacion = AutorizadoTitular(
            titular_entidad_id=titular_id,
            autorizado_entidad_id=autorizado_id,
            observaciones=observaciones,
            activo=True
        )
        
        return autorizacion
