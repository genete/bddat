-- ============================================================
-- DDL PostgreSQL - Schema: legacy
-- Origen: BDD ALTA TENSION.mdb (Access 2000)
-- Generado: 2026-02-17
--
-- Mapeo de tipos Access → PostgreSQL:
--   Boolean(1)    → BOOLEAN
--   Long Int(4)   → INTEGER
--   Single(7)     → REAL
--   Double(5)     → DOUBLE PRECISION
--   Date/Time(8)  → TIMESTAMP
--   Text(10)      → VARCHAR(n)
--   Memo(12)      → TEXT
--
-- FK DEFERRABLE: permite carga inicial sin integridad garantizada.
-- FK implícitas comentadas: verificar huérfanos antes de activar:
--   SELECT COUNT(*) FROM legacy.hijo WHERE fk NOT IN
--     (SELECT pk FROM legacy.padre WHERE pk IS NOT NULL)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS legacy;
SET search_path TO legacy;

-- ------------------------------------------------------------
-- PROVINCIAS
-- ------------------------------------------------------------
CREATE TABLE provincias (
    d_provincia VARCHAR(255) NOT NULL,
    id_provincia INTEGER NOT NULL,
    CONSTRAINT pk_provincias PRIMARY KEY (id_provincia)
);
COMMENT ON TABLE provincias IS 'Access original: PROVINCIAS';

-- ------------------------------------------------------------
-- MUNICIPIOS
-- ------------------------------------------------------------
CREATE TABLE municipios (
    d_municipio VARCHAR(255),
    d_provincia VARCHAR(50),
    id_municipio INTEGER NOT NULL,
    id_provincia INTEGER,
    CONSTRAINT pk_municipios PRIMARY KEY (id_municipio)
);
COMMENT ON TABLE municipios IS 'Access original: MUNICIPIOS';

-- ------------------------------------------------------------
-- CODIGOS POSTALES
-- ------------------------------------------------------------
CREATE TABLE codigos_postales (
    callejero BOOLEAN,
    codigo_postal VARCHAR(50),
    d_municipio VARCHAR(255),
    id_municipio INTEGER NOT NULL,
    provincia VARCHAR(50),
    CONSTRAINT pk_codigos_postales PRIMARY KEY (id_municipio)
);
COMMENT ON TABLE codigos_postales IS 'Access original: CODIGOS POSTALES';

-- ------------------------------------------------------------
-- TENSION_LI
-- ------------------------------------------------------------
CREATE TABLE tension_li (
    id INTEGER NOT NULL,
    tension INTEGER,
    CONSTRAINT pk_tension_li PRIMARY KEY (id)
);
COMMENT ON TABLE tension_li IS 'Access original: TENSION_LI';

-- ------------------------------------------------------------
-- TIPO_LI
-- ------------------------------------------------------------
CREATE TABLE tipo_li (
    id INTEGER NOT NULL,
    tipo VARCHAR(255),
    CONSTRAINT pk_tipo_li PRIMARY KEY (id)
);
COMMENT ON TABLE tipo_li IS 'Access original: TIPO_LI';

-- ------------------------------------------------------------
-- CONDUCTORES_LI
-- ------------------------------------------------------------
CREATE TABLE conductores_li (
    conductores VARCHAR(255),
    id INTEGER NOT NULL,
    CONSTRAINT pk_conductores_li PRIMARY KEY (id)
);
COMMENT ON TABLE conductores_li IS 'Access original: CONDUCTORES_LI';

-- ------------------------------------------------------------
-- APOYOS_LI
-- ------------------------------------------------------------
CREATE TABLE apoyos_li (
    apoyos VARCHAR(255),
    id INTEGER NOT NULL,
    CONSTRAINT pk_apoyos_li PRIMARY KEY (id)
);
COMMENT ON TABLE apoyos_li IS 'Access original: APOYOS_LI';

-- ------------------------------------------------------------
-- TIPO_CT
-- ------------------------------------------------------------
CREATE TABLE tipo_ct (
    id INTEGER NOT NULL,
    tipo VARCHAR(255),
    CONSTRAINT pk_tipo_ct PRIMARY KEY (id)
);
COMMENT ON TABLE tipo_ct IS 'Access original: TIPO_CT';

-- ------------------------------------------------------------
-- RELACION_CT
-- ------------------------------------------------------------
CREATE TABLE relacion_ct (
    id INTEGER NOT NULL,
    relacion VARCHAR(255),
    CONSTRAINT pk_relacion_ct PRIMARY KEY (id)
);
COMMENT ON TABLE relacion_ct IS 'Access original: RELACION_CT';

-- ------------------------------------------------------------
-- COMPOSICION_CT
-- ------------------------------------------------------------
CREATE TABLE composicion_ct (
    composicion VARCHAR(255),
    id INTEGER NOT NULL,
    CONSTRAINT pk_composicion_ct PRIMARY KEY (id)
);
COMMENT ON TABLE composicion_ct IS 'Access original: COMPOSICION_CT';

