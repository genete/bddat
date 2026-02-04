--
-- PostgreSQL database dump
--

\restrict AVJQrvdVqkYwVPFjvaxEkdP0fzioOgyFynNiP0aEKrkOumQ3kLQkIq0sL5McrvR

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
-- Name: estructura; Type: SCHEMA; Schema: -; Owner: bddat_admin
--

CREATE SCHEMA estructura;


ALTER SCHEMA estructura OWNER TO bddat_admin;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: bddat_admin
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO bddat_admin;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: bddat_admin
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: municipios; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.municipios (
    id integer NOT NULL,
    codigo character varying(10) NOT NULL,
    nombre character varying(200) NOT NULL,
    provincia character varying(100) NOT NULL
);


ALTER TABLE estructura.municipios OWNER TO bddat_admin;

--
-- Name: COLUMN municipios.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.municipios.id IS 'Identificador ├║nico autogenerado del municipio';


--
-- Name: COLUMN municipios.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.municipios.codigo IS 'C├│digo INE oficial del municipio (5 d├¡gitos)';


--
-- Name: COLUMN municipios.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.municipios.nombre IS 'Denominaci├│n oficial del municipio';


--
-- Name: COLUMN municipios.provincia; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.municipios.provincia IS 'Provincia a la que pertenece el municipio';


--
-- Name: municipios_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.municipios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.municipios_id_seq OWNER TO bddat_admin;

--
-- Name: municipios_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.municipios_id_seq OWNED BY estructura.municipios.id;


--
-- Name: tipos_entidades; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_entidades (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(100) NOT NULL,
    tabla_metadatos character varying(100) NOT NULL,
    puede_ser_solicitante boolean DEFAULT false NOT NULL,
    puede_ser_consultado boolean DEFAULT false NOT NULL,
    puede_publicar boolean DEFAULT false NOT NULL,
    descripcion text
);


ALTER TABLE estructura.tipos_entidades OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_entidades.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.id IS 'Identificador ├║nico del tipo de entidad';


--
-- Name: COLUMN tipos_entidades.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.codigo IS 'C├│digo ├║nico del tipo (ADMINISTRADO, ORGANISMO_PUBLICO, AYUNTAMIENTO, DIPUTACION, EMPRESA_SERVICIO_PUBLICO)';


--
-- Name: COLUMN tipos_entidades.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.nombre IS 'Nombre descriptivo del tipo de entidad';


--
-- Name: COLUMN tipos_entidades.tabla_metadatos; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.tabla_metadatos IS 'Nombre de la tabla entidades_* donde se almacenan los metadatos espec├¡ficos (ej: entidades_administrados)';


--
-- Name: COLUMN tipos_entidades.puede_ser_solicitante; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.puede_ser_solicitante IS 'Indica si este tipo puede actuar como solicitante de solicitudes';


--
-- Name: COLUMN tipos_entidades.puede_ser_consultado; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.puede_ser_consultado IS 'Indica si este tipo puede emitir informes como organismo consultado';


--
-- Name: COLUMN tipos_entidades.puede_publicar; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.puede_publicar IS 'Indica si este tipo puede publicar edictos (tabl├│n ayuntamiento o BOP diputaci├│n)';


--
-- Name: COLUMN tipos_entidades.descripcion; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_entidades.descripcion IS 'Descripci├│n detallada del tipo de entidad, roles y caracter├¡sticas';


--
-- Name: tipos_entidades_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_entidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_entidades_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_entidades_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_entidades_id_seq OWNED BY estructura.tipos_entidades.id;


--
-- Name: tipos_expedientes; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_expedientes (
    id integer NOT NULL,
    tipo character varying(100),
    descripcion character varying(200)
);


ALTER TABLE estructura.tipos_expedientes OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_expedientes.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_expedientes.id IS 'Identificador ├║nico autogenerado del tipo de expediente';


--
-- Name: COLUMN tipos_expedientes.tipo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_expedientes.tipo IS 'Denominaci├│n del tipo seg├║n clasificaci├│n normativa';


--
-- Name: COLUMN tipos_expedientes.descripcion; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_expedientes.descripcion IS 'Descripci├│n detallada de caracter├¡sticas y particularidades procedimentales';


--
-- Name: tipos_expedientes_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_expedientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_expedientes_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_expedientes_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_expedientes_id_seq OWNED BY estructura.tipos_expedientes.id;


