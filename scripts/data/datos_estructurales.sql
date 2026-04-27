-- =============================================================================
-- datos_estructurales.sql — Datos de catálogo del sistema BDDAT
-- Generado: 2026-04-26
--
-- Uso: ejecutar tras `flask db upgrade` en cualquier instalación limpia.
--   psql -U bddat_admin -h localhost bddat < scripts/data/datos_estructurales.sql
--
-- municipios (8132 registros) se carga aparte:
--   psql -U bddat_admin -h localhost bddat < scripts/data/municipios.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- roles
-- -----------------------------------------------------------------------------
INSERT INTO roles (id, nombre, descripcion) VALUES (1, 'ADMIN', 'Administrador total: gestiona alembic_version y schema legacy');
INSERT INTO roles (id, nombre, descripcion) VALUES (2, 'SUPERVISOR', 'Gestión de usuarios, tablas maestras y configuración del sistema');
INSERT INTO roles (id, nombre, descripcion) VALUES (3, 'TRAMITADOR', 'Tramitación de expedientes con acceso lectura a estructura');
INSERT INTO roles (id, nombre, descripcion) VALUES (4, 'ADMINISTRATIVO', 'Tareas administrativas con acceso lectura a estructura');

-- -----------------------------------------------------------------------------
-- tipos_expedientes
-- -----------------------------------------------------------------------------
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (1, 'Transporte', 'Expediente que tramita instalaciones de transporte de energía eléctrica', 'Transporte');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (2, 'Distribución', 'Expediente que tramita instalaciones de distribución de energía eléctrica', 'Distribución');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (3, 'Distribución cedida', 'Expediente que tramita instalaciones de distribución de energía eléctrica cedidas de particular a compañía', 'Distribución cedida');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (4, 'Renovable', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes renovables', 'Renovable');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (5, 'Autoconsumo', 'Expediente que tramita instalaciones de autoconsumo', 'Autoconsumo');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (6, 'LineaDirecta', 'Expediente que tramita líneas directas para consumo', 'Línea Directa');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (7, 'Convencional', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes convencionales', 'Convencional');
INSERT INTO tipos_expedientes (id, tipo, descripcion, nombre_en_plantilla) VALUES (8, 'Otros', 'Otros tipos de expedientes', 'Otros');

