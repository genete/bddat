"""Modelo para gestión de permisos por tabla mediante metadatos.

Este modelo implementa un sistema de control de accesos basado en metadatos
con tres niveles de permisos: lectura, escritura (INSERT+UPDATE) y eliminación (DELETE).

Roles de la organización:
- ADMIN (id=1): Control total sobre todas las tablas
- SUPERVISOR (id=2): Control sobre tablas estructurales y operacionales, gestión de usuarios
- TRAMITADOR (id=3): Lectura/escritura en tablas operacionales, sin eliminación
- ADMINISTRATIVO (id=4): Lectura/escritura limitada en campos específicos de tablas operacionales
- CONTROLADOR (id=5): Solo lectura para estadísticas

Issue: #85
"""

from app import db
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import event
from datetime import datetime


class TablaMetadata(db.Model):
    """Configuración de permisos por tabla para control de accesos.
    
    PROPÓSITO:
        Define qué roles tienen permisos de lectura, escritura y eliminación
        sobre cada tabla del sistema.
    
    TRES NIVELES DE PERMISOS:
        - roles_lectura: Pueden hacer SELECT (ver registros)
        - roles_escritura: Pueden hacer INSERT y UPDATE (crear y modificar registros)
        - roles_eliminacion: Pueden hacer DELETE (borrar registros)
    
    INVARIANTES DE INTEGRIDAD:
        - roles_escritura ⊆ roles_lectura (quien escribe debe poder leer)
        - roles_eliminacion ⊆ roles_escritura (quien elimina debe poder escribir)
        - Validación automática mediante hooks SQLAlchemy
    
    CATEGORÍAS:
        - 'estructural': Tablas maestras (municipios, tipos_*, roles, usuarios)
        - 'operacional': Tablas de trabajo (expedientes, documentos, solicitudes, etc.)
        - 'sistema': Configuración interna (tabla_metadata, logs, etc.)
    
    EJEMPLOS DE USO:
        # Verificar si un usuario puede leer expedientes
        metadata = TablaMetadata.obtener_metadatos('expedientes')
        if metadata and metadata.usuario_puede_leer(usuario.rol_id):
            # Permitir acceso
            pass
        
        # Obtener todos los permisos de un usuario sobre una tabla
        permisos = metadata.obtener_permisos(usuario.rol_id)
        # {'leer': True, 'escribir': True, 'eliminar': False}
    """
    
    __tablename__ = 'tabla_metadata'
    __table_args__ = ({'schema': 'public'},)
    
    id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True,
        comment='Identificador único autogenerado'
    )
    
    nombre_tabla = db.Column(
        db.String(100), 
        nullable=False, 
        unique=True, 
        index=True,
        comment='Nombre completo de la tabla (schema.tabla o tabla). Ejemplo: public.expedientes, municipios'
    )
    
    # Arrays de role_id para cada nivel de permiso
    roles_lectura = db.Column(
        ARRAY(db.Integer), 
        nullable=True,
        comment='Array de role_id con permiso SELECT. NULL = nadie puede leer, [] = nadie, [1,2,3] = ADMIN, SUPERVISOR, TRAMITADOR'
    )
    
    roles_escritura = db.Column(
        ARRAY(db.Integer), 
        nullable=True,
        comment='Array de role_id con permiso INSERT+UPDATE. Debe ser subconjunto de roles_lectura'
    )
    
    roles_eliminacion = db.Column(
        ARRAY(db.Integer), 
        nullable=True,
        comment='Array de role_id con permiso DELETE. Debe ser subconjunto de roles_escritura'
    )
    
    # Metadatos descriptivos
    descripcion = db.Column(
        db.Text,
        comment='Descripción del propósito y contenido de la tabla'
    )
    
    categoria = db.Column(
        db.String(50),
        comment="Categoría de la tabla: 'estructural', 'operacional', 'sistema'"
    )
    
    # Auditoría
    fecha_creacion = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        comment='Fecha y hora de creación del registro'
    )
    
    ultima_modificacion = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False,
        comment='Fecha y hora de última modificación'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TablaMetadata {self.nombre_tabla} [{self.categoria}]>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.nombre_tabla} ({self.categoria})'
    
    # ========================================================================
    # MÉTODOS DE CONSULTA
    # ========================================================================
    
    @classmethod
    def obtener_metadatos(cls, nombre_tabla):
        """Obtiene metadatos de una tabla específica.
        
        Args:
            nombre_tabla (str): Nombre de la tabla a consultar
            
        Returns:
            TablaMetadata: Objeto con configuración de permisos o None si no existe
        
        Ejemplo:
            metadata = TablaMetadata.obtener_metadatos('expedientes')
            if metadata:
                print(metadata.descripcion)
        """
        return cls.query.filter_by(nombre_tabla=nombre_tabla).first()
    
    def usuario_puede_leer(self, usuario_rol_id):
        """Verifica si un rol puede leer (SELECT) esta tabla.
        
        Args:
            usuario_rol_id (int): ID del rol del usuario actual
            
        Returns:
            bool: True si tiene permiso de lectura
        
        Lógica:
            - Si roles_lectura es None o []: nadie puede leer
            - Si usuario_rol_id está en roles_lectura: puede leer
        """
        if not self.roles_lectura:
            return False  # Sin roles = nadie puede leer
        return usuario_rol_id in self.roles_lectura
    
    def usuario_puede_escribir(self, usuario_rol_id):
        """Verifica si un rol puede escribir (INSERT, UPDATE) en esta tabla.
        
        Args:
            usuario_rol_id (int): ID del rol del usuario actual
            
        Returns:
            bool: True si tiene permiso de escritura
        
        Lógica:
            - Si roles_escritura es None o []: nadie puede escribir
            - Si usuario_rol_id está en roles_escritura: puede escribir
        """
        if not self.roles_escritura:
            return False  # Sin roles = nadie puede escribir
        return usuario_rol_id in self.roles_escritura
    
    def usuario_puede_eliminar(self, usuario_rol_id):
        """Verifica si un rol puede eliminar (DELETE) registros de esta tabla.
        
        Args:
            usuario_rol_id (int): ID del rol del usuario actual
            
        Returns:
            bool: True si tiene permiso de eliminación
        
        Lógica:
            - Si roles_eliminacion es None o []: nadie puede eliminar
            - Si usuario_rol_id está en roles_eliminacion: puede eliminar
        """
        if not self.roles_eliminacion:
            return False  # Sin roles = nadie puede eliminar
        return usuario_rol_id in self.roles_eliminacion
    
    def obtener_permisos(self, usuario_rol_id):
        """Obtiene todos los permisos de un rol sobre esta tabla.
        
        Args:
            usuario_rol_id (int): ID del rol del usuario actual
            
        Returns:
            dict: Diccionario con claves 'leer', 'escribir', 'eliminar'
        
        Ejemplo:
            permisos = metadata.obtener_permisos(3)  # TRAMITADOR
            # {'leer': True, 'escribir': True, 'eliminar': False}
            
            if permisos['eliminar']:
                # Mostrar botón eliminar
                pass
        """
        return {
            'leer': self.usuario_puede_leer(usuario_rol_id),
            'escribir': self.usuario_puede_escribir(usuario_rol_id),
            'eliminar': self.usuario_puede_eliminar(usuario_rol_id)
        }
    
    # ========================================================================
    # VALIDACIONES
    # ========================================================================
    
    def validar_coherencia_permisos(self):
        """Valida que los permisos sean coherentes entre sí.
        
        Reglas de negocio:
            1. roles_escritura ⊆ roles_lectura
               (Todo rol que puede escribir debe poder leer)
            
            2. roles_eliminacion ⊆ roles_escritura
               (Todo rol que puede eliminar debe poder escribir)
        
        Raises:
            ValueError: Si hay incoherencias en los permisos con mensaje descriptivo
        
        Ejemplo:
            try:
                metadata.validar_coherencia_permisos()
            except ValueError as e:
                print(f"Error de coherencia: {e}")
        """
        # Convertir None a lista vacía para comparaciones
        lectura = set(self.roles_lectura or [])
        escritura = set(self.roles_escritura or [])
        eliminacion = set(self.roles_eliminacion or [])
        
        # Validar: escritura ⊆ lectura
        if not escritura.issubset(lectura):
            roles_invalidos = escritura - lectura
            raise ValueError(
                f"Tabla '{self.nombre_tabla}': Roles en 'roles_escritura' deben estar en 'roles_lectura'. "
                f"Roles inválidos: {roles_invalidos}"
            )
        
        # Validar: eliminacion ⊆ escritura
        if not eliminacion.issubset(escritura):
            roles_invalidos = eliminacion - escritura
            raise ValueError(
                f"Tabla '{self.nombre_tabla}': Roles en 'roles_eliminacion' deben estar en 'roles_escritura'. "
                f"Roles inválidos: {roles_invalidos}"
            )
    
    def validar_roles_existen(self):
        """Verifica que todos los role_id referenciados existan en la tabla roles.
        
        Raises:
            ValueError: Si algún role_id no existe en la tabla public.roles
        
        Nota:
            Solo valida si hay roles definidos. Si todos son None/[], no valida.
        """
        from app.models.usuarios import Rol
        
        # Recopilar todos los role_id mencionados
        todos_roles = set()
        if self.roles_lectura:
            todos_roles.update(self.roles_lectura)
        if self.roles_escritura:
            todos_roles.update(self.roles_escritura)
        if self.roles_eliminacion:
            todos_roles.update(self.roles_eliminacion)
        
        if not todos_roles:
            return  # Sin roles = sin validación necesaria
        
        # Consultar roles existentes
        roles_existentes = {r.id for r in Rol.query.filter(Rol.id.in_(todos_roles)).all()}
        roles_inexistentes = todos_roles - roles_existentes
        
        if roles_inexistentes:
            raise ValueError(
                f"Tabla '{self.nombre_tabla}': role_id inexistentes en 'public.roles': {roles_inexistentes}"
            )
    
    def validar_todo(self):
        """Ejecuta todas las validaciones.
        
        Validaciones:
            1. Coherencia de permisos (subconjuntos)
            2. Existencia de roles en la tabla roles
        
        Raises:
            ValueError: Si alguna validación falla
        
        Nota:
            Este método se ejecuta automáticamente antes de INSERT/UPDATE
            mediante hooks SQLAlchemy.
        """
        self.validar_coherencia_permisos()
        self.validar_roles_existen()


# ============================================================================
# HOOKS DE SQLALCHEMY - Validación automática antes de INSERT/UPDATE
# ============================================================================

@event.listens_for(TablaMetadata, 'before_insert')
@event.listens_for(TablaMetadata, 'before_update')
def validar_antes_guardar(mapper, connection, target):
    """Valida coherencia de permisos antes de guardar en BD.
    
    Se ejecuta automáticamente antes de cada INSERT o UPDATE.
    Si la validación falla, lanza excepción y cancela la operación.
    
    Args:
        mapper: Mapper de SQLAlchemy
        connection: Conexión a la BD
        target: Instancia de TablaMetadata siendo guardada
    
    Raises:
        ValueError: Si las validaciones fallan
    """
    target.validar_todo()