-- ------------------------------------------------------------
-- POTENCIA_CT
-- ------------------------------------------------------------
CREATE TABLE potencia_ct (
    id INTEGER NOT NULL,
    potencia INTEGER,
    CONSTRAINT pk_potencia_ct PRIMARY KEY (id)
);
COMMENT ON TABLE potencia_ct IS 'Access original: POTENCIA_CT';

-- ------------------------------------------------------------
-- Beneficiaria
-- ------------------------------------------------------------
CREATE TABLE beneficiaria (
    cif VARCHAR(50),
    contacto VARCHAR(50),
    correo VARCHAR(50),
    cp VARCHAR(5),
    direccion VARCHAR(60),
    dnicontacto VARCHAR(9),
    id INTEGER NOT NULL,
    nombre VARCHAR(50),
    notario VARCHAR(50),
    poblacion VARCHAR(50),
    poder TIMESTAMP,
    protocolo VARCHAR(50),
    provincia VARCHAR(50),
    telefono VARCHAR(50),
    CONSTRAINT pk_beneficiaria PRIMARY KEY (id)
);
COMMENT ON TABLE beneficiaria IS 'Access original: Beneficiaria';

-- ------------------------------------------------------------
-- Gestora
-- ------------------------------------------------------------
CREATE TABLE gestora (
    cif VARCHAR(50),
    contacto VARCHAR(50),
    correo VARCHAR(50),
    cp VARCHAR(5),
    direccion VARCHAR(60),
    id INTEGER NOT NULL,
    nombre VARCHAR(50),
    poblacion VARCHAR(50),
    provincia VARCHAR(50),
    telefono VARCHAR(50),
    CONSTRAINT pk_gestora PRIMARY KEY (id)
);
COMMENT ON TABLE gestora IS 'Access original: Gestora';

-- ------------------------------------------------------------
-- FIRMANTES
-- ------------------------------------------------------------
CREATE TABLE firmantes (
    firmante VARCHAR(50),
    firmante_jd VARCHAR(50),
    firmante_js VARCHAR(50),
    firmante_secre VARCHAR(50),
    id_firmante INTEGER NOT NULL,
    pie_de_firma VARCHAR(50),
    pie_de_firma_2 VARCHAR(50),
    pie_de_firma_2_jd VARCHAR(50),
    pie_de_firma_2_js VARCHAR(50),
    pie_de_firma_jd VARCHAR(50),
    pie_de_firma_js VARCHAR(50),
    pie_de_firma_secre VARCHAR(50),
    pie_de_sirma_2_secre VARCHAR(50),
    CONSTRAINT pk_firmantes PRIMARY KEY (id_firmante)
);
COMMENT ON TABLE firmantes IS 'Access original: FIRMANTES';

-- ------------------------------------------------------------
-- DIARIO
-- ------------------------------------------------------------
CREATE TABLE diario (
    cargo VARCHAR(50),
    cp VARCHAR(50),
    direccion VARCHAR(50),
    id INTEGER NOT NULL,
    nombre VARCHAR(50),
    poblacion VARCHAR(50),
    provincia VARCHAR(50),
    CONSTRAINT pk_diario PRIMARY KEY (id)
);
COMMENT ON TABLE diario IS 'Access original: DIARIO';

-- ------------------------------------------------------------
-- organismos
-- ------------------------------------------------------------
CREATE TABLE organismos (
    ayto BOOLEAN,
    cp VARCHAR(50),
    direccion VARCHAR(60),
    id INTEGER NOT NULL,
    nombre VARCHAR(100),
    poblacion VARCHAR(50),
    provincia VARCHAR(50),
    tratamiento VARCHAR(50),
    CONSTRAINT pk_organismos PRIMARY KEY (id)
);
COMMENT ON TABLE organismos IS 'Access original: organismos';

-- ------------------------------------------------------------
-- motivos_reque
-- ------------------------------------------------------------
CREATE TABLE motivos_reque (
    id INTEGER NOT NULL,
    textocorto VARCHAR(50),
    textolargo TEXT,
    CONSTRAINT pk_motivos_reque PRIMARY KEY (id)
);
COMMENT ON TABLE motivos_reque IS 'Access original: motivos_reque';

-- ------------------------------------------------------------
-- Entidades
-- NOTA: el campo id_tipoentidad apuntaba a 'Consulta General Tipos
-- de Entidades' que ya no existe en la BD origen. Se incluye la tabla
-- con sus datos pero sin FK a tipos. Contiene ayuntamientos y entidades
-- locales clasificadas usadas en notificaciones.
-- ------------------------------------------------------------
CREATE TABLE entidades (
    codigopostal VARCHAR(12) NOT NULL,
    den_entidad VARCHAR(250) NOT NULL,
    direccion VARCHAR(250),
    id_tipoentidad INTEGER NOT NULL,  -- FK a catálogo de tipos no recuperable
    identidad INTEGER,
    municipio VARCHAR(250),
    provincia VARCHAR(50),
    representante VARCHAR(50),
    saludo VARCHAR(50),
    tratamiento VARCHAR(50),
    CONSTRAINT pk_entidades PRIMARY KEY (identidad)
);
COMMENT ON TABLE entidades IS 'Access original: Entidades. Catálogo de ayuntamientos y entidades locales para notificaciones. id_tipoentidad sin FK recuperable (consulta origen eliminada).';

