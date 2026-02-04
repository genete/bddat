# app/models/entidad_ayuntamiento.py
"""
Modelo EntidadAyuntamiento - Metadatos de ayuntamientos.

Tabla: ENTIDADES_AYUNTAMIENTOS (O_018)
Descripción: Corporaciones locales.
             Múltiples roles: solicitante ocasional, organismo consultado, publicador tablón.
"""

from app import db


class EntidadAyuntamiento(db.Model):
    """
    Metadatos específicos para ayuntamientos.
    
    Roles:
    - Solicitante ocasional (instalaciones municipales)
    - Organismo consultado (informes)
    - Publicador (tablón edictos municipal)
    
    Notificaciones: SIR (DIR3) como organismo, Notifica como solicitante.
    """
    
    __tablename__ = 'entidades_ayuntamientos'
    __table_args__ = {'schema': 'public'}
    
    # Campos
    entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.entidades.id', ondelete='CASCADE'), 
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
    
    observaciones = db.Column(
        db.Text,
        nullable=True,
        comment='Observaciones sobre el ayuntamiento'
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_ayuntamiento')
    
    def __repr__(self):
        dir3 = f'DIR3:{self.codigo_dir3}' if self.codigo_dir3 else 'SIN DIR3'
        return f'<EntidadAyuntamiento {self.entidad_id}: {dir3}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'codigo_dir3': self.codigo_dir3,
            'observaciones': self.observaciones
        }
    
    @property
    def tiene_dir3(self):
        """Indica si tiene código DIR3."""
        return bool(self.codigo_dir3)
    
    @staticmethod
    def buscar_por_dir3(codigo):
        """Buscar ayuntamiento por código DIR3."""
        return EntidadAyuntamiento.query.filter_by(codigo_dir3=codigo).first()
