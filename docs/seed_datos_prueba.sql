-- ============================================================
-- DATOS DE PRUEBA — 10 Entidades + 10 Expedientes/Proyectos
-- Ejecutar en orden (respetar FKs)
--
-- NOTA: Los signals after_insert de SQLAlchemy NO se disparan
--       desde SQL directo. Se incluyen INSERTs manuales para
--       historico_titulares_expediente.
-- ============================================================

BEGIN;

-- ============================================================
-- 1) ENTIDADES (10)
-- Roles binarios: rol_titular | rol_consultado | rol_publicador
-- ============================================================

-- 110 → titular=1, consultado=1, publicador=0
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES ('B41000001', 'Energías del Sur S.L.', TRUE, TRUE, FALSE, 'info@energiassur.es', '955100001', 'Avda. de la Constitución 10', '41001', TRUE, NOW(), NOW());

-- 111 → titular=1, consultado=1, publicador=1
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES ('A29000002', 'Renovables Andalucía S.A.', TRUE, TRUE, TRUE, 'contacto@renovandalucia.es', '952200002', 'C/ Larios 15', '29001', TRUE, NOW(), NOW());

-- 010 → titular=0, consultado=1, publicador=0
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES ('Q1400000B', 'Confederación Hidrográfica del Guadalquivir', FALSE, TRUE, FALSE, 'consultas@chguadalquivir.es', '957300003', 'Plaza de España s/n', '14001', TRUE, NOW(), NOW());

-- 001 → titular=0, consultado=0, publicador=1
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES ('P1100000E', 'Diputación Provincial de Cádiz', FALSE, FALSE, TRUE, 'bop@dipcadiz.es', '956400004', 'Avda. Ramón de Carranza 11', '11006', TRUE, NOW(), NOW());

-- 011 → titular=0, consultado=1, publicador=1
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES ('P2300000J', 'Diputación Provincial de Jaén', FALSE, TRUE, TRUE, 'bop@dipujaen.es', '953500005', 'Plaza de San Francisco 2', '23001', TRUE, NOW(), NOW());

-- 100 × 5 → titular=1, consultado=0, publicador=0
INSERT INTO public.entidades (nif, nombre_completo, rol_titular, rol_consultado, rol_publicador, email, telefono, direccion, codigo_postal, activo, created_at, updated_at)
VALUES
  ('B18000006', 'Fotovoltaica Granada S.L.',    TRUE, FALSE, FALSE, 'admin@fvgranada.es',   '958600006', 'Gran Vía de Colón 28',        '18001', TRUE, NOW(), NOW()),
  ('B04000007', 'Eólica Almería S.L.',          TRUE, FALSE, FALSE, 'info@eolicaalmeria.es', '950700007', 'Paseo de Almería 50',         '04001', TRUE, NOW(), NOW()),
  ('A21000008', 'Huelva Solar S.A.',            TRUE, FALSE, FALSE, 'solar@huelvasolar.es',  '959800008', 'Avda. Martín Alonso Pinzón 7', '21001', TRUE, NOW(), NOW()),
  ('B14000009', 'Termosolar Córdoba S.L.',      TRUE, FALSE, FALSE, 'info@termocordoba.es',  '957900009', 'C/ Claudio Marcelo 1',         '14003', TRUE, NOW(), NOW()),
  ('A41000010', 'Red Eléctrica Provincial S.A.', TRUE, FALSE, FALSE, 'rep@redprovincial.es', '954000010', 'C/ Imagen 8',                  '41003', TRUE, NOW(), NOW());

-- ============================================================
-- 2) PROYECTOS (10)
-- ============================================================

