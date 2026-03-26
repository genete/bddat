# app/models/entidad.py
"""
Modelo Entidad - Tabla base para todas las entidades del sistema.

Tabla: ENTIDADES (O_013)
Descripción: Centraliza personas físicas, jurídicas y organismos con campos comunes.
             Usa roles booleanos para determinar capacidad (titular/consultado/publicador).
             
Cambios Issue #103:
- Eliminada jerarquía tipos_entidades (polimorfismo obsoleto)
- Añadidos roles booleanos para capacidad operativa
- Mantenida estructura de dirección separada para formateo elegante en oficios
"""

from app import db
from datetime import datetime
from sqlalchemy import CheckConstraint
import re


class Entidad(db.Model):
    """
    Tabla base que centraliza todas las entidades del sistema.
    
    Arquitectura simplificada (Issue #103):
    - Campos comunes en esta tabla
    - Roles booleanos para capacidad (titular, consultado, publicador)
    - Direcciones de notificación específicas en tabla direcciones_notificacion (1:N)
    """
    
    __tablename__ = 'entidades'
    __table_args__ = (
        CheckConstraint(
            'rol_titular OR rol_consultado OR rol_publicador',
            name='chk_al_menos_un_rol'
        ),
        {'schema': 'public'}
    )
    
    # === IDENTIFICACIÓN ===
    id = db.Column(
        db.Integer, 
        primary_key=True,
        comment='Identificador único de la entidad'
    )
    
    nif = db.Column(
        db.String(20), 
        unique=True, 
        index=True, 
        nullable=True,
        comment='NIF (DNI/NIE para personas físicas, antiguo CIF para jurídicas). Normalizado: mayúsculas, sin espacios/guiones. NULL permitido para organismos históricos'
    )
    
    nombre_completo = db.Column(
        db.String(200), 
        nullable=False, 
        index=True,
        comment='Razón social, nombre completo o nombre oficial. Personas físicas: nombre completo. Jurídicas/organismos: razón social/nombre oficial'
    )
    
    # === ROLES OPERATIVOS ===
    rol_titular = db.Column(
        db.Boolean, 
        nullable=False, 
        default=False,
        comment='Puede ser titular de expedientes. Ej: promotores de instalaciones, solicitantes de autorizaciones'
    )
    
    rol_consultado = db.Column(
        db.Boolean, 
        nullable=False, 
        default=False,
        comment='Puede ser consultado en trámites. Ej: organismos afectados, empresas distribuidoras'
    )
    
    rol_publicador = db.Column(
        db.Boolean, 
        nullable=False, 
        default=False,
        comment='Puede publicar anuncios/notificaciones. Ej: diputaciones, ayuntamientos'
    )
    
    tipo_titular = db.Column(
        db.String(30),
        nullable=True,
        comment='Categoría del administrado cuando actúa como titular. '
                'NULL para entidades sin rol_titular. '
                'Valores: GRAN_DISTRIBUIDORA | DISTRIBUIDOR_MENOR | PROMOTOR | ORGANISMO_PUBLICO | OTRO'
    )

    # === CONTACTO GENERAL ===
    email = db.Column(
        db.String(120), 
        nullable=True,
        comment='Email general de contacto. Para emails de notificación específicos ver tabla direcciones_notificacion'
    )
    
    telefono = db.Column(
        db.String(20), 
        nullable=True,
        comment='Teléfono de contacto general. Formato libre'
    )
    
    # === DIRECCIÓN PRINCIPAL (campos separados para formateo en oficios) ===
    direccion = db.Column(
        db.Text, 
        nullable=True,
        comment='Calle, número, piso, puerta. Usar junto con codigo_postal y municipio_id (preferente para España)'
    )
    
    codigo_postal = db.Column(
        db.String(10), 
        nullable=True,
        comment='Código postal. Texto libre. Futuro: sugerencias desde tabla codigos_postales'
    )
    
    municipio_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.municipios.id'),
        nullable=True, 
        index=True,
        comment='Municipio de la dirección. Preferente sobre direccion_fallback. Permite deducir provincia'
    )
    
    direccion_fallback = db.Column(
        db.Text, 
        nullable=True,
        comment='Dirección completa en texto libre. Para casos excepcionales (extranjero, datos históricos). Ej: "23, Peny Lane, St, 34523, London, England"'
    )
    
    # === CONTROL ===
    activo = db.Column(
        db.Boolean, 
        nullable=False, 
        default=True, 
        index=True,
        comment='Indica si la entidad está activa. Borrado lógico'
    )
    
    notas = db.Column(
        db.Text, 
        nullable=True,
        comment='Observaciones generales sobre la entidad. Campo libre para anotaciones'
    )
    
    # === AUDITORÍA ===
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
    
    # === RELACIONES ===
    municipio = db.relationship(
        'Municipio',
        foreign_keys=[municipio_id],
        backref='entidades'
    )
    
    # Relación 1:N con direcciones de notificación específicas
    direcciones_notificacion = db.relationship(
        'DireccionNotificacion', 
        back_populates='entidad', 
        cascade='all, delete-orphan',
        order_by='DireccionNotificacion.activo.desc(), DireccionNotificacion.fecha_inicio.desc()'
    )
    
    def __repr__(self):
        roles = []
        if self.rol_titular: roles.append('T')
        if self.rol_consultado: roles.append('C')
        if self.rol_publicador: roles.append('P')
        return f'<Entidad {self.id}: {self.nombre_completo} [{"|".join(roles)}]>'
    
    def to_dict(self, include_direcciones=False):
        """Serialización para API."""
        data = {
            'id': self.id,
            'nif': self.nif,
            'nombre_completo': self.nombre_completo,
            'rol_titular': self.rol_titular,
            'rol_consultado': self.rol_consultado,
            'rol_publicador': self.rol_publicador,
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
        
        # Incluir direcciones de notificación si se solicita
        if include_direcciones:
            data['direcciones_notificacion'] = [
                d.to_dict() for d in self.direcciones_notificacion
            ]
        
        return data
    
    def direccion_formateada(self):
        """Devuelve la dirección principal en formato de oficio tradicional.
        
        Returns:
            dict con claves: linea1 (dirección), linea2 (CP municipio), provincia
        """
        if self.direccion_fallback:
            return {
                'linea1': self.direccion_fallback,
                'linea2': '',
                'provincia': ''
            }
        
        linea2_parts = []
        if self.codigo_postal:
            linea2_parts.append(self.codigo_postal)
        if self.municipio:
            linea2_parts.append(self.municipio.nombre)
        
        return {
            'linea1': self.direccion or '',
            'linea2': ' '.join(linea2_parts),
            'provincia': self.municipio.provincia.nombre if self.municipio else ''
        }
    
    @staticmethod
    def normalizar_nif(valor):
        """Normalizar NIF: mayúsculas, sin espacios/guiones."""
        if not valor:
            return None
        return re.sub(r'[\s\-]', '', valor.upper())
    
    @staticmethod
    def validar_nif(valor):
        """
        Validación básica de formato NIF/NIE español.
        
        TODO: Implementar validación completa con algoritmo oficial
        (NIF: letra calculada, NIE: letra + número, etc.)
        """
        if not valor:
            return True  # Permitir NULL
        
        # Patrón básico: letra(s) + dígitos + letra/dígito
        patron = r'^[A-Z]{1,2}\d{7,8}[A-Z0-9]$'
        return bool(re.match(patron, valor))
    
    @staticmethod
    def buscar_por_nif(nif):
        """Buscar entidad por NIF normalizado."""
        nif_norm = Entidad.normalizar_nif(nif)
        return Entidad.query.filter_by(nif=nif_norm).first()
    
    @staticmethod
    def buscar_por_nombre(texto):
        """Buscar entidades por nombre (coincidencia parcial)."""
        return Entidad.query.filter(
            Entidad.nombre_completo.ilike(f'%{texto}%')
        ).filter_by(activo=True).all()
    
    @staticmethod
    def listar_por_rol(titular=None, consultado=None, publicador=None, solo_activos=True):
        """Listar entidades por roles.
        
        Args:
            titular: True/False/None (None = no filtrar)
            consultado: True/False/None
            publicador: True/False/None
            solo_activos: Filtrar solo entidades activas
        """
        query = Entidad.query
        
        if titular is not None:
            query = query.filter(Entidad.rol_titular == titular)
        if consultado is not None:
            query = query.filter(Entidad.rol_consultado == consultado)
        if publicador is not None:
            query = query.filter(Entidad.rol_publicador == publicador)
        if solo_activos:
            query = query.filter(Entidad.activo == True)
        
        return query.all()