-- ------------------------------------------------------------
-- EXPEDIENTES
-- ------------------------------------------------------------
CREATE TABLE expedientes (
    f_2_ayuntamiento_actas VARCHAR(50),
    f_2_dias_de_actas_previas VARCHAR(50),
    f_20_dias BOOLEAN,
    f_2servicio TIMESTAMP,
    aau BOOLEAN,
    acuerdo_cpv TIMESTAMP,
    alborada BOOLEAN,
    ano VARCHAR(2),
    archivo TIMESTAMP,
    boe VARCHAR(100),
    boe_energia VARCHAR(50),
    boe_energia_des VARCHAR(50),
    boe_energia_fecha TIMESTAMP,
    boe_energia_res VARCHAR(50),
    boe_legisla VARCHAR(50),
    boe_legisla_fecha TIMESTAMP,
    boja VARCHAR(100),
    boja_energia VARCHAR(50),
    boja_energia_des VARCHAR(50),
    boja_energia_fecha TIMESTAMP,
    boja_energia_res VARCHAR(50),
    boja_legisla VARCHAR(50),
    boja_legisla_fecha TIMESTAMP,
    bop VARCHAR(100),
    bop_energia VARCHAR(50),
    bop_energia_des VARCHAR(50),
    bop_energia_fecha TIMESTAMP,
    bop_energia_res VARCHAR(50),
    bop_legisla VARCHAR(50),
    bop_legisla_fecha TIMESTAMP,
    caja VARCHAR(50),
    caja2 VARCHAR(50),
    caja3 VARCHAR(50),
    caja4 VARCHAR(50),
    caja5 VARCHAR(50),
    cajaenergia VARCHAR(50),
    cedente VARCHAR(250),
    contenido VARCHAR(255),
    contenido2 VARCHAR(255),
    contenido3 VARCHAR(255),
    contenido4 VARCHAR(255),
    contenido5 VARCHAR(255),
    cp_cedente VARCHAR(50),
    departamento VARCHAR(50),
    descripcion_gas TEXT,
    diarios VARCHAR(100),
    dias_de_actas_previas VARCHAR(250),
    domicilio VARCHAR(255),
    domicilio_cedente VARCHAR(250),
    dospes BOOLEAN,
    dp INTEGER  -- Campo sin uso identificado en interfaz.,
    dup BOOLEAN,
    emplazamiento VARCHAR(255),
    entrada TIMESTAMP,
    entrada_reque TIMESTAMP,
    envio_a_cpv TIMESTAMP,
    envio_resolucion_aa TIMESTAMP,
    estado VARCHAR(50),
    estadoe VARCHAR(50),
    exped INTEGER NOT NULL  -- Número administrativo formal del expediente, calculado automáticamente. No es FK.,
    fecha_aa_y_ap TIMESTAMP,
    fecha_boe_energia_des TIMESTAMP,
    fecha_boe_energia_res TIMESTAMP,
    fecha_boja_energia_des TIMESTAMP,
    fecha_boja_energia_res TIMESTAMP,
    fecha_bop_energia_des TIMESTAMP,
    fecha_bop_energia_res TIMESTAMP,
    fecha_contrato TIMESTAMP,
    fecha_diario TIMESTAMP,
    fecha_diario_rup TIMESTAMP,
    fecha_diario2 TIMESTAMP,
    fecha_inspeccion TIMESTAMP,
    fecha_cesion TIMESTAMP,
    finalidad VARCHAR(250),
    id_beneficiaria INTEGER,
    id_diario INTEGER,
    id_diario_rup INTEGER,
    id_firmante INTEGER,
    id_gestora INTEGER,
    ide INTEGER NOT NULL  -- PK interna. EXPED es el número visible en documentos.,
    iid_diario2 INTEGER,
    lineas_electricas TEXT,
    localidad VARCHAR(255),
    localidad_cedente VARCHAR(250),
    municipio VARCHAR(255),
    n_alborada VARCHAR(50),
    nombre VARCHAR(255),
    notificacion_ha_beneficiaria TIMESTAMP,
    observaciones TEXT,
    observaciones_e TEXT,
    parcelas TEXT,
    propuesta_valoracion_cpv TIMESTAMP,
    provincia_cedente VARCHAR(50),
    re REAL  -- Número de registro especial de la instalación. No es FK.,
    requerimiento_ha_beneficiaria TIMESTAMP,
    requerimiento_ha TIMESTAMP,
    resolucion_utilidad_pub TIMESTAMP,
    rup_leg TIMESTAMP,
    ruta VARCHAR(255),
    ruta_leg VARCHAR(255),
    salida_reque TIMESTAMP,
    separatas BOOLEAN,
    servicio TIMESTAMP,
    signatura VARCHAR(50),
    signatura2 VARCHAR(50),
    signatura3 VARCHAR(50),
    signatura4 VARCHAR(50),
    signatura5 VARCHAR(50),
    simplificada BOOLEAN,
    solicitud_acta_previa TIMESTAMP,
    subsanacion TEXT,
    tipo VARCHAR(3),
    tipoexpe VARCHAR(50),
    titular VARCHAR(255),
    todosayuntamientos TEXT,
    todosorganismos TEXT,
    CONSTRAINT pk_expedientes PRIMARY KEY (ide)
);
COMMENT ON TABLE expedientes IS 'Access original: EXPEDIENTES';

