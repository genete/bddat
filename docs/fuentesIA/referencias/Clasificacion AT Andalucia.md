# Clasificación legal de instalaciones y expedientes AT (Andalucía)

> Alcance de esta **capa 1**: clasificación base apoyada en Ley 24/2013 (LSE) y RD 1955/2000 (procedimiento sectorial), y en normativa/operativa andaluza publicada (procedimientos y formularios) y reglamentos técnicos estatales que Andalucía declara aplicables en sus trámites.[^1][^2][^3][^4]

## Sección 1: Árbol de tipos de instalación con subtipos

### 1.1. Por función en el sistema eléctrico (LSE / RD 1955/2000)

- **Producción / generación** (incluye sus infraestructuras de evacuación cuando formen parte del proyecto de generación).[^5][^1]
- **Transporte** (red de transporte y sus elementos).[^2]
- **Distribución** (redes e instalaciones destinadas a distribuir energía a consumidores y otros puntos de conexión).[^1]
- **Líneas directas** (conexiones eléctricas directas definidas y reguladas en la normativa sectorial, con autorización en régimen análogo a otras instalaciones).[^6][^1]
- **Acometidas y elementos asociados** (cuando entren en el ámbito de instalaciones autorizables por la CCAA según la propia tramitación andaluza).[^6]

### 1.2. Transporte (según RD 1955/2000, red de transporte)

- **Líneas de tensión ≥ 220 kV**.[^2]
- **Líneas de interconexión internacional** (independientemente de su tensión).[^2]
- **Parques (subestaciones) de tensión ≥ 220 kV**.[^2]
- **Transformadores 400/220 kV**.[^2]
- **Elementos de control de potencia activa/reactiva** conectados a redes de 400 kV y 220 kV (y los conectados a terciarios de transformadores de la red de transporte).[^2]
- **Interconexiones** península–sistemas insulares/extrapeninsulares y conexiones interinsulares.[^2]
- **Otras instalaciones** (cualquier tensión) que se declaren de transporte por planificación.[^2]

> Nota procedimental (Andalucía): en la práctica autonómica, los expedientes típicos tramitados por Delegaciones Territoriales se encuadran en “transporte secundario” y “distribución” por debajo de los umbrales de competencia estatal, y la sede electrónica andaluza explicita la referencia a tensión inferior a 380 kV para ciertos trámites de explotación.[^1][^6]

### 1.3. Distribución y transporte secundario (visión procedimental andaluza)

- **Instalaciones de transporte secundario, distribución y acometidas** de tensión **inferior a 380 kV** (categoría administrativa de tramitación en Andalucía para autorización de explotación).[^6]
- **Instalaciones no propiedad** de empresas de transporte/distribución que **vayan a ser cedidas** a empresas de transporte/distribución (relevante como subtipo procedimental por el destino/titularidad).[^6]

### 1.4. Infraestructuras de evacuación (visión procedimental andaluza)

- **Líneas de evacuación** (como categoría explícita de autorización de explotación en Andalucía).[^6]

### 1.5. Líneas directas (visión procedimental andaluza)

- **Líneas directas conectadas a instalaciones de generación de competencia autonómica** (categoría explícita en Andalucía).[^6]

### 1.6. Tipologías “físicas” (aerial/subterránea/subestación/CT) y base normativa

La Junta de Andalucía indica expresamente que el RD 223/2008 (Reglamento de líneas AT e ITC-LAT) y el RD 337/2014 (Reglamento de instalaciones AT e ITC-RAT) son normativa de referencia en la tramitación autonómica, y que sus ITC (ITC-LAT 04 e ITC-RAT-22) determinan qué instalaciones de AT quedan sujetas a autorización.[^3]

Con esa base (y sin entrar aún en el detalle literal de cada ITC en esta capa), el árbol físico mínimo que conviene modelar en el sistema de expedientes incluye:

- **Líneas eléctricas AT** (aéreas / subterráneas; simple circuito / doble circuito; entrada/salida en subestación; reforma; soterramiento; variación de trazado).[^7][^3]
- **Subestaciones / parques de intemperie o blindados** (nuevas, ampliaciones de posiciones, sustitución de aparamenta, cambios de configuración, nuevas celdas).[^3][^2]
- **Centros de transformación (CT) y centros de seccionamiento** (cuando se encuadren como “centros de transformación y de seccionamiento” en el ámbito autorizable indicado por la LSE).[^5]
- **Instalaciones de generación** (como “instalaciones de producción” en la LSE y en la práctica andaluza de expedientes de autorización previa/construcción).[^8][^5]

> Subtipos relevantes de generación por procedimiento (pendiente de abrir en capa 2): la práctica administrativa distingue al menos por tecnología (p.ej., fotovoltaica) y por magnitudes del proyecto (p.ej., potencia instalada) en resoluciones andaluzas.[^9][^8]

