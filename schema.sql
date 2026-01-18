--
-- PostgreSQL database dump
--

\restrict ferRp7yM8gE0LVazBLNHnQgyTj7iFHTJuFht99ZjeelWmkOBbNQ36nCVcbNlpGJ

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

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
-- Name: tipos_expedientes id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_expedientes ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_expedientes_id_seq'::regclass);


--
-- Name: tipos_ia id; Type: DEFAULT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_ia ALTER COLUMN id SET DEFAULT nextval('estructura.tipos_ia_id_seq'::regclass);


--
-- Name: expedientes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expedientes ALTER COLUMN id SET DEFAULT nextval('public.expedientes_id_seq'::regclass);


--
-- Name: proyectos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.proyectos ALTER COLUMN id SET DEFAULT nextval('public.proyectos_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: tipos_expedientes tipos_expedientes_pkey; Type: CONSTRAINT; Schema: estructura; Owner: postgres
--

ALTER TABLE ONLY estructura.tipos_expedientes
    ADD CONSTRAINT tipos_expedientes_pkey PRIMARY KEY (id);


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
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


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

\unrestrict ferRp7yM8gE0LVazBLNHnQgyTj7iFHTJuFht99ZjeelWmkOBbNQ36nCVcbNlpGJ

