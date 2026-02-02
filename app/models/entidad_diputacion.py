# app/models/entidad_diputacion.py
"""
Modelo EntidadDiputacion - Metadatos de diputaciones provinciales.

Tabla: ENTIDADES_DIPUTACIONES (O_019)
Descripción: Corporaciones provinciales.
             Roles: solicitante ocasional, organismo consultado, publicador BOP.
"""

from app import db


class EntidadDiputacion(db.Model):
    """
    Metadatos específicos para diputaciones provinciales.
    
    Roles:
    - Solicitante ocasional (construyen para ayuntamientos)
    - Organismo consultado (informes)
    - Publicador BOP (Boletín Oficial Provincial)
    
    Notificaciones: SIR (DIR3) como organismo, Notifica como solicitante.
    """
    
    __tablename__ = 'entidades_diputaciones'
    
    # Campos
    entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('entidades.id', ondelete='CASCADE'), 
        primary_key=True,
        comment='Referencia a entidad base (PK y FK con CASCADE)'
    )
    
    codigo_dir3 = db.Column(
        db.String(20), 
        unique=True, 
        nullable=True, 
        index=True,
        comment='Código DIR3 para notificaciones SIR'
    )
    
    provincia_id = db.Column(
        db.Integer, 
        db.ForeignKey('estructura.provincias.id'), 
        unique=True, 
        nullable=True, 
        index=True,
        comment='Provincia a la que pertenece (relación 1:1, una provincia = una diputación)'
    )
    
    email_publicacion_bop = db.Column(
        db.String(120), 
        nullable=True,
        comment='Email para envío de publicaciones al BOP'
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_diputacion')
    provincia = db.relationship('Provincia', backref='diputacion')
    
    def __repr__(self):
        return f'<EntidadDiputacion {self.entidad_id}: Prov {self.provincia_id or "?"}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'codigo_dir3': self.codigo_dir3,
            'provincia_id': self.provincia_id,
            'email_publicacion_bop': self.email_publicacion_bop
        }
    
    @property
    def tiene_dir3(self):
        """Indica si tiene código DIR3."""
        return bool(self.codigo_dir3)
    
    @staticmethod
    def buscar_por_dir3(codigo):
        """Buscar diputación por código DIR3."""
        return EntidadDiputacion.query.filter_by(codigo_dir3=codigo).first()
    
    @staticmethod
    def buscar_por_provincia(provincia_id):
        """Buscar diputación por provincia."""
        return EntidadDiputacion.query.filter_by(provincia_id=provincia_id).first()