INSERT INTO public.proyectos (titulo, descripcion, fecha, finalidad, emplazamiento, ia_id)
VALUES
  ('LAAT 220kV SE Alcalá - SE Carmona',
   'Línea aérea de alta tensión a 220kV de doble circuito entre las subestaciones de Alcalá de Guadaíra y Carmona, 32 km de longitud.',
   '2025-03-15', 'Transporte de energía eléctrica', 'TT.MM. Alcalá de Guadaíra y Carmona (Sevilla)', 2),

  ('PSF El Coronil 50 MW',
   'Planta solar fotovoltaica de 50 MW de potencia instalada con seguimiento a un eje y subestación transformadora 30/220kV.',
   '2025-04-20', 'Generación renovable fotovoltaica', 'T.M. El Coronil (Sevilla)', 2),

  ('PE Sierra de Líjar 30 MW',
   'Parque eólico de 10 aerogeneradores de 3 MW cada uno con línea de evacuación subterránea a 30kV.',
   '2025-05-10', 'Generación renovable eólica', 'TT.MM. Algodonales y Olvera (Cádiz)', 1),

  ('SET Distribución Motril 66/20kV',
   'Nueva subestación de distribución 66/20kV con dos transformadores de 40 MVA para refuerzo de la red.',
   '2025-06-01', 'Distribución de energía eléctrica', 'T.M. Motril (Granada)', 5),

  ('LSAT 400kV SE Baza - SE Caparacena',
   'Línea subterránea de alta tensión a 400kV de 85 km entre las subestaciones de Baza y Caparacena.',
   '2025-07-22', 'Transporte de energía eléctrica', 'TT.MM. Baza, Guadix y Granada (Granada)', 1),

  ('PSF Autoconsumo Polígono Juncaril 2 MW',
   'Instalación fotovoltaica de autoconsumo colectivo de 2 MW sobre cubiertas del polígono industrial Juncaril.',
   '2025-08-05', 'Autoconsumo colectivo industrial', 'T.M. Albolote (Granada)', 5),

  ('PE Comarca de Antequera 45 MW',
   'Parque eólico de 15 aerogeneradores de 3 MW con subestación colectora 30/132kV y línea de evacuación.',
   '2025-09-18', 'Generación renovable eólica', 'TT.MM. Antequera y Archidona (Málaga)', 2),

  ('Línea directa 132kV Fábrica Cementos - SE Carboneras',
   'Línea directa aérea a 132kV de 8 km para suministro industrial a fábrica de cementos.',
   '2025-10-30', 'Suministro industrial por línea directa', 'T.M. Carboneras (Almería)', 5),

  ('Red distribución MT 20kV Costa Occidental Huelva',
   'Ampliación red de distribución en media tensión 20kV con 15 km de línea subterránea y 3 centros de transformación.',
   '2025-11-12', 'Distribución de energía eléctrica', 'TT.MM. Lepe, Cartaya e Isla Cristina (Huelva)', 5),

  ('PSF Baena 75 MW + BESS 25 MWh',
   'Planta solar fotovoltaica de 75 MW con sistema de almacenamiento en baterías de 25 MWh y subestación 30/220kV.',
   '2025-12-01', 'Generación renovable fotovoltaica con almacenamiento', 'T.M. Baena (Córdoba)', 2);

-- ============================================================
-- 3) EXPEDIENTES (10) + HISTÓRICO TITULARES
--    Bloque PL/pgSQL para resolver IDs dinámicamente
--    y asignar numero_at gapless.
-- ============================================================

DO $$
DECLARE
  -- IDs de entidades titulares
  v_ent_energias   INTEGER;
  v_ent_renov      INTEGER;
  v_ent_fvgranada  INTEGER;
  v_ent_eolica     INTEGER;
  v_ent_huelva     INTEGER;
  v_ent_termo      INTEGER;
  v_ent_red        INTEGER;

  -- IDs de proyectos
  v_proy_ids       INTEGER[];

  -- Variables del bucle
  v_numero_at      INTEGER;
  v_tipo_exp       INTEGER;
  v_titular        INTEGER;
  v_exp_id         INTEGER;