## Sección 2: Lista de tipos de solicitud/autorización con descripción breve

### 2.1. Núcleo de autorizaciones sectoriales (LSE art. 53 y RD 1955/2000)

- **Autorización administrativa previa (AAP)**: habilita sobre el anteproyecto y puede tramitarse coordinadamente con el estudio/procedimiento ambiental, según describe el MITECO al resumir el RD 1955/2000.[^1]
- **Autorización administrativa de construcción (AAC)**: resolución sobre el proyecto de ejecución/constructivo (en Andalucía se tramita como procedimiento específico dentro del modelo normalizado de solicitudes).[^4]
- **Autorización de explotación (AE)**: autorización de puesta en servicio/funcionamiento (Andalucía diferencia procedimientos de explotación para producción y para distribución/transporte secundario, y contempla expresamente evacuación, líneas directas y acometidas <380 kV en el trámite de explotación).[^4][^6]

### 2.2. Otras solicitudes frecuentes (LSE / RD 1955/2000) y su reflejo en Andalucía

- **Declaración, en concreto, de utilidad pública (DUP)**: se tramita para habilitar efectos expropiatorios/servidumbres y aparece en la tramitación conjunta con AAP y AAC en expedientes andaluces publicados en BOE/BOJA.[^10][^11]
- **Autorización de transmisión**: cambio de titularidad (procedimiento autonómico explicitado en el modelo normalizado andaluz).[^4]
- **Autorización de cierre**: cierre de instalaciones (procedimiento autonómico explicitado en el modelo normalizado andaluz).[^4]
- **Modificación / ampliación** (sustancial vs no sustancial): Andalucía dispone criterios y una instrucción específica para la tramitación de modificaciones y ampliaciones de líneas e instalaciones AT.[^7]

### 2.3. Combinaciones y tramitación conjunta (patrones)

- **AAP + AAC**: en Andalucía es común la tramitación conjunta (y su concesión conjunta) para instalaciones de AT.[^12]
- **AAP + AAC + DUP**: también se tramita conjuntamente en expedientes de líneas AT publicados en BOE, citando expresamente la LSE y el RD 1955/2000 para el trámite de información pública.[^11][^10]

## Sección 3: Tabla de variables diferenciadores de procedimiento

| Variable (qué discrimina) | Valores/umbrales típicos que aparecen en norma o práctica citada | Efecto procedimental (cómo cambia el expediente) |
|---|---|---|
| **Ámbito territorial** | Instalaciones que “excedan del ámbito territorial” de una CCAA (o discurran por más de una) frente a las íntegramente ubicadas en Andalucía. [^1][^6] | Determina **competencia** (Estado vs Junta de Andalucía) y, por tanto, órgano sustantivo/tramitador. [^1][^6] |
| **Potencia instalada (generación)** | Umbral de **> 50 MW** para competencia estatal en producción peninsular (incluyendo infraestructuras de evacuación) y supuestos en mar territorial. [^1] | Determina si el expediente de generación lo tramita AGE o CCAA; en Andalucía, por debajo del umbral se tramitan AAP/AAC/AE por Delegaciones. [^1][^8] |
| **Nivel de tensión (red y competencia)** | Red de transporte definida, entre otros, por **líneas ≥ 220 kV** y parques ≥220 kV. [^2] | Ayuda a clasificar la instalación como transporte (con implicaciones de planificación/competencia) frente a otras redes. [^2][^1] |
| **Nivel de tensión (procedimientos autonómicos de explotación)** | La sede andaluza explicita **tensión < 380 kV** para transporte secundario/distribución/acometidas en un procedimiento de explotación. [^6] | Determina el encaje del expediente en procedimientos autonómicos específicos (p.ej., AE para distribución/transporte secundario). [^6] |
| **Tipo de instalación (función)** | Producción, transporte, distribución, líneas directas y evacuación aparecen como categorías sometidas a autorizaciones (puesta en funcionamiento, modificación, transmisión, cierre). [^1][^5][^6] | Determina el “paquete” de autorizaciones (AAP/AAC/AE) y trámites asociados (información pública, condicionados técnicos, etc.). [^1][^10] |
| **Necesidad de pronunciamiento ambiental** | Andalucía declara coordinación órgano sustantivo–ambiental mediante una **Instrucción Conjunta 1/2022** para infraestructuras que lo requieran. [^3] | El expediente puede incorporar o coordinarse con el **procedimiento ambiental** (plazos, hitos, documentación y condicionados). [^3][^1] |
| **Afección expropiatoria / servidumbres** | Tramitación de DUP “en concreto” con relación de bienes y derechos afectados y sometimiento a información pública (LSE y RD citados en expedientes). [^10][^11] | Activa el bloque de **utilidad pública/expropiación/servidumbres** y condiciona publicaciones, notificaciones individualizadas y actas previas. [^10][^11] |
| **Tipo de actuación sobre una instalación existente** | Modificación/ampliación y criterios para “no sustancial” (en Andalucía: instrucción específica y referencia a normativa técnica de líneas AT). [^7] | Puede cambiar si exige AAP/AAC completas o un trámite simplificado, y cómo se documenta y publica. [^7] |
| **Titularidad/destino (cesión)** | Instalaciones “no propiedad” de transportista/distribuidora que “vayan a ser cedidas”. [^6] | Implica requisitos documentales/actores distintos (promotor vs futuro titular), y puede afectar a fases de explotación y entrega. [^6] |

