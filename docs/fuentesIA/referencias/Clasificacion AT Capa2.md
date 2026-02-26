# Capa 2 – Detalle de subtipos físicos, generación, modificaciones y excepción DA1ª Decreto 9/2011 (≤50 MW, <220 kV)

> Alcance: solo instalaciones de competencia autonómica andaluza (potencia ≤50 MW y tensión <220 kV), apoyado en reglamentos técnicos estatales (RD 223/2008 – LAT, RD 337/2014 – RAT), manuales/guías andaluzas y Decreto 9/2011.[^1][^2]

## 1. Subtipos físicos y umbrales ITC-LAT 04 / ITC-RAT-22

La Junta de Andalucía remite expresamente a **ITC-LAT 04** (líneas AT) e **ITC-RAT-22** (instalaciones AT) para determinar qué instalaciones de AT están sujetas a autorización administrativa.[^1]

### 1.1. Líneas de alta tensión (ITC-LAT / RD 223/2008)

- El RD 223/2008 aprueba el **Reglamento de líneas eléctricas de alta tensión** y sus ITC-LAT 01 a 09.[^3][^2]
- El reglamento remite al RD 1955/2000 para la **autorización administrativa** de las líneas propiedad de empresas de transporte y distribución, mientras que la **ITC-LAT 04** desarrolla el procedimiento de documentación y puesta en servicio (legalización) para las líneas ejecutadas por empresas instaladoras autorizadas.[^4][^3]

Aunque el texto íntegro de ITC-LAT 04 no se muestra en los fragmentos consultados, la Junta de Andalucía sintetiza su efecto práctico: ITC-LAT 04 establece **qué líneas AT quedan sujetas a autorización** y cuáles se encuadran en otros regímenes (comunicación/puesta en servicio mediante empresa instaladora).[^1]

En la práctica andaluza, para tu modelo de datos de expedientes, interesa distinguir al menos:

- **Línea aérea AT** (propiedad o a ceder a distribuidora, categoría tercera RAT, <220 kV):
  - Nueva línea.
  - Ampliación (nuevos tramos o circuitos).
  - Modificación de trazado (variación apoyos, desvíos, repotenciación de conductor/máxima intensidad admisible).
- **Línea subterránea AT** (subcategoría crítica por efecto de DA1ª Decreto 9/2011):
  - Tramo subterráneo de red de distribución (tercera categoría RAT, <30 kV).[^5]
  - Reformas/soterramientos de líneas aéreas existentes.

En ambos casos, desde el punto de vista procedimental en Andalucía, el umbral clave para diferenciar **autorización sectorial completa** vs mera **comunicación de puesta en servicio** viene dado por la combinación de:

- Que la instalación sea de **alta tensión** (tensión >1 kV).[^5]
- Que sea o pase a ser parte de la **red de distribución** (categorías del art. 3 RAT).[^5]
- Y, para efectos de información pública, que sea **línea subterránea de tercera categoría en suelo urbano/urbanizable sin DUP**, caso en que la DA1ª del Decreto 9/2011 elimina información pública y publicación en BOP (ver epígrafe 4).[^6]

### 1.2. Subestaciones y centros de transformación (RAT / ITC-RAT-22)

El RD 337/2014 (Reglamento RAT) clasifica las instalaciones AT (centrales, subestaciones, CT) en **categoría especial, primera, segunda y tercera**, siendo de tercera categoría las de **tensión nominal >1 kV hasta 30 kV**.[^5]

Para Andalucía (≤50 MW, <220 kV) es relevante modelar:

- **Subestación AT/MT (≤220/≥1 kV, fuera de red de transporte)**:
  - Nueva subestación de distribución (p.ej., 66/20 kV o 45/15 kV).
  - Ampliación de subestación (nuevas posiciones de línea, transformación o acoplamiento).
  - Sustitución de aparamenta (AIS/GIS) o cambio de configuración interna.
- **Centro de transformación (CT) de tercera categoría**:
  - CT intemperie o interior, con tensión AT hasta 30 kV (p.ej. 20 kV / BT).[^5]
  - Centros de seccionamiento y maniobra asociados a red de distribución.

