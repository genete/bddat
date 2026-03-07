--
-- Crear usuario ADMIN inicial para el sistema BDDAT
-- Este archivo se ejecuta una sola vez tras cargar datos_roles.sql
-- IMPORTANTE: Cambiar la contraseña tras el primer login
-- Usuario: ADMIN
-- Password: admin123
-- Ubicación: raíz del proyecto
--

-- Crear usuario ADMIN inicial
INSERT INTO public.usuarios (siglas, nombre, apellido1, apellido2, email, activo, password_hash) 
VALUES (
    'ADMIN',
    'Administrador',
    'Sistema',
    NULL,
    'admin@bddat.local',
    true,
    'scrypt:32768:8:1$TU_HASH_REAL_AQUI'  -- Reemplazar con el hash generado
)
ON CONFLICT (siglas) DO NOTHING;

-- Asignar rol ADMIN al usuario
INSERT INTO public.usuarios_roles (usuario_id, rol_id)
SELECT u.id, r.id
FROM public.usuarios u, public.roles r
WHERE u.siglas = 'ADMIN' AND r.nombre = 'ADMIN'
ON CONFLICT DO NOTHING;

-- Actualizar hash para password 'admin123' cambiar obligaroriamente.
UPDATE public.usuarios 
SET password_hash = 'scrypt:32768:8:1$0BX6LMEjARw1X4Ix$85e914815e4e83cdf8edd39e8c6f287a1b66753799390e3ee914355673e8f79f0a4cfae0784b83d58b362c2827e3c076855c19d8e9a8b65f2489cb73c81124e2'
WHERE siglas = 'ADMIN';



-- Verificar que se creó correctamente
SELECT 
    u.id,
    u.siglas,
    u.nombre,
    u.apellido1,
    u.email,
    u.activo,
    r.nombre AS rol
FROM public.usuarios u
JOIN public.usuarios_roles ur ON u.id = ur.usuario_id
JOIN public.roles r ON ur.rol_id = r.id
WHERE u.siglas = 'ADMIN';
