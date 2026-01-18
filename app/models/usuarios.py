# En desarrollo
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

# Tabla de asociación Muchos-a-Muchos (Usuario <-> Rol)
usuarios_roles = db.Table('usuarios_roles',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)  # ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO
    descripcion = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siglas = db.Column(db.String(50), nullable=False, unique=True, default='NULO')
    nombre = db.Column(db.String(100), nullable=False, default='Usuario')
    apellido1 = db.Column(db.String(50), nullable=False, default='no asignado')
    apellido2 = db.Column(db.String(50))
    email = db.Column(db.String(120), unique=True, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Seguridad y Roles
    password_hash = db.Column(db.String(256))
    
    # Recuperación de contraseña
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relación M:N con Roles
    roles = db.relationship('Rol', secondary=usuarios_roles, backref=db.backref('usuarios', lazy='dynamic'))

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
    def tiene_rol(self, nombre_rol):
        return any(rol.nombre == nombre_rol for rol in self.roles)

    @property
    def es_admin(self):
        return self.tiene_rol('ADMIN')
    
    @property
    def es_supervisor(self):
        return self.tiene_rol('SUPERVISOR')
    
    def __repr__(self):
        return f'<Usuario {self.siglas} - {self.nombre} {self.apellido1}>'