***

## Resumen (5 líneas)

1) La LSE concentra el régimen de autorizaciones para producción, transporte, distribución, líneas directas y operaciones como puesta en funcionamiento, modificación, transmisión y cierre.[^5][^1]
2) El RD 1955/2000 define la red de transporte (p.ej., líneas ≥220 kV) y, junto con la LSE, soporta el esquema AAP + AAC + AE.[^1][^2]
3) En Andalucía, la sede de trámites explicita categorías como transporte secundario/distribución/acometidas <380 kV, líneas directas y evacuación para autorización de explotación.[^6]
4) La DUP se combina frecuentemente con AAP y AAC y desencadena información pública y relación de bienes y derechos afectados.[^10][^11]
5) Variables clave para modelar procedimientos: competencia territorial, potencia (50 MW), niveles de tensión (220 kV/380 kV), necesidad de pronunciamiento ambiental y tipo de actuación (nueva vs modificación).[^7][^3][^1][^2]

**Confirmación requerida**: si la estructura anterior encaja con lo que quieres modelar, confirma y en la siguiente capa se abrirán (con artículos/ITC concretas) los subtipos físicos (línea aérea/subterránea, subestación, CT, etc.) y los criterios de modificación/no sustancial, además de integrar normativa ambiental y urbanística relevante en Andalucía.

---

## References

1. [Tramitación de instalaciones](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/tramitacion-instalaciones.html) - Tramitación de instalaciones

2. [Real Decreto 1955/2000, de 1 de diciembre, por el que se regulan ...](https://www.boe.es/buscar/act.php?id=BOE-A-2000-24019) - BOE-A-2000-24019 Real Decreto 1955/2000, de 1 de diciembre, por el que se regulan las actividades de...

3. [Energía eléctrica](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html) - Infórmate de actuaciones y organismos relacionados con el suministro de electricidad

4. [RESOLUCIÓN DE 13 DE OCTUBRE DE 2023 JUNTA ...](https://web.ingenierosdecadiz.es/secretaria/noticias/17-documentacion/documentacion-tecnica/6804-resolucion-de-13-de-octubre-de-2023-junta-de-andalucia-autorizaciones-de-instalaciones-electricas-2) - Publicada en el Boletín Oficial de Andalucía la

5. [Ley 24/2013, de 26 de diciembre, del Sector Eléctrico](https://www.boe.es/buscar/act.php?id=BOE-A-2013-13645) - BOE-A-2013-13645 Ley 24/2013, de 26 de diciembre, del Sector Eléctrico.

6. [Junta de Andalucía - Autorización de explotación para instalaciones de distribución y transporte secundario, acometidas (](https://www.juntadeandalucia.es/servicios/sede/tramites/procedimientos/detalle/11996.html)

7. [Tramitación de modificaciones y ampliaciones de líneas e ...](https://laadministracionaldia.inap.es/noticia.asp?id=1163455) - Instrucción de 1 de marzo de 2017, de la Dirección General de Industria, Energía y Minas, sobre tram...

8. [Resolución de 17 de noviembre de 2025, de la Delegación ...](https://www.misionandalucia.es/boja/2025/238/25) - ... autorización administrativa previa y autorización administrativa de construcción para la instala...

9. [Boletín Oficial de la Junta de Andalucía - Histórico del BOJA Boletín número 57 de 21/03/2024](https://www.juntadeandalucia.es/boja/2024/57/26)

10. [BOE-B-2025-38575 Resolución de la Delegación Territorial ...](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2025-38575) - Esta autorización administrativa previa y autorización administrativa de construcción se concede de ...

11. [Documento BOE-B-2021-51929](https://www.boe.es/diario_boe/txt.php?id=BOE-B-2021-51929) - BOE-B-2021-51929 Resolución de la Delegación del Gobierno de la Junta de Andalucía en Córdoba por la...

12. [junta de andalucia](https://bop.dipucordoba.es/visor-pdf/16-02-2026/BOP-A-2026-351.pdf)