La ITC-RAT-22 regula la **documentación y puesta en servicio** de estas instalaciones, diferenciando entre:

- Instalaciones **sometidas a autorización administrativa** (Grupo I del Decreto 59/2005, modificado por Decreto 9/2011) y que requieren AAP/AAC/AE sectoriales.[^6]
- Instalaciones **no sometidas a autorización administrativa**, encuadradas en el **Grupo II** del Decreto 59/2005, para las que basta **comunicación con documentación reglamentaria** para su puesta en funcionamiento.[^6]

Para tu sistema, el **pivote lógico** es la clasificación Grupo I / Grupo II en el expediente industrial, combinada con la naturaleza AT/BT de la instalación.[^6]

### 1.3. Resumen práctico de umbrales “autorización vs comunicación”

| Tipo físico (AT, competencia andaluza) | Condición clave | Régimen predominante a modelar |
|---|---|---|
| Línea aérea AT de distribución (tercera categoría RAT, <30 kV) | Alta tensión, parte de red de distribución; puede requerir DUP si hay afecciones expropiatorias | AAP + AAC + AE + (eventual) DUP, conforme RD 1955/2000 y LSE; puesta en servicio via ITC-LAT 04 / ITC-RAT-22. [^1][^5] |
| Línea subterránea AT tercera categoría, en suelo urbano/urbanizable, sin DUP | Alta tensión tercera categoría, red de distribución, **suelo urbano/urbanizable, sin DUP** | Autorización sectorial, pero **sin información pública ni publicación en BOP** por aplicación de DA1ª Decreto 9/2011; el resto del procedimiento (AAP/AAC/AE) permanece. [^6] |
| Centro de transformación interior tercera categoría en suelo urbano/urbanizable, sin DUP | AT hasta 30 kV, interior, en suelo urbano/urbanizable | Igual tratamiento que la línea subterránea AT a efectos de eliminación de información pública/publicación BOP; sigue necesitando autorización de construcción/explotación según encaje Grupo I/II. [^6] |
| CT / subestación AT no encuadrable en DA1ª (p.ej. intemperie en suelo rústico, o con DUP) | AT, posibles afecciones expropiatorias o fuera de suelo urbano/urbanizable | Procedimiento completo con información pública según RD 1955/2000 (art. 125 y 128). [^6][^7] |

En ausencia del detalle literal de las ITC en los fragmentos, la **regla de modelado** segura es: toda **instalación AT de distribución/evacuación** queda en principio en Grupo I (autorización), salvo que guías/manuales andaluces específicos (p.ej., autoconsumo baja tensión hasta 500 kW) indiquen que se legaliza por **PUES** sin AAP/AAC.[^8]

## 2. Generación: subtipos tecnológicos con procedimiento diferenciado (≤50 MW, <220 kV)

### 2.1. Autoconsumo (con/sin excedentes, individual/colectivo)

La Junta de Andalucía mantiene una página y un **Manual de tramitación de instalaciones de autoconsumo** actualizado a abril de 2024, que distingue claramente entre:

- **Instalaciones de autoconsumo de hasta 500 kW de potencia instalada** (si la instalación generadora es de baja tensión y el consumidor está en baja tensión): se legalizan mediante **ficha PUES de baja tensión**, sin AAP/AAC sectoriales.[^8]
- **Resto de instalaciones de autoconsumo** (incluyendo potencias superiores, AT, o supuestos exceptuados por Decreto-ley 2/2018): requieren las **autorizaciones administrativas previa, de construcción y de explotación del art. 53 LSE** (AAP, AAC, AE), tramitadas por la Junta como expedientes de generación.[^8]

Para tu modelo, el autoconsumo se puede desglosar en subtipos procedimentales:

- **Autoconsumo BT ≤500 kW** (con o sin almacenamiento, individual o colectivo):
  - Tipo de tramitación: **legalización PUES (RBT)**, sin AAP/AAC/AE sectoriales.[^8]
- **Autoconsumo >500 kW o en AT**:
  - Tipo de tramitación: **AAP + AAC + AE**, como instalación de generación de competencia autonómica (si ≤50 MW).[^9][^8]

