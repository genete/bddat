--
-- PostgreSQL database dump
--

\restrict lZf6Tf80m9dCOJKsm98Ra3rvkOx78oCuCDgKmBUL10dD1lsu0goMP6iruBSUzBZ

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
-- Name: estructura; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA estructura;


ALTER SCHEMA estructura OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: municipios; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.municipios (
    id integer NOT NULL,
    codigo character varying(10) NOT NULL,
    nombre character varying(200) NOT NULL,
    provincia character varying(100) NOT NULL
);


ALTER TABLE estructura.municipios OWNER TO postgres;

--
-- Name: COLUMN municipios.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.municipios.id IS 'Identificador único autogenerado del municipio';


--
-- Name: COLUMN municipios.codigo; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.municipios.codigo IS 'Código INE oficial de 5 dígitos';


--
-- Name: COLUMN municipios.nombre; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.municipios.nombre IS 'Denominación oficial del municipio';


--
-- Name: COLUMN municipios.provincia; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.municipios.provincia IS 'Provincia a la que pertenece el municipio';


--
-- Name: municipios_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.municipios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.municipios_id_seq OWNER TO postgres;

--
-- Name: municipios_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.municipios_id_seq OWNED BY estructura.municipios.id;


--
-- Name: solicitudes_tipos; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.solicitudes_tipos (
    id integer NOT NULL,
    solicitudid integer NOT NULL,
    tiposolicitudid integer NOT NULL
);


ALTER TABLE estructura.solicitudes_tipos OWNER TO postgres;

--
-- Name: TABLE solicitudes_tipos; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON TABLE estructura.solicitudes_tipos IS 'Tabla puente que relaciona solicitudes con sus tipos individuales.
Una solicitud puede tener múltiples tipos (AAP+AAC+DUP → 3 registros).
Permite motor de reglas basado en tipos individuales sin duplicación de lógica.';


--
-- Name: COLUMN solicitudes_tipos.solicitudid; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.solicitudes_tipos.solicitudid IS 'FK a estructura.solicitudes(id)';


--
-- Name: COLUMN solicitudes_tipos.tiposolicitudid; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.solicitudes_tipos.tiposolicitudid IS 'FK a estructura.tipos_solicitudes(id)';


--
-- Name: solicitudes_tipos_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.solicitudes_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.solicitudes_tipos_id_seq OWNER TO postgres;

--
-- Name: solicitudes_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.solicitudes_tipos_id_seq OWNED BY estructura.solicitudes_tipos.id;


--
-- Name: tipos_expedientes; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_expedientes (
    id integer NOT NULL,
    tipo character varying(100),
    descripcion character varying(200)
);


ALTER TABLE estructura.tipos_expedientes OWNER TO postgres;

--
-- Name: tipos_expedientes_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_expedientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_expedientes_id_seq OWNER TO postgres;

--
-- Name: tipos_expedientes_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_expedientes_id_seq OWNED BY estructura.tipos_expedientes.id;


