# Hallazgos DL 2/2018 — Decreto-ley 2/2018, de 26 de junio, de medidas urgentes para el impulso de los proyectos de interés estratégico de Andalucía (Junta de Andalucía)
<!-- Fuente: sedeboja_26974 | Analizado con NotebookLM (prompt cruzado LSE + RD1955 + LPACAP + EIA + D9) | Revisado manualmente -->

### Reglas del Motor de Tramitación (Decreto-ley 2/2018)

| **ID-NN** | Descripción | Tipo_solicitud | Fase_afectada | Condición_activación | Excepción_de | Fuente_legal | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DL2-01** | **Unificación procedimental** bajo el RD 1955/2000 para producción (incl. FV) | AAP, AAC, AE | Todas | Siempre (instalaciones competencia CCAA) | N/A | DA Única.1 | **Complementa a RD1955-01**. Confirma que el Título VII del RD 1955/2000 es el cauce único en Andalucía. |
| **DL2-02** | **Sustitución de AE por Puesta en Servicio** para pequeña potencia | AE | Finalización | `potencia_instalada_mw` ≤ 0.5 (500 kW) AND `es_instalacion_produccion` = true | **LSE-01** (en fase AE) | DA Única.2 | **Supera a LSE-01** en Andalucía por especialidad. Tramitación vía Orden 5/3/2013. |
| **DL2-03** | **Regla anti-fraccionamiento** (Agrupación de instalaciones) | AAP, AAC | Diseño | `tiene_linea_evacuacion_comun` AND `suma_potencia_grupo` > 0.5 MW AND (`misma_ref_catastral` OR `distancia` < 3000m) | **DL2-02** | DA Única.2 | **Restringe a DL2-02**. Obliga a tramitar AAP y AAC completas si hay indicios de fraccionamiento. |
| **DL2-04** | **DR de consultas previas** para agilizar separatas | AAP, AAC | Instrucción | `promotor_presento_dr_consultas` = true | N/A | DA Única.3 | **Complementa a RD1955-04**. La Administración solo envía separatas a los organismos no incluidos en la DR. |
| **DL2-05** | **Verificación de incidencia territorial** (LISTA) | AAP | Admisión | Siempre (instalaciones sometidas a autorización) | N/A | DA Única.4 | **Complementa a RD1955-01**. Obliga a presentar informe o DR de no incidencia según el Reglamento LISTA. |
| **DL2-06** | **Impulso preferente y urgente** para renovables | Todas | Instrucción | `es_instalacion_generacion_renovable` = true AND NOT `regimen_retributivo_especifico` | N/A | Art. 3.2 | **Complementa a LPACAP-01**. Obliga a una tramitación prioritaria ante cualquier administración andaluza. |

---

### 1. Plazos — Días, silencio administrativo y resolución

*   **Silencio Administrativo:** Al remitir al Título VII del RD 1955/2000, se confirma que el silencio es **desestimatorio** para todos los procedimientos.
*   **Plazo de resolución:** El documento no altera los plazos del RD 1955/2000 (3 meses para AAP/AAC), pero impone un deber de **"impulso preferente y urgente"** para proyectos renovables sin régimen retributivo.
*   **Quién resuelve:** Las **Delegaciones Territoriales** (para proyectos en una provincia) o la **Dirección General** competente en energía (proyectos supraprovinciales), conforme a la estructura de delegación vigente en Andalucía.

---

### 2. Variables del ContextAssembler

| Variable | Tipo | Naturaleza | Estado | Norma de origen |
| :--- | :--- | :--- | :--- | :--- |
| `potencia_instalada_mw` | numérico | `dato` | Ya existe (ver **LSE-01**) | DA Única.2 DL 2/2018 |
| `potencia_instalada_mw` | numérico | `dato` | Ya existe (ver LSE-01) | DA Única.2 DL 2/2018 |
| `tiene_linea_evacuacion_comun` | boolean | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.128)** | DA Única.2 DL 2/2018 |
| `suma_potencia_grupo_evacuacion_kw` | numérico | `calculado` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.129)** | DA Única.2 DL 2/2018 |
| `misma_referencia_catastral_grupo` | boolean | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.130)** | DA Única.2.a DL 2/2018 |
| `distancia_minima_instalaciones_grupo_m` | numérico | `dato` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.131)** | DA Única.2.b DL 2/2018 |
| `promotor_presento_dr_consultas` | boolean | `derivado_doc` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.132)** | DA Única.3 DL 2/2018 |
| `requiere_informe_incidencia_territorial` | boolean | `calculado` | **Ya existe (ver NORMATIVA_EXCEPCIONES_AT.md §7)** | DA Única.4 DL 2/2018 |
| `promotor_aporto_doc_incidencia_territorial` | boolean | `derivado_doc` | **Ya existe (ver DISEÑO_CONTEXT_ASSEMBLER.md l.134)** | DA Única.4 DL 2/2018 |

---

### 3. Excepciones y regímenes simplificados

*   **Exención de AE (DA Única.2):** Las instalaciones de producción ≤ 500 kW están exentas de la resolución de autorización de explotación (AE), sustituyéndola por una **puesta en servicio industrial**. Esta excepción es una **ampliación** de la simplificación procedimental iniciada en el Decreto 9/2011.
*   **Declaración Responsable de Consultas (DA Única.3):** Permite al promotor sustituir el trámite de consultas de la Administración mediante la aportación de los pronunciamientos obtenidos directamente. Es una excepción al flujo estándar de instrucción del **RD 1955/2000 (Art. 127 y 131)**.

---

### 4. Contradicciones o complementos (OBLIGATORIA)

*   **Unificación de procedimientos (Complemento a RD1955-01):**
    *   El **RD 1955/2000** es la norma base estatal. El **DL 2/2018 (DA Única.1)** lo adopta formalmente como el cauce único para Andalucía, superando la dualidad que existía con el derogado Decreto 50/2008 para fotovoltaica.
    *   **Prevalencia:** **Gana el DL 2/2018** por ser norma posterior y específica para el territorio andaluz.

*   **Simplificación AE (Contradicción con LSE-01):**
    *   La **LSE (Art. 53.1.c)** exige autorización administrativa de explotación para toda instalación. El **DL 2/2018 (DA Única.2)** la sustituye por puesta en servicio para ≤ 500 kW.
    *   **Prevalencia:** **Gana el DL 2/2018** en Andalucía por ejercicio de competencias de simplificación administrativa.

*   **Tramitación de Consultas (Complemento a RD1955-04):**
    *   El **RD 1955/2000 (Art. 127)** obliga a la administración a enviar separatas. El **DL 2/2018 (DA Única.3)** permite que el promotor aporte los informes (DR), reduciendo la actuación administrativa a los órganos no consultados.
    *   **Prevalencia:** **Consenso normativo**; el DL 2/2018 optimiza el trámite sin contradecir la obligatoriedad del informe previo.

*   **Derogación del Decreto 50/2008:**
    *   El **DL 2/2018 (Art. 1.c)** deroga expresamente el **Decreto 50/2008** (salvo competencias), eliminando cualquier contradicción procedimental previa para instalaciones fotovoltaicas.
    *   **Prevalencia:** **Gana el DL 2/2018** por fecha y rango jerárquico.