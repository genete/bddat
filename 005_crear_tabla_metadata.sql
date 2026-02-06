-- =====================================================================
-- Migración 005: Crear tabla TABLA_METADATA
-- Issue: #85 - Metadatos de tablas para visualización y permisos
-- Fecha: 2026-02-06
-- Fase: 1 - Estructura base y datos iniciales
-- =====================================================================

-- PROPÓSITO:
--   Centralizar la configuración de cómo se visualizan y gestionan las tablas
--   en la interfaz de usuario, incluyendo permisos de visualización y eliminación
--   por rol.

-- FILOSOFÍA:
--   - Separar lógica de presentación de lógica de negocio
--   - Control granular de permisos por rol usando arrays de INTEGER
--   - Administrable sin cambios de código
--   - Validaciones fuertes a nivel de BD

-- ROLES (IDs de referencia):
--   1 = ADMIN        - Acceso completo al sistema
--   2 = SUPERVISOR   - Supervisión y gestión amplia
--   3 = TRAMITADOR   - Tramitación de expedientes
--   4 = ADMINISTRATIVO - Soporte administrativo
--   5 = CONTROLADOR  - Control y validación

-- =====================================================================
-- 1. CREAR TABLA
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.tabla_metadata (
    id SERIAL PRIMARY KEY,
    
    -- Identificación de la tabla
    nombre_tabla VARCHAR(100) NOT NULL UNIQUE,
    
    -- Títulos para interfaz
    titulo_singular VARCHAR(100) NOT NULL,
    titulo_plural VARCHAR(100) NOT NULL,
    
    -- Configuración de ordenamiento
    campo_orden_defecto VARCHAR(100) NOT NULL,
    orden_asc BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Permisos por rol (arrays de INTEGER)
    roles_pueden_eliminar INTEGER[],
    roles_pueden_visualizar INTEGER[]
);

-- =====================================================================
-- 2. COMENTARIOS EN LA TABLA Y COLUMNAS
-- =====================================================================

COMMENT ON TABLE public.tabla_metadata IS 
'Metadatos de configuración para tablas del sistema. Define cómo se visualizan, ordenan y gestionan las tablas en la interfaz, incluyendo permisos de visualización y eliminación por rol.';

COMMENT ON COLUMN public.tabla_metadata.id IS 
'Identificador único autogenerado';

COMMENT ON COLUMN public.tabla_metadata.nombre_tabla IS 
'Nombre completo de la tabla (schema.tabla). Ejemplo: public.usuarios, expedientes.expedientes';

COMMENT ON COLUMN public.tabla_metadata.titulo_singular IS 
'Nombre singular para mostrar en interfaz. Ejemplo: Usuario, Expediente, Provincia';

COMMENT ON COLUMN public.tabla_metadata.titulo_plural IS 
'Nombre plural para mostrar en interfaz. Ejemplo: Usuarios, Expedientes, Provincias';

COMMENT ON COLUMN public.tabla_metadata.campo_orden_defecto IS 
'Campo por defecto para ordenar listados. Ejemplo: apellido1, fecha_alta, nombre';

COMMENT ON COLUMN public.tabla_metadata.orden_asc IS 
'Dirección del orden por defecto. TRUE=Ascendente (A-Z, 0-9, antiguos primero), FALSE=Descendente (Z-A, 9-0, recientes primero)';

COMMENT ON COLUMN public.tabla_metadata.roles_pueden_eliminar IS 
'Array de role_id que tienen permiso para eliminar registros. Ejemplo: ARRAY[1,2] = ADMIN y SUPERVISOR. NULL = usar permisos por defecto, ARRAY[]::INTEGER[] = nadie puede eliminar';

COMMENT ON COLUMN public.tabla_metadata.roles_pueden_visualizar IS 
'Array de role_id que tienen permiso para visualizar la tabla. Ejemplo: ARRAY[1,2,3,4,5] = todos. NULL = usar permisos por defecto, ARRAY[]::INTEGER[] = nadie puede visualizar';

-- =====================================================================
-- 3. CONSTRAINTS DE VALIDACIÓN
-- =====================================================================

-- Validar que campos obligatorios no estén vacíos
ALTER TABLE public.tabla_metadata
    ADD CONSTRAINT chk_nombre_tabla_not_empty 
    CHECK (nombre_tabla IS NOT NULL AND TRIM(nombre_tabla) != '');

ALTER TABLE public.tabla_metadata
    ADD CONSTRAINT chk_titulo_singular_not_empty 
    CHECK (titulo_singular IS NOT NULL AND TRIM(titulo_singular) != '');

ALTER TABLE public.tabla_metadata
    ADD CONSTRAINT chk_titulo_plural_not_empty 
    CHECK (titulo_plural IS NOT NULL AND TRIM(titulo_plural) != '');