-- ------------------------------------------------------------
-- EXPROPIADOS
-- ------------------------------------------------------------
CREATE TABLE expropiados (
    f_2_convocatoria BOOLEAN,
    abono_dp BOOLEAN,
    acta_previa TIMESTAMP,
    acuerdo BOOLEAN,
    acuerdo_cancelacion BOOLEAN,
    acuerdo_cancelacion_jp BOOLEAN,
    afectado BOOLEAN,
    beneficiario TIMESTAMP,
    consignacionjp BOOLEAN,
    cp VARCHAR(5),
    cuantia_dp REAL,
    desconocido BOOLEAN,
    direccion VARCHAR(250),
    excluido BOOLEAN,
    expropiado TIMESTAMP,
    expropiados VARCHAR(70),
    finca VARCHAR(250),
    hora TIMESTAMP,
    id INTEGER NOT NULL,
    idexpe INTEGER,
    imp_justiprecio DOUBLE PRECISION,
    intereses DOUBLE PRECISION,
    justiprecio TIMESTAMP,
    nif VARCHAR(50),
    nif_representante VARCHAR(50),
    nombre VARCHAR(70),
    noreciberesol BOOLEAN,
    notificacion_consignacion_jp BOOLEAN,
    notificacion_ha BOOLEAN,
    notificacion_requerimiento BOOLEAN,
    observaciones VARCHAR(255),
    observaciones_e VARCHAR(255),
    poblacion VARCHAR(50),
    provincia VARCHAR(50),
    remision_cpv TIMESTAMP,
    representante VARCHAR(50),
    requerimiento_expropiado TIMESTAMP,
    solicitud_dp TIMESTAMP,
    telefono VARCHAR(50),
    termino_municipal VARCHAR(50),
    tlfno_representante VARCHAR(50),
    todaslasfincas TEXT,
    CONSTRAINT pk_expropiados PRIMARY KEY (id)
);
COMMENT ON TABLE expropiados IS 'Access original: EXPROPIADOS';

-- ------------------------------------------------------------
-- FINCAS
-- ------------------------------------------------------------
CREATE TABLE fincas (
    dia_citacion TIMESTAMP,
    dia_citacion_2 TIMESTAMP,
    dia_pago TIMESTAMP,
    finca VARCHAR(50),
    hora_citacion TIMESTAMP,
    hora_citacion_2 TIMESTAMP,
    hora_pago TIMESTAMP,
    id INTEGER NOT NULL,
    idexpe INTEGER,
    justiprecio DOUBLE PRECISION,
    municipio VARCHAR(50),
    parcela VARCHAR(50),
    poligono VARCHAR(50),
    sinacuerdo BOOLEAN,
    CONSTRAINT pk_fincas PRIMARY KEY (id)
);
COMMENT ON TABLE fincas IS 'Access original: FINCAS';

-- ------------------------------------------------------------
-- EXPROPIADOSFINCAS
-- ------------------------------------------------------------
CREATE TABLE expropiadosfincas (
    finca VARCHAR(100),
    idexpropiados INTEGER,
    idfincas INTEGER
);
COMMENT ON TABLE expropiadosfincas IS 'Access original: EXPROPIADOSFINCAS';

-- ------------------------------------------------------------
-- REQUERIMIENTOS
-- ------------------------------------------------------------
CREATE TABLE requerimientos (
    entrada_reque TIMESTAMP,
    entrada_reque_rei TIMESTAMP,
    id_reque INTEGER NOT NULL,
    idexpediente INTEGER,
    registro_entrada VARCHAR(50),
    registro_entrada_rei VARCHAR(50),
    registro_salida VARCHAR(50),
    registro_salida_rei VARCHAR(50),
    reitero_requerimiento TEXT,
    reque1 BOOLEAN,
    reque10 BOOLEAN,
    reque11 BOOLEAN,
    reque12 BOOLEAN,
    reque13 BOOLEAN,
    reque14 BOOLEAN,
    reque15 BOOLEAN,
    reque16 BOOLEAN,
    reque17 BOOLEAN,
    reque18 BOOLEAN,
    reque19 BOOLEAN,
    reque2 BOOLEAN,
    reque20 BOOLEAN,
    reque3 BOOLEAN,
    reque4 BOOLEAN,
    reque5 BOOLEAN,
    reque6 BOOLEAN,
    reque7 BOOLEAN,
    reque8 BOOLEAN,
    reque9 BOOLEAN,
    requerimiento TEXT,
    salida_reque TIMESTAMP,
    salida_reque_rei TIMESTAMP,
    CONSTRAINT pk_requerimientos PRIMARY KEY (id_reque)
);
COMMENT ON TABLE requerimientos IS 'Access original: REQUERIMIENTOS';