BEGIN
  -- Resolver IDs de entidades por NIF
  SELECT id INTO v_ent_energias  FROM public.entidades WHERE nif = 'B41000001';
  SELECT id INTO v_ent_renov     FROM public.entidades WHERE nif = 'A29000002';
  SELECT id INTO v_ent_fvgranada FROM public.entidades WHERE nif = 'B18000006';
  SELECT id INTO v_ent_eolica    FROM public.entidades WHERE nif = 'B04000007';
  SELECT id INTO v_ent_huelva    FROM public.entidades WHERE nif = 'A21000008';
  SELECT id INTO v_ent_termo     FROM public.entidades WHERE nif = 'B14000009';
  SELECT id INTO v_ent_red       FROM public.entidades WHERE nif = 'A41000010';

  -- Resolver IDs de los 10 proyectos recién insertados (por fecha)
  SELECT array_agg(id ORDER BY fecha, id)
    INTO v_proy_ids
    FROM public.proyectos
   WHERE titulo IN (
     'LAAT 220kV SE Alcalá - SE Carmona',
     'PSF El Coronil 50 MW',
     'PE Sierra de Líjar 30 MW',
     'SET Distribución Motril 66/20kV',
     'LSAT 400kV SE Baza - SE Caparacena',
     'PSF Autoconsumo Polígono Juncaril 2 MW',
     'PE Comarca de Antequera 45 MW',
     'Línea directa 132kV Fábrica Cementos - SE Carboneras',
     'Red distribución MT 20kV Costa Occidental Huelva',
     'PSF Baena 75 MW + BESS 25 MWh'
   );

  -- Crear 10 expedientes
  FOR i IN 1..10 LOOP
    -- Obtener siguiente numero_at (gapless)
    UPDATE public.contador_numero_at SET valor = valor + 1 RETURNING valor INTO v_numero_at;

    -- Tipo de expediente según proyecto
    v_tipo_exp := CASE i
      WHEN 1 THEN 1   -- Transporte
      WHEN 2 THEN 4   -- Renovable
      WHEN 3 THEN 4   -- Renovable
      WHEN 4 THEN 2   -- Distribución
      WHEN 5 THEN 1   -- Transporte
      WHEN 6 THEN 5   -- Autoconsumo
      WHEN 7 THEN 4   -- Renovable
      WHEN 8 THEN 6   -- LineaDirecta
      WHEN 9 THEN 2   -- Distribución
      WHEN 10 THEN 4  -- Renovable
    END;

    -- Titular según proyecto
    v_titular := CASE i
      WHEN 1 THEN v_ent_red        -- Red Eléctrica Provincial
      WHEN 2 THEN v_ent_energias   -- Energías del Sur
      WHEN 3 THEN v_ent_eolica     -- Eólica Almería
      WHEN 4 THEN v_ent_fvgranada  -- Fotovoltaica Granada
      WHEN 5 THEN v_ent_red        -- Red Eléctrica Provincial
      WHEN 6 THEN v_ent_fvgranada  -- Fotovoltaica Granada
      WHEN 7 THEN v_ent_renov      -- Renovables Andalucía
      WHEN 8 THEN v_ent_termo      -- Termosolar Córdoba
      WHEN 9 THEN v_ent_huelva     -- Huelva Solar
      WHEN 10 THEN v_ent_termo     -- Termosolar Córdoba
    END;

    -- Insertar expediente
    INSERT INTO public.expedientes (numero_at, responsable_id, tipo_expediente_id, heredado, proyecto_id, titular_id)
    VALUES (v_numero_at, NULL, v_tipo_exp, FALSE, v_proy_ids[i], v_titular)
    RETURNING id INTO v_exp_id;

    -- Histórico de titulares (simula el signal after_insert de SQLAlchemy)
    INSERT INTO public.historico_titulares_expediente (expediente_id, titular_id, fecha_desde, motivo)
    VALUES (v_exp_id, v_titular, NOW(), 'INICIAL');

  END LOOP;
END $$;

-- ============================================================
-- 4) SOLICITUDES (1 por expediente, tipos AAP + AAC)
-- ============================================================

INSERT INTO public.solicitudes (expediente_id, entidad_id, fecha_solicitud, estado, observaciones)
SELECT
  e.id,
  e.titular_id,
  (p.fecha + INTERVAL '30 days')::date,
  'EN_TRAMITE',
  'Solicitud inicial de prueba — expediente AT-' || e.numero_at
FROM public.expedientes e
JOIN public.proyectos p ON p.id = e.proyecto_id
WHERE p.titulo IN (
  'LAAT 220kV SE Alcalá - SE Carmona',
  'PSF El Coronil 50 MW',
  'PE Sierra de Líjar 30 MW',
  'SET Distribución Motril 66/20kV',
  'LSAT 400kV SE Baza - SE Caparacena',
  'PSF Autoconsumo Polígono Juncaril 2 MW',
  'PE Comarca de Antequera 45 MW',
  'Línea directa 132kV Fábrica Cementos - SE Carboneras',
  'Red distribución MT 20kV Costa Occidental Huelva',
  'PSF Baena 75 MW + BESS 25 MWh'
)
ORDER BY e.numero_at;

-- Tipos de solicitud: AAP (id=1) + AAC (id=2) para cada solicitud
INSERT INTO public.solicitudes_tipos (solicitudid, tiposolicitudid)
SELECT s.id, 1  -- AAP
FROM public.solicitudes s
WHERE s.observaciones LIKE 'Solicitud inicial de prueba%';

INSERT INTO public.solicitudes_tipos (solicitudid, tiposolicitudid)
SELECT s.id, 2  -- AAC
FROM public.solicitudes s
WHERE s.observaciones LIKE 'Solicitud inicial de prueba%';

COMMIT;
