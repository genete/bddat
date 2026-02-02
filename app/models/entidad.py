# app/models/entidad.py
"""
Modelo Entidad - Tabla base polimórfica para todas las entidades del sistema.

Tabla: ENTIDADES (O_013)
Descripción: Centraliza personas físicas, jurídicas y organismos con campos comunes.
             Usa arquitectura de tablas inversas para metadatos específicos.
"""

from app import db
from datetime import datetime
import re


class Entidad(db.Model):
    """
    Tabla base que centraliza todas las entidades del sistema.
    
    Arquitectura polimórfica:
    - Campos comunes en esta tabla
    - Metadatos específicos en tablas entidades_* según tipo
    - Relaciones 1:1 con tablas de metadatos
    """
    
    __tablename__ = 'entidades'
    
    # Campos
    id = db.Column(db.Integer, primary_key=True)
    tipo_entidad_id = db.Column(db.Integer, db.ForeignKey('tipos_entidades.id'), nullable=False, index=True)
    cif_nif = db.Column(db.String(20), unique=True, index=True, nullable=True)
    nombre_completo = db.Column(db.String(200), nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    codigo_postal = db.Column(db.String(10), nullable=True)
    municipio_id = db.Column(db.Integer, db.ForeignKey('estructura.municipios.id'), nullable=True, index=True)
    direccion_fallback = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    notas = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tipo_entidad = db.relationship('TipoEntidad', back_populates='entidades')
    municipio = db.relationship('Municipio', backref='entidades')
    
    # Relaciones polimórficas con tablas de metadatos (1:1)
    datos_administrado = db.relationship('EntidadAdministrado', uselist=False, back_populates='entidad', cascade='all, delete-orphan')
    datos_empresa = db.relationship('EntidadEmpresaServicioPublico', uselist=False, back_populates='entidad', cascade='all, delete-orphan')
    datos_organismo = db.relationship('EntidadOrganismoPublico', uselist=False, back_populates='entidad', cascade='all, delete-orphan')
    datos_ayuntamiento = db.relationship('EntidadAyuntamiento', uselist=False, back_populates='entidad', cascade='all, delete-orphan')
    datos_diputacion = db.relationship('EntidadDiputacion', uselist=False, back_populates='entidad', cascade='all, delete-orphan')
    
    # Relaciones inversas con tablas operacionales
    # TODO: Descomentar cuando se migren las tablas EXPEDIENTES y SOLICITUDES para usar ENTIDADES
    # expedientes_titular = db.relationship('Expediente', foreign_keys='Expediente.titular_id', backref='titular')
    # solicitudes_solicitante = db.relationship('Solicitud', foreign_keys='Solicitud.solicitante_id', backref='solicitante')
    # solicitudes_autorizado = db.relationship('Solicitud', foreign_keys='Solicitud.autorizado_id', backref='autorizado')
    
    def __repr__(self):
        return f'<Entidad {self.id}: {self.nombre_completo} ({self.tipo_entidad.codigo if self.tipo_entidad else "?"})>'
    
    def to_dict(self, include_metadatos=False):
        """Serialización para API."""
        data = {
            'id': self.id,
            'tipo_entidad': self.tipo_entidad.to_dict() if self.tipo_entidad else None,
            'cif_nif': self.cif_nif,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'codigo_postal': self.codigo_postal,
            'municipio_id': self.municipio_id,
            'direccion_fallback': self.direccion_fallback,
            'activo': self.activo,
            'notas': self.notas,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Incluir metadatos específicos si se solicita
        if include_metadatos:
            if self.datos_administrado:
                data['metadatos'] = self.datos_administrado.to_dict()
            elif self.datos_empresa:
                data['metadatos'] = self.datos_empresa.to_dict()
            elif self.datos_organismo:
                data['metadatos'] = self.datos_organismo.to_dict()
            elif self.datos_ayuntamiento:
                data['metadatos'] = self.datos_ayuntamiento.to_dict()
            elif self.datos_diputacion:
                data['metadatos'] = self.datos_diputacion.to_dict()
        
        return data
    
    @staticmethod
    def normalizar_cif_nif(valor):
        """Normalizar CIF/NIF: mayúsculas, sin espacios/guiones."""
        if not valor:
            return None
        return re.sub(r'[\s\-]', '', valor.upper())
    
    @staticmethod
    def validar_cif_nif(valor):
        """
        Validación básica de formato CIF/NIF/NIE español.
        
        TODO: Implementar validación completa con algoritmo oficial
        (NIF: letra calculada, CIF: dígito de control, etc.)
        """
        if not valor:
            return True  # Permitir NULL
        
        # Patrón básico: letra(s) + dígitos + letra/dígito
        patron = r'^[A-Z]{1,2}\d{7,8}[A-Z0-9]$'
        return bool(re.match(patron, valor))
    
    @staticmethod
    def buscar_por_cif_nif(cif_nif):
        """Buscar entidad por CIF/NIF normalizado."""
        cif_nif_norm = Entidad.normalizar_cif_nif(cif_nif)
        return Entidad.query.filter_by(cif_nif=cif_nif_norm).first()
    
    @staticmethod
    def buscar_por_nombre(texto):
        """Buscar entidades por nombre (coincidencia parcial)."""
        return Entidad.query.filter(
            Entidad.nombre_completo.ilike(f'%{texto}%')
        ).filter_by(activo=True).all()
    
    @staticmethod
    def listar_por_tipo(tipo_codigo, solo_activos=True):
        """Listar entidades por tipo."""
        query = Entidad.query.join(TipoEntidad).filter(TipoEntidad.codigo == tipo_codigo)
        if solo_activos:
            query = query.filter(Entidad.activo == True)
        return query.all()