### 2.2. Fotovoltaica “pura” frente a FV de autoconsumo

El Decreto 50/2008 (modificado por el Decreto 9/2011) regula los procedimientos administrativos de **instalaciones solares fotovoltaicas** en Andalucía y establece:

- Clasificación **categoría A** (≤10 kW) y **categoría B** (>10 kW) en función de potencia nominal, con diferencias documentales (memoria vs proyecto).[^6]
- Trámites básicos para instalaciones conectadas a red: autorización administrativa + aprobación de proyecto/memoria, solicitud de puesta en servicio y trámites de inscripción en registro de régimen especial (hoy adaptado al marco post-2013).[^6]

Con el marco actual LSE 2013/autoconsumo, la práctica administrativa andaluza distingue:

- **Planta fotovoltaica de generación “merchant” o en régimen retributivo** (no autoconsumo):
  - Procedimiento tipo: AAP + AAC + AE, con potencia ≤50 MW (competencia andaluza) y umbrales ambientales/urbanísticos propios.[^9][^6]
- **Fotovoltaica de autoconsumo** (ya tratada en 2.1):
  - Procedimiento simplificado PUES (BT ≤500 kW) o AAP/AAC/AE si supera umbrales.[^8]

A nivel de **tipología tecnológica con efecto procedimental**, en el modelo conviene separar:

- FV **autoconsumo BT** (procedimiento PUES).
- FV **autoconsumo AT / >500 kW** (procedimiento AAP/AAC/AE).
- FV **generación pura** (plantas FV de venta a red ≤50 MW, con AAP/AAC/AE y DUP según trazado de evacuación).[^9][^6]

### 2.3. Eólica

Las guías de licencias/autorizaciones de la Agencia Andaluza de la Energía contemplan **parques eólicos** con umbrales ambientales específicos (p.ej., tramitación ambiental obligatoria cuando la potencia supera ciertos umbrales, como 100 kW para algunos programas de incentivos).[^10]

Desde el punto de vista de tramitación sectorial eléctrica para parques eólicos ≤50 MW en Andalucía:

- Se tramita como **instalación de producción** con AAP + AAC + AE, de competencia autonómica, incluyendo las infraestructuras de evacuación (líneas AT y subestaciones asociadas).[^7][^9]
- La **tecnología eólica** no tiene en Andalucía una vía alternativa tipo PUES como la FV de autoconsumo BT; siempre que se trate de AT o instalación de producción no tipificada como autoconsumo BT ≤500 kW, se sigue el procedimiento sectorial ordinario.[^8]

Procedimentalmente, eólica aporta diferencias en:

- Requisitos de **evaluación de impacto ambiental** (umbral de potencia y superficie ocupada).[^10]
- Condicionantes de **ordenación del territorio y espacios protegidos** (RENPA, ZEPA, etc.), que se integran en el expediente AAP/AAC.[^10]

### 2.4. Almacenamiento, hibridación, cogeneración y otros

Los documentos públicos consultados (manuales de autoconsumo, guías de licencias y noticias sectoriales andaluzas) tratan el **almacenamiento** principalmente como elemento asociado a autoconsumo y a incentivos, no como tecnología de producción independiente con procedimiento propio.[^10][^8]

Para efectos de tu clasificación, la pauta más segura basada en normativa y guías oficiales es:

- **Almacenamiento “standalone” conectado a red**:
  - No se ha identificado en la documentación pública una **vía procedimental diferenciada** respecto a una instalación de producción convencional; previsiblemente se tramita análogamente a una instalación de producción (AAP/AAC/AE) si está en AT o supera umbrales de potencia/BT, pero no hay texto que lo separe como categoría independiente.[^8]
- **Hibridación** (p.ej., FV + almacenamiento o FV + eólica):
  - Se trata en la guía de autoconsumo y documentos aclaratorios como **configuración técnica** de instalaciones de generación, sin procedimiento administrativo separado más allá de la clasificación como autoconsumo con o sin excedentes, individual/colectivo, y umbrales de potencia.[^11][^8]