ALTER TABLE public.tabla_metadata
    ADD CONSTRAINT chk_campo_orden_not_empty 
    CHECK (campo_orden_defecto IS NOT NULL AND TRIM(campo_orden_defecto) != '');

-- =====================================================================
-- 4. ÍNDICES
-- =====================================================================

-- Índice para búsquedas frecuentes por nombre_tabla
CREATE INDEX IF NOT EXISTS idx_tabla_metadata_nombre 
    ON public.tabla_metadata(nombre_tabla);

-- =====================================================================
-- 5. DATOS INICIALES - Tablas principales del sistema
-- =====================================================================

-- TABLA: public.usuarios
-- Permisos: Solo ADMIN puede eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'public.usuarios',
    'Usuario',
    'Usuarios',
    'apellido1',
    TRUE,
    ARRAY[1]::INTEGER[],  -- Solo ADMIN
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: public.roles
-- Permisos: Solo ADMIN puede eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'public.roles',
    'Rol',
    'Roles',
    'nombre',
    TRUE,
    ARRAY[1]::INTEGER[],  -- Solo ADMIN
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: estructura.municipios
-- Permisos: Solo ADMIN puede eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'estructura.municipios',
    'Municipio',
    'Municipios',
    'nombre',
    TRUE,
    ARRAY[1]::INTEGER[],  -- Solo ADMIN
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: estructura.tipos_instalacion
-- Permisos: ADMIN y SUPERVISOR pueden eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'estructura.tipos_instalacion',
    'Tipo de Instalación',
    'Tipos de Instalación',
    'nombre',
    TRUE,
    ARRAY[1, 2]::INTEGER[],  -- ADMIN y SUPERVISOR
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: estructura.tipos_documento
-- Permisos: ADMIN y SUPERVISOR pueden eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'estructura.tipos_documento',
    'Tipo de Documento',
    'Tipos de Documento',
    'nombre',
    TRUE,
    ARRAY[1, 2]::INTEGER[],  -- ADMIN y SUPERVISOR
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: estructura.estados_expediente
-- Permisos: Solo ADMIN puede eliminar, todos pueden visualizar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'estructura.estados_expediente',
    'Estado de Expediente',
    'Estados de Expediente',
    'orden_visualizacion',
    TRUE,
    ARRAY[1]::INTEGER[],  -- Solo ADMIN
    ARRAY[1, 2, 3, 4, 5]::INTEGER[]  -- Todos
);

-- TABLA: expedientes.expedientes
-- Permisos: ADMIN y SUPERVISOR pueden eliminar, no visible para ADMINISTRATIVO
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'expedientes.expedientes',
    'Expediente',
    'Expedientes',
    'fecha_alta',
    FALSE,  -- Más recientes primero
    ARRAY[1, 2]::INTEGER[],  -- ADMIN y SUPERVISOR
    ARRAY[1, 2, 3, 5]::INTEGER[]  -- Todos excepto ADMINISTRATIVO
);

-- TABLA: expedientes.documentos
-- Permisos: ADMIN, SUPERVISOR y TRAMITADOR pueden eliminar
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'expedientes.documentos',
    'Documento',
    'Documentos',
    'fecha_carga',
    FALSE,  -- Más recientes primero
    ARRAY[1, 2, 3]::INTEGER[],  -- ADMIN, SUPERVISOR, TRAMITADOR
    ARRAY[1, 2, 3, 5]::INTEGER[]  -- No ADMINISTRATIVO
);

-- TABLA: expedientes.seguimiento
-- Permisos: Solo ADMIN puede eliminar, visible para roles de gestión
INSERT INTO public.tabla_metadata (
    nombre_tabla,
    titulo_singular,
    titulo_plural,
    campo_orden_defecto,
    orden_asc,
    roles_pueden_eliminar,
    roles_pueden_visualizar
) VALUES (
    'expedientes.seguimiento',
    'Seguimiento',
    'Seguimientos',
    'fecha',
    FALSE,  -- Más recientes primero
    ARRAY[1]::INTEGER[],  -- Solo ADMIN
    ARRAY[1, 2, 3, 5]::INTEGER[]  -- Roles de gestión
);

-- =====================================================================
-- 6. VERIFICACIÓN
-- =====================================================================

-- Mostrar resumen de registros insertados
SELECT 
    nombre_tabla,
    titulo_plural,
    ARRAY_LENGTH(roles_pueden_eliminar, 1) as num_roles_eliminan,
    ARRAY_LENGTH(roles_pueden_visualizar, 1) as num_roles_visualizan
FROM public.tabla_metadata
ORDER BY nombre_tabla;

-- =====================================================================
-- NOTAS PARA ROLLBACK:
-- =====================================================================
-- DROP TABLE IF EXISTS public.tabla_metadata CASCADE;

-- =====================================================================
-- FIN DE MIGRACIÓN 005
-- =====================================================================
