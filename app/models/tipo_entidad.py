# app/models/tipo_entidad.py
"""
Modelo TipoEntidad - Catálogo de tipos de entidades del sistema.

Tabla: TIPOS_ENTIDADES (E_009)
Descripción: Define los tipos de entidades (ADMINISTRADO, ORGANISMO_PUBLICO, etc.)
             con sus capacidades de rol (solicitante, consultado, publicador)
"""

from app import db
from datetime import datetime


class TipoEntidad(db.Model):
    """
    Catálogo de tipos de entidades con definición de roles permitidos.
    
    Tipos definidos:
    - ADMINISTRADO: Personas físicas/jurídicas privadas
    - EMPRESA_SERVICIO_PUBLICO: Operadores infraestructuras críticas
    - ORGANISMO_PUBLICO: Administraciones públicas (Junta, AGE)
    - AYUNTAMIENTO: Corporaciones locales
    - DIPUTACION: Corporaciones provinciales
    """
    
    __tablename__ = 'tipos_entidades'
    
    # Campos
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    tabla_metadatos = db.Column(db.String(100), nullable=False)
    puede_ser_solicitante = db.Column(db.Boolean, nullable=False, default=False)
    puede_ser_consultado = db.Column(db.Boolean, nullable=False, default=False)
    puede_publicar = db.Column(db.Boolean, nullable=False, default=False)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Relaciones
    entidades = db.relationship('Entidad', back_populates='tipo_entidad', lazy='dynamic')
    
    def __repr__(self):
        return f'<TipoEntidad {self.codigo}: {self.nombre}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'tabla_metadatos': self.tabla_metadatos,
            'puede_ser_solicitante': self.puede_ser_solicitante,
            'puede_ser_consultado': self.puede_ser_consultado,
            'puede_publicar': self.puede_publicar,
            'descripcion': self.descripcion
        }
    
    @staticmethod
    def get_by_codigo(codigo):
        """Obtener tipo de entidad por código."""
        return TipoEntidad.query.filter_by(codigo=codigo).first()
    
    @staticmethod
    def get_solicitantes():
        """Obtener tipos que pueden ser solicitantes."""
        return TipoEntidad.query.filter_by(puede_ser_solicitante=True).all()
    
    @staticmethod
    def get_consultados():
        """Obtener tipos que pueden ser organismos consultados."""
        return TipoEntidad.query.filter_by(puede_ser_consultado=True).all()
    
    @staticmethod
    def get_publicadores():
        """Obtener tipos que pueden publicar (tablón/BOP)."""
        return TipoEntidad.query.filter_by(puede_publicar=True).all()