-- ------------------------------------------------------------
-- ALEGACIONES EXPROPIADOS
-- ------------------------------------------------------------
CREATE TABLE alegaciones_expropiados (
    alegacion TIMESTAMP,
    contesta_titular TIMESTAMP,
    envio_afectado TIMESTAMP,
    envio_titular TIMESTAMP,
    id_alegacion INTEGER NOT NULL,
    idexpe INTEGER,
    idexpropiado INTEGER,
    CONSTRAINT pk_alegaciones_expropiados PRIMARY KEY (id_alegacion)
);
COMMENT ON TABLE alegaciones_expropiados IS 'Access original: ALEGACIONES EXPROPIADOS';

-- ------------------------------------------------------------
-- AYUNTAMIENTOSAFECTADOS
-- ------------------------------------------------------------
CREATE TABLE ayuntamientosafectados (
    ayuntamiento VARCHAR(100),
    diapago TIMESTAMP,
    horafinpago TIMESTAMP,
    horainiciopago TIMESTAMP,
    idayuntamiento INTEGER NOT NULL,
    idexpediente INTEGER,
    municipio VARCHAR(50),
    tablon TIMESTAMP,
    CONSTRAINT pk_ayuntamientosafectados PRIMARY KEY (idayuntamiento)
);
COMMENT ON TABLE ayuntamientosafectados IS 'Access original: AYUNTAMIENTOSAFECTADOS';

-- ------------------------------------------------------------
-- AYUNTAMIENTOSDESCONOCIDOS
-- ------------------------------------------------------------
CREATE TABLE ayuntamientosdesconocidos (
    ayuntamiento VARCHAR(100),
    idayuntamiento INTEGER NOT NULL,
    idexpediente INTEGER,
    tablon TIMESTAMP,
    CONSTRAINT pk_ayuntamientosdesconocidos PRIMARY KEY (idayuntamiento)
);
COMMENT ON TABLE ayuntamientosdesconocidos IS 'Access original: AYUNTAMIENTOSDESCONOCIDOS';

-- ------------------------------------------------------------
-- ORGANISMOSAFECTADOS
-- ------------------------------------------------------------
CREATE TABLE organismosafectados (
    f_2_contestacion_organismo TIMESTAMP,
    f_2_traslado_titular TIMESTAMP,
    ayuntamiento VARCHAR(100),
    contestacion_organismo TIMESTAMP,
    envio_separata TIMESTAMP,
    idexpediente INTEGER,
    idorganismo INTEGER,
    notifica1 TIMESTAMP,
    notifica2 TIMESTAMP,
    notifica3 TIMESTAMP,
    notifica4 TIMESTAMP,
    notificaraa TIMESTAMP,
    organismo VARCHAR(100),
    registro_envio VARCHAR(50),
    registro_reitero VARCHAR(50),
    reitero_separata TIMESTAMP,
    remision_respuesta TIMESTAMP,
    respuesta_titular TIMESTAMP,
    tablon TIMESTAMP,
    traslado_titular TIMESTAMP
);
COMMENT ON TABLE organismosafectados IS 'Access original: ORGANISMOSAFECTADOS';

-- ------------------------------------------------------------
-- LINEAS
-- ------------------------------------------------------------
CREATE TABLE lineas (
    li_apoyos INTEGER,
    li_conductor INTEGER,
    li_descripcion VARCHAR(255),
    li_final_de VARCHAR(255),
    li_final_re INTEGER  -- Referencia experimental a EXPEDIENTES.RE, 99% vacío. Sin FK.,
    li_id INTEGER NOT NULL,
    li_idexp INTEGER,
    li_longitud REAL,
    li_num INTEGER,
    li_origen_de VARCHAR(255),
    li_origen_re INTEGER  -- Referencia experimental a EXPEDIENTES.RE, 99% vacío. Sin FK.,
    li_otros VARCHAR(255),
    li_re INTEGER  -- Referencia experimental a EXPEDIENTES.RE, 99% vacío. Sin FK.,
    li_tension INTEGER,
    li_tipo INTEGER,
    CONSTRAINT pk_lineas PRIMARY KEY (li_id)
);
COMMENT ON TABLE lineas IS 'Access original: LINEAS';

