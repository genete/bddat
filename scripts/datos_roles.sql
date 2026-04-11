--
-- Datos iniciales de roles del sistema BDDAT
-- Este archivo se ejecuta una sola vez tras crear el schema
-- Ubicación: raíz del proyecto junto a schema.sql y datos_estructurales.sql
--

-- Insertar roles básicos del sistema
INSERT INTO public.roles (id, nombre, descripcion) VALUES
(1, 'ADMIN', 'Administrador total: gestiona alembic_version y schema legacy'),
(2, 'SUPERVISOR', 'Gestión de usuarios, tablas maestras y configuración del sistema'),
(3, 'TRAMITADOR', 'Tramitación de expedientes con acceso lectura a estructura'),
(4, 'ADMINISTRATIVO', 'Tareas administrativas con acceso lectura a estructura')
ON CONFLICT (id) DO NOTHING;

-- Ajustar secuencia para próximo ID
SELECT setval('public.roles_id_seq', 4, true);

-- Verificación
SELECT id, nombre, descripcion FROM public.roles ORDER BY id;
