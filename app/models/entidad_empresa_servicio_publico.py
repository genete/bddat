# app/models/entidad_empresa_servicio_publico.py
"""
Modelo EntidadEmpresaServicioPublico - Metadatos de empresas operadoras de servicios públicos.

Tabla: ENTIDADES_EMPRESAS_SERVICIO_PUBLICO (O_016)
Descripción: Operadores de infraestructuras críticas (Enagas, E-Distribución, REE, etc.)
             Pueden ser solicitantes Y emitir informes sobre afecciones.
"""

from app import db


class EntidadEmpresaServicioPublico(db.Model):
    """
    Metadatos específicos para empresas de servicio público.
    
    Ejemplos:
    - Enagas (gas)
    - E-Distribución (electricidad)
    - REE (Red Eléctrica Española)
    - Consorcios de Aguas
    
    Roles: Solicitantes ocasionales + Organismos consultados (informes técnicos)
    Notificaciones: SIR/BandeJA (DIR3) como organismo, Notifica como solicitante
    """
    
    __tablename__ = 'entidades_empresas_servicio_publico'
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
        comment='Código DIR3 para notificaciones SIR (opcional, no todas las empresas tienen)'
    )
    
    # Relación inversa con Entidad
    entidad = db.relationship('Entidad', back_populates='datos_empresa')
    
    def __repr__(self):
        dir3 = f'DIR3:{self.codigo_dir3}' if self.codigo_dir3 else 'SIN DIR3'
        return f'<EntidadEmpresa {self.entidad_id}: {dir3}>'
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'entidad_id': self.entidad_id,
            'codigo_dir3': self.codigo_dir3
        }
    
    @property
    def tiene_dir3(self):
        """Indica si tiene código DIR3."""
        return bool(self.codigo_dir3)
    
    @staticmethod
    def buscar_por_dir3(codigo):
        """Buscar empresa por código DIR3."""
        return EntidadEmpresaServicioPublico.query.filter_by(codigo_dir3=codigo).first()
