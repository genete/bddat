# app/models/direccion_notificacion.py
"""
Modelo DireccionNotificacion - Direcciones específicas de notificación por rol/trámite.

Tabla: DIRECCIONES_NOTIFICACION
Descripción: Direcciones de notificación específicas según el rol que desempeña la entidad.
             Una entidad puede tener múltiples direcciones según actúe como titular,
             consultado o publicador.
             
Ejemplo: Iberdrola puede tener:
  - Dirección como TITULAR (solicitante de autorizaciones)
  - Dirección como CONSULTADO (empresa distribuidora afectada)
  - Diferentes direcciones por delegaciones/territorios
"""

from app import db
from datetime import datetime
from sqlalchemy import CheckConstraint, func


class DireccionNotificacion(db.Model):
    """
    Direcciones de notificación específicas de una entidad según su rol.
    
    Arquitectura:
    - Relación N:1 con Entidad (una entidad puede tener múltiples direcciones)
    - Bit flags para roles (tipo_rol): 1=TITULAR, 2=CONSULTADO, 4=PUBLICADOR
    - Dirección estructurada (direccion, CP, municipio) para formateo elegante
    - Múltiples canales: email, DIR3, SIR, postal
    """
    
    __tablename__ = 'direcciones_notificacion'
    __table_args__ = (
        CheckConstraint('tipo_rol BETWEEN 1 AND 7', name='chk_tipo_rol_valido'),
        CheckConstraint(
            'email IS NOT NULL OR codigo_sir IS NOT NULL OR codigo_dir3 IS NOT NULL OR direccion IS NOT NULL',
            name='chk_al_menos_un_canal'
        ),
        {'schema': 'public'}
    )
    
    # === IDENTIFICACIÓN ===
    id = db.Column(
        db.Integer, 
        primary_key=True,
        comment='Identificador único de la dirección de notificación'
    )
    
    entidad_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.entidades.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment='FK a ENTIDADES. Borrado en cascada'
    )
    
    descripcion = db.Column(
        db.Text,
        comment='Descripción libre. Ej: "Sede Central", "Delegación Norte", "Contacto para expedientes de BT"'
    )
    
    # === BIT FLAGS DE ROLES ===
    # 1 = TITULAR, 2 = CONSULTADO, 4 = PUBLICADOR
    # Permite combinaciones: 3 = TITULAR+CONSULTADO, 7 = TODOS
    tipo_rol = db.Column(
        db.SmallInteger, 
        nullable=False,
        index=True,
        comment='Bit flags: 1=TITULAR, 2=CONSULTADO, 4=PUBLICADOR. Ej: 3=TITULAR+CONSULTADO'
    )
    
    # === CANALES DIGITALES ===
    email = db.Column(
        db.String(120),
        comment='Email de notificación electrónica'
    )
    
    telefono = db.Column(
        db.String(20),
        comment='Teléfono de contacto para este rol'
    )
    
    codigo_sir = db.Column(
        db.String(50),
        comment='Código SIR (Sistema de Información del Registro). Para notificaciones telemáticas'
    )
    
    codigo_dir3 = db.Column(
        db.String(20),
        comment='Código DIR3 de la unidad orgánica. Para organismos públicos'
    )
    
    # === DIRECCIÓN POSTAL (campos separados para formateo elegante) ===
    direccion = db.Column(
        db.Text,
        comment='Calle, número, piso, puerta. Usar junto con codigo_postal y municipio_id'
    )
    
    codigo_postal = db.Column(
        db.String(10),
        comment='Código postal. Texto libre'
    )
    
    municipio_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.municipios.id'),
        index=True,
        comment='Municipio de la dirección. Permite deducir provincia'
    )
    
    direccion_fallback = db.Column(
        db.Text,
        comment='Dirección completa en texto libre. Para extranjero o casos excepcionales'
    )
    
    # === IDENTIFICACIÓN FISCAL/ADMINISTRATIVA ===
    nif = db.Column(
        db.String(20),
        comment='NIF específico para este rol (si difiere del NIF principal de la entidad). Ej: delegaciones con NIF propio'
    )
    
    # === DOCUMENTO SOPORTE ===
    documento_autorizacion_id = db.Column(
        db.Integer, 
        db.ForeignKey('public.documentos.id', ondelete='SET NULL'),
        comment='Documento que autoriza esta dirección (poder notarial, autorización de representación, etc.)'
    )
    
    # === CONTROL TEMPORAL ===
    activo = db.Column(
        db.Boolean, 
        default=True, 
        nullable=False,
        index=True,
        comment='Indica si la dirección está activa. Borrado lógico'
    )
    
    fecha_inicio = db.Column(
        db.Date, 
        default=func.current_date(),
        comment='Fecha de inicio de vigencia'
    )
    
    fecha_fin = db.Column(
        db.Date,
        comment='Fecha de fin de vigencia (NULL = indefinida)'
    )
    
    notas = db.Column(
        db.Text,
        comment='Observaciones sobre esta dirección de notificación'
    )
    
    # === AUDITORÍA ===
    created_at = db.Column(
        db.DateTime, 
        default=func.now(), 
        nullable=False,
        comment='Fecha y hora de creación del registro'
    )
    
    updated_at = db.Column(
        db.DateTime, 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False,
        comment='Fecha y hora de última actualización'
    )
    
    # === RELACIONES ===
    entidad = db.relationship('Entidad', back_populates='direcciones_notificacion')
    municipio = db.relationship('Municipio')
    documento_autorizacion = db.relationship('Documento')
    
    def __repr__(self):
        roles = []
        if self.es_titular: roles.append('T')
        if self.es_consultado: roles.append('C')
        if self.es_publicador: roles.append('P')
        desc = f" ({self.descripcion})" if self.descripcion else ""
        return f'<DireccionNotif {self.id}: Entidad={self.entidad_id} [{"|".join(roles)}]{desc}>'
    
    # === MÉTODOS HELPER PARA BIT FLAGS ===
    
    @staticmethod
    def calcular_tipo_rol(es_titular=False, es_consultado=False, es_publicador=False):
        """Convierte roles booleanos a bit flags.
        
        Args:
            es_titular: True si la dirección es para rol TITULAR
            es_consultado: True si la dirección es para rol CONSULTADO
            es_publicador: True si la dirección es para rol PUBLICADOR
        
        Returns:
            int: Bit flags combinados (1-7)
        
        Examples:
            >>> calcular_tipo_rol(es_titular=True)
            1
            >>> calcular_tipo_rol(es_titular=True, es_consultado=True)
            3
            >>> calcular_tipo_rol(es_titular=True, es_consultado=True, es_publicador=True)
            7
        """
        return (1 if es_titular else 0) | \
               (2 if es_consultado else 0) | \
               (4 if es_publicador else 0)
    
    @staticmethod
    def tiene_rol_titular(tipo_rol):
        """Comprueba si el tipo_rol tiene activado el bit TITULAR."""
        return bool(tipo_rol & 1)
    
    @staticmethod
    def tiene_rol_consultado(tipo_rol):
        """Comprueba si el tipo_rol tiene activado el bit CONSULTADO."""
        return bool(tipo_rol & 2)
    
    @staticmethod
    def tiene_rol_publicador(tipo_rol):
        """Comprueba si el tipo_rol tiene activado el bit PUBLICADOR."""
        return bool(tipo_rol & 4)
    
    # === PROPIEDADES DE CONVENIENCIA ===
    
    @property
    def es_titular(self):
        """Property: True si esta dirección es para rol TITULAR."""
        return self.tiene_rol_titular(self.tipo_rol)
    
    @property
    def es_consultado(self):
        """Property: True si esta dirección es para rol CONSULTADO."""
        return self.tiene_rol_consultado(self.tipo_rol)
    
    @property
    def es_publicador(self):
        """Property: True si esta dirección es para rol PUBLICADOR."""
        return self.tiene_rol_publicador(self.tipo_rol)
    
    @property
    def roles_lista(self):
        """Devuelve lista legible de roles. Ej: ['TITULAR', 'CONSULTADO']."""
        roles = []
        if self.es_titular: roles.append('TITULAR')
        if self.es_consultado: roles.append('CONSULTADO')
        if self.es_publicador: roles.append('PUBLICADOR')
        return roles
    
    # === MÉTODOS DE NEGOCIO ===
    
    def direccion_formateada(self):
        """Devuelve la dirección en formato de oficio tradicional.
        
        Returns:
            dict con claves:
                - linea1: Dirección (calle, número)
                - linea2: Código postal y municipio
                - provincia: Nombre de la provincia
        
        Examples:
            >>> d.direccion_formateada()
            {
                'linea1': 'C/ Tomás Redondo, 1',
                'linea2': '28033 Madrid',
                'provincia': 'MADRID'
            }
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
    
    def to_dict(self):
        """Serialización para API."""
        return {
            'id': self.id,
            'entidad_id': self.entidad_id,
            'descripcion': self.descripcion,
            'tipo_rol': self.tipo_rol,
            'roles': self.roles_lista,
            'email': self.email,
            'telefono': self.telefono,
            'codigo_sir': self.codigo_sir,
            'codigo_dir3': self.codigo_dir3,
            'direccion': self.direccion,
            'codigo_postal': self.codigo_postal,
            'municipio_id': self.municipio_id,
            'direccion_fallback': self.direccion_fallback,
            'nif': self.nif,
            'documento_autorizacion_id': self.documento_autorizacion_id,
            'activo': self.activo,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'notas': self.notas,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # === MÉTODOS ESTÁTICOS DE CONSULTA ===
    
    @staticmethod
    def obtener_direccion_notificacion(entidad_id, es_titular=False, es_consultado=False, es_publicador=False):
        """Obtiene la dirección de notificación activa para un rol específico.
        
        Args:
            entidad_id: ID de la entidad
            es_titular: Buscar dirección para rol TITULAR
            es_consultado: Buscar dirección para rol CONSULTADO
            es_publicador: Buscar dirección para rol PUBLICADOR
        
        Returns:
            DireccionNotificacion o None si no existe
        
        Lógica:
            - Busca direcciones activas
            - Filtra por tipo_rol usando bit flags
            - Ordena por fecha_inicio DESC (más reciente primero)
        """
        tipo_rol_buscado = DireccionNotificacion.calcular_tipo_rol(
            es_titular, es_consultado, es_publicador
        )
        
        return DireccionNotificacion.query.filter(
            DireccionNotificacion.entidad_id == entidad_id,
            DireccionNotificacion.activo == True,
            DireccionNotificacion.tipo_rol.op('&')(tipo_rol_buscado) > 0  # Bit AND
        ).order_by(
            DireccionNotificacion.fecha_inicio.desc()
        ).first()
