# En desarrollo
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# Tabla de asociación Muchos-a-Muchos (Usuario <-> Rol)
usuarios_roles = db.Table('usuarios_roles',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Rol(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column("NOMBRE", db.String(50), unique=True, nullable=False)  # ADMIN, TECNICO...
    descripcion = db.Column("DESCRIPCION", db.String(200))
    
    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siglas = db.Column(db.String(50), nullable=False, unique=True, default='NULO')
    nombre = db.Column(db.String(100), nullable=False, default='Usuario')
    apellido1 = db.Column(db.String(50), nullable=False, default='no asignado')
    apellido2 = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)
    
    # Seguridad y Roles
    password_hash = db.Column("PASSWORD_HASH", db.String(256))
    
    # Relación M:N con Roles
    roles = db.relationship('Rol', secondary=usuarios_roles, backref=db.backref('usuarios', lazy='dynamic'))

    # Gestión de contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helpers de permisos
    def tiene_rol(self, nombre_rol):
        return any(rol.nombre == nombre_rol for rol in self.roles)

    @property
    def es_admin(self):
        return self.tiene_rol('ADMIN')
    
    def __repr__(self):
        return f'<Usuario {self.siglas} - {self.nombre} {self.apellido1}>'