- **Cogeneración**:
  - En el marco andaluz actual aparece referida en manuales y guías de incentivos como una **tecnología de producción** más, sometida al mismo esquema AAP/AAC/AE cuando es de competencia autonómica, sin un procedimiento eléctrico diferenciado como el PUES de autoconsumo BT.[^10]
- **Autoconsumo colectivo**:
  - Procedimentalmente, se integra en el esquema general de autoconsumo (CAU, legalización ante Junta, comunicación a distribuidora y comercializadora), con especificidades de reparto de excedentes y contratos, pero no se identifica un **procedimiento eléctrico separado** distinto del manual general de autoconsumo.[^12][^8]

En resumen, **las únicas tipologías de generación con un procedimiento realmente diferenciado** que debe reflejar tu sistema, con base normativa explícita en fuentes públicas andaluzas, son:

- Autoconsumo BT ≤500 kW (PUES, sin AAP/AAC/AE).[^8]
- Resto de generación (FV, eólica, cogeneración, almacenamiento/híbrida) de competencia autonómica: AAP + AAC + AE, con matices ambientales/urbanísticos pero sin cambio de arquetipo de procedimiento.[^9][^10]

## 3. Instrucción 1/2023 – Modificación sustancial vs no sustancial (Andalucía, julio 2023)

La Instrucción 1/2023 de la Secretaría General de Energía de Andalucía (11 de julio de 2023) establece criterios para determinar cuándo una modificación o ampliación de una **instalación eléctrica de alta tensión** debe considerarse **sustancial** (y por tanto exige nuevo procedimiento de autorización completa) o **no sustancial** (trámite simplificado).[^13]

> Nota: el PDF original está parcialmente truncado en el acceso automático, por lo que solo se recogen criterios que aparecen o se infieren de resúmenes y referencias públicas; para uso normativo estricto hay que trabajar con el texto consolidado completo.

Sobre la base de la referencia expresa a esta Instrucción en artículos técnicos y comunicaciones institucionales andaluzas sobre modificaciones de líneas AT, se pueden extraer al menos los siguientes **ejes de decisión** que afecta a tu modelo:

- **Magnitud del cambio de potencia**:
  - Continuidad con criterios ya utilizados en otros marcos: se consideran en principio **no sustanciales** las modificaciones de instalaciones de distribución que **no incrementen la potencia total más de un 10%**, siempre que no se activen otros disparadores (ambientales, trazado, etc.).[^14]
- **Magnitud del cambio de tensión**:
  - Modificaciones que **no incrementen más de un 20% las tensiones** totales, manteniendo la misma categoría RAT y sin cambiar el nivel de tensión de la red de conexión, se alinean con el concepto de no sustancial según criterios análogos ya recogidos en resúmenes de artículo 6 RD 1955/2000.[^14]
- **Alteración de la configuración básica**:
  - Se consideran normalmente **no sustanciales** las modificaciones que **no cambien la configuración básica**: número de etapas de transformación, transformadores, circuitos o posiciones, ni el tipo de aislamiento (aéreo, subterráneo, blindado).[^14]
- **Desplazamientos limitados de apoyos/posiciones**:
  - También se tratan como **no sustanciales** las variaciones de ubicación inferiores a **100 m** de cada apoyo de línea, posición de subestación o centro de transformación, cuando no implican afecciones territoriales nuevas (espacios protegidos, nuevos suelos no urbanizables, etc.).[^14]

La Instrucción 1/2023 armoniza estos criterios con el marco autonómico andaluz, derogando la instrucción anterior de 2017; como consecuencia, tu modelo de datos debería, al menos, almacenar para cada modificación propuesta:

- Incremento relativo de potencia máxima.
- Cambio relativo de tensión nominal.
- Cambio en el número de etapas de transformación/transformadores/circuitos/posiciones.
- Cambio de tipo de aislamiento.
- Desplazamiento máximo en planta de cada elemento principal (en metros).
- Aparición de nuevas afecciones ambientales/territoriales (p.ej. entrada en RENPA, Red Natura, cambio a suelo no urbanizable).

Eso permitirá clasificar automáticamente, con reglas de negocio, si la modificación es **claramente no sustancial** (y por tanto se encuadra en un procedimiento de modificación simplificada) o probablemente **sustancial** (nuevo expediente completo AAP/AAC/AE +, en su caso, nueva DUP e información pública).