--
-- Name: tipos_fases; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_fases (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_fases OWNER TO postgres;

--
-- Name: TABLE tipos_fases; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON TABLE estructura.tipos_fases IS 'Tabla maestra que define las fases procedimentales de tramitación administrativa. 
Basadas en estructura normativa del procedimiento administrativo eléctrico.
El CODIGO es inmutable y se usa en lógica de reglas de negocio.';


--
-- Name: COLUMN tipos_fases.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_fases.id IS 'Identificador único del tipo de fase';


--
-- Name: COLUMN tipos_fases.codigo; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_fases.codigo IS 'Código único identificativo de la fase (sin espacios, inmutable)';


--
-- Name: COLUMN tipos_fases.nombre; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_fases.nombre IS 'Denominación completa de la fase para interfaz de usuario';


--
-- Name: tipos_fases_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_fases_id_seq OWNER TO postgres;

--
-- Name: tipos_fases_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_fases_id_seq OWNED BY estructura.tipos_fases.id;


--
-- Name: tipos_ia; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_ia (
    id integer NOT NULL,
    siglas character varying(10) NOT NULL,
    descripcion character varying(200)
);


ALTER TABLE estructura.tipos_ia OWNER TO postgres;

--
-- Name: tipos_ia_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_ia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_ia_id_seq OWNER TO postgres;

--
-- Name: tipos_ia_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_ia_id_seq OWNED BY estructura.tipos_ia.id;


--
-- Name: tipos_resultados_fases; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_resultados_fases (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_resultados_fases OWNER TO postgres;

--
-- Name: COLUMN tipos_resultados_fases.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.id IS 'Identificador único autogenerado del tipo de resultado';


--
-- Name: COLUMN tipos_resultados_fases.codigo; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.codigo IS 'Código único inmutable del resultado (usado en lógica de reglas)';


--
-- Name: COLUMN tipos_resultados_fases.nombre; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.nombre IS 'Denominación completa del resultado para interfaz de usuario';


--
-- Name: tipos_resultados_fases_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_resultados_fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_resultados_fases_id_seq OWNER TO postgres;

--
-- Name: tipos_resultados_fases_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_resultados_fases_id_seq OWNED BY estructura.tipos_resultados_fases.id;


--
-- Name: tipos_solicitudes; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_solicitudes (
    id integer NOT NULL,
    siglas character varying(100) NOT NULL,
    descripcion character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_solicitudes OWNER TO postgres;

--
-- Name: TABLE tipos_solicitudes; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON TABLE estructura.tipos_solicitudes IS 'Tabla maestra de tipos de solicitudes individuales.
Las combinaciones (AAP+AAC, etc.) se gestionan mediante tabla puente solicitudes_tipos.
Motor de reglas aplica lógica sobre tipos individuales, no sobre combinaciones.
Basada en nomenclatura legal establecida en normativa sectorial eléctrica (RD 1955/2000).';


--
-- Name: COLUMN tipos_solicitudes.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_solicitudes.id IS 'Identificador único del tipo de solicitud';


--
-- Name: COLUMN tipos_solicitudes.siglas; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_solicitudes.siglas IS 'Siglas normalizadas del acto administrativo (AAP, AAC, DUP, etc.)';


--
-- Name: COLUMN tipos_solicitudes.descripcion; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_solicitudes.descripcion IS 'Descripción completa del acto administrativo solicitado';


--
-- Name: tipos_solicitudes_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_solicitudes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_solicitudes_id_seq OWNER TO postgres;

--
-- Name: tipos_solicitudes_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_solicitudes_id_seq OWNED BY estructura.tipos_solicitudes.id;


--
-- Name: tipos_tareas; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_tareas (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_tareas OWNER TO postgres;

--
-- Name: COLUMN tipos_tareas.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tareas.id IS 'Identificador único autogenerado del tipo de tarea';


--
-- Name: COLUMN tipos_tareas.codigo; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tareas.codigo IS 'Código único inmutable de la tarea (usado en lógica de reglas)';


--
-- Name: COLUMN tipos_tareas.nombre; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tareas.nombre IS 'Denominación completa de la tarea para interfaz de usuario';


--
-- Name: tipos_tareas_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_tareas_id_seq OWNER TO postgres;

--
-- Name: tipos_tareas_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_tareas_id_seq OWNED BY estructura.tipos_tareas.id;


--
-- Name: tipos_tramites; Type: TABLE; Schema: estructura; Owner: postgres
--

CREATE TABLE estructura.tipos_tramites (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_tramites OWNER TO postgres;

--
-- Name: COLUMN tipos_tramites.id; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tramites.id IS 'Identificador único autogenerado del tipo de trámite';


--
-- Name: COLUMN tipos_tramites.codigo; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tramites.codigo IS 'Código único inmutable del trámite (usado en lógica de reglas)';


--
-- Name: COLUMN tipos_tramites.nombre; Type: COMMENT; Schema: estructura; Owner: postgres
--

COMMENT ON COLUMN estructura.tipos_tramites.nombre IS 'Denominación completa del trámite para interfaz de usuario';


--
-- Name: tipos_tramites_id_seq; Type: SEQUENCE; Schema: estructura; Owner: postgres
--

CREATE SEQUENCE estructura.tipos_tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_tramites_id_seq OWNER TO postgres;

--
-- Name: tipos_tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: postgres
--

ALTER SEQUENCE estructura.tipos_tramites_id_seq OWNED BY estructura.tipos_tramites.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: documentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documentos (
    id integer NOT NULL,
    expediente_id integer NOT NULL,
    url character varying(500) NOT NULL,
    tipo_contenido character varying(50),
    fecha_administrativa date NOT NULL,
    asunto character varying(500),
    origen character varying(100),
    prioridad integer,
    nombre_display character varying(200),
    hash_md5 character varying(32),
    observaciones character varying(2000)
);


ALTER TABLE public.documentos OWNER TO postgres;

--
-- Name: COLUMN documentos.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.id IS 'Identificador único autogenerado del documento';


--
-- Name: COLUMN documentos.expediente_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.expediente_id IS 'FK a EXPEDIENTES. ÚNCO FK del documento (tabla agnóstica)';


--
-- Name: COLUMN documentos.url; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.url IS 'Ruta o URL del archivo físico en sistema de archivos o repositorio';


--
-- Name: COLUMN documentos.tipo_contenido; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.tipo_contenido IS 'Tipo MIME del archivo (ej: application/pdf)';


--
-- Name: COLUMN documentos.fecha_administrativa; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.fecha_administrativa IS 'Fecha con valor administrativo oficial (firma, registro, publicación)';


--
-- Name: COLUMN documentos.asunto; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.asunto IS 'Descripción o asunto del documento';


--
-- Name: COLUMN documentos.origen; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.origen IS 'Procedencia del documento (EXTERNO, INTERNO, ORGANISMO_X, etc.)';


--
-- Name: COLUMN documentos.prioridad; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.prioridad IS 'Nivel de prioridad o relevancia (default: 0)';


--
-- Name: COLUMN documentos.nombre_display; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.nombre_display IS 'Nombre legible para mostrar en interfaz';


--
-- Name: COLUMN documentos.hash_md5; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.hash_md5 IS 'Hash MD5 para verificación de integridad y detección de duplicados';


--
-- Name: COLUMN documentos.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos.observaciones IS 'Notas o comentarios adicionales del técnico';


--
-- Name: documentos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documentos_id_seq OWNER TO postgres;

--
-- Name: documentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documentos_id_seq OWNED BY public.documentos.id;


--
-- Name: documentos_proyecto; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documentos_proyecto (
    id integer NOT NULL,
    proyecto_id integer NOT NULL,
    documento_id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    observaciones character varying(500)
);


ALTER TABLE public.documentos_proyecto OWNER TO postgres;

--
-- Name: COLUMN documentos_proyecto.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos_proyecto.id IS 'Identificador único autogenerado del registro';


--
-- Name: COLUMN documentos_proyecto.proyecto_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos_proyecto.proyecto_id IS 'FK a PROYECTOS. Proyecto al que pertenece el documento';


--
-- Name: COLUMN documentos_proyecto.documento_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos_proyecto.documento_id IS 'FK UNIQUE a DOCUMENTOS. Un documento solo puede estar en un proyecto';


--
-- Name: COLUMN documentos_proyecto.tipo; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos_proyecto.tipo IS 'Tipo de documento: PRINCIPAL, MODIFICADO, REFUNDIDO, ANEXO';


--
-- Name: COLUMN documentos_proyecto.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.documentos_proyecto.observaciones IS 'Notas del técnico sobre la incorporación del documento';


--
-- Name: documentos_proyecto_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documentos_proyecto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documentos_proyecto_id_seq OWNER TO postgres;

--
-- Name: documentos_proyecto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documentos_proyecto_id_seq OWNED BY public.documentos_proyecto.id;


--
-- Name: expedientes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expedientes (
    id integer NOT NULL,
    numero_at integer NOT NULL,
    responsable_id integer NOT NULL,
    tipo_expediente_id integer,
    heredado boolean,
    proyecto_id integer NOT NULL
);


ALTER TABLE public.expedientes OWNER TO postgres;

--
-- Name: expedientes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expedientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expedientes_id_seq OWNER TO postgres;

--
-- Name: expedientes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expedientes_id_seq OWNED BY public.expedientes.id;


--
-- Name: fases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fases (
    id integer NOT NULL,
    solicitud_id integer NOT NULL,
    tipo_fase_id integer NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    resultado_fase_id integer,
    documento_resultado_id integer,
    observaciones character varying(2000)
);


ALTER TABLE public.fases OWNER TO postgres;

--
-- Name: COLUMN fases.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.id IS 'Identificador único autogenerado de la fase';


--
-- Name: COLUMN fases.solicitud_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.solicitud_id IS 'FK a SOLICITUDES. Solicitud a la que pertenece la fase';


--
-- Name: COLUMN fases.tipo_fase_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.tipo_fase_id IS 'FK a TIPOS_FASES. Tipo de fase (ADMISIBILIDAD, CONSULTAS, etc.)';


--
-- Name: COLUMN fases.fecha_inicio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.fecha_inicio IS 'Fecha de inicio de la fase. NULL = fase planificada no iniciada';


--
-- Name: COLUMN fases.fecha_fin; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.fecha_fin IS 'Fecha de finalización de la fase. NULL = fase pendiente o en curso';


--
-- Name: COLUMN fases.resultado_fase_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.resultado_fase_id IS 'FK a TIPOS_RESULTADOS_FASES. Resultado de la fase al finalizar';


--
-- Name: COLUMN fases.documento_resultado_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.documento_resultado_id IS 'FK a DOCUMENTOS. Documento oficial que formaliza el resultado';


--
-- Name: COLUMN fases.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.fases.observaciones IS 'Notas o comentarios adicionales del técnico';


--
-- Name: fases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fases_id_seq OWNER TO postgres;

--
-- Name: fases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fases_id_seq OWNED BY public.fases.id;


--
-- Name: municipios_proyecto; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.municipios_proyecto (
    id integer NOT NULL,
    municipio_id integer NOT NULL,
    proyecto_id integer NOT NULL
);


ALTER TABLE public.municipios_proyecto OWNER TO postgres;

--
-- Name: COLUMN municipios_proyecto.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.municipios_proyecto.id IS 'Identificador único autogenerado del registro puente';


--
-- Name: COLUMN municipios_proyecto.municipio_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.municipios_proyecto.municipio_id IS 'FK a MUNICIPIOS. Municipio afectado por el proyecto';


--
-- Name: COLUMN municipios_proyecto.proyecto_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.municipios_proyecto.proyecto_id IS 'FK a PROYECTOS. Proyecto técnico que afecta al municipio';


--
-- Name: municipios_proyecto_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.municipios_proyecto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.municipios_proyecto_id_seq OWNER TO postgres;

--
-- Name: municipios_proyecto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.municipios_proyecto_id_seq OWNED BY public.municipios_proyecto.id;


--
-- Name: proyectos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.proyectos (
    id integer NOT NULL,
    titulo character varying(500) DEFAULT '⚠️ Falta el título del proyecto'::character varying NOT NULL,
    descripcion character varying(10000) DEFAULT '⚠️ Falta la descripción del proyecto'::character varying NOT NULL,
    fecha date DEFAULT CURRENT_DATE NOT NULL,
    finalidad character varying(500) DEFAULT '⚠️ Falta la finalidad del proyecto'::character varying NOT NULL,
    emplazamiento character varying(200) DEFAULT '⚠️ Falta el emplazamiento'::character varying NOT NULL,
    ia_id integer
);


ALTER TABLE public.proyectos OWNER TO postgres;

--
-- Name: proyectos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.proyectos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proyectos_id_seq OWNER TO postgres;

--
-- Name: proyectos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.proyectos_id_seq OWNED BY public.proyectos.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(200)
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: solicitudes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solicitudes (
    id integer NOT NULL,
    expediente_id integer NOT NULL,
    solicitud_afectada_id integer,
    fecha_solicitud date NOT NULL,
    estado character varying(20) NOT NULL,
    observaciones character varying(2000)
);


ALTER TABLE public.solicitudes OWNER TO postgres;

--
-- Name: COLUMN solicitudes.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.id IS 'Identificador único autogenerado de la solicitud';


--
-- Name: COLUMN solicitudes.expediente_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.expediente_id IS 'FK a EXPEDIENTES. Expediente al que pertenece la solicitud';


--
-- Name: COLUMN solicitudes.solicitud_afectada_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.solicitud_afectada_id IS 'FK a SOLICITUDES. Para DESISTIMIENTO/RENUNCIA, solicitud que se desiste';


--
-- Name: COLUMN solicitudes.fecha_solicitud; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.fecha_solicitud IS 'Fecha oficial de presentación de la solicitud';


--
-- Name: COLUMN solicitudes.estado; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.estado IS 'Estado: EN_TRAMITE, RESUELTA, DESISTIDA, ARCHIVADA';


--
-- Name: COLUMN solicitudes.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.solicitudes.observaciones IS 'Notas o comentarios adicionales del técnico';


--
-- Name: solicitudes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solicitudes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solicitudes_id_seq OWNER TO postgres;

--
-- Name: solicitudes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.solicitudes_id_seq OWNED BY public.solicitudes.id;


--
-- Name: tareas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tareas (
    id integer NOT NULL,
    tramite_id integer NOT NULL,
    tipo_tarea_id integer NOT NULL,
    documento_usado_id integer,
    documento_producido_id integer,
    fecha_inicio date,
    fecha_fin date,
    notas character varying(2000)
);


ALTER TABLE public.tareas OWNER TO postgres;

--
-- Name: COLUMN tareas.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.id IS 'Identificador único autogenerado de la tarea';


--
-- Name: COLUMN tareas.tramite_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.tramite_id IS 'FK a TRAMITES. Trámite al que pertenece la tarea';


--
-- Name: COLUMN tareas.tipo_tarea_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.tipo_tarea_id IS 'FK a TIPOS_TAREAS. Tipo de tarea atómica (7 tipos posibles)';


--
-- Name: COLUMN tareas.documento_usado_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.documento_usado_id IS 'FK a DOCUMENTOS. Documento usado como input de la tarea';


--
-- Name: COLUMN tareas.documento_producido_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.documento_producido_id IS 'FK UNIQUE a DOCUMENTOS. Documento generado como output de la tarea';


--
-- Name: COLUMN tareas.fecha_inicio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.fecha_inicio IS 'Fecha de inicio de la tarea. NULL = tarea planificada no iniciada';


--
-- Name: COLUMN tareas.fecha_fin; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.fecha_fin IS 'Fecha de finalización de la tarea. NULL = tarea pendiente o en curso';


--
-- Name: COLUMN tareas.notas; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tareas.notas IS 'Observaciones o información adicional (plazos, referencia, remitente, etc.)';


--
-- Name: tareas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tareas_id_seq OWNER TO postgres;

--
-- Name: tareas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tareas_id_seq OWNED BY public.tareas.id;


--
-- Name: tramites; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tramites (
    id integer NOT NULL,
    fase_id integer NOT NULL,
    tipo_tramite_id integer NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    observaciones character varying(2000)
);


ALTER TABLE public.tramites OWNER TO postgres;

--
-- Name: COLUMN tramites.id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.id IS 'Identificador único autogenerado del trámite';


--
-- Name: COLUMN tramites.fase_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.fase_id IS 'FK a FASES. Fase a la que pertenece el trámite';


--
-- Name: COLUMN tramites.tipo_tramite_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.tipo_tramite_id IS 'FK a TIPOS_TRAMITES. Tipo de trámite';


--
-- Name: COLUMN tramites.fecha_inicio; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.fecha_inicio IS 'Fecha de inicio del trámite. NULL = trámite planificado no iniciado';


--
-- Name: COLUMN tramites.fecha_fin; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.fecha_fin IS 'Fecha de finalización del trámite. NULL = trámite pendiente o en curso';


--
-- Name: COLUMN tramites.observaciones; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.tramites.observaciones IS 'Notas o comentarios adicionales del técnico';


--
-- Name: tramites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tramites_id_seq OWNER TO postgres;

--
-- Name: tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tramites_id_seq OWNED BY public.tramites.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    siglas character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    apellido1 character varying(50) NOT NULL,
    apellido2 character varying(50),
    email character varying(120),
    activo boolean,
    password_hash character varying(256),
    reset_token character varying(100),
    reset_token_expiry timestamp without time zone
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: usuarios_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios_roles (
    usuario_id integer NOT NULL,
    rol_id integer NOT NULL
);


ALTER TABLE public.usuarios_roles OWNER TO postgres;

--
-- Name: municipios id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.municipios ALTER COLUMN id SET DEFAULT nextval('estructura.municipios_id_seq'::regclass);


--
-- Name: solicitudes_tipos id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.solicitudes_tipos ALTER COLUMN id SET DEFAULT nextval('estructura.solicitudes_tipos_id_seq'::regclass);


--
-- Name: tipos_expedientes id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_expedientes ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_expedientes_id_seq'::regclass);


--
-- Name: tipos_fases id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_fases ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_fases_id_seq'::regclass);


--
-- Name: tipos_ia id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_ia ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_ia_id_seq'::regclass);


--
-- Name: tipos_resultados_fases id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_resultados_fases ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_resultados_fases_id_seq'::regclass);


--
-- Name: tipos_solicitudes id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_solicitudes ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_solicitudes_id_seq'::regclass);


--
-- Name: tipos_tareas id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tareas ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_tareas_id_seq'::regclass);


--
-- Name: tipos_tramites id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tramites ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_tramites_id_seq'::regclass);


--
-- Name: documentos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos ALTER COLUMN id SET DEFAULT nextval('public.documentos_id_seq'::regclass);


--
-- Name: documentos_proyecto id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_proyecto ALTER COLUMN id SET DEFAULT nextval('public.documentos_proyecto_id_seq'::regclass);


--
-- Name: expedientes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes ALTER COLUMN id SET DEFAULT nextval('public.expedientes_id_seq'::regclass);


--
-- Name: fases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases ALTER COLUMN id SET DEFAULT nextval('public.fases_id_seq'::regclass);


--
-- Name: municipios_proyecto id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.municipios_proyecto ALTER COLUMN id SET DEFAULT nextval('public.municipios_proyecto_id_seq'::regclass);


--
-- Name: proyectos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proyectos ALTER COLUMN id SET DEFAULT nextval('public.proyectos_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: solicitudes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes ALTER COLUMN id SET DEFAULT nextval('public.solicitudes_id_seq'::regclass);


--
-- Name: tareas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas ALTER COLUMN id SET DEFAULT nextval('public.tareas_id_seq'::regclass);


--
-- Name: tramites id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites ALTER COLUMN id SET DEFAULT nextval('public.tramites_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: municipios municipios_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.municipios
    ADD CONSTRAINT municipios_codigo_key UNIQUE (codigo);


--
-- Name: municipios municipios_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.municipios
    ADD CONSTRAINT municipios_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_tipos solicitudes_tipos_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_tipos solicitudes_tipos_solicitudid_tiposolicitudid_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_solicitudid_tiposolicitudid_key UNIQUE (solicitudid, tiposolicitudid);


--
-- Name: tipos_expedientes tipos_expedientes_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_expedientes
    ADD CONSTRAINT tipos_expedientes_pkey PRIMARY KEY (id);


--
-- Name: tipos_fases tipos_fases_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_fases
    ADD CONSTRAINT tipos_fases_codigo_key UNIQUE (codigo);


--
-- Name: tipos_fases tipos_fases_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_fases
    ADD CONSTRAINT tipos_fases_pkey PRIMARY KEY (id);


--
-- Name: tipos_ia tipos_ia_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_ia
    ADD CONSTRAINT tipos_ia_pkey PRIMARY KEY (id);


--
-- Name: tipos_ia tipos_ia_siglas_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_ia
    ADD CONSTRAINT tipos_ia_siglas_key UNIQUE (siglas);


--
-- Name: tipos_resultados_fases tipos_resultados_fases_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_resultados_fases
    ADD CONSTRAINT tipos_resultados_fases_codigo_key UNIQUE (codigo);


--
-- Name: tipos_resultados_fases tipos_resultados_fases_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_resultados_fases
    ADD CONSTRAINT tipos_resultados_fases_pkey PRIMARY KEY (id);


--
-- Name: tipos_solicitudes tipos_solicitudes_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_solicitudes
    ADD CONSTRAINT tipos_solicitudes_pkey PRIMARY KEY (id);


--
-- Name: tipos_solicitudes tipos_solicitudes_siglas_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_solicitudes
    ADD CONSTRAINT tipos_solicitudes_siglas_key UNIQUE (siglas);


--
-- Name: tipos_tareas tipos_tareas_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tareas
    ADD CONSTRAINT tipos_tareas_codigo_key UNIQUE (codigo);


--
-- Name: tipos_tareas tipos_tareas_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tareas
    ADD CONSTRAINT tipos_tareas_pkey PRIMARY KEY (id);


--
-- Name: tipos_tramites tipos_tramites_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tramites
    ADD CONSTRAINT tipos_tramites_codigo_key UNIQUE (codigo);


--
-- Name: tipos_tramites tipos_tramites_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_tramites
    ADD CONSTRAINT tipos_tramites_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: documentos documentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos
    ADD CONSTRAINT documentos_pkey PRIMARY KEY (id);


--
-- Name: documentos_proyecto documentos_proyecto_documento_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_documento_id_key UNIQUE (documento_id);


--
-- Name: documentos_proyecto documentos_proyecto_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_pkey PRIMARY KEY (id);


--
-- Name: expedientes expedientes_numero_at_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_numero_at_key UNIQUE (numero_at);


--
-- Name: expedientes expedientes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_pkey PRIMARY KEY (id);


--
-- Name: expedientes expedientes_proyecto_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_proyecto_id_key UNIQUE (proyecto_id);


--
-- Name: fases fases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_pkey PRIMARY KEY (id);


--
-- Name: municipios_proyecto municipios_proyecto_municipio_proyecto_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_municipio_proyecto_key UNIQUE (municipio_id, proyecto_id);


--
-- Name: municipios_proyecto municipios_proyecto_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_pkey PRIMARY KEY (id);


--
-- Name: proyectos proyectos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proyectos
    ADD CONSTRAINT proyectos_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: solicitudes solicitudes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes
    ADD CONSTRAINT solicitudes_pkey PRIMARY KEY (id);


--
-- Name: tareas tareas_documento_producido_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_producido_id_key UNIQUE (documento_producido_id);


--
-- Name: tareas tareas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_pkey PRIMARY KEY (id);


--
-- Name: tramites tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios_roles usuarios_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_pkey PRIMARY KEY (usuario_id, rol_id);


--
-- Name: usuarios usuarios_siglas_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_siglas_key UNIQUE (siglas);


--
-- Name: idx_municipios_codigo; Type: INDEX; Schema: estructura; Owner: postgres
--

CREATE INDEX idx_municipios_codigo ON estructura.municipios USING btree (codigo);


--
-- Name: idx_municipios_nombre; Type: INDEX; Schema: estructura; Owner: postgres
--

CREATE INDEX idx_municipios_nombre ON estructura.municipios USING btree (nombre);


--
-- Name: idx_municipios_provincia; Type: INDEX; Schema: estructura; Owner: postgres
--

CREATE INDEX idx_municipios_provincia ON estructura.municipios USING btree (provincia);


--
-- Name: idx_solicitudes_tipos_solicitud; Type: INDEX; Schema: estructura; Owner: postgres
--

CREATE INDEX idx_solicitudes_tipos_solicitud ON estructura.solicitudes_tipos USING btree (solicitudid);


--
-- Name: idx_solicitudes_tipos_tipo; Type: INDEX; Schema: estructura; Owner: postgres
--

CREATE INDEX idx_solicitudes_tipos_tipo ON estructura.solicitudes_tipos USING btree (tiposolicitudid);


--
-- Name: idx_documentos_expediente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documentos_expediente ON public.documentos USING btree (expediente_id);


--
-- Name: idx_documentos_fecha_administrativa; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documentos_fecha_administrativa ON public.documentos USING btree (fecha_administrativa);


--
-- Name: idx_documentos_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documentos_hash ON public.documentos USING btree (hash_md5);


--
-- Name: idx_documentos_proyecto_proyecto; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documentos_proyecto_proyecto ON public.documentos_proyecto USING btree (proyecto_id);


--
-- Name: idx_documentos_proyecto_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documentos_proyecto_tipo ON public.documentos_proyecto USING btree (proyecto_id, tipo);


--
-- Name: idx_fases_fechas; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fases_fechas ON public.fases USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_fases_resultado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fases_resultado ON public.fases USING btree (resultado_fase_id);


--
-- Name: idx_fases_solicitud; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fases_solicitud ON public.fases USING btree (solicitud_id);


--
-- Name: idx_fases_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_fases_tipo ON public.fases USING btree (tipo_fase_id);


--
-- Name: idx_municipios_proyecto_municipio; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_municipios_proyecto_municipio ON public.municipios_proyecto USING btree (municipio_id);


--
-- Name: idx_municipios_proyecto_proyecto; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_municipios_proyecto_proyecto ON public.municipios_proyecto USING btree (proyecto_id);


--
-- Name: idx_solicitudes_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solicitudes_estado ON public.solicitudes USING btree (estado);


--
-- Name: idx_solicitudes_expediente; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solicitudes_expediente ON public.solicitudes USING btree (expediente_id);


--
-- Name: idx_solicitudes_fecha; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solicitudes_fecha ON public.solicitudes USING btree (fecha_solicitud);


--
-- Name: idx_tareas_documento_usado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tareas_documento_usado ON public.tareas USING btree (documento_usado_id);


--
-- Name: idx_tareas_fechas; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tareas_fechas ON public.tareas USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_tareas_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tareas_tipo ON public.tareas USING btree (tipo_tarea_id);


--
-- Name: idx_tareas_tramite; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tareas_tramite ON public.tareas USING btree (tramite_id);


--
-- Name: idx_tramites_fase; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_fase ON public.tramites USING btree (fase_id);


--
-- Name: idx_tramites_fechas; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_fechas ON public.tramites USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_tramites_tipo; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tramites_tipo ON public.tramites USING btree (tipo_tramite_id);


--
-- Name: documentos_proyecto documentos_proyecto_documento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_documento_id_fkey FOREIGN KEY (documento_id) REFERENCES public.documentos(id) ON DELETE CASCADE;


--
-- Name: expedientes expedientes_proyecto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_proyecto_id_fkey FOREIGN KEY (proyecto_id) REFERENCES public.proyectos(id);


--
-- Name: expedientes expedientes_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.usuarios(id);


--
-- Name: fases fases_documento_resultado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_documento_resultado_id_fkey FOREIGN KEY (documento_resultado_id) REFERENCES public.documentos(id);


--
-- Name: fases fases_resultado_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_resultado_fase_id_fkey FOREIGN KEY (resultado_fase_id) REFERENCES estructura.tipos_resultados_fases(id);


--
-- Name: fases fases_solicitud_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_solicitud_id_fkey FOREIGN KEY (solicitud_id) REFERENCES public.solicitudes(id) ON DELETE CASCADE;


--
-- Name: fases fases_tipo_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_tipo_fase_id_fkey FOREIGN KEY (tipo_fase_id) REFERENCES estructura.tipos_fases(id);


--
-- Name: expedientes fk_expedientes_tipo_expediente; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT fk_expedientes_tipo_expediente FOREIGN KEY (tipo_expediente_id) REFERENCES estructura.tipos_expedientes(id);


--
-- Name: proyectos fk_proyectos_ia_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proyectos
    ADD CONSTRAINT fk_proyectos_ia_id FOREIGN KEY (ia_id) REFERENCES estructura.tipos_ia(id);


--
-- Name: municipios_proyecto municipios_proyecto_municipio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_municipio_id_fkey FOREIGN KEY (municipio_id) REFERENCES estructura.municipios(id);


--
-- Name: solicitudes solicitudes_solicitud_afectada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solicitudes
    ADD CONSTRAINT solicitudes_solicitud_afectada_id_fkey FOREIGN KEY (solicitud_afectada_id) REFERENCES public.solicitudes(id);


--
-- Name: tareas tareas_documento_producido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_producido_id_fkey FOREIGN KEY (documento_producido_id) REFERENCES public.documentos(id);


--
-- Name: tareas tareas_documento_usado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_usado_id_fkey FOREIGN KEY (documento_usado_id) REFERENCES public.documentos(id);


--
-- Name: tareas tareas_tipo_tarea_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_tipo_tarea_id_fkey FOREIGN KEY (tipo_tarea_id) REFERENCES estructura.tipos_tareas(id);


--
-- Name: tareas tareas_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_tramite_id_fkey FOREIGN KEY (tramite_id) REFERENCES public.tramites(id) ON DELETE CASCADE;


--
-- Name: tramites tramites_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_fase_id_fkey FOREIGN KEY (fase_id) REFERENCES public.fases(id) ON DELETE CASCADE;


--
-- Name: tramites tramites_tipo_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_tipo_tramite_id_fkey FOREIGN KEY (tipo_tramite_id) REFERENCES estructura.tipos_tramites(id);


--
-- Name: usuarios_roles usuarios_roles_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- Name: usuarios_roles usuarios_roles_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- PostgreSQL database dump complete
--

\unrestrict lZf6Tf80m9dCOJKsm98Ra3rvkOx78oCuCDgKmBUL10dD1lsu0goMP6iruBSUzBZ

