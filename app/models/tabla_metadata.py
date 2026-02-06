from app import db
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import CheckConstraint

class TablaMetadata(db.Model):
    """
    Metadatos de configuración para tablas del sistema.
    
    PROPÓSITO:
        Define cómo se visualizan, ordenan y gestionan las tablas en la interfaz.
        Centraliza la configuración de permisos de eliminación y visualización por rol.
        
    FILOSOFÍA:
        - Configuración centralizada: Toda la metadata de tablas en un solo lugar
        - Control granular por rol: Diferentes permisos para eliminar y visualizar
        - Separación de concerns: Lógica de presentación separada de lógica de negocio
        - Administrable: Los administradores pueden ajustar configuración sin código
        
    CARACTERÍSTICAS:
        - nombre_tabla: Identificador único de la tabla (schema.tabla)
        - titulo_singular/plural: Nombres legibles para la interfaz
        - campo_orden_defecto: Campo por defecto para ordenar listados
        - orden_asc: Dirección del orden (TRUE=ASC, FALSE=DESC)
        - roles_pueden_eliminar: Array de role_id que pueden eliminar registros
        - roles_pueden_visualizar: Array de role_id que pueden ver la tabla
        
    ROLES (IDs):
        1 = ADMIN        - Acceso completo
        2 = SUPERVISOR   - Supervisión y gestión
        3 = TRAMITADOR   - Tramitación de expedientes
        4 = ADMINISTRATIVO - Soporte administrativo
        5 = CONTROLADOR  - Control y validación
        
    EJEMPLOS DE USO:
        # Tabla de usuarios: solo ADMIN puede eliminar, todos pueden ver
        TablaMetadata(
            nombre_tabla='public.usuarios',
            titulo_singular='Usuario',
            titulo_plural='Usuarios',
            campo_orden_defecto='apellido1',
            orden_asc=True,
            roles_pueden_eliminar=[1],  # Solo ADMIN
            roles_pueden_visualizar=[1, 2, 3, 4, 5]  # Todos
        )
        
        # Tabla de expedientes: ADMIN y SUPERVISOR pueden eliminar
        TablaMetadata(
            nombre_tabla='expedientes.expedientes',
            titulo_singular='Expediente',
            titulo_plural='Expedientes',
            campo_orden_defecto='fecha_alta',
            orden_asc=False,  # Más recientes primero
            roles_pueden_eliminar=[1, 2],  # ADMIN y SUPERVISOR
            roles_pueden_visualizar=[1, 2, 3, 5]  # No ADMINISTRATIVO
        )
        
    VALIDACIONES:
        - nombre_tabla debe ser único
        - campos obligatorios no pueden ser NULL ni vacíos
        - role_id en arrays deben ser únicos (no duplicados)
        - roles_pueden_eliminar ⊆ roles_pueden_visualizar
          (solo puedes eliminar lo que puedes ver)
          
    REGLAS DE NEGOCIO:
        1. Una tabla sin metadata usa valores por defecto del sistema
        2. Array vacío [] significa "ningún rol tiene permiso"
        3. NULL en arrays se interpreta como "usar permisos por defecto"
        4. ADMIN (role_id=1) siempre debe estar en roles_pueden_visualizar
        5. Si una tabla tiene FK a otra, esa otra debe estar en metadata
        
    RELACIONES:
        - Ninguna directa (tabla de configuración)
        - Referencia indirecta a ROLES vía role_id en arrays
        - Referencia indirecta a tablas del sistema vía nombre_tabla
        
    MANTENIMIENTO:
        - Insertar metadata al crear nuevas tablas importantes
        - Actualizar permisos cuando cambien requisitos de seguridad
        - Revisar periódicamente consistencia con estructura real de BD
    """
    __tablename__ = 'tabla_metadata'
    __table_args__ = (
        # Índices para consultas frecuentes
        db.Index('idx_tabla_metadata_nombre', 'nombre_tabla'),
        
        # Constraints de validación
        CheckConstraint(
            "nombre_tabla IS NOT NULL AND TRIM(nombre_tabla) != ''",
            name='chk_nombre_tabla_not_empty'
        ),
        CheckConstraint(
            "titulo_singular IS NOT NULL AND TRIM(titulo_singular) != ''",
            name='chk_titulo_singular_not_empty'
        ),
        CheckConstraint(
            "titulo_plural IS NOT NULL AND TRIM(titulo_plural) != ''",
            name='chk_titulo_plural_not_empty'
        ),
        CheckConstraint(
            "campo_orden_defecto IS NOT NULL AND TRIM(campo_orden_defecto) != ''",
            name='chk_campo_orden_not_empty'
        ),
        
        {'schema': 'public'}
    )
    
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
        comment='Nombre completo de la tabla (schema.tabla). Ejemplo: public.usuarios, expedientes.expedientes'
    )
    
    titulo_singular = db.Column(
        db.String(100),
        nullable=False,
        comment='Nombre singular para mostrar en interfaz. Ejemplo: Usuario, Expediente, Provincia'
    )
    
    titulo_plural = db.Column(
        db.String(100),
        nullable=False,
        comment='Nombre plural para mostrar en interfaz. Ejemplo: Usuarios, Expedientes, Provincias'
    )
    
    campo_orden_defecto = db.Column(
        db.String(100),
        nullable=False,
        comment='Campo por defecto para ordenar listados. Ejemplo: apellido1, fecha_alta, nombre'
    )
    
    orden_asc = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Dirección del orden por defecto. TRUE=Ascendente (A-Z, 0-9, antiguos primero), FALSE=Descendente (Z-A, 9-0, recientes primero)'
    )
    
    roles_pueden_eliminar = db.Column(
        ARRAY(db.Integer),
        nullable=True,
        comment='Array de role_id que tienen permiso para eliminar registros. Ejemplo: [1,2] = ADMIN y SUPERVISOR. NULL = usar permisos por defecto, [] = nadie puede eliminar'
    )
    
    roles_pueden_visualizar = db.Column(
        ARRAY(db.Integer),
        nullable=True,
        comment='Array de role_id que tienen permiso para visualizar la tabla. Ejemplo: [1,2,3,4,5] = todos. NULL = usar permisos por defecto, [] = nadie puede visualizar'
    )
    
    def __repr__(self):
        """Representación técnica para debugging."""
        return f'<TablaMetadata {self.nombre_tabla}>'
    
    def __str__(self):
        """Representación legible para interfaz."""
        return f'{self.titulo_plural} ({self.nombre_tabla})'
    
    def puede_eliminar(self, usuario):
        """
        Verifica si un usuario puede eliminar registros de esta tabla.
        
        Args:
            usuario: Instancia de Usuario con roles cargados
            
        Returns:
            bool: True si el usuario tiene permiso para eliminar
            
        Lógica:
            - Si roles_pueden_eliminar es None: usar lógica por defecto (solo ADMIN)
            - Si roles_pueden_eliminar es []: nadie puede eliminar
            - Si roles_pueden_eliminar tiene valores: verificar si algún rol del usuario está en la lista
        """
        if self.roles_pueden_eliminar is None:
            # Permiso por defecto: solo ADMIN
            return usuario.tiene_rol('ADMIN')
        
        if not self.roles_pueden_eliminar:
            # Array vacío: nadie puede eliminar
            return False
        
        # Verificar si algún rol del usuario está en la lista
        role_ids_usuario = [rol.id for rol in usuario.roles]
        return any(role_id in self.roles_pueden_eliminar for role_id in role_ids_usuario)
    
    def puede_visualizar(self, usuario):
        """
        Verifica si un usuario puede visualizar esta tabla.
        
        Args:
            usuario: Instancia de Usuario con roles cargados
            
        Returns:
            bool: True si el usuario tiene permiso para visualizar
            
        Lógica:
            - Si roles_pueden_visualizar es None: usar lógica por defecto (todos los autenticados)
            - Si roles_pueden_visualizar es []: nadie puede visualizar
            - Si roles_pueden_visualizar tiene valores: verificar si algún rol del usuario está en la lista
        """
        if self.roles_pueden_visualizar is None:
            # Permiso por defecto: todos los usuarios autenticados
            return True
        
        if not self.roles_pueden_visualizar:
            # Array vacío: nadie puede visualizar
            return False
        
        # Verificar si algún rol del usuario está en la lista
        role_ids_usuario = [rol.id for rol in usuario.roles]
        return any(role_id in self.roles_pueden_visualizar for role_id in role_ids_usuario)
    
    @staticmethod
    def validar_roles_unicos(role_ids):
        """
        Valida que no haya role_id duplicados en un array.
        
        Args:
            role_ids: Lista de role_id a validar
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
            
        Ejemplo:
            valido, error = TablaMetadata.validar_roles_unicos([1, 2, 3])
            if not valido:
                raise ValueError(error)
        """
        if role_ids is None:
            return True, None
        
        if len(role_ids) != len(set(role_ids)):
            duplicados = [r for r in role_ids if role_ids.count(r) > 1]
            return False, f'role_id duplicados: {set(duplicados)}'
        
        return True, None
    
    @staticmethod
    def validar_eliminar_subset_visualizar(roles_eliminar, roles_visualizar):
        """
        Valida que roles_pueden_eliminar ⊆ roles_pueden_visualizar.
        Solo puedes eliminar lo que puedes ver.
        
        Args:
            roles_eliminar: Array de role_id que pueden eliminar
            roles_visualizar: Array de role_id que pueden visualizar
            
        Returns:
            tuple: (es_valido: bool, mensaje_error: str)
        """
        if roles_eliminar is None or roles_visualizar is None:
            # Si alguno es None, no validamos (usa defaults)
            return True, None
        
        set_eliminar = set(roles_eliminar)
        set_visualizar = set(roles_visualizar)
        
        if not set_eliminar.issubset(set_visualizar):
            no_pueden_ver = set_eliminar - set_visualizar
            return False, f'Roles con permiso de eliminación pero sin visualización: {no_pueden_ver}'
        
        return True, None
