# app/models/entidad_organismo_publico.py
"""
Modelo EntidadOrganismoPublico - Metadatos de organismos públicos.

Tabla: ENTIDADES_ORGANISMOS_PUBLICOS (O_017)
Descripción: Administraciones públicas (Junta, Ministerios, Confederaciones, ADIF, Defensa, AESA)
             Emiten informes. Excepcionalmente solicitantes (ej: depuradoras).
"""

from app import db


class EntidadOrganismoPublico(db.Model):
    """
    Metadatos específicos para organismos públicos.
    
    Ejemplos:
    - Consejerías Junta de Andalucía
    - Ministerios AGE
    - Confederaciones Hidrográficas
    - ADIF, Defensa, AESA, etc.
    
    Roles: Principalmente organismos consultados. Excepcionalmente solicitantes.
    Notificaciones: SIR/BandeJA (DIR3) como organismo, Notifica como solicitante.
    """
    
    __tablename__ = 'entidades_organismos_publicos'
    
    # Campos
    entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.entidades.id', ondelete='CASCADE'), 
        primary_key=True,
        comment='Referencia a entidad base (PK y FK con CASCADE)'
    )
    
    codigo_dir3 = db.Column(
        db.String(20), 
        nullable=True, 
        index=True,
        comment='Código DIR3 para notificaciones SIR/BandeJA'
    )
    
    legislatura = db.Column(
        db.String(50), 
        nullable=True, 
        index=True,
        comment='Legislatura asociada. Ej: "2019-2023", "2023-2027"'
    )
    
    fecha_desde = db.Column(
        db.Date, 
        nullable=True,
        comment='Fecha inicio vigencia del organismo'
    )
    
    fecha_hasta = db.Column(
        db.Date, 
        nullable=True,
        comment='Fecha fin vigencia del organismo (NULL si sigue activo)'
    )
    
    ambito = db.Column(
        db.String(50), 
        nullable=True, 
        index=True,
        comment='Ámbito del organismo: ESTATAL, AUTONOMICO, LOCAL'
    )
    
    tipo_organismo = db.Column(
        db.String(50), 
        nullable=True,
        comment='Tipo específico: Consejería, Ministerio, Confederación, Entidad Pública, etc.'
    )
    
    # Constraint CHECK para ámbito
    __table_args__ = (
        db.CheckConstraint(
            "ambito IN ('ESTATAL', 'AUTONOMICO', 'LOCAL')",
            name='chk_organismos_ambito'
        ),
        {'schema': 'public'}
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_organismo')
    
    def __repr__(self):
        return f'<EntidadOrganismo {self.entidad_id}: {self.ambito or "?"}>' 
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'codigo_dir3': self.codigo_dir3,
            'legislatura': self.legislatura,
            'fecha_desde': self.fecha_desde.isoformat() if self.fecha_desde else None,
            'fecha_hasta': self.fecha_hasta.isoformat() if self.fecha_hasta else None,
            'ambito': self.ambito,
            'tipo_organismo': self.tipo_organismo
        }
    
    @property
    def esta_vigente(self):
        """Indica si el organismo está actualmente vigente."""
        from datetime import date
        hoy = date.today()
        
        if self.fecha_desde and hoy < self.fecha_desde:
            return False
        
        if self.fecha_hasta and hoy > self.fecha_hasta:
            return False
        
        return True
    
    @staticmethod
    def buscar_por_dir3(codigo):
        """Buscar organismo por código DIR3."""
        return EntidadOrganismoPublico.query.filter_by(codigo_dir3=codigo).first()
    
    @staticmethod
    def listar_por_ambito(ambito):
        """Listar organismos por ámbito."""
        return EntidadOrganismoPublico.query.filter_by(ambito=ambito).all()
