from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin
import secrets

# Tabla de asociación Muchos-a-Muchos (Usuario <-> Rol)
# Relación N:M que permite asignar múltiples roles a cada usuario
usuarios_roles = db.Table('usuarios_roles',
    db.Column('usuario_id', db.Integer, db.ForeignKey('public.usuarios.id'), primary_key=True,
              comment='FK a USUARIOS. Usuario al que se asigna el rol'),
    db.Column('rol_id', db.Integer, db.ForeignKey('public.roles.id'), primary_key=True,
              comment='FK a ROLES. Rol asignado al usuario'),
    schema='public'
)

class Rol(db.Model):
    """
    Catálogo de roles de sistema para control de acceso.
    
    PROPÓSITO:
        Define los roles de usuario que determinan permisos y accesos en el sistema.
        Implementa control de acceso basado en roles (RBAC).
    
    FILOSOFÍA:
        - Un usuario puede tener múltiples roles (relación N:M)
        - Los roles determinan permisos funcionales, no son jerárquicos
        - Roles estándar: ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO
    
    ROLES ESTÁNDAR:
        ADMIN:
            - Acceso completo al sistema
            - Gestión de usuarios y roles
            - Configuración del sistema
        
        SUPERVISOR:
            - Acceso a todos los expedientes
            - Supervisión de tramitadores
            - Gestión de asignaciones
        
        TRAMITADOR:
            - Acceso a expedientes asignados
            - Gestión completa de expedientes propios
            - No puede gestionar usuarios ni configuración
        
        ADMINISTRATIVO:
            - Acceso de lectura a expedientes
            - Tareas de soporte administrativo
            - Sin permisos de modificación
    
    RELACIONES:
        - usuarios (N:M) ← tabla usuarios_roles → USUARIOS
    
    REGLAS DE NEGOCIO:
        1. El nombre del rol debe ser único
        2. Los roles estándar no deben eliminarse
        3. Un usuario sin roles tiene acceso mínimo de lectura
    """
    __tablename__ = 'roles'
    __table_args__ = ({'schema': 'public'},)
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del rol'
    )
    
    nombre = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False,
        comment='Nombre del rol (ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO)'
    )
    
    descripcion = db.Column(
        db.String(200),
        comment='Descripción del propósito y permisos del rol'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Rol {self.nombre}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return self.nombre

class Usuario(UserMixin, db.Model):
    """
    Usuarios del sistema de tramitación administrativa.
    
    PROPÓSITO:
        Representa usuarios técnicos del sistema (tramitadores, supervisores, etc.).
        Gestiona autenticación, autorización y datos personales básicos.
        Integrado con Flask-Login para gestión de sesiones.
    
    FILOSOFÍA:
        - Usuario = persona con acceso al sistema
        - Identificación por SIGLAS (código corto interno)
        - Autenticación mediante email + password
        - Autorización mediante roles (relación N:M con ROLES)
        - Usuarios desactivados (ACTIVO=FALSE) mantienen historial
    
    CARACTERÍSTICAS:
        - Hereda de UserMixin (Flask-Login) para gestión de sesiones
        - Password hasheado (werkzeug.security)
        - Sistema de recuperación de contraseña con token temporal
        - Email opcional (puede ser NULL, constraint UNIQUE)
        - Campo ACTIVO para deshabilitar sin eliminar
    
    CAMPOS ESPECIALES:
        SIGLAS:
            - Código identificativo corto del usuario
            - Único en el sistema
            - Usado en referencias y visualizaciones compactas
            - Default "NULO" permite creación rápida
        
        EMAIL:
            - Property que convierte cadenas vacías a NULL
            - Evita violación de constraint UNIQUE con múltiples strings vacíos
            - Puede ser NULL si el usuario no tiene email
        
        ACTIVO:
            - TRUE: Usuario habilitado, puede iniciar sesión
            - FALSE: Usuario desactivado, no puede iniciar sesión
            - Permite deshabilitar sin perder historial de expedientes asignados
        
        PASSWORD_HASH:
            - Almacena hash bcrypt de la contraseña
            - NUNCA se almacena la contraseña en texto plano
            - Gestionado mediante métodos set_password() / check_password()
        
        RESET_TOKEN / RESET_TOKEN_EXPIRY:
            - Sistema de recuperación de contraseña
            - Token temporal con expiración (default 1 hora)
            - Se limpia automáticamente tras cambio de contraseña
    
    RELACIONES:
        - roles (N:M) → tabla usuarios_roles → ROLES
        - expedientes_responsable (1:N) ← EXPEDIENTES.responsable_id
    
    MÉTODOS DE AUTENTICACIÓN:
        set_password(password):
            - Genera y almacena hash de la contraseña
        
        check_password(password):
            - Verifica si la contraseña proporcionada es correcta
        
        generate_reset_token(expiry_hours=1):
            - Genera token temporal para recuperación de contraseña
        
        verify_reset_token(token):
            - Verifica si el token es válido y no ha expirado
        
        reset_password(new_password):
            - Cambia la contraseña y limpia el token de recuperación
    
    MÉTODOS DE AUTORIZACIÓN:
        tiene_rol(*nombres_roles):
            - Verifica si el usuario tiene al menos uno de los roles especificados
            - Ejemplo: usuario.tiene_rol('ADMIN', 'SUPERVISOR')
        
        es_admin (property):
            - True si el usuario tiene rol ADMIN
        
        es_supervisor (property):
            - True si el usuario tiene rol SUPERVISOR
    
    REGLAS DE NEGOCIO:
        1. SIGLAS debe ser único en el sistema
        2. EMAIL debe ser único si no es NULL
        3. Un usuario desactivado no puede iniciar sesión
        4. Los usuarios no se eliminan, solo se desactivan (historial)
        5. Defaults con valores estándar permiten creación rápida
    
    USO ADMINISTRATIVO:
        - EXPEDIENTES.responsable_id: Tramitador asignado
        - Auditoría futura: CREADO_POR, MODIFICADO_POR en otras tablas
        - Filtros por tramitador, asignaciones, estadísticas
    
    VALORES POR DEFECTO:
        Los defaults ("NULO", "Usuario", "no asignado") permiten creación
        rápida mientras se completa información, pero en producción todos
        los campos deberían tener valores reales.
    """
    __tablename__ = 'usuarios'
    __table_args__ = (
        db.Index('idx_usuarios_siglas', 'siglas'),
        db.Index('idx_usuarios_email', 'email'),  # Corregido: 'email' no '_email'
        {'schema': 'public'}
    )
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado del usuario'
    )
    
    siglas = db.Column(
        db.String(50), 
        nullable=False, 
        unique=True, 
        default='NULO',
        comment='Código identificativo corto del usuario (único)'
    )
    
    nombre = db.Column(
        db.String(100), 
        nullable=False, 
        default='Usuario',
        comment='Nombre de pila del usuario'
    )
    
    apellido1 = db.Column(
        db.String(50), 
        nullable=False, 
        default='no asignado',
        comment='Primer apellido del usuario'
    )
    
    apellido2 = db.Column(
        db.String(50),
        comment='Segundo apellido del usuario (opcional)'
    )
    
    _email = db.Column(
        'email', 
        db.String(120), 
        unique=True, 
        nullable=True,
        comment='Email del usuario (opcional, único si no es NULL)'
    )
    
    activo = db.Column(
        db.Boolean, 
        default=True,
        comment='TRUE=habilitado, FALSE=desactivado (mantiene historial)'
    )
    
    # Seguridad y Roles
    password_hash = db.Column(
        db.String(256),
        comment='Hash bcrypt de la contraseña (nunca almacenar en texto plano)'
    )
    
    # Recuperación de contraseña
    reset_token = db.Column(
        db.String(100), 
        nullable=True,
        comment='Token temporal para recuperación de contraseña'
    )
    
    reset_token_expiry = db.Column(
        db.DateTime, 
        nullable=True,
        comment='Fecha de expiración del token de recuperación'
    )
    
    # Relación M:N con Roles
    roles = db.relationship(
        'Rol', 
        secondary=usuarios_roles, 
        backref=db.backref('usuarios', lazy='dynamic')
    )

    # Property para email que convierte cadenas vacías a None
    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        """Convierte cadenas vacías a None para evitar violación de constraint UNIQUE"""
        if value == '' or (isinstance(value, str) and value.strip() == ''):
            self._email = None
        else:
            self._email = value

    # Flask-Login: sobrescribir is_active para usar nuestro campo activo
    @property
    def is_active(self):
        return self.activo

    # Gestión de contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Gestión de token de recuperación
    def generate_reset_token(self, expiry_hours=1):
        """Genera un token de recuperación con expiración"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verifica si el token es válido y no ha expirado"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True
    
    def reset_password(self, new_password):
        """Cambia la contraseña y limpia el token"""
        self.set_password(new_password)
        self.reset_token = None
        self.reset_token_expiry = None

    # Helpers de permisos
    def tiene_rol(self, *nombres_roles):
        """Verifica si el usuario tiene al menos uno de los roles especificados
        
        Args:
            *nombres_roles: Uno o más nombres de roles a verificar
            
        Returns:
            bool: True si el usuario tiene al menos uno de los roles
            
        Ejemplos:
            usuario.tiene_rol('ADMIN')
            usuario.tiene_rol('ADMIN', 'SUPERVISOR')
            usuario.tiene_rol('ADMIN', 'SUPERVISOR', 'TRAMITADOR')
        """
        return any(rol.nombre in nombres_roles for rol in self.roles)

    def rol_por_id(self, rol_id: int):
        """Devuelve el Rol si está asignado al usuario, None en caso contrario.
        Usado para validar el rol seleccionado en /auth/seleccionar-rol."""
        return next((r for r in self.roles if r.id == rol_id), None)

    @property
    def es_admin(self):
        return self.tiene_rol('ADMIN')

    @property
    def es_supervisor(self):
        return self.tiene_rol('SUPERVISOR')
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<Usuario {self.siglas} - {self.nombre} {self.apellido1}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.nombre} {self.apellido1} ({self.siglas})'