-- -----------------------------------------------------------------------------
-- tipos_fases
-- -----------------------------------------------------------------------------
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (1, 'ANALISIS_SOLICITUD', 'Análisis de Solicitud', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (2, 'CONSULTA_MINISTERIO', 'Consulta al Ministerio', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (3, 'COMPATIBILIDAD_AMBIENTAL', 'Compatibilidad Ambiental', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (4, 'CONSULTAS', 'Consultas a Organismos', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (5, 'INFORMACION_PUBLICA', 'Información Pública', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (6, 'FIGURA_AMBIENTAL_EXTERNA', 'Instrumento Ambiental Externo', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (7, 'AAU_AAUS_INTEGRADA', 'AAU/AAUS Integrada', NULL, NULL, FALSE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (8, 'RESOLUCION', 'Resolución', NULL, NULL, TRUE);
INSERT INTO tipos_fases (id, codigo, nombre, abrev, nombre_en_plantilla, es_finalizadora) VALUES (9, 'RECONOCIMIENTO_INTERESADO', 'Reconocimiento de Interesado', 'Rec. Interesado', 'Reconocimiento de Interesado', TRUE);

-- -----------------------------------------------------------------------------
-- tipos_tramites
-- -----------------------------------------------------------------------------
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (1, 'ANALISIS_DOCUMENTAL', 'Análisis Documental', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (2, 'REQUERIMIENTO_SUBSANACION', 'Requerimiento de Subsanación', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (3, 'COMUNICACION_INICIO', 'Comunicación de Inicio', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (4, 'SOLICITUD_INFORME', 'Solicitud de Informe', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (5, 'RECEPCION_INFORME', 'Recepción de Informe', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (6, 'SOLICITUD_COMPATIBILIDAD', 'Solicitud de Compatibilidad', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (7, 'AUDIENCIA', 'Audiencia', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (8, 'CONSULTA_SEPARATA', 'Separata a Organismo', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (9, 'CONSULTA_TRASLADO_TITULAR', 'Traslado al Titular', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (10, 'CONSULTA_TRASLADO_ORGANISMO', 'Traslado al Organismo', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (11, 'ANUNCIO_BOE', 'Anuncio en BOE', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (12, 'ANUNCIO_BOP', 'Anuncio en BOP', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (13, 'ANUNCIO_PRENSA', 'Anuncio en Prensa', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (14, 'TABLON_AYUNTAMIENTOS', 'Tablón de Ayuntamientos', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (15, 'PORTAL_TRANSPARENCIA', 'Portal de Transparencia', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (16, 'RECEPCION_ALEGACION', 'Recepción de Alegación', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (17, 'ANALISIS_ALEGACIONES', 'Análisis de Alegaciones', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (18, 'SOLICITUD_FIGURA', 'Solicitud de Instrumento Ambiental', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (19, 'RECEPCION_FIGURA', 'Recepción de Instrumento Ambiental', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (20, 'REMISION_MEDIO_AMBIENTE', 'Remisión a Medio Ambiente', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (21, 'RECEPCION_DICTAMEN', 'Recepción de Dictamen Ambiental', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (22, 'ELABORACION', 'Elaboración de Resolución', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (23, 'NOTIFICACION', 'Notificación de Resolución', NULL, NULL);
INSERT INTO tipos_tramites (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (24, 'PUBLICACION', 'Publicación de Resolución', NULL, NULL);

-- -----------------------------------------------------------------------------
-- fases_tramites
-- -----------------------------------------------------------------------------
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (1, 1);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (1, 2);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (1, 3);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (2, 4);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (2, 5);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (3, 5);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (3, 6);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (3, 7);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (4, 8);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (4, 9);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (4, 10);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 11);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 12);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 13);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 14);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 15);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 16);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (5, 17);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (6, 18);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (6, 19);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (7, 20);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (7, 21);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (8, 22);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (8, 23);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (8, 24);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (9, 22);
INSERT INTO fases_tramites (tipo_fase_id, tipo_tramite_id) VALUES (9, 23);

-- -----------------------------------------------------------------------------
-- tipos_tareas
-- -----------------------------------------------------------------------------
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (1, 'ANALIZAR', 'Revisión técnica o jurídica de documentación con generación de informe', 'ANÁLISIS', 'Análisis');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (2, 'REDACTAR', 'Creación de documento administrativo (borrador)', 'REDACTAR', 'Redacción');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (3, 'FIRMAR', 'Firma autorizada del documento', 'FIRMAR', 'Firma');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (4, 'NOTIFICAR', 'Comunicación a destinatario identificado', 'NOTIFICAR', 'Notificación');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (5, 'PUBLICAR', 'Publicación en medios oficiales (BOE, BOP, tablón, portal)', 'PUBLICAR', 'Publicación');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (6, 'ESPERAR_PLAZO', 'Suspensión temporal con fecha límite o indefinida', 'PLAZO', 'Espera');
INSERT INTO tipos_tareas (id, codigo, nombre, abrev, nombre_en_plantilla) VALUES (7, 'INCORPORAR', 'Incorporación de documentación externa al sistema', 'INCORPORAR', 'Incorporación');

-- -----------------------------------------------------------------------------
-- tipos_documentos
-- -----------------------------------------------------------------------------
INSERT INTO tipos_documentos (id, codigo, nombre, descripcion, origen) VALUES (1, 'OTROS', 'Otros / Sin clasificar', 'Cajón de sastre para documentos sin tipo semántico definido', 'AMBOS');
INSERT INTO tipos_documentos (id, codigo, nombre, descripcion, origen) VALUES (2, 'DR_NO_DUP', 'Declaración Responsable de No Duplicidad', 'Requerida para iniciar la fase de Información Pública (salvo AAU/AAUS)', 'EXTERNO');

-- -----------------------------------------------------------------------------
-- tipos_solicitudes
-- -----------------------------------------------------------------------------
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (1, 'AAP', 'Autorización Administrativa Previa', 'AAP');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (2, 'AAC', 'Autorización Administrativa de Construcción', 'AAC');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (3, 'DUP', 'Declaración de Utilidad Pública', 'DUP');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (4, 'AE_PROVISIONAL', 'Autorización de Explotación Provisional para Pruebas', 'AAE Provisional');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (5, 'AE_DEFINITIVA', 'Autorización de Explotación Definitiva', 'AAE Definitiva');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (6, 'AAT', 'Autorización de Transmisión de Titularidad', 'AAT');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (7, 'RAIPEE_PREVIA', 'Inscripción Previa en RAIPEE', 'RAIPEE Previa');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (8, 'RAIPEE_DEFINITIVA', 'Inscripción Definitiva en RAIPEE', 'RAIPEE Definitiva');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (9, 'RADNE', 'Inscripción en Registro de Autoconsumo', 'RADNE');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (10, 'CIERRE', 'Autorización de Cierre de Instalación', 'Cierre');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (11, 'DESISTIMIENTO', 'Desistimiento de la Solicitud', 'Desistimiento');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (12, 'RENUNCIA', 'Renuncia de la Autorización', 'Renuncia');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (13, 'AMPLIACION_PLAZO', 'Ampliación de Plazo de Ejecución', 'Ampliación de Plazo');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (14, 'INTERESADO', 'Condición de Interesado en el Expediente', 'Interesado');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (15, 'RECURSO', 'Recurso Administrativo', 'Recurso');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (16, 'CORRECCION_ERRORES', 'Corrección de Errores en Resolución', 'Corrección de Errores');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (17, 'OTRO', 'Otro tipo de solicitud', 'Otro');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (18, 'AAP+AAC', 'Autorización Administrativa Previa + Autorización Administrativa de Construcción', 'AAP+AAC');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (19, 'AAP+AAC+DUP', 'Autorización Administrativa Previa + Construcción + Declaración de Utilidad Pública', 'AAP+AAC+DUP+AAE');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (20, 'AAC+DUP', 'Autorización Administrativa de Construcción + Declaración de Utilidad Pública', 'AAP+AAC+RAIPEE+RADNE');
INSERT INTO tipos_solicitudes (id, siglas, descripcion, nombre_en_plantilla) VALUES (21, 'AE_DEFINITIVA+AAT', 'Autorización de Explotación Definitiva + Autorización de Transmisión de Titularidad', 'AAT+Ampliación Plazo');

-- -----------------------------------------------------------------------------
-- tipos_resultados_fases
-- -----------------------------------------------------------------------------
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (1, 'FAVORABLE', 'Favorable');
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (2, 'FAVORABLE_CONDICIONADO', 'Favorable con Condiciones');
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (3, 'DESFAVORABLE', 'Desfavorable');
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (4, 'NO_PROCEDE', 'No Procede');
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (5, 'DESISTIDA', 'Desistida por el Solicitante');
INSERT INTO tipos_resultados_fases (id, codigo, nombre) VALUES (6, 'ARCHIVADA', 'Archivada');

-- -----------------------------------------------------------------------------
-- tipos_ia
-- -----------------------------------------------------------------------------
INSERT INTO tipos_ia (id, siglas, descripcion) VALUES (1, 'AAI', 'Autorización Ambiental Integrada');
INSERT INTO tipos_ia (id, siglas, descripcion) VALUES (2, 'AAU', 'Autorización Ambiental Unificada');
INSERT INTO tipos_ia (id, siglas, descripcion) VALUES (3, 'AAUS', 'Autorización Ambiental Unificada Simplificada');
INSERT INTO tipos_ia (id, siglas, descripcion) VALUES (4, 'CA', 'Calificación Ambiental');
INSERT INTO tipos_ia (id, siglas, descripcion) VALUES (5, 'EXENTO', 'Exento de instrumento ambiental');

-- -----------------------------------------------------------------------------
-- solicitudes_fases (whitelist tipo_solicitud × tipo_fase)
-- -----------------------------------------------------------------------------
INSERT INTO solicitudes_fases (tipo_solicitud_id, tipo_fase_id) VALUES (14, 9);  -- INTERESADO → RECONOCIMIENTO_INTERESADO
INSERT INTO solicitudes_fases (tipo_solicitud_id, tipo_fase_id) VALUES (11, 8);  -- DESISTIMIENTO → RESOLUCION
INSERT INTO solicitudes_fases (tipo_solicitud_id, tipo_fase_id) VALUES (12, 8);  -- RENUNCIA → RESOLUCION
INSERT INTO solicitudes_fases (tipo_solicitud_id, tipo_fase_id) VALUES (17, 8);  -- OTRO → RESOLUCION

-- normas
-- -----------------------------------------------------------------------------
INSERT INTO normas (id, codigo, titulo, url_eli) VALUES (3, 'RD1955_2000', 'Real Decreto 1955/2000, de 1 de diciembre', NULL);
INSERT INTO normas (id, codigo, titulo, url_eli) VALUES (4, 'D9_2011', 'Decreto 9/2011, de 26 de enero (Junta de Andalucía)', NULL);

-- -----------------------------------------------------------------------------
-- catalogo_variables (depende de normas)
-- -----------------------------------------------------------------------------
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (1, 'fase_ip_finalizada', 'Fase IP finalizada (o existente)', 'boolean', NULL, true);
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (2, 'tramite_publicar_existe', 'Trámite PUBLICAR existe en fase RESOLUCIÓN', 'boolean', NULL, true);
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (3, 'sin_linea_aerea', 'Sin línea aérea (instalación íntegramente subterránea)', 'boolean', NULL, true);
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (4, 'max_tension_nominal_kv', 'Tensión nominal máxima (kV)', 'numerico', NULL, true);
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (5, 'solo_suelo_urbano_urbanizable', 'Recorrido íntegro en suelo urbano o urbanizable', 'boolean', NULL, true);
INSERT INTO catalogo_variables (id, nombre, etiqueta, tipo_dato, norma_id, activa) VALUES (6, 'existe_fase_finalizadora_cerrada', 'Existe fase finalizadora cerrada en la solicitud', 'boolean', NULL, true);

-- municipios: cargar aparte con scripts/data/municipios.sql