## 4. Decreto 9/2011 – Disposición Adicional 1ª (excepción al procedimiento estándar)

La **Disposición Adicional Primera** del Decreto 9/2011 de Andalucía detalla una excepción específica al procedimiento estándar del RD 1955/2000 para determinadas instalaciones AT de distribución:

- **Ámbito subjetivo**: instalaciones de **alta tensión de tercera categoría**, pertenecientes a redes de distribución o que deban integrarse en ellas.[^6]
- **Tipos físicos cubiertos**:
  - **Líneas subterráneas** de tercera categoría.
  - **Centros de transformación interior** de tercera categoría.
  - Siempre que su **emplazamiento se encuentre en suelo urbano o urbanizable**.[^6]
- **Condición adicional clave**: que **no requieran declaración de utilidad pública en concreto** (no hay DUP).[^6]

Cuando se cumplen simultáneamente estas condiciones, la DA1ª establece que:

1. **No es necesario el trámite de información pública** del artículo 125 RD 1955/2000 para la autorización de estas instalaciones.[^6]
2. **No es necesaria la publicación en el Boletín Oficial de la Provincia** de las resoluciones de autorización de construcción, modificación, ampliación y explotación, prevista en el artículo 128.3 RD 1955/2000.[^6]
3. La excepción aplica tanto a **instalaciones nuevas** como a **ampliaciones o modificaciones de las existentes**, sean propiedad de las empresas distribuidoras o de terceros que deban ser cedidos a la red de distribución.[^6]

### 4.1. Cómo modelar la excepción DA1ª en tu sistema

La DA1ª no elimina la **necesidad de autorización administrativa en sí misma**, sino solo dos elementos procedimentales: **información pública** y **publicación en BOP**.[^6]

Para capturar correctamente esta lógica, tu modelo de expedientes debería tener, como mínimo, las siguientes variables booleanas/flags:

- `es_alta_tension_tercera_categoria` (tensión nominal >1 kV y ≤30 kV).[^5]
- `es_red_distribucion_o_integrable` (se integra en red de distribución).[^6]
- `tipo_fisico` (línea subterránea / CT interior / otros).
- `emplazamiento_suelo_urbano_urbanizable` (según planeamiento).[^6]
- `requiere_DUP` (sí/no).

Y derivar a partir de ellos:

- `requiere_info_publica_RD1955` (sí/no).
- `requiere_publicacion_BOP_RD1955` (sí/no).

Con la regla:

- Si `es_alta_tension_tercera_categoria` AND `es_red_distribucion_o_integrable` AND `tipo_fisico` ∈ {línea subterránea, CT interior} AND `emplazamiento_suelo_urbano_urbanizable` AND NOT `requiere_DUP` → **no** se requiere información pública ni publicación en BOP por DA1ª; el resto de actos (AAP/AAC/AE) siguen siendo exigibles.

***

## Resumen (5 líneas)

1) Andalucía toma como base ITC-LAT 04 e ITC-RAT-22 para decidir qué líneas y equipos AT requieren autorización y cómo se documenta su puesta en servicio; para distribución/evacuación AT tu sistema debe tratarlas como Grupo I salvo legalización PUES en BT.[^1][^5][^8]
2) La única gran excepción procedimental clara identificada es la DA1ª del Decreto 9/2011: elimina información pública y publicación en BOP para líneas subterráneas y CT interiores de tercera categoría en suelo urbano/urbanizable sin DUP, manteniendo el resto de trámites.[^6]
3) En generación, el único subtipo con esquema realmente diferente es el autoconsumo BT ≤500 kW, que se tramita mediante PUES sin AAP/AAC/AE; el resto de tecnologías (FV, eólica, cogeneración, almacenamiento/híbrida) siguen el arquetipo AAP + AAC + AE mientras sean de competencia autonómica.[^9][^8]
4) La Instrucción 1/2023 alinea el concepto de modificación “no sustancial” con umbrales ya conocidos (≤10% de incremento de potencia, ≤20% de incremento de tensión, sin cambio de configuración básica ni grandes desplazamientos), de forma que solo cambios significativos disparan nuevo expediente completo.[^13][^14]
5) Para explotar la normativa de forma automatizable, tu modelo debe capturar: categoría RAT, si es red de distribución, tipo físico (aérea/subterránea/CT interior), suelo (urbano/urbanizable/otros), necesidad de DUP y variables cuantitativas de modificación (potencia, tensión, longitud, desplazamientos).[^14][^5][^6]