-- ------------------------------------------------------------
-- CT
-- ------------------------------------------------------------
CREATE TABLE ct (
    ct_composicion INTEGER,
    ct_descripcion VARCHAR(255),
    ct_emplazamiento VARCHAR(255),
    ct_id INTEGER NOT NULL,
    ct_idexp INTEGER,
    ct_num INTEGER,
    ct_potencia VARCHAR(255),
    ct_re INTEGER  -- Referencia experimental a EXPEDIENTES.RE, 99% vacío. Sin FK.,
    ct_relacion INTEGER,
    ct_tipo INTEGER,
    CONSTRAINT pk_ct PRIMARY KEY (ct_id)
);
COMMENT ON TABLE ct IS 'Access original: CT';

-- ------------------------------------------------------------
-- Transformadores
-- ------------------------------------------------------------
CREATE TABLE transformadores (
    tr_ct_id INTEGER,
    tr_id INTEGER NOT NULL,
    tr_potencia INTEGER,
    CONSTRAINT pk_transformadores PRIMARY KEY (tr_id)
);
COMMENT ON TABLE transformadores IS 'Access original: Transformadores';


-- ============================================================
-- CLAVES FORÁNEAS - Relaciones formales (MSysRelationships)
-- ============================================================

-- MUNICIPIOS.id_municipio → CODIGOS POSTALES.id_municipio
ALTER TABLE municipios ADD CONSTRAINT fk_municipios_id_municipio
    FOREIGN KEY (id_municipio) REFERENCES codigos_postales (id_municipio)
    DEFERRABLE INITIALLY DEFERRED;

-- MUNICIPIOS.id_provincia → PROVINCIAS.id_provincia
ALTER TABLE municipios ADD CONSTRAINT fk_municipios_id_provincia
    FOREIGN KEY (id_provincia) REFERENCES provincias (id_provincia)
    DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.ID BENEFICIARIA → Beneficiaria.ID
ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_id_beneficiaria
    FOREIGN KEY (id_beneficiaria) REFERENCES beneficiaria (id)
    DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.ID GESTORA → Gestora.ID
ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_id_gestora
    FOREIGN KEY (id_gestora) REFERENCES gestora (id)
    DEFERRABLE INITIALLY DEFERRED;

-- EXPROPIADOS.IDEXPE → EXPEDIENTES.IDE
ALTER TABLE expropiados ADD CONSTRAINT fk_expropiados_idexpe
    FOREIGN KEY (idexpe) REFERENCES expedientes (ide)
    DEFERRABLE INITIALLY DEFERRED;

-- REQUERIMIENTOS.IDEXPEDIENTE → EXPEDIENTES.IDE
ALTER TABLE requerimientos ADD CONSTRAINT fk_requerimientos_idexpediente
    FOREIGN KEY (idexpediente) REFERENCES expedientes (ide)
    DEFERRABLE INITIALLY DEFERRED;

-- EXPROPIADOSFINCAS.IDEXPROPIADOS → EXPROPIADOS.ID
ALTER TABLE expropiadosfincas ADD CONSTRAINT fk_expropiadosfincas_idexpropiados
    FOREIGN KEY (idexpropiados) REFERENCES expropiados (id)
    DEFERRABLE INITIALLY DEFERRED;

-- EXPROPIADOSFINCAS.IDFINCAS → FINCAS.ID
ALTER TABLE expropiadosfincas ADD CONSTRAINT fk_expropiadosfincas_idfincas
    FOREIGN KEY (idfincas) REFERENCES fincas (id)
    DEFERRABLE INITIALLY DEFERRED;

-- ORGANISMOSAFECTADOS.IDORGANISMO → organismos.id
ALTER TABLE organismosafectados ADD CONSTRAINT fk_organismosafectados_idorganismo
    FOREIGN KEY (idorganismo) REFERENCES organismos (id)
    DEFERRABLE INITIALLY DEFERRED;


-- ============================================================
-- CLAVES FORÁNEAS IMPLÍCITAS - confirmadas por el usuario
-- Verificar antes de activar:
--   SELECT COUNT(*) FROM legacy.hijo
--   WHERE fk IS NOT NULL AND fk NOT IN (SELECT pk FROM legacy.padre)
-- ============================================================

-- AYUNTAMIENTOSAFECTADOS.IDEXPEDIENTE → EXPEDIENTES.IDE
-- ALTER TABLE ayuntamientosafectados ADD CONSTRAINT fk_ayuntamientosafectados_idexpediente
--     FOREIGN KEY (idexpediente) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- AYUNTAMIENTOSDESCONOCIDOS.IDEXPEDIENTE → EXPEDIENTES.IDE
-- ALTER TABLE ayuntamientosdesconocidos ADD CONSTRAINT fk_ayuntamientosdesconocidos_idexpediente
--     FOREIGN KEY (idexpediente) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- ALEGACIONES EXPROPIADOS.IDEXPE → EXPEDIENTES.IDE
-- ALTER TABLE alegaciones_expropiados ADD CONSTRAINT fk_alegaciones_expropiados_idexpe
--     FOREIGN KEY (idexpe) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- FINCAS.IDEXPE → EXPEDIENTES.IDE
-- ALTER TABLE fincas ADD CONSTRAINT fk_fincas_idexpe
--     FOREIGN KEY (idexpe) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- LINEAS.li_idexp → EXPEDIENTES.IDE
-- ALTER TABLE lineas ADD CONSTRAINT fk_lineas_li_idexp
--     FOREIGN KEY (li_idexp) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- CT.ct_idexp → EXPEDIENTES.IDE
-- ALTER TABLE ct ADD CONSTRAINT fk_ct_ct_idexp
--     FOREIGN KEY (ct_idexp) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- ORGANISMOSAFECTADOS.IDEXPEDIENTE → EXPEDIENTES.IDE
-- ALTER TABLE organismosafectados ADD CONSTRAINT fk_organismosafectados_idexpediente
--     FOREIGN KEY (idexpediente) REFERENCES expedientes (ide)
--     DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.id firmante → FIRMANTES.id firmante
-- ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_id_firmante
--     FOREIGN KEY (id_firmante) REFERENCES firmantes (id_firmante)
--     DEFERRABLE INITIALLY DEFERRED;

