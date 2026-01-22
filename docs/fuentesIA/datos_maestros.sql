-- =====================================================
-- DATOS MAESTROS - Definición de lógica de negocio
-- =====================================================
-- Actualizado: 22/01/2026
-- Tablas: tipos_expedientes, tipos_fases, tipos_ia, tipos_solicitudes
-- =====================================================

-- Tabla: tipos_expedientes (8 tipos, IDs 1-8)
-- --------------------------------------------------
INSERT INTO estructura.tipos_expedientes (tipo, descripcion) VALUES
('Transporte', 'Expediente que tramita instalaciones de transporte de energía eléctrica'),
('Distribución', 'Expediente que tramita instalaciones de distribución de energía eléctrica'),
('Distribución cedida', 'Expediente que tramita instalaciones de distribución de energía eléctrica cedidas de particular a compañía'),
('Renovable', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes renovables'),
('Autoconsumo', 'Expediente que tramita instalaciones de autoconsumo'),
('Línea Directa', 'Expediente que tramita líneas directas para consumo'),
('Convencional', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes convencionales'),
('Otros', 'Otros tipos de expedientes');

-- Tabla: tipos_ia (5 tipos, IDs 1-5)
-- --------------------------------------------------
INSERT INTO estructura.tipos_ia (siglas, descripcion) VALUES
('AAI', 'Autorización Ambiental Integrada'),
('AAU', 'Autorización Ambiental Unificada'),
('AAUS', 'Autorización Ambiental Unificada Simplificada'),
('CA', 'Calificación Ambiental'),
('NO_SUJETO', 'No Sujeto a Instrumento Ambiental');

-- Tabla: tipos_fases (11 fases, IDs 1-11)
-- --------------------------------------------------
INSERT INTO estructura.tipos_fases (codigo, nombre) VALUES
('REGISTRO_SOLICITUD', 'Registro de Solicitud'),
('ADMISIBILIDAD', 'Admisibilidad de la Solicitud'),
('ANALISIS_TECNICO', 'Análisis Técnico'),
('CONSULTA_MINISTERIO', 'Consulta al Ministerio'),
('COMPATIBILIDAD_AMBIENTAL', 'Compatibilidad Ambiental'),
('ADMISION_TRAMITE', 'Admisión a Trámite'),
('CONSULTAS', 'Consultas a Organismos'),
('INFORMACION_PUBLICA', 'Información Pública'),
('FIGURA_AMBIENTAL_EXTERNA', 'Instrumento Ambiental Externo'),
('AAU_AAUS_INTEGRADA', 'AAU/AAUS Integrada'),
('RESOLUCION', 'Resolución');

-- Tabla: tipos_solicitudes (17 tipos individuales, IDs 1-17)
-- --------------------------------------------------
-- Filosofía v3.0: Tipos INDIVIDUALES sin combinaciones explícitas
-- Las combinaciones (AAP+AAC, AAP+DUP, etc.) se gestionan mediante
-- tabla puente solicitudes_tipos (relación N:M)
-- Basado en: LSE 24/2013, RD 1955/2000, RD 413/2014, RDL 7/2025, RD 244/2019
-- --------------------------------------------------

INSERT INTO estructura.tipos_solicitudes (siglas, descripcion) VALUES
-- Fase PREVIA (art. 53.1.a LSE)
('AAP', 'Autorización Administrativa Previa'),

-- Fase CONSTRUCCIÓN (art. 53.1.b LSE)
('AAC', 'Autorización Administrativa de Construcción'),

-- Declaración Utilidad Pública (art. 54 LSE)
('DUP', 'Declaración de Utilidad Pública'),

-- Fase EXPLOTACIÓN (art. 53.1.c LSE - dividida desde RDL 7/2025)
('AAE_PROVISIONAL', 'Autorización de Explotación Provisional para Pruebas'),
('AAE_DEFINITIVA', 'Autorización de Explotación Definitiva'),

-- Transmisión de titularidad (art. 56 LSE)
('AAT', 'Autorización de Transmisión de Titularidad'),

-- RAIPEE - Renovables producción (RD 413/2014 art. 37-42)
('RAIPEE_PREVIA', 'Inscripción Previa en RAIPEE'),
('RAIPEE_DEFINITIVA', 'Inscripción Definitiva en RAIPEE'),

-- RADNE - Autoconsumo (RD 244/2019)
('RADNE', 'Inscripción en Registro de Autoconsumo'),

-- Cierre de instalación
('CIERRE', 'Autorización de Cierre de Instalación'),

-- Actos sobre solicitudes
('DESISTIMIENTO', 'Desistimiento de la Solicitud'),
('RENUNCIA', 'Renuncia de la Autorización'),

-- Gestión de expedientes
('AMPLIACION_PLAZO', 'Ampliación de Plazo de Ejecución'),
('INTERESADO', 'Condición de Interesado en el Expediente'),
('RECURSO', 'Recurso Administrativo'),

-- Otros procedimientos administrativos
('CORRECCION_ERRORES', 'Corrección de Errores en Resolución'),
('OTRO', 'Otro tipo de solicitud');

-- Verificación de secuencias
SELECT setval('estructura.tipos_expedientes_id_seq', (SELECT MAX(id) FROM estructura.tipos_expedientes));
SELECT setval('estructura.tipos_ia_id_seq', (SELECT MAX(id) FROM estructura.tipos_ia));
SELECT setval('estructura.tipos_fases_id_seq', (SELECT MAX(id) FROM estructura.tipos_fases));
SELECT setval('estructura.tipos_solicitudes_id_seq', (SELECT MAX(id) FROM estructura.tipos_solicitudes));
