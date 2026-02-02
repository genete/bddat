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
    
    NOTA: La provincia se obtiene indirectamente vía entidad.municipio.provincia
          (la diputación tiene sede en la capital provincial).
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
        nullable=False, 
        index=True,
        comment='Código DIR3 oficial para notificaciones SIR como organismo consultado. Formato: 1-2 letras + 7-8 números. Ej: L01110002'
    )
    
    email_publicacion_bop = db.Column(
        db.String(255), 
        nullable=True,
        comment='Email para solicitar publicaciones en BOP. Ej: boletin@bopcadiz.org. Método tradicional: correo con datos pagador + texto'
    )
    
    observaciones = db.Column(
        db.Text, 
        nullable=True,
        comment='Notas sobre procedimientos publicación, tarifas, plataformas alternativas, contactos específicos. Ej: "Concesionaria: Asociación Prensa Cádiz"'
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_diputacion')
    
    def __repr__(self):
        return f'<EntidadDiputacion {self.entidad_id}: DIR3={self.codigo_dir3}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'codigo_dir3': self.codigo_dir3,
            'email_publicacion_bop': self.email_publicacion_bop,
            'observaciones': self.observaciones
        }
    
    @property
    def tiene_email_bop(self):
        """Indica si tiene email para publicación en BOP."""
        return bool(self.email_publicacion_bop)
    
    @property
    def provincia(self):
        """
        Obtiene la provincia indirectamente vía municipio de la sede.
        La diputación tiene su sede en la capital provincial.
        """
        if self.entidad and self.entidad.municipio:
            return self.entidad.municipio.provincia
        return None
    
    @staticmethod
    def buscar_por_dir3(codigo):
        """Buscar diputación por código DIR3."""
        return EntidadDiputacion.query.filter_by(codigo_dir3=codigo).first()