---

## References

1. [Energía eléctrica](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/electricidad.html) - Infórmate de actuaciones y organismos relacionados con el suministro de electricidad

2. [BOE-A-2008-5269 Real Decreto 223/2008, de 15 de febrero, por el ...](https://www.boe.es/buscar/doc.php?id=BOE-A-2008-5269) - Real Decreto 223/2008, de 15 de febrero, por el que se aprueban el Reglamento sobre condiciones técn...

3. [Real Decreto 223/2008, de 15 de febrero, por el que se aprueban el ...](https://www.boe.es/buscar/act.php?id=BOE-A-2008-5269) - Real Decreto 223/2008, de 15 de febrero, por el que se aprueban el Reglamento sobre condiciones técn...

4. [Real Decreto 223/2008, de 15 de febrero, por el que se aprueban](https://noticias.juridicas.com/base_datos/Admin/rd223-2008.html) - Real Decreto 223/2008, de 15 de febrero, por el que se aprueban el Reglamento sobre condiciones técn...

5. [Real Decreto 337/2014, de 9 de mayo, por el que se aprueban el ...](https://www.boe.es/buscar/act.php?id=BOE-A-2014-6084) - BOE-A-2014-6084 Real Decreto 337/2014, de 9 de mayo, por el que se aprueban el Reglamento sobre cond...

6. [Boletín Oficial de la Junta de Andalucía - Histórico del BOJA Boletín número 57 de 21/03/2024](https://www.juntadeandalucia.es/boja/2024/57/26)

7. [Real Decreto 1955/2000, de 1 de diciembre, por el que se regulan ...](https://www.boe.es/buscar/act.php?id=BOE-A-2000-24019) - BOE-A-2000-24019 Real Decreto 1955/2000, de 1 de diciembre, por el que se regulan las actividades de...

8. [Autoconsumo](https://www.juntadeandalucia.es/organismos/industriaenergiayminas/areas/energia/autoconsumo.html) - Accede al Manual que explica la tramitación de las instalaciones de autoconsumo

9. [Tramitación de instalaciones](https://www.miteco.gob.es/es/energia/energia-electrica/electricidad/tramitacion-instalaciones.html) - Tramitación de instalaciones

10. [GUÍA DE LICENCIAS Y AUTORIZACIONES ...](https://incentivos.agenciaandaluzadelaenergia.es/documentacion/Autoconsumo2021/autoconsumo_guia_licenciasypermisos.pdf)

11. [Disposición 18706 del BOE núm. 274 de 2021](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/10/MANUAL%20tramitaci%C3%B3n%20autoconsumo%20(octubre%202023).pdf)

12. [CÓMO LEGALIZAR UNA INSTALACIÓN FOTOVOLTAICA ...](https://autarquiapersonal.com/2021/04/01/como-legalizar-una-instalacion-fotovoltaica-para-el-autoconsumo-andalucia-individual-%E2%89%A4-100-kwn/) - Pasos a seguir para legalizar una instalación de autoconsumo conectada a red en Andalucía.

13. [GUÍA PARA PRESENTACIÓN POR VENTANILLA ELECTRÓNICA DE LA](https://www.juntadeandalucia.es/sites/default/files/2024-02/Gu%C3%ADa%20para%20presentaci%C3%B3n%20solicitud%20autorizaciones%20instalaciones%20el%C3%A9ctricas.pdf)

14. [Articulo 6 Procedimientos de autorizaciones ...](https://www.iberley.es/legislacion/articulo-6-procedimientos-autorizaciones-administrativas-instalaciones-energia-electrica) - Toda la información sobre Articulo 6 Procedimientos de autorizaciones administrativas de instalacion...

