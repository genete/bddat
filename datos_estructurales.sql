--
-- PostgreSQL database dump
--

\restrict osGzSIHQ7azwPzahb0hVk1N2RCZUjXd7Mmd9jdqkDrTQ10TeIJjB0ypmWtkwX33

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: municipios; Type: TABLE DATA; Schema: estructura; Owner: -
--



--
-- Data for Name: tipos_expedientes; Type: TABLE DATA; Schema: estructura; Owner: -
--

INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (1, 'Transporte', 'Expediente que tramita instalaciones de transporte de energía eléctrica');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (2, 'Distribución', 'Expediente que tramita instalaciones de distribución de energía eléctrica');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (3, 'Distribución cedida', 'Expediente que tramita instalaciones de distribución de energía eléctrica cedidas de particular a compañía');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (4, 'Renovable', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes renovables');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (5, 'Autoconsumo', 'Expediente que tramita instalaciones de autoconsumo');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (6, 'LineaDirecta', 'Expediente que tramita líneas directas para consumo');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (7, 'Convencional', 'Expediente que tramita instalaciones de generación de energía eléctrica por fuentes convencionales');
INSERT INTO estructura.tipos_expedientes (id, tipo, descripcion) VALUES (8, 'Otros', 'Otros tipos de expedientes');


--
-- Data for Name: tipos_fases; Type: TABLE DATA; Schema: estructura; Owner: -
--

INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (1, 'REGISTRO_SOLICITUD', 'Registro de Solicitud');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (2, 'ADMISIBILIDAD', 'Admisibilidad Administrativa de la Solicitud');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (3, 'ANALISIS_TECNICO', 'Análisis Técnico');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (4, 'CONSULTA_MINISTERIO', 'Consulta al Ministerio');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (5, 'COMPATIBILIDAD_AMBIENTAL', 'Compatibilidad Ambiental');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (6, 'ADMISION_TRAMITE', 'Admisión a Trámite para expedientes de generación renovable');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (7, 'CONSULTAS', 'Consultas a Organismos');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (8, 'INFORMACION_PUBLICA', 'Información Pública');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (9, 'FIGURA_AMBIENTAL_EXTERNA', 'Instrumento Ambiental Externo, no integrado en la autorización sustantiva');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (10, 'AAU_AAUS_INTEGRADA', 'AAU/AAUS Integrada en la autorización sustantiva');
INSERT INTO estructura.tipos_fases (id, codigo, nombre) VALUES (11, 'RESOLUCION', 'Resolución');


--
-- Data for Name: tipos_ia; Type: TABLE DATA; Schema: estructura; Owner: -
--

INSERT INTO estructura.tipos_ia (id, siglas, descripcion) VALUES (1, 'AAI', 'Autorización Ambiental Integrada');
INSERT INTO estructura.tipos_ia (id, siglas, descripcion) VALUES (2, 'AAU', 'Autorización Ambiental Unificada');
INSERT INTO estructura.tipos_ia (id, siglas, descripcion) VALUES (3, 'AAUS', 'Autorización Ambiental Unificada Simplificada');
INSERT INTO estructura.tipos_ia (id, siglas, descripcion) VALUES (4, 'CA', 'Calificación Ambiental');
INSERT INTO estructura.tipos_ia (id, siglas, descripcion) VALUES (5, 'EXENTO', 'Exento de instrumento ambiental');


--
-- Data for Name: tipos_resultados_fases; Type: TABLE DATA; Schema: estructura; Owner: -
--



--
-- Data for Name: tipos_solicitudes; Type: TABLE DATA; Schema: estructura; Owner: -
--

INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (1, 'AAP', 'Autorización Administrativa Previa');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (2, 'AAC', 'Autorización Administrativa de Construcción');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (3, 'DUP', 'Declaración de Utilidad Pública');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (4, 'AAE_PROVISIONAL', 'Autorización de Explotación Provisional para Pruebas');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (5, 'AAE_DEFINITIVA', 'Autorización de Explotación Definitiva');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (6, 'AAT', 'Autorización de Transmisión de Titularidad');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (7, 'RAIPEE_PREVIA', 'Inscripción Previa en RAIPEE');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (8, 'RAIPEE_DEFINITIVA', 'Inscripción Definitiva en RAIPEE');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (9, 'RADNE', 'Inscripción en Registro de Autoconsumo');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (10, 'CIERRE', 'Autorización de Cierre de Instalación');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (11, 'DESISTIMIENTO', 'Desistimiento de la Solicitud');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (12, 'RENUNCIA', 'Renuncia de la Autorización');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (13, 'AMPLIACION_PLAZO', 'Ampliación de Plazo de Ejecución');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (14, 'INTERESADO', 'Condición de Interesado en el Expediente');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (15, 'RECURSO', 'Recurso Administrativo');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (16, 'CORRECCION_ERRORES', 'Corrección de Errores en Resolución');
INSERT INTO estructura.tipos_solicitudes (id, siglas, descripcion) VALUES (17, 'OTRO', 'Otro tipo de solicitud');


--
-- Data for Name: tipos_tareas; Type: TABLE DATA; Schema: estructura; Owner: -
--



--
-- Data for Name: tipos_tramites; Type: TABLE DATA; Schema: estructura; Owner: -
--



--
-- Name: municipios_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.municipios_id_seq', 1, false);


--
-- Name: tipos_expedientes_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_expedientes_id_seq', 8, true);


--
-- Name: tipos_fases_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_fases_id_seq', 11, true);


--
-- Name: tipos_ia_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_ia_id_seq', 5, true);


--
-- Name: tipos_resultados_fases_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_resultados_fases_id_seq', 1, false);


--
-- Name: tipos_solicitudes_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_solicitudes_id_seq', 17, true);


--
-- Name: tipos_tareas_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_tareas_id_seq', 1, false);


--
-- Name: tipos_tramites_id_seq; Type: SEQUENCE SET; Schema: estructura; Owner: -
--

SELECT pg_catalog.setval('estructura.tipos_tramites_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict osGzSIHQ7azwPzahb0hVk1N2RCZUjXd7Mmd9jdqkDrTQ10TeIJjB0ypmWtkwX33