-- ALEGACIONES EXPROPIADOS.IDEXPROPIADO → EXPROPIADOS.ID
-- ALTER TABLE alegaciones_expropiados ADD CONSTRAINT fk_alegaciones_expropiados_idexpropiado
--     FOREIGN KEY (idexpropiado) REFERENCES expropiados (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- Transformadores.tr_ct_id → CT.ct_id
-- ALTER TABLE transformadores ADD CONSTRAINT fk_transformadores_tr_ct_id
--     FOREIGN KEY (tr_ct_id) REFERENCES ct (ct_id)
--     DEFERRABLE INITIALLY DEFERRED;

-- LINEAS.li_tension → TENSION_LI.ID
-- ALTER TABLE lineas ADD CONSTRAINT fk_lineas_li_tension
--     FOREIGN KEY (li_tension) REFERENCES tension_li (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- LINEAS.li_tipo → TIPO_LI.id
-- ALTER TABLE lineas ADD CONSTRAINT fk_lineas_li_tipo
--     FOREIGN KEY (li_tipo) REFERENCES tipo_li (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- LINEAS.li_conductor → CONDUCTORES_LI.id
-- ALTER TABLE lineas ADD CONSTRAINT fk_lineas_li_conductor
--     FOREIGN KEY (li_conductor) REFERENCES conductores_li (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- LINEAS.li_apoyos → APOYOS_LI.id
-- ALTER TABLE lineas ADD CONSTRAINT fk_lineas_li_apoyos
--     FOREIGN KEY (li_apoyos) REFERENCES apoyos_li (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- CT.ct_tipo → TIPO_CT.id
-- ALTER TABLE ct ADD CONSTRAINT fk_ct_ct_tipo
--     FOREIGN KEY (ct_tipo) REFERENCES tipo_ct (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- CT.ct_relacion → RELACION_CT.id
-- ALTER TABLE ct ADD CONSTRAINT fk_ct_ct_relacion
--     FOREIGN KEY (ct_relacion) REFERENCES relacion_ct (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- CT.ct_composicion → COMPOSICION_CT.id
-- ALTER TABLE ct ADD CONSTRAINT fk_ct_ct_composicion
--     FOREIGN KEY (ct_composicion) REFERENCES composicion_ct (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- Transformadores.tr_potencia → POTENCIA_CT.ID
-- ALTER TABLE transformadores ADD CONSTRAINT fk_transformadores_tr_potencia
--     FOREIGN KEY (tr_potencia) REFERENCES potencia_ct (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.ID DIARIO → DIARIO.ID
-- ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_id_diario
--     FOREIGN KEY (id_diario) REFERENCES diario (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.ID DIARIO RUP → DIARIO.ID
-- ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_id_diario_rup
--     FOREIGN KEY (id_diario_rup) REFERENCES diario (id)
--     DEFERRABLE INITIALLY DEFERRED;

-- EXPEDIENTES.iID DIARIO2 → DIARIO.ID
-- ALTER TABLE expedientes ADD CONSTRAINT fk_expedientes_iid_diario2
--     FOREIGN KEY (iid_diario2) REFERENCES diario (id)
--     DEFERRABLE INITIALLY DEFERRED;


-- ============================================================
-- ÍNDICES sobre columnas FK
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_municipios_id_municipio ON municipios (id_municipio);
CREATE INDEX IF NOT EXISTS idx_municipios_id_provincia ON municipios (id_provincia);
CREATE INDEX IF NOT EXISTS idx_expedientes_id_beneficiaria ON expedientes (id_beneficiaria);
CREATE INDEX IF NOT EXISTS idx_expedientes_id_gestora ON expedientes (id_gestora);
CREATE INDEX IF NOT EXISTS idx_expropiados_idexpe ON expropiados (idexpe);
CREATE INDEX IF NOT EXISTS idx_requerimientos_idexpediente ON requerimientos (idexpediente);
CREATE INDEX IF NOT EXISTS idx_expropiadosfincas_idexpropiados ON expropiadosfincas (idexpropiados);
CREATE INDEX IF NOT EXISTS idx_expropiadosfincas_idfincas ON expropiadosfincas (idfincas);
CREATE INDEX IF NOT EXISTS idx_organismosafectados_idorganismo ON organismosafectados (idorganismo);
CREATE INDEX IF NOT EXISTS idx_ayuntamientosafectados_idexpediente ON ayuntamientosafectados (idexpediente);
CREATE INDEX IF NOT EXISTS idx_ayuntamientosdesconocidos_idexpediente ON ayuntamientosdesconocidos (idexpediente);
CREATE INDEX IF NOT EXISTS idx_alegaciones_expropiados_idexpe ON alegaciones_expropiados (idexpe);
CREATE INDEX IF NOT EXISTS idx_fincas_idexpe ON fincas (idexpe);
CREATE INDEX IF NOT EXISTS idx_lineas_li_idexp ON lineas (li_idexp);
CREATE INDEX IF NOT EXISTS idx_ct_ct_idexp ON ct (ct_idexp);
CREATE INDEX IF NOT EXISTS idx_organismosafectados_idexpediente ON organismosafectados (idexpediente);
CREATE INDEX IF NOT EXISTS idx_expedientes_id_firmante ON expedientes (id_firmante);
CREATE INDEX IF NOT EXISTS idx_alegaciones_expropiados_idexpropiado ON alegaciones_expropiados (idexpropiado);
CREATE INDEX IF NOT EXISTS idx_transformadores_tr_ct_id ON transformadores (tr_ct_id);
CREATE INDEX IF NOT EXISTS idx_lineas_li_tension ON lineas (li_tension);
CREATE INDEX IF NOT EXISTS idx_lineas_li_tipo ON lineas (li_tipo);
CREATE INDEX IF NOT EXISTS idx_lineas_li_conductor ON lineas (li_conductor);
CREATE INDEX IF NOT EXISTS idx_lineas_li_apoyos ON lineas (li_apoyos);
CREATE INDEX IF NOT EXISTS idx_ct_ct_tipo ON ct (ct_tipo);
CREATE INDEX IF NOT EXISTS idx_ct_ct_relacion ON ct (ct_relacion);
CREATE INDEX IF NOT EXISTS idx_ct_ct_composicion ON ct (ct_composicion);
CREATE INDEX IF NOT EXISTS idx_transformadores_tr_potencia ON transformadores (tr_potencia);
CREATE INDEX IF NOT EXISTS idx_expedientes_id_diario ON expedientes (id_diario);
CREATE INDEX IF NOT EXISTS idx_expedientes_id_diario_rup ON expedientes (id_diario_rup);
CREATE INDEX IF NOT EXISTS idx_expedientes_iid_diario2 ON expedientes (iid_diario2);

-- ============================================================
-- VERIFICACIÓN DE INTEGRIDAD (ejecutar antes de activar FK)
-- Detecta huérfanos en relaciones implícitas
-- ============================================================

-- EXPROPIADOS huérfanos sin expediente
-- SELECT COUNT(*) FROM legacy.expropiados WHERE idexpe IS NOT NULL AND idexpe NOT IN (SELECT ide FROM legacy.expedientes);

-- FINCAS huérfanas sin expediente
-- SELECT COUNT(*) FROM legacy.fincas WHERE idexpe IS NOT NULL AND idexpe NOT IN (SELECT ide FROM legacy.expedientes);

-- AYUNTAMIENTOSAFECTADOS huérfanos
-- SELECT COUNT(*) FROM legacy.ayuntamientosafectados WHERE idexpediente IS NOT NULL AND idexpediente NOT IN (SELECT ide FROM legacy.expedientes);

-- LINEAS huérfanas sin expediente
-- SELECT COUNT(*) FROM legacy.lineas WHERE li_idexp IS NOT NULL AND li_idexp NOT IN (SELECT ide FROM legacy.expedientes);

-- CT huérfanos sin expediente
-- SELECT COUNT(*) FROM legacy.ct WHERE ct_idexp IS NOT NULL AND ct_idexp NOT IN (SELECT ide FROM legacy.expedientes);

-- ORGANISMOSAFECTADOS huérfanos
-- SELECT COUNT(*) FROM legacy.organismosafectados WHERE idexpediente IS NOT NULL AND idexpediente NOT IN (SELECT ide FROM legacy.expedientes);

-- ALEGACIONES sin expediente válido
-- SELECT COUNT(*) FROM legacy.alegaciones_expropiados WHERE idexpe IS NOT NULL AND idexpe NOT IN (SELECT ide FROM legacy.expedientes);

-- ALEGACIONES sin expropiado válido
-- SELECT COUNT(*) FROM legacy.alegaciones_expropiados WHERE idexpropiado IS NOT NULL AND idexpropiado NOT IN (SELECT id FROM legacy.expropiados);

-- Transformadores sin CT válido
-- SELECT COUNT(*) FROM legacy.transformadores WHERE tr_ct_id IS NOT NULL AND tr_ct_id NOT IN (SELECT ct_id FROM legacy.ct);