--
-- Name: tipos_fases; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_fases (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_fases OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_fases.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_fases.id IS 'Identificador ├║nico autogenerado del tipo de fase';


--
-- Name: COLUMN tipos_fases.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_fases.codigo IS 'C├│digo ├║nico inmutable de la fase (usado en l├│gica de reglas)';


--
-- Name: COLUMN tipos_fases.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_fases.nombre IS 'Denominaci├│n completa de la fase para interfaz de usuario';


--
-- Name: tipos_fases_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_fases_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_fases_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_fases_id_seq OWNED BY estructura.tipos_fases.id;


--
-- Name: tipos_ia; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_ia (
    id integer NOT NULL,
    siglas character varying(10) NOT NULL,
    descripcion character varying(200)
);


ALTER TABLE estructura.tipos_ia OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_ia.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_ia.id IS 'Identificador ├║nico autogenerado del tipo de instrumento ambiental';


--
-- Name: COLUMN tipos_ia.siglas; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_ia.siglas IS 'C├│digo del instrumento ambiental (ver datos_maestros.sql)';


--
-- Name: COLUMN tipos_ia.descripcion; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_ia.descripcion IS 'Denominaci├│n completa del instrumento ambiental';


--
-- Name: tipos_ia_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_ia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_ia_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_ia_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_ia_id_seq OWNED BY estructura.tipos_ia.id;


--
-- Name: tipos_resultados_fases; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_resultados_fases (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_resultados_fases OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_resultados_fases.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.id IS 'Identificador ├║nico autogenerado del tipo de resultado';


--
-- Name: COLUMN tipos_resultados_fases.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.codigo IS 'C├│digo ├║nico inmutable del resultado (usado en l├│gica de reglas)';


--
-- Name: COLUMN tipos_resultados_fases.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_resultados_fases.nombre IS 'Denominaci├│n completa del resultado para interfaz de usuario';


--
-- Name: tipos_resultados_fases_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_resultados_fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_resultados_fases_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_resultados_fases_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_resultados_fases_id_seq OWNED BY estructura.tipos_resultados_fases.id;


--
-- Name: tipos_solicitudes; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_solicitudes (
    id integer NOT NULL,
    siglas character varying(100) NOT NULL,
    descripcion character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_solicitudes OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_solicitudes.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_solicitudes.id IS 'Identificador ├║nico autogenerado del tipo de solicitud';


--
-- Name: COLUMN tipos_solicitudes.siglas; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_solicitudes.siglas IS 'C├│digo normalizado del acto administrativo (AAP, AAC, DUP, etc.)';


--
-- Name: COLUMN tipos_solicitudes.descripcion; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_solicitudes.descripcion IS 'Descripci├│n completa del acto administrativo solicitado';


--
-- Name: tipos_solicitudes_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_solicitudes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_solicitudes_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_solicitudes_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_solicitudes_id_seq OWNED BY estructura.tipos_solicitudes.id;


--
-- Name: tipos_tareas; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_tareas (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_tareas OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_tareas.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tareas.id IS 'Identificador ├║nico autogenerado del tipo de tarea';


--
-- Name: COLUMN tipos_tareas.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tareas.codigo IS 'C├│digo ├║nico inmutable de la tarea (usado en l├│gica de reglas)';


--
-- Name: COLUMN tipos_tareas.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tareas.nombre IS 'Denominaci├│n completa de la tarea para interfaz de usuario';


--
-- Name: tipos_tareas_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_tareas_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_tareas_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_tareas_id_seq OWNED BY estructura.tipos_tareas.id;


--
-- Name: tipos_tramites; Type: TABLE; Schema: estructura; Owner: bddat_admin
--

CREATE TABLE estructura.tipos_tramites (
    id integer NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(200) NOT NULL
);


ALTER TABLE estructura.tipos_tramites OWNER TO bddat_admin;

--
-- Name: COLUMN tipos_tramites.id; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tramites.id IS 'Identificador ├║nico autogenerado del tipo de tr├ímite';


--
-- Name: COLUMN tipos_tramites.codigo; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tramites.codigo IS 'C├│digo ├║nico inmutable del tr├ímite (usado en l├│gica de reglas)';


--
-- Name: COLUMN tipos_tramites.nombre; Type: COMMENT; Schema: estructura; Owner: bddat_admin
--

COMMENT ON COLUMN estructura.tipos_tramites.nombre IS 'Denominaci├│n completa del tr├ímite para interfaz de usuario';


--
-- Name: tipos_tramites_id_seq; Type: SEQUENCE; Schema: estructura; Owner: bddat_admin
--

CREATE SEQUENCE estructura.tipos_tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE estructura.tipos_tramites_id_seq OWNER TO bddat_admin;

--
-- Name: tipos_tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: estructura; Owner: bddat_admin
--

ALTER SEQUENCE estructura.tipos_tramites_id_seq OWNED BY estructura.tipos_tramites.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO bddat_admin;

--
-- Name: autorizados_titular; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.autorizados_titular (
    id integer NOT NULL,
    titular_entidad_id integer NOT NULL,
    autorizado_entidad_id integer NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    observaciones text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_no_autoautorizacion CHECK ((titular_entidad_id <> autorizado_entidad_id))
);


ALTER TABLE public.autorizados_titular OWNER TO bddat_admin;

--
-- Name: COLUMN autorizados_titular.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.id IS 'Identificador ├║nico del registro de autorizaci├│n';


--
-- Name: COLUMN autorizados_titular.titular_entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.titular_entidad_id IS 'Administrado titular que concede la autorizaci├│n. Debe tener entrada en entidades_administrados';


--
-- Name: COLUMN autorizados_titular.autorizado_entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.autorizado_entidad_id IS 'Administrado autorizado para representar al titular. Debe tener entrada en entidades_administrados';


--
-- Name: COLUMN autorizados_titular.activo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.activo IS 'Indica si la autorizaci├│n est├í vigente. FALSE = revocada/suspendida';


--
-- Name: COLUMN autorizados_titular.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.observaciones IS 'Notas libres del tramitador. Usos: ├ímbito (expediente espec├¡fico/general), vigencia temporal, motivo desactivaci├│n, tipo de poder';


--
-- Name: COLUMN autorizados_titular.created_at; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.created_at IS 'Fecha y hora de creaci├│n del registro';


--
-- Name: COLUMN autorizados_titular.updated_at; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.autorizados_titular.updated_at IS 'Fecha y hora de ├║ltima actualizaci├│n';


--
-- Name: autorizados_titular_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.autorizados_titular_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.autorizados_titular_id_seq OWNER TO bddat_admin;

--
-- Name: autorizados_titular_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.autorizados_titular_id_seq OWNED BY public.autorizados_titular.id;


--
-- Name: documentos; Type: TABLE; Schema: public; Owner: bddat_admin
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


ALTER TABLE public.documentos OWNER TO bddat_admin;

--
-- Name: COLUMN documentos.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.id IS 'Identificador ├║nico autogenerado del documento';


--
-- Name: COLUMN documentos.expediente_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.expediente_id IS 'FK a EXPEDIENTES. ├ÜNCO FK del documento (tabla agn├│stica)';


--
-- Name: COLUMN documentos.url; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.url IS 'Ruta o URL del archivo f├¡sico en sistema de archivos o repositorio';


--
-- Name: COLUMN documentos.tipo_contenido; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.tipo_contenido IS 'Tipo MIME del archivo (ej: application/pdf)';


--
-- Name: COLUMN documentos.fecha_administrativa; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.fecha_administrativa IS 'Fecha con valor administrativo oficial (firma, registro, publicaci├│n)';


--
-- Name: COLUMN documentos.asunto; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.asunto IS 'Descripci├│n o asunto del documento';


--
-- Name: COLUMN documentos.origen; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.origen IS 'Procedencia del documento (EXTERNO, INTERNO, ORGANISMO_X, etc.)';


--
-- Name: COLUMN documentos.prioridad; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.prioridad IS 'Nivel de prioridad o relevancia (default: 0)';


--
-- Name: COLUMN documentos.nombre_display; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.nombre_display IS 'Nombre legible para mostrar en interfaz';


--
-- Name: COLUMN documentos.hash_md5; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.hash_md5 IS 'Hash MD5 para verificaci├│n de integridad y detecci├│n de duplicados';


--
-- Name: COLUMN documentos.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos.observaciones IS 'Notas o comentarios adicionales del t├®cnico';


--
-- Name: documentos_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.documentos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documentos_id_seq OWNER TO bddat_admin;

--
-- Name: documentos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.documentos_id_seq OWNED BY public.documentos.id;


--
-- Name: documentos_proyecto; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.documentos_proyecto (
    id integer NOT NULL,
    proyecto_id integer NOT NULL,
    documento_id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    observaciones character varying(500)
);


ALTER TABLE public.documentos_proyecto OWNER TO bddat_admin;

--
-- Name: COLUMN documentos_proyecto.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos_proyecto.id IS 'Identificador ├║nico autogenerado del registro';


--
-- Name: COLUMN documentos_proyecto.proyecto_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos_proyecto.proyecto_id IS 'FK a PROYECTOS. Proyecto al que pertenece el documento';


--
-- Name: COLUMN documentos_proyecto.documento_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos_proyecto.documento_id IS 'FK UNIQUE a DOCUMENTOS. Un documento solo puede estar en un proyecto';


--
-- Name: COLUMN documentos_proyecto.tipo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos_proyecto.tipo IS 'Tipo de documento: PRINCIPAL, MODIFICADO, REFUNDIDO, ANEXO';


--
-- Name: COLUMN documentos_proyecto.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.documentos_proyecto.observaciones IS 'Notas del t├®cnico sobre la incorporaci├│n del documento';


--
-- Name: documentos_proyecto_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.documentos_proyecto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documentos_proyecto_id_seq OWNER TO bddat_admin;

--
-- Name: documentos_proyecto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.documentos_proyecto_id_seq OWNED BY public.documentos_proyecto.id;


--
-- Name: entidades; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades (
    id integer NOT NULL,
    tipo_entidad_id integer NOT NULL,
    cif_nif character varying(20),
    nombre_completo character varying(200) NOT NULL,
    email character varying(120),
    telefono character varying(20),
    direccion text,
    codigo_postal character varying(10),
    municipio_id integer,
    direccion_fallback text,
    activo boolean DEFAULT true NOT NULL,
    notas text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.entidades OWNER TO bddat_admin;

--
-- Name: COLUMN entidades.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.id IS 'Identificador ├║nico de la entidad';


--
-- Name: COLUMN entidades.tipo_entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.tipo_entidad_id IS 'Tipo de entidad que determina tabla de metadatos. Define qu├® tabla entidades_* usar';


--
-- Name: COLUMN entidades.cif_nif; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.cif_nif IS 'CIF/NIF/NIE normalizado. May├║sculas, sin espacios/guiones. Ej: "12345678A", "B12345678". NULL para algunos organismos hist├│ricos';


--
-- Name: COLUMN entidades.nombre_completo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.nombre_completo IS 'Raz├│n social, nombre completo o nombre oficial. Personas f├¡sicas: nombre completo. Jur├¡dicas/organismos: raz├│n social/nombre oficial';


--
-- Name: COLUMN entidades.email; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.email IS 'Email general de contacto. NO es el email de notificaciones (va en entidades_administrados)';


--
-- Name: COLUMN entidades.telefono; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.telefono IS 'Tel├®fono de contacto general. Formato libre';


--
-- Name: COLUMN entidades.direccion; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.direccion IS 'Calle, n├║mero, piso, puerta. Usar junto con codigo_postal y municipio_id (preferente para Espa├▒a)';


--
-- Name: COLUMN entidades.codigo_postal; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.codigo_postal IS 'C├│digo postal. Texto libre. Futuro: sugerencias desde tabla codigos_postales';


--
-- Name: COLUMN entidades.municipio_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.municipio_id IS 'Municipio de la direcci├│n. Preferente sobre direccion_fallback';


--
-- Name: COLUMN entidades.direccion_fallback; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.direccion_fallback IS 'Direcci├│n completa en texto libre. Para casos excepcionales (extranjero, datos hist├│ricos). Ej: "23, Peny Lane, St, 34523, London, England"';


--
-- Name: COLUMN entidades.activo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.activo IS 'Indica si la entidad est├í activa. Borrado l├│gico';


--
-- Name: COLUMN entidades.notas; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.notas IS 'Observaciones generales sobre la entidad. Campo libre para anotaciones';


--
-- Name: COLUMN entidades.created_at; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.created_at IS 'Fecha y hora de creaci├│n del registro';


--
-- Name: COLUMN entidades.updated_at; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades.updated_at IS 'Fecha y hora de ├║ltima actualizaci├│n';


--
-- Name: entidades_administrados; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades_administrados (
    entidad_id integer NOT NULL,
    email_notificaciones character varying(120) NOT NULL,
    representante_nif_cif character varying(20),
    representante_nombre character varying(200),
    representante_telefono character varying(20),
    representante_email character varying(120),
    notas_representacion text,
    CONSTRAINT chk_representante_coherente CHECK ((((representante_nif_cif IS NULL) AND (representante_nombre IS NULL)) OR ((representante_nif_cif IS NOT NULL) AND (representante_nombre IS NOT NULL))))
);


ALTER TABLE public.entidades_administrados OWNER TO bddat_admin;

--
-- Name: COLUMN entidades_administrados.entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.entidad_id IS 'Referencia a entidad base (PK y FK con CASCADE)';


--
-- Name: COLUMN entidades_administrados.email_notificaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.email_notificaciones IS 'Email oficial para sistema Notifica. Puede ser personal o corporativo donde se reciben notificaciones electr├│nicas oficiales';


--
-- Name: COLUMN entidades_administrados.representante_nif_cif; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.representante_nif_cif IS 'NIF/CIF de quien representa/gestiona. NULL si autorepresentado (persona f├¡sica) o gesti├│n corporativa directa. Normalizado como CIF/NIF';


--
-- Name: COLUMN entidades_administrados.representante_nombre; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.representante_nombre IS 'Nombre completo del representante. NULL si autorepresentado. Puede ser persona f├¡sica (administrador ├║nico) o jur├¡dica (consultora contratada)';


--
-- Name: COLUMN entidades_administrados.representante_telefono; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.representante_telefono IS 'Tel├®fono del representante. Contacto directo con quien gestiona';


--
-- Name: COLUMN entidades_administrados.representante_email; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.representante_email IS 'Email del representante. Email de contacto (NO oficial para notificaciones, solo coordinaci├│n)';


--
-- Name: COLUMN entidades_administrados.notas_representacion; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_administrados.notas_representacion IS 'Observaciones sobre la representaci├│n. Tipo de cargo o relaci├│n: "Administrador ├║nico", "Consultora ACME SL contratada", "Apoderado con poder notarial", etc.';


--
-- Name: entidades_ayuntamientos; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades_ayuntamientos (
    entidad_id integer NOT NULL,
    codigo_dir3 character varying(20) NOT NULL,
    codigo_ine_municipio character varying(5) NOT NULL,
    url_tablon_edictos character varying(255),
    observaciones text
);


ALTER TABLE public.entidades_ayuntamientos OWNER TO bddat_admin;

--
-- Name: COLUMN entidades_ayuntamientos.entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_ayuntamientos.entidad_id IS 'Referencia a entidad base (PK y FK con CASCADE)';


--
-- Name: COLUMN entidades_ayuntamientos.codigo_dir3; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_ayuntamientos.codigo_dir3 IS 'C├│digo DIR3 oficial del ayuntamiento. Obligatorio para identificaci├│n ├║nica en sistemas oficiales';


--
-- Name: COLUMN entidades_ayuntamientos.codigo_ine_municipio; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_ayuntamientos.codigo_ine_municipio IS 'C├│digo INE de 5 d├¡gitos del municipio. Relaciona con estructura.municipios';


--
-- Name: COLUMN entidades_ayuntamientos.url_tablon_edictos; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_ayuntamientos.url_tablon_edictos IS 'URL del tabl├│n de anuncios/edictos electr├│nico. Para verificar publicaciones obligatorias';


--
-- Name: COLUMN entidades_ayuntamientos.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_ayuntamientos.observaciones IS 'Notas adicionales sobre el ayuntamiento. Horarios especiales, contactos t├®cnicos, particularidades de publicaci├│n';


--
-- Name: entidades_diputaciones; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades_diputaciones (
    entidad_id integer NOT NULL,
    codigo_dir3 character varying(20) NOT NULL,
    codigo_ine_municipio_sede character varying(5) NOT NULL,
    url_bop character varying(255),
    email_publicacion_bop character varying(255),
    observaciones text
);


ALTER TABLE public.entidades_diputaciones OWNER TO bddat_admin;

--
-- Name: COLUMN entidades_diputaciones.entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.entidad_id IS 'Referencia a entidad base (PK y FK con CASCADE)';


--
-- Name: COLUMN entidades_diputaciones.codigo_dir3; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.codigo_dir3 IS 'C├│digo DIR3 oficial de la diputaci├│n. Obligatorio';


--
-- Name: COLUMN entidades_diputaciones.codigo_ine_municipio_sede; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.codigo_ine_municipio_sede IS 'C├│digo INE del municipio donde tiene sede (capital provincial). 5 d├¡gitos';


--
-- Name: COLUMN entidades_diputaciones.url_bop; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.url_bop IS 'URL del Bolet├¡n Oficial de la Provincia (BOP) electr├│nico. Para consulta de publicaciones';


--
-- Name: COLUMN entidades_diputaciones.email_publicacion_bop; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.email_publicacion_bop IS 'Email para env├¡o de solicitudes de publicaci├│n en BOP. Direcci├│n de contacto del servicio de publicaciones';


--
-- Name: COLUMN entidades_diputaciones.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_diputaciones.observaciones IS 'Notas adicionales sobre la diputaci├│n. Procedimientos de publicaci├│n, plazos, contactos espec├¡ficos';


--
-- Name: entidades_empresas_servicio_publico; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades_empresas_servicio_publico (
    entidad_id integer NOT NULL,
    nombre_comercial character varying(200),
    sector character varying(100),
    codigo_cnae character varying(10),
    observaciones text
);


ALTER TABLE public.entidades_empresas_servicio_publico OWNER TO bddat_admin;

--
-- Name: COLUMN entidades_empresas_servicio_publico.entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_empresas_servicio_publico.entidad_id IS 'Referencia a entidad base (PK y FK con CASCADE)';


--
-- Name: COLUMN entidades_empresas_servicio_publico.nombre_comercial; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_empresas_servicio_publico.nombre_comercial IS 'Nombre comercial o marca si difiere de raz├│n social. Ej: "Endesa Distribuci├│n" vs "Endesa Distribuci├│n El├®ctrica S.L."';


--
-- Name: COLUMN entidades_empresas_servicio_publico.sector; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_empresas_servicio_publico.sector IS 'Sector de actividad. Ej: "Distribuci├│n el├®ctrica", "Telecomunicaciones", "Transporte ferroviario"';


--
-- Name: COLUMN entidades_empresas_servicio_publico.codigo_cnae; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_empresas_servicio_publico.codigo_cnae IS 'C├│digo CNAE de actividad econ├│mica. 4 d├¡gitos. Ej: "3511" (Producci├│n de energ├¡a el├®ctrica)';


--
-- Name: COLUMN entidades_empresas_servicio_publico.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_empresas_servicio_publico.observaciones IS 'Notas adicionales sobre la empresa. Relaciones con otras operadoras, particularidades t├®cnicas, hist├│rico de incidencias';


--
-- Name: entidades_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.entidades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entidades_id_seq OWNER TO bddat_admin;

--
-- Name: entidades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.entidades_id_seq OWNED BY public.entidades.id;


--
-- Name: entidades_organismos_publicos; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.entidades_organismos_publicos (
    entidad_id integer NOT NULL,
    codigo_dir3 character varying(20) NOT NULL,
    ambito character varying(50) NOT NULL,
    tipo_organismo character varying(100),
    url_sede_electronica character varying(255),
    observaciones text
);


ALTER TABLE public.entidades_organismos_publicos OWNER TO bddat_admin;

--
-- Name: COLUMN entidades_organismos_publicos.entidad_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.entidad_id IS 'Referencia a entidad base (PK y FK con CASCADE)';


--
-- Name: COLUMN entidades_organismos_publicos.codigo_dir3; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.codigo_dir3 IS 'C├│digo DIR3 oficial (directorio com├║n de unidades org├ínicas). Identificador ├║nico de organismo p├║blico. Obligatorio';


--
-- Name: COLUMN entidades_organismos_publicos.ambito; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.ambito IS '├ümbito administrativo. Valores: "ESTATAL", "AUTONOMICO", "LOCAL", "EUROPEO"';


--
-- Name: COLUMN entidades_organismos_publicos.tipo_organismo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.tipo_organismo IS 'Clasificaci├│n del organismo. Ej: "Ministerio", "Consejer├¡a", "Direcci├│n General", "Agencia", "Organismo Aut├│nomo"';


--
-- Name: COLUMN entidades_organismos_publicos.url_sede_electronica; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.url_sede_electronica IS 'URL de la sede electr├│nica del organismo. Para env├¡os telem├íticos y consulta de servicios';


--
-- Name: COLUMN entidades_organismos_publicos.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.entidades_organismos_publicos.observaciones IS 'Notas adicionales sobre el organismo. Competencias espec├¡ficas, particularidades procedimentales, contactos alternativos';


--
-- Name: expedientes; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.expedientes (
    id integer NOT NULL,
    numero_at integer NOT NULL,
    responsable_id integer,
    tipo_expediente_id integer,
    heredado boolean,
    proyecto_id integer NOT NULL
);


ALTER TABLE public.expedientes OWNER TO bddat_admin;

--
-- Name: COLUMN expedientes.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.id IS 'Identificador t├®cnico ├║nico autogenerado';


--
-- Name: COLUMN expedientes.numero_at; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.numero_at IS 'N├║mero administrativo del expediente (formato legacy, ├║nico en organizaci├│n)';


--
-- Name: COLUMN expedientes.responsable_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.responsable_id IS 'FK a USUARIOS. Tramitador asignado con permisos de gesti├│n completa';


--
-- Name: COLUMN expedientes.tipo_expediente_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.tipo_expediente_id IS 'FK a TIPOS_EXPEDIENTES. Clasificaci├│n normativa que define procedimiento';


--
-- Name: COLUMN expedientes.heredado; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.heredado IS 'TRUE si proviene del sistema anterior (datos incompletos posibles)';


--
-- Name: COLUMN expedientes.proyecto_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.expedientes.proyecto_id IS 'FK a PROYECTOS. Relaci├│n 1:1, un expediente tiene exactamente un proyecto';


--
-- Name: expedientes_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.expedientes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expedientes_id_seq OWNER TO bddat_admin;

--
-- Name: expedientes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.expedientes_id_seq OWNED BY public.expedientes.id;


--
-- Name: fases; Type: TABLE; Schema: public; Owner: bddat_admin
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


ALTER TABLE public.fases OWNER TO bddat_admin;

--
-- Name: COLUMN fases.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.id IS 'Identificador ├║nico autogenerado de la fase';


--
-- Name: COLUMN fases.solicitud_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.solicitud_id IS 'FK a SOLICITUDES. Solicitud a la que pertenece la fase';


--
-- Name: COLUMN fases.tipo_fase_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.tipo_fase_id IS 'FK a TIPOS_FASES. Tipo de fase (ADMISIBILIDAD, CONSULTAS, etc.)';


--
-- Name: COLUMN fases.fecha_inicio; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.fecha_inicio IS 'Fecha de inicio de la fase. NULL = fase planificada no iniciada';


--
-- Name: COLUMN fases.fecha_fin; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.fecha_fin IS 'Fecha de finalizaci├│n de la fase. NULL = fase pendiente o en curso';


--
-- Name: COLUMN fases.resultado_fase_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.resultado_fase_id IS 'FK a TIPOS_RESULTADOS_FASES. Resultado de la fase al finalizar';


--
-- Name: COLUMN fases.documento_resultado_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.documento_resultado_id IS 'FK a DOCUMENTOS. Documento oficial que formaliza el resultado';


--
-- Name: COLUMN fases.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.fases.observaciones IS 'Notas o comentarios adicionales del t├®cnico';


--
-- Name: fases_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.fases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fases_id_seq OWNER TO bddat_admin;

--
-- Name: fases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.fases_id_seq OWNED BY public.fases.id;


--
-- Name: municipios_proyecto; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.municipios_proyecto (
    id integer NOT NULL,
    municipio_id integer NOT NULL,
    proyecto_id integer NOT NULL
);


ALTER TABLE public.municipios_proyecto OWNER TO bddat_admin;

--
-- Name: COLUMN municipios_proyecto.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.municipios_proyecto.id IS 'Identificador ├║nico autogenerado del registro puente';


--
-- Name: COLUMN municipios_proyecto.municipio_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.municipios_proyecto.municipio_id IS 'FK a MUNICIPIOS. Municipio afectado por el proyecto';


--
-- Name: COLUMN municipios_proyecto.proyecto_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.municipios_proyecto.proyecto_id IS 'FK a PROYECTOS. Proyecto t├®cnico que afecta al municipio';


--
-- Name: municipios_proyecto_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.municipios_proyecto_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.municipios_proyecto_id_seq OWNER TO bddat_admin;

--
-- Name: municipios_proyecto_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.municipios_proyecto_id_seq OWNED BY public.municipios_proyecto.id;


--
-- Name: proyectos; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.proyectos (
    id integer NOT NULL,
    titulo character varying(500) NOT NULL,
    descripcion character varying(10000) NOT NULL,
    fecha date NOT NULL,
    finalidad character varying(500) NOT NULL,
    emplazamiento character varying(200) NOT NULL,
    ia_id integer
);


ALTER TABLE public.proyectos OWNER TO bddat_admin;

--
-- Name: COLUMN proyectos.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.id IS 'Identificador t├®cnico ├║nico autogenerado';


--
-- Name: COLUMN proyectos.titulo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.titulo IS 'T├¡tulo descriptivo del proyecto t├®cnico';


--
-- Name: COLUMN proyectos.descripcion; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.descripcion IS 'Descripci├│n t├®cnica detallada del proyecto (texto libre extenso)';


--
-- Name: COLUMN proyectos.fecha; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.fecha IS 'Fecha t├®cnica del proyecto (firma/visado), NO fecha administrativa de presentaci├│n';


--
-- Name: COLUMN proyectos.finalidad; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.finalidad IS 'Finalidad o uso previsto de la instalaci├│n el├®ctrica';


--
-- Name: COLUMN proyectos.emplazamiento; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.emplazamiento IS 'Ubicaci├│n geogr├ífica de la instalaci├│n (descripci├│n textual)';


--
-- Name: COLUMN proyectos.ia_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.proyectos.ia_id IS 'FK a TIPOS_IA. Instrumento ambiental aplicable (AAI, AAU, AAUS, CA, EXENTO)';


--
-- Name: proyectos_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.proyectos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.proyectos_id_seq OWNER TO bddat_admin;

--
-- Name: proyectos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.proyectos_id_seq OWNED BY public.proyectos.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(200)
);


ALTER TABLE public.roles OWNER TO bddat_admin;

--
-- Name: COLUMN roles.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.roles.id IS 'Identificador ├║nico autogenerado del rol';


--
-- Name: COLUMN roles.nombre; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.roles.nombre IS 'Nombre del rol (ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO)';


--
-- Name: COLUMN roles.descripcion; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.roles.descripcion IS 'Descripci├│n del prop├│sito y permisos del rol';


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO bddat_admin;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: solicitudes; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.solicitudes (
    id integer NOT NULL,
    expediente_id integer NOT NULL,
    solicitud_afectada_id integer,
    fecha_solicitud date NOT NULL,
    estado character varying(20) NOT NULL,
    observaciones character varying(2000)
);


ALTER TABLE public.solicitudes OWNER TO bddat_admin;

--
-- Name: COLUMN solicitudes.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.id IS 'Identificador ├║nico autogenerado de la solicitud';


--
-- Name: COLUMN solicitudes.expediente_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.expediente_id IS 'FK a EXPEDIENTES. Expediente al que pertenece la solicitud';


--
-- Name: COLUMN solicitudes.solicitud_afectada_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.solicitud_afectada_id IS 'FK a SOLICITUDES. Para DESISTIMIENTO/RENUNCIA, solicitud que se desiste';


--
-- Name: COLUMN solicitudes.fecha_solicitud; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.fecha_solicitud IS 'Fecha oficial de presentaci├│n de la solicitud';


--
-- Name: COLUMN solicitudes.estado; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.estado IS 'Estado: EN_TRAMITE, RESUELTA, DESISTIDA, ARCHIVADA';


--
-- Name: COLUMN solicitudes.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes.observaciones IS 'Notas o comentarios adicionales del t├®cnico';


--
-- Name: solicitudes_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.solicitudes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solicitudes_id_seq OWNER TO bddat_admin;

--
-- Name: solicitudes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.solicitudes_id_seq OWNED BY public.solicitudes.id;


--
-- Name: solicitudes_tipos; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.solicitudes_tipos (
    id integer NOT NULL,
    solicitudid integer NOT NULL,
    tiposolicitudid integer NOT NULL
);


ALTER TABLE public.solicitudes_tipos OWNER TO bddat_admin;

--
-- Name: COLUMN solicitudes_tipos.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes_tipos.id IS 'Identificador ├║nico autogenerado del registro puente';


--
-- Name: COLUMN solicitudes_tipos.solicitudid; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes_tipos.solicitudid IS 'FK a SOLICITUDES. Solicitud que contiene este tipo';


--
-- Name: COLUMN solicitudes_tipos.tiposolicitudid; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.solicitudes_tipos.tiposolicitudid IS 'FK a TIPOS_SOLICITUDES. Tipo individual asignado a la solicitud';


--
-- Name: solicitudes_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.solicitudes_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solicitudes_tipos_id_seq OWNER TO bddat_admin;

--
-- Name: solicitudes_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.solicitudes_tipos_id_seq OWNED BY public.solicitudes_tipos.id;


--
-- Name: tareas; Type: TABLE; Schema: public; Owner: bddat_admin
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


ALTER TABLE public.tareas OWNER TO bddat_admin;

--
-- Name: COLUMN tareas.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.id IS 'Identificador ├║nico autogenerado de la tarea';


--
-- Name: COLUMN tareas.tramite_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.tramite_id IS 'FK a TRAMITES. Tr├ímite al que pertenece la tarea';


--
-- Name: COLUMN tareas.tipo_tarea_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.tipo_tarea_id IS 'FK a TIPOS_TAREAS. Tipo de tarea at├│mica (7 tipos posibles)';


--
-- Name: COLUMN tareas.documento_usado_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.documento_usado_id IS 'FK a DOCUMENTOS. Documento usado como input de la tarea';


--
-- Name: COLUMN tareas.documento_producido_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.documento_producido_id IS 'FK UNIQUE a DOCUMENTOS. Documento generado como output de la tarea';


--
-- Name: COLUMN tareas.fecha_inicio; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.fecha_inicio IS 'Fecha de inicio de la tarea. NULL = tarea planificada no iniciada';


--
-- Name: COLUMN tareas.fecha_fin; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.fecha_fin IS 'Fecha de finalizaci├│n de la tarea. NULL = tarea pendiente o en curso';


--
-- Name: COLUMN tareas.notas; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tareas.notas IS 'Observaciones o informaci├│n adicional (plazos, referencia, remitente, etc.)';


--
-- Name: tareas_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.tareas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tareas_id_seq OWNER TO bddat_admin;

--
-- Name: tareas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.tareas_id_seq OWNED BY public.tareas.id;


--
-- Name: tramites; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.tramites (
    id integer NOT NULL,
    fase_id integer NOT NULL,
    tipo_tramite_id integer NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    observaciones character varying(2000)
);


ALTER TABLE public.tramites OWNER TO bddat_admin;

--
-- Name: COLUMN tramites.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.id IS 'Identificador ├║nico autogenerado del tr├ímite';


--
-- Name: COLUMN tramites.fase_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.fase_id IS 'FK a FASES. Fase a la que pertenece el tr├ímite';


--
-- Name: COLUMN tramites.tipo_tramite_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.tipo_tramite_id IS 'FK a TIPOS_TRAMITES. Tipo de tr├ímite';


--
-- Name: COLUMN tramites.fecha_inicio; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.fecha_inicio IS 'Fecha de inicio del tr├ímite. NULL = tr├ímite planificado no iniciado';


--
-- Name: COLUMN tramites.fecha_fin; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.fecha_fin IS 'Fecha de finalizaci├│n del tr├ímite. NULL = tr├ímite pendiente o en curso';


--
-- Name: COLUMN tramites.observaciones; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.tramites.observaciones IS 'Notas o comentarios adicionales del t├®cnico';


--
-- Name: tramites_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.tramites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tramites_id_seq OWNER TO bddat_admin;

--
-- Name: tramites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.tramites_id_seq OWNED BY public.tramites.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: bddat_admin
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


ALTER TABLE public.usuarios OWNER TO bddat_admin;

--
-- Name: COLUMN usuarios.id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.id IS 'Identificador ├║nico autogenerado del usuario';


--
-- Name: COLUMN usuarios.siglas; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.siglas IS 'C├│digo identificativo corto del usuario (├║nico)';


--
-- Name: COLUMN usuarios.nombre; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.nombre IS 'Nombre de pila del usuario';


--
-- Name: COLUMN usuarios.apellido1; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.apellido1 IS 'Primer apellido del usuario';


--
-- Name: COLUMN usuarios.apellido2; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.apellido2 IS 'Segundo apellido del usuario (opcional)';


--
-- Name: COLUMN usuarios.email; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.email IS 'Email del usuario (opcional, ├║nico si no es NULL)';


--
-- Name: COLUMN usuarios.activo; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.activo IS 'TRUE=habilitado, FALSE=desactivado (mantiene historial)';


--
-- Name: COLUMN usuarios.password_hash; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.password_hash IS 'Hash bcrypt de la contrase├▒a (nunca almacenar en texto plano)';


--
-- Name: COLUMN usuarios.reset_token; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.reset_token IS 'Token temporal para recuperaci├│n de contrase├▒a';


--
-- Name: COLUMN usuarios.reset_token_expiry; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios.reset_token_expiry IS 'Fecha de expiraci├│n del token de recuperaci├│n';


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: bddat_admin
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO bddat_admin;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bddat_admin
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: usuarios_roles; Type: TABLE; Schema: public; Owner: bddat_admin
--

CREATE TABLE public.usuarios_roles (
    usuario_id integer NOT NULL,
    rol_id integer NOT NULL
);


ALTER TABLE public.usuarios_roles OWNER TO bddat_admin;

--
-- Name: COLUMN usuarios_roles.usuario_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios_roles.usuario_id IS 'FK a USUARIOS. Usuario al que se asigna el rol';


--
-- Name: COLUMN usuarios_roles.rol_id; Type: COMMENT; Schema: public; Owner: bddat_admin
--

COMMENT ON COLUMN public.usuarios_roles.rol_id IS 'FK a ROLES. Rol asignado al usuario';


--
-- Name: municipios id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.municipios ALTER COLUMN id SET DEFAULT nextval('estructura.municipios_id_seq'::regclass);


--
-- Name: tipos_entidades id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_entidades ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_entidades_id_seq'::regclass);


--
-- Name: tipos_expedientes id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_expedientes ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_expedientes_id_seq'::regclass);


--
-- Name: tipos_fases id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_fases ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_fases_id_seq'::regclass);


--
-- Name: tipos_ia id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_ia ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_ia_id_seq'::regclass);


--
-- Name: tipos_resultados_fases id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_resultados_fases ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_resultados_fases_id_seq'::regclass);


--
-- Name: tipos_solicitudes id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_solicitudes ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_solicitudes_id_seq'::regclass);


--
-- Name: tipos_tareas id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tareas ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_tareas_id_seq'::regclass);


--
-- Name: tipos_tramites id; Type: DEFAULT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tramites ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_tramites_id_seq'::regclass);


--
-- Name: autorizados_titular id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.autorizados_titular ALTER COLUMN id SET DEFAULT nextval('public.autorizados_titular_id_seq'::regclass);


--
-- Name: documentos id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos ALTER COLUMN id SET DEFAULT nextval('public.documentos_id_seq'::regclass);


--
-- Name: documentos_proyecto id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos_proyecto ALTER COLUMN id SET DEFAULT nextval('public.documentos_proyecto_id_seq'::regclass);


--
-- Name: entidades id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades ALTER COLUMN id SET DEFAULT nextval('public.entidades_id_seq'::regclass);


--
-- Name: expedientes id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes ALTER COLUMN id SET DEFAULT nextval('public.expedientes_id_seq'::regclass);


--
-- Name: fases id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases ALTER COLUMN id SET DEFAULT nextval('public.fases_id_seq'::regclass);


--
-- Name: municipios_proyecto id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.municipios_proyecto ALTER COLUMN id SET DEFAULT nextval('public.municipios_proyecto_id_seq'::regclass);


--
-- Name: proyectos id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.proyectos ALTER COLUMN id SET DEFAULT nextval('public.proyectos_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: solicitudes id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes ALTER COLUMN id SET DEFAULT nextval('public.solicitudes_id_seq'::regclass);


--
-- Name: solicitudes_tipos id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes_tipos ALTER COLUMN id SET DEFAULT nextval('public.solicitudes_tipos_id_seq'::regclass);


--
-- Name: tareas id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas ALTER COLUMN id SET DEFAULT nextval('public.tareas_id_seq'::regclass);


--
-- Name: tramites id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tramites ALTER COLUMN id SET DEFAULT nextval('public.tramites_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: municipios municipios_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.municipios
    ADD CONSTRAINT municipios_codigo_key UNIQUE (codigo);


--
-- Name: municipios municipios_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.municipios
    ADD CONSTRAINT municipios_pkey PRIMARY KEY (id);


--
-- Name: tipos_entidades tipos_entidades_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_entidades
    ADD CONSTRAINT tipos_entidades_codigo_key UNIQUE (codigo);


--
-- Name: tipos_entidades tipos_entidades_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_entidades
    ADD CONSTRAINT tipos_entidades_pkey PRIMARY KEY (id);


--
-- Name: tipos_expedientes tipos_expedientes_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_expedientes
    ADD CONSTRAINT tipos_expedientes_pkey PRIMARY KEY (id);


--
-- Name: tipos_fases tipos_fases_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_fases
    ADD CONSTRAINT tipos_fases_codigo_key UNIQUE (codigo);


--
-- Name: tipos_fases tipos_fases_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_fases
    ADD CONSTRAINT tipos_fases_pkey PRIMARY KEY (id);


--
-- Name: tipos_ia tipos_ia_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_ia
    ADD CONSTRAINT tipos_ia_pkey PRIMARY KEY (id);


--
-- Name: tipos_ia tipos_ia_siglas_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_ia
    ADD CONSTRAINT tipos_ia_siglas_key UNIQUE (siglas);


--
-- Name: tipos_resultados_fases tipos_resultados_fases_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_resultados_fases
    ADD CONSTRAINT tipos_resultados_fases_codigo_key UNIQUE (codigo);


--
-- Name: tipos_resultados_fases tipos_resultados_fases_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_resultados_fases
    ADD CONSTRAINT tipos_resultados_fases_pkey PRIMARY KEY (id);


--
-- Name: tipos_solicitudes tipos_solicitudes_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_solicitudes
    ADD CONSTRAINT tipos_solicitudes_pkey PRIMARY KEY (id);


--
-- Name: tipos_solicitudes tipos_solicitudes_siglas_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_solicitudes
    ADD CONSTRAINT tipos_solicitudes_siglas_key UNIQUE (siglas);


--
-- Name: tipos_tareas tipos_tareas_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tareas
    ADD CONSTRAINT tipos_tareas_codigo_key UNIQUE (codigo);


--
-- Name: tipos_tareas tipos_tareas_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tareas
    ADD CONSTRAINT tipos_tareas_pkey PRIMARY KEY (id);


--
-- Name: tipos_tramites tipos_tramites_codigo_key; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tramites
    ADD CONSTRAINT tipos_tramites_codigo_key UNIQUE (codigo);


--
-- Name: tipos_tramites tipos_tramites_pkey; Type: CONSTRAINT; Schema: estructura; Owner: bddat_admin
--

ALTER TABLE ONLY estructura.tipos_tramites
    ADD CONSTRAINT tipos_tramites_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: autorizados_titular autorizados_titular_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.autorizados_titular
    ADD CONSTRAINT autorizados_titular_pkey PRIMARY KEY (id);


--
-- Name: documentos documentos_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos
    ADD CONSTRAINT documentos_pkey PRIMARY KEY (id);


--
-- Name: documentos_proyecto documentos_proyecto_documento_id_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_documento_id_key UNIQUE (documento_id);


--
-- Name: documentos_proyecto documentos_proyecto_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_pkey PRIMARY KEY (id);


--
-- Name: entidades_administrados entidades_administrados_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_administrados
    ADD CONSTRAINT entidades_administrados_pkey PRIMARY KEY (entidad_id);


--
-- Name: entidades_ayuntamientos entidades_ayuntamientos_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_ayuntamientos
    ADD CONSTRAINT entidades_ayuntamientos_pkey PRIMARY KEY (entidad_id);


--
-- Name: entidades entidades_cif_nif_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades
    ADD CONSTRAINT entidades_cif_nif_key UNIQUE (cif_nif);


--
-- Name: entidades_diputaciones entidades_diputaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_diputaciones
    ADD CONSTRAINT entidades_diputaciones_pkey PRIMARY KEY (entidad_id);


--
-- Name: entidades_empresas_servicio_publico entidades_empresas_servicio_publico_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_empresas_servicio_publico
    ADD CONSTRAINT entidades_empresas_servicio_publico_pkey PRIMARY KEY (entidad_id);


--
-- Name: entidades_organismos_publicos entidades_organismos_publicos_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_organismos_publicos
    ADD CONSTRAINT entidades_organismos_publicos_pkey PRIMARY KEY (entidad_id);


--
-- Name: entidades entidades_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades
    ADD CONSTRAINT entidades_pkey PRIMARY KEY (id);


--
-- Name: expedientes expedientes_numero_at_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_numero_at_key UNIQUE (numero_at);


--
-- Name: expedientes expedientes_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_pkey PRIMARY KEY (id);


--
-- Name: expedientes expedientes_proyecto_id_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_proyecto_id_key UNIQUE (proyecto_id);


--
-- Name: fases fases_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_pkey PRIMARY KEY (id);


--
-- Name: municipios_proyecto municipios_proyecto_municipio_proyecto_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_municipio_proyecto_key UNIQUE (municipio_id, proyecto_id);


--
-- Name: municipios_proyecto municipios_proyecto_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_pkey PRIMARY KEY (id);


--
-- Name: proyectos proyectos_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.proyectos
    ADD CONSTRAINT proyectos_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: solicitudes solicitudes_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes
    ADD CONSTRAINT solicitudes_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_tipos solicitudes_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_tipos solicitudes_tipos_solicitudid_tiposolicitudid_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_solicitudid_tiposolicitudid_key UNIQUE (solicitudid, tiposolicitudid);


--
-- Name: tareas tareas_documento_producido_id_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_producido_id_key UNIQUE (documento_producido_id);


--
-- Name: tareas tareas_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_pkey PRIMARY KEY (id);


--
-- Name: tramites tramites_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_pkey PRIMARY KEY (id);


--
-- Name: autorizados_titular uq_titular_autorizado; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.autorizados_titular
    ADD CONSTRAINT uq_titular_autorizado UNIQUE (titular_entidad_id, autorizado_entidad_id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios_roles usuarios_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_pkey PRIMARY KEY (usuario_id, rol_id);


--
-- Name: usuarios usuarios_siglas_key; Type: CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_siglas_key UNIQUE (siglas);


--
-- Name: ix_estructura_tipos_entidades_codigo; Type: INDEX; Schema: estructura; Owner: bddat_admin
--

CREATE INDEX ix_estructura_tipos_entidades_codigo ON estructura.tipos_entidades USING btree (codigo);


--
-- Name: idx_documentos_expediente; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_documentos_expediente ON public.documentos USING btree (expediente_id);


--
-- Name: idx_documentos_fecha_administrativa; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_documentos_fecha_administrativa ON public.documentos USING btree (fecha_administrativa);


--
-- Name: idx_documentos_hash; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_documentos_hash ON public.documentos USING btree (hash_md5);


--
-- Name: idx_documentos_proyecto_proyecto; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_documentos_proyecto_proyecto ON public.documentos_proyecto USING btree (proyecto_id);


--
-- Name: idx_documentos_proyecto_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_documentos_proyecto_tipo ON public.documentos_proyecto USING btree (proyecto_id, tipo);


--
-- Name: idx_expedientes_numero_at; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_expedientes_numero_at ON public.expedientes USING btree (numero_at);


--
-- Name: idx_expedientes_proyecto; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_expedientes_proyecto ON public.expedientes USING btree (proyecto_id);


--
-- Name: idx_expedientes_responsable; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_expedientes_responsable ON public.expedientes USING btree (responsable_id);


--
-- Name: idx_expedientes_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_expedientes_tipo ON public.expedientes USING btree (tipo_expediente_id);


--
-- Name: idx_fases_fechas; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_fases_fechas ON public.fases USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_fases_resultado; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_fases_resultado ON public.fases USING btree (resultado_fase_id);


--
-- Name: idx_fases_solicitud; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_fases_solicitud ON public.fases USING btree (solicitud_id);


--
-- Name: idx_fases_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_fases_tipo ON public.fases USING btree (tipo_fase_id);


--
-- Name: idx_municipios_proyecto_municipio; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_municipios_proyecto_municipio ON public.municipios_proyecto USING btree (municipio_id);


--
-- Name: idx_municipios_proyecto_proyecto; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_municipios_proyecto_proyecto ON public.municipios_proyecto USING btree (proyecto_id);


--
-- Name: idx_proyectos_fecha; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_proyectos_fecha ON public.proyectos USING btree (fecha);


--
-- Name: idx_proyectos_ia; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_proyectos_ia ON public.proyectos USING btree (ia_id);


--
-- Name: idx_solicitudes_estado; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_solicitudes_estado ON public.solicitudes USING btree (estado);


--
-- Name: idx_solicitudes_expediente; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_solicitudes_expediente ON public.solicitudes USING btree (expediente_id);


--
-- Name: idx_solicitudes_fecha; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_solicitudes_fecha ON public.solicitudes USING btree (fecha_solicitud);


--
-- Name: idx_solicitudes_tipos_solicitud; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_solicitudes_tipos_solicitud ON public.solicitudes_tipos USING btree (solicitudid);


--
-- Name: idx_solicitudes_tipos_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_solicitudes_tipos_tipo ON public.solicitudes_tipos USING btree (tiposolicitudid);


--
-- Name: idx_tareas_documento_usado; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tareas_documento_usado ON public.tareas USING btree (documento_usado_id);


--
-- Name: idx_tareas_fechas; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tareas_fechas ON public.tareas USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_tareas_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tareas_tipo ON public.tareas USING btree (tipo_tarea_id);


--
-- Name: idx_tareas_tramite; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tareas_tramite ON public.tareas USING btree (tramite_id);


--
-- Name: idx_titular_activo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_titular_activo ON public.autorizados_titular USING btree (titular_entidad_id, activo);


--
-- Name: idx_tramites_fase; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tramites_fase ON public.tramites USING btree (fase_id);


--
-- Name: idx_tramites_fechas; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tramites_fechas ON public.tramites USING btree (fecha_inicio, fecha_fin);


--
-- Name: idx_tramites_tipo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_tramites_tipo ON public.tramites USING btree (tipo_tramite_id);


--
-- Name: idx_usuarios_email; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_usuarios_email ON public.usuarios USING btree (email);


--
-- Name: idx_usuarios_siglas; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX idx_usuarios_siglas ON public.usuarios USING btree (siglas);


--
-- Name: ix_public_autorizados_titular_activo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_autorizados_titular_activo ON public.autorizados_titular USING btree (activo);


--
-- Name: ix_public_autorizados_titular_autorizado_entidad_id; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_autorizados_titular_autorizado_entidad_id ON public.autorizados_titular USING btree (autorizado_entidad_id);


--
-- Name: ix_public_autorizados_titular_titular_entidad_id; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_autorizados_titular_titular_entidad_id ON public.autorizados_titular USING btree (titular_entidad_id);


--
-- Name: ix_public_entidades_activo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_activo ON public.entidades USING btree (activo);


--
-- Name: ix_public_entidades_administrados_email_notificaciones; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_administrados_email_notificaciones ON public.entidades_administrados USING btree (email_notificaciones);


--
-- Name: ix_public_entidades_administrados_representante_nif_cif; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_administrados_representante_nif_cif ON public.entidades_administrados USING btree (representante_nif_cif);


--
-- Name: ix_public_entidades_ayuntamientos_codigo_dir3; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE UNIQUE INDEX ix_public_entidades_ayuntamientos_codigo_dir3 ON public.entidades_ayuntamientos USING btree (codigo_dir3);


--
-- Name: ix_public_entidades_ayuntamientos_codigo_ine_municipio; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_ayuntamientos_codigo_ine_municipio ON public.entidades_ayuntamientos USING btree (codigo_ine_municipio);


--
-- Name: ix_public_entidades_cif_nif; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_cif_nif ON public.entidades USING btree (cif_nif);


--
-- Name: ix_public_entidades_diputaciones_codigo_dir3; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE UNIQUE INDEX ix_public_entidades_diputaciones_codigo_dir3 ON public.entidades_diputaciones USING btree (codigo_dir3);


--
-- Name: ix_public_entidades_diputaciones_codigo_ine_municipio_sede; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_diputaciones_codigo_ine_municipio_sede ON public.entidades_diputaciones USING btree (codigo_ine_municipio_sede);


--
-- Name: ix_public_entidades_municipio_id; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_municipio_id ON public.entidades USING btree (municipio_id);


--
-- Name: ix_public_entidades_nombre_completo; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_nombre_completo ON public.entidades USING btree (nombre_completo);


--
-- Name: ix_public_entidades_organismos_publicos_codigo_dir3; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE UNIQUE INDEX ix_public_entidades_organismos_publicos_codigo_dir3 ON public.entidades_organismos_publicos USING btree (codigo_dir3);


--
-- Name: ix_public_entidades_tipo_entidad_id; Type: INDEX; Schema: public; Owner: bddat_admin
--

CREATE INDEX ix_public_entidades_tipo_entidad_id ON public.entidades USING btree (tipo_entidad_id);


--
-- Name: autorizados_titular autorizados_titular_autorizado_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.autorizados_titular
    ADD CONSTRAINT autorizados_titular_autorizado_entidad_id_fkey FOREIGN KEY (autorizado_entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: autorizados_titular autorizados_titular_titular_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.autorizados_titular
    ADD CONSTRAINT autorizados_titular_titular_entidad_id_fkey FOREIGN KEY (titular_entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: documentos documentos_expediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos
    ADD CONSTRAINT documentos_expediente_id_fkey FOREIGN KEY (expediente_id) REFERENCES public.expedientes(id);


--
-- Name: documentos_proyecto documentos_proyecto_documento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT documentos_proyecto_documento_id_fkey FOREIGN KEY (documento_id) REFERENCES public.documentos(id) ON DELETE CASCADE;


--
-- Name: entidades_administrados entidades_administrados_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_administrados
    ADD CONSTRAINT entidades_administrados_entidad_id_fkey FOREIGN KEY (entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: entidades_ayuntamientos entidades_ayuntamientos_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_ayuntamientos
    ADD CONSTRAINT entidades_ayuntamientos_entidad_id_fkey FOREIGN KEY (entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: entidades_diputaciones entidades_diputaciones_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_diputaciones
    ADD CONSTRAINT entidades_diputaciones_entidad_id_fkey FOREIGN KEY (entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: entidades_empresas_servicio_publico entidades_empresas_servicio_publico_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_empresas_servicio_publico
    ADD CONSTRAINT entidades_empresas_servicio_publico_entidad_id_fkey FOREIGN KEY (entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: entidades entidades_municipio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades
    ADD CONSTRAINT entidades_municipio_id_fkey FOREIGN KEY (municipio_id) REFERENCES estructura.municipios(id);


--
-- Name: entidades_organismos_publicos entidades_organismos_publicos_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades_organismos_publicos
    ADD CONSTRAINT entidades_organismos_publicos_entidad_id_fkey FOREIGN KEY (entidad_id) REFERENCES public.entidades(id) ON DELETE CASCADE;


--
-- Name: entidades entidades_tipo_entidad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.entidades
    ADD CONSTRAINT entidades_tipo_entidad_id_fkey FOREIGN KEY (tipo_entidad_id) REFERENCES estructura.tipos_entidades(id);


--
-- Name: expedientes expedientes_proyecto_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_proyecto_id_fkey FOREIGN KEY (proyecto_id) REFERENCES public.proyectos(id);


--
-- Name: expedientes expedientes_responsable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_responsable_id_fkey FOREIGN KEY (responsable_id) REFERENCES public.usuarios(id);


--
-- Name: expedientes expedientes_tipo_expediente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.expedientes
    ADD CONSTRAINT expedientes_tipo_expediente_id_fkey FOREIGN KEY (tipo_expediente_id) REFERENCES estructura.tipos_expedientes(id);


--
-- Name: fases fases_documento_resultado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_documento_resultado_id_fkey FOREIGN KEY (documento_resultado_id) REFERENCES public.documentos(id);


--
-- Name: fases fases_resultado_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_resultado_fase_id_fkey FOREIGN KEY (resultado_fase_id) REFERENCES estructura.tipos_resultados_fases(id);


--
-- Name: fases fases_solicitud_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_solicitud_id_fkey FOREIGN KEY (solicitud_id) REFERENCES public.solicitudes(id) ON DELETE CASCADE;


--
-- Name: fases fases_tipo_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.fases
    ADD CONSTRAINT fases_tipo_fase_id_fkey FOREIGN KEY (tipo_fase_id) REFERENCES estructura.tipos_fases(id);


--
-- Name: documentos_proyecto fk_documentos_proyecto_proyecto; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.documentos_proyecto
    ADD CONSTRAINT fk_documentos_proyecto_proyecto FOREIGN KEY (proyecto_id) REFERENCES public.proyectos(id) ON DELETE CASCADE;


--
-- Name: municipios_proyecto municipios_proyecto_municipio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.municipios_proyecto
    ADD CONSTRAINT municipios_proyecto_municipio_id_fkey FOREIGN KEY (municipio_id) REFERENCES estructura.municipios(id);


--
-- Name: proyectos proyectos_ia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.proyectos
    ADD CONSTRAINT proyectos_ia_id_fkey FOREIGN KEY (ia_id) REFERENCES estructura.tipos_ia(id);


--
-- Name: solicitudes solicitudes_solicitud_afectada_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes
    ADD CONSTRAINT solicitudes_solicitud_afectada_id_fkey FOREIGN KEY (solicitud_afectada_id) REFERENCES public.solicitudes(id);


--
-- Name: solicitudes_tipos solicitudes_tipos_solicitudid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_solicitudid_fkey FOREIGN KEY (solicitudid) REFERENCES public.solicitudes(id) ON DELETE CASCADE;


--
-- Name: solicitudes_tipos solicitudes_tipos_tiposolicitudid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.solicitudes_tipos
    ADD CONSTRAINT solicitudes_tipos_tiposolicitudid_fkey FOREIGN KEY (tiposolicitudid) REFERENCES estructura.tipos_solicitudes(id);


--
-- Name: tareas tareas_documento_producido_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_producido_id_fkey FOREIGN KEY (documento_producido_id) REFERENCES public.documentos(id);


--
-- Name: tareas tareas_documento_usado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_documento_usado_id_fkey FOREIGN KEY (documento_usado_id) REFERENCES public.documentos(id);


--
-- Name: tareas tareas_tipo_tarea_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_tipo_tarea_id_fkey FOREIGN KEY (tipo_tarea_id) REFERENCES estructura.tipos_tareas(id);


--
-- Name: tareas tareas_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tareas
    ADD CONSTRAINT tareas_tramite_id_fkey FOREIGN KEY (tramite_id) REFERENCES public.tramites(id) ON DELETE CASCADE;


--
-- Name: tramites tramites_fase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_fase_id_fkey FOREIGN KEY (fase_id) REFERENCES public.fases(id) ON DELETE CASCADE;


--
-- Name: tramites tramites_tipo_tramite_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.tramites
    ADD CONSTRAINT tramites_tipo_tramite_id_fkey FOREIGN KEY (tipo_tramite_id) REFERENCES estructura.tipos_tramites(id);


--
-- Name: usuarios_roles usuarios_roles_rol_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_rol_id_fkey FOREIGN KEY (rol_id) REFERENCES public.roles(id);


--
-- Name: usuarios_roles usuarios_roles_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: bddat_admin
--

ALTER TABLE ONLY public.usuarios_roles
    ADD CONSTRAINT usuarios_roles_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: bddat_admin
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: estructura; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA estructura GRANT ALL ON SEQUENCES TO bddat_admin;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: estructura; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA estructura GRANT ALL ON TABLES TO bddat_admin;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO bddat_admin;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO bddat_admin;


--
-- PostgreSQL database dump complete
--

\unrestrict AVJQrvdVqkYwVPFjvaxEkdP0fzioOgyFynNiP0aEKrkOumQ3kLQkIq0sL5McrvR